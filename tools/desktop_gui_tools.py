from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

try:
    from pywinauto import Application, Desktop
    from pywinauto.base_wrapper import BaseWrapper
except ImportError:  # pragma: no cover - optional runtime dependency
    Application = None
    Desktop = None
    BaseWrapper = Any  # type: ignore[assignment]


server = FastMCP("desktop_gui")
DEFAULT_BACKEND = "uia"


def _ensure_backend() -> None:
    if Application is None or Desktop is None:
        raise RuntimeError(
            "desktop_gui_tools requires `pywinauto`. Install it before using this MCP server."
        )


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _normalize_keys(keys: str) -> str:
    normalized = keys.strip()
    replacements = {
        "{Ctrl+k}": "^k",
        "{Ctrl+l}": "^l",
        "{Ctrl+f}": "^f",
        "{Alt+1}": "%1",
        "{Down}": "{DOWN}",
        "{Up}": "{UP}",
        "{Left}": "{LEFT}",
        "{Right}": "{RIGHT}",
        "{Enter}": "{ENTER}",
        "{Esc}": "{ESC}",
        "{Tab}": "{TAB}",
        "{Space}": " ",
    }
    return replacements.get(normalized, normalized)


def _window_payload(wrapper: BaseWrapper) -> dict[str, Any]:
    try:
        rect = wrapper.rectangle()
        rectangle = {
            "left": rect.left,
            "top": rect.top,
            "right": rect.right,
            "bottom": rect.bottom,
        }
    except Exception:
        rectangle = None

    try:
        process_id = wrapper.process_id()
    except Exception:
        process_id = None

    try:
        class_name = wrapper.class_name()
    except Exception:
        class_name = None

    try:
        control_type = wrapper.element_info.control_type
    except Exception:
        control_type = None

    try:
        automation_id = wrapper.element_info.automation_id
    except Exception:
        automation_id = None

    handle = getattr(wrapper, "handle", None)
    return {
        "handle": int(handle) if handle is not None else None,
        "title": wrapper.window_text(),
        "class_name": class_name,
        "control_type": control_type,
        "automation_id": automation_id,
        "process_id": process_id,
        "rectangle": rectangle,
    }


def _resolve_window(
    *,
    handle: int | None = None,
    title: str | None = None,
    title_re: str | None = None,
) -> BaseWrapper:
    _ensure_backend()
    desktop = Desktop(backend=DEFAULT_BACKEND)

    if handle is not None:
        return desktop.window(handle=handle).wrapper_object()
    if title_re is not None:
        return desktop.window(title_re=title_re).wrapper_object()
    if title is not None:
        return desktop.window(title=title).wrapper_object()
    raise ValueError("One of `handle`, `title`, or `title_re` is required.")


def _child_window_kwargs(
    *,
    control_text: str | None = None,
    auto_id: str | None = None,
    control_type: str | None = None,
    title_re: str | None = None,
    found_index: int | None = None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if control_text is not None:
        kwargs["title"] = control_text
    if auto_id is not None:
        kwargs["auto_id"] = auto_id
    if control_type is not None:
        kwargs["control_type"] = control_type
    if title_re is not None:
        kwargs["title_re"] = title_re
    if found_index is not None:
        kwargs["found_index"] = found_index
    if not kwargs:
        raise ValueError(
            "At least one control selector is required: control_text, auto_id, control_type, or title_re."
        )
    return kwargs


def _resolve_control(
    window: BaseWrapper,
    *,
    control_text: str | None = None,
    auto_id: str | None = None,
    control_type: str | None = None,
    title_re: str | None = None,
    found_index: int | None = None,
) -> BaseWrapper:
    kwargs = _child_window_kwargs(
        control_text=control_text,
        auto_id=auto_id,
        control_type=control_type,
        title_re=title_re,
        found_index=found_index,
    )
    candidates = list(window.descendants())
    matched: list[BaseWrapper] = []
    for candidate in candidates:
        info = getattr(candidate, "element_info", None)
        candidate_title = candidate.window_text()
        candidate_auto_id = getattr(info, "automation_id", None) if info is not None else None
        candidate_control_type = (
            getattr(info, "control_type", None) if info is not None else None
        )

        if "title" in kwargs and candidate_title != kwargs["title"]:
            continue
        if "title_re" in kwargs:
            import re

            if re.search(kwargs["title_re"], candidate_title or "") is None:
                continue
        if "auto_id" in kwargs and candidate_auto_id != kwargs["auto_id"]:
            continue
        if "control_type" in kwargs and candidate_control_type != kwargs["control_type"]:
            continue
        matched.append(candidate)

    if not matched:
        raise RuntimeError(f"No control matched selector: {kwargs}")
    index = kwargs.get("found_index", 0)
    if index >= len(matched):
        raise RuntimeError(
            f"Control selector matched {len(matched)} items, but found_index={index} is out of range."
        )
    return matched[index]


def _tree_node(
    wrapper: BaseWrapper,
    *,
    depth: int,
    max_children: int,
) -> dict[str, Any]:
    node = _window_payload(wrapper)
    node["text"] = wrapper.window_text()
    if depth <= 0:
        return node

    children_payload: list[dict[str, Any]] = []
    try:
        children = wrapper.children()
    except Exception:
        children = []

    for child in children[:max_children]:
        children_payload.append(
            _tree_node(
                child,
                depth=depth - 1,
                max_children=max_children,
            )
        )
    if len(children) > max_children:
        node["truncated_children"] = len(children) - max_children
    node["children"] = children_payload
    return node


def launch_app(
    executable: str,
    *,
    arguments: list[str] | None = None,
    wait_seconds: float = 8.0,
) -> dict[str, Any]:
    _ensure_backend()
    executable_path = Path(executable)
    if not executable_path.exists():
        raise FileNotFoundError(f"Executable does not exist: {executable}")

    cmdline = f'"{executable_path}"'
    if arguments:
        cmdline += " " + " ".join(arguments)

    app = Application(backend=DEFAULT_BACKEND).start(cmdline)
    time.sleep(max(wait_seconds, 0))
    windows = [wrapper for wrapper in app.windows()]
    return {
        "launched": True,
        "cmdline": cmdline,
        "process_id": app.process,
        "windows": [_window_payload(wrapper) for wrapper in windows],
    }


def list_windows(
    *,
    title_filter: str | None = None,
    visible_only: bool = True,
    limit: int = 50,
) -> dict[str, Any]:
    _ensure_backend()
    desktop = Desktop(backend=DEFAULT_BACKEND)
    windows = desktop.windows()
    payload: list[dict[str, Any]] = []
    title_filter_normalized = _normalize_text(title_filter)

    for wrapper in windows:
        if visible_only:
            try:
                if not wrapper.is_visible():
                    continue
            except Exception:
                continue
        title = wrapper.window_text()
        if title_filter_normalized and title_filter_normalized.lower() not in title.lower():
            continue
        payload.append(_window_payload(wrapper))
        if len(payload) >= limit:
            break

    return {"windows": payload, "count": len(payload)}


def focus_window(
    *,
    handle: int | None = None,
    title: str | None = None,
    title_re: str | None = None,
) -> dict[str, Any]:
    wrapper = _resolve_window(handle=handle, title=title, title_re=title_re)
    try:
        wrapper.restore()
    except Exception:
        pass
    wrapper.set_focus()
    return {"focused": True, "window": _window_payload(wrapper)}


def get_accessibility_tree(
    *,
    handle: int | None = None,
    title: str | None = None,
    title_re: str | None = None,
    depth: int = 2,
    max_children: int = 50,
) -> dict[str, Any]:
    wrapper = _resolve_window(handle=handle, title=title, title_re=title_re)
    return {
        "window": _window_payload(wrapper),
        "tree": _tree_node(
            wrapper,
            depth=max(depth, 0),
            max_children=max(max_children, 1),
        ),
    }


def type_text(
    text: str,
    *,
    window_handle: int | None = None,
    window_title: str | None = None,
    window_title_re: str | None = None,
    control_text: str | None = None,
    control_auto_id: str | None = None,
    control_type: str | None = None,
    control_title_re: str | None = None,
    found_index: int | None = None,
    clear_first: bool = True,
    submit: bool = False,
) -> dict[str, Any]:
    window = _resolve_window(
        handle=window_handle,
        title=window_title,
        title_re=window_title_re,
    )
    control = _resolve_control(
        window,
        control_text=control_text,
        auto_id=control_auto_id,
        control_type=control_type,
        title_re=control_title_re,
        found_index=found_index,
    )
    control.set_focus()
    if clear_first:
        try:
            control.set_edit_text("")
        except Exception:
            control.type_keys("^a{BACKSPACE}", set_foreground=True)
    try:
        control.set_edit_text(text)
    except Exception:
        control.type_keys(text, with_spaces=True, set_foreground=True)
    if submit:
        control.type_keys("{ENTER}", set_foreground=True)
    return {
        "typed": True,
        "text": text,
        "window": _window_payload(window),
        "control": _window_payload(control),
    }


def click_control(
    *,
    window_handle: int | None = None,
    window_title: str | None = None,
    window_title_re: str | None = None,
    control_text: str | None = None,
    control_auto_id: str | None = None,
    control_type: str | None = None,
    control_title_re: str | None = None,
    found_index: int | None = None,
    double: bool = False,
) -> dict[str, Any]:
    window = _resolve_window(
        handle=window_handle,
        title=window_title,
        title_re=window_title_re,
    )
    control = _resolve_control(
        window,
        control_text=control_text,
        auto_id=control_auto_id,
        control_type=control_type,
        title_re=control_title_re,
        found_index=found_index,
    )
    control.set_focus()
    if double:
        control.double_click_input()
    else:
        control.click_input()
    return {
        "clicked": True,
        "double": double,
        "window": _window_payload(window),
        "control": _window_payload(control),
    }


def press_key(
    keys: str,
    *,
    window_handle: int | None = None,
    window_title: str | None = None,
    window_title_re: str | None = None,
    control_text: str | None = None,
    control_auto_id: str | None = None,
    control_type: str | None = None,
    control_title_re: str | None = None,
    found_index: int | None = None,
) -> dict[str, Any]:
    window = _resolve_window(
        handle=window_handle,
        title=window_title,
        title_re=window_title_re,
    )
    target = window
    if any(
        value is not None
        for value in (
            control_text,
            control_auto_id,
            control_type,
            control_title_re,
            found_index,
        )
    ):
        target = _resolve_control(
            window,
            control_text=control_text,
            auto_id=control_auto_id,
            control_type=control_type,
            title_re=control_title_re,
            found_index=found_index,
        )
    target.set_focus()
    normalized_keys = _normalize_keys(keys)
    target.type_keys(normalized_keys, set_foreground=True)
    return {
        "pressed": True,
        "keys": normalized_keys,
        "window": _window_payload(window),
        "target": _window_payload(target),
    }


def wait(seconds: float = 1.0) -> dict[str, Any]:
    duration = max(seconds, 0.0)
    time.sleep(duration)
    return {"waited": True, "seconds": duration}


@server.tool()
def launch_app_tool(
    executable: str,
    arguments: list[str] | None = None,
    wait_seconds: float = 8.0,
) -> dict[str, Any]:
    return launch_app(
        executable,
        arguments=arguments,
        wait_seconds=wait_seconds,
    )


@server.tool()
def list_windows_tool(
    title_filter: str | None = None,
    visible_only: bool = True,
    limit: int = 50,
) -> dict[str, Any]:
    return list_windows(
        title_filter=title_filter,
        visible_only=visible_only,
        limit=limit,
    )


@server.tool()
def focus_window_tool(
    handle: int | None = None,
    title: str | None = None,
    title_re: str | None = None,
) -> dict[str, Any]:
    return focus_window(handle=handle, title=title, title_re=title_re)


@server.tool()
def get_accessibility_tree_tool(
    handle: int | None = None,
    title: str | None = None,
    title_re: str | None = None,
    depth: int = 2,
    max_children: int = 50,
) -> dict[str, Any]:
    return get_accessibility_tree(
        handle=handle,
        title=title,
        title_re=title_re,
        depth=depth,
        max_children=max_children,
    )


@server.tool()
def type_text_tool(
    text: str,
    window_handle: int | None = None,
    window_title: str | None = None,
    window_title_re: str | None = None,
    control_text: str | None = None,
    control_auto_id: str | None = None,
    control_type: str | None = None,
    control_title_re: str | None = None,
    found_index: int | None = None,
    clear_first: bool = True,
    submit: bool = False,
) -> dict[str, Any]:
    return type_text(
        text,
        window_handle=window_handle,
        window_title=window_title,
        window_title_re=window_title_re,
        control_text=control_text,
        control_auto_id=control_auto_id,
        control_type=control_type,
        control_title_re=control_title_re,
        found_index=found_index,
        clear_first=clear_first,
        submit=submit,
    )


@server.tool()
def click_control_tool(
    window_handle: int | None = None,
    window_title: str | None = None,
    window_title_re: str | None = None,
    control_text: str | None = None,
    control_auto_id: str | None = None,
    control_type: str | None = None,
    control_title_re: str | None = None,
    found_index: int | None = None,
    double: bool = False,
) -> dict[str, Any]:
    return click_control(
        window_handle=window_handle,
        window_title=window_title,
        window_title_re=window_title_re,
        control_text=control_text,
        control_auto_id=control_auto_id,
        control_type=control_type,
        control_title_re=control_title_re,
        found_index=found_index,
        double=double,
    )


@server.tool()
def press_key_tool(
    keys: str,
    window_handle: int | None = None,
    window_title: str | None = None,
    window_title_re: str | None = None,
    control_text: str | None = None,
    control_auto_id: str | None = None,
    control_type: str | None = None,
    control_title_re: str | None = None,
    found_index: int | None = None,
) -> dict[str, Any]:
    return press_key(
        keys,
        window_handle=window_handle,
        window_title=window_title,
        window_title_re=window_title_re,
        control_text=control_text,
        control_auto_id=control_auto_id,
        control_type=control_type,
        control_title_re=control_title_re,
        found_index=found_index,
    )


@server.tool()
def wait_tool(seconds: float = 1.0) -> dict[str, Any]:
    return wait(seconds)


def main() -> int:
    args = os.sys.argv[1:]
    if args and args[0] == "--mcp":
        server.run()
        return 0

    result = {
        "message": (
            "usage: python tools/desktop_gui_tools.py --mcp\n"
            "This file is primarily intended to run as the desktop_gui MCP server."
        )
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
