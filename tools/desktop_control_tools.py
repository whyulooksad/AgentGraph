from __future__ import annotations

import json
import os
import subprocess
import time
import winreg
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP


server = FastMCP("desktop_control")


def _read_reg_value(root: Any, subkey: str, value_name: str = "") -> str | None:
    try:
        with winreg.OpenKey(root, subkey) as key:
            value, _ = winreg.QueryValueEx(key, value_name)
            return str(value)
    except OSError:
        return None


def _list_subkeys(root: Any, subkey: str) -> list[str]:
    try:
        with winreg.OpenKey(root, subkey) as key:
            names: list[str] = []
            index = 0
            while True:
                try:
                    names.append(winreg.EnumKey(key, index))
                    index += 1
                except OSError:
                    break
            return names
    except OSError:
        return []


def _normalize_scheme(scheme: str) -> str:
    normalized = scheme.strip()
    if normalized.endswith(":"):
        normalized = normalized[:-1]
    return normalized.lower()


def launch_app(
    executable: str,
    *,
    arguments: list[str] | None = None,
    cwd: str | None = None,
    wait_seconds: float = 0.0,
) -> dict[str, Any]:
    executable_path = Path(executable)
    if not executable_path.exists():
        raise FileNotFoundError(f"Executable does not exist: {executable}")

    cmd = [str(executable_path), *(arguments or [])]
    process = subprocess.Popen(  # noqa: S603
        cmd,
        cwd=cwd or str(executable_path.parent),
        shell=False,
    )
    if wait_seconds > 0:
        time.sleep(wait_seconds)

    return {
        "launched": True,
        "pid": process.pid,
        "command": cmd,
        "cwd": cwd or str(executable_path.parent),
    }


def open_uri(
    uri: str,
    *,
    wait_seconds: float = 0.0,
) -> dict[str, Any]:
    os.startfile(uri)
    if wait_seconds > 0:
        time.sleep(wait_seconds)
    return {
        "opened": True,
        "uri": uri,
    }


def query_uri_scheme(
    scheme: str,
) -> dict[str, Any]:
    normalized = _normalize_scheme(scheme)
    shell_key = f"{normalized}\\shell\\open\\command"
    command = _read_reg_value(winreg.HKEY_CLASSES_ROOT, shell_key)
    friendly_name = _read_reg_value(winreg.HKEY_CLASSES_ROOT, normalized)
    url_protocol = _read_reg_value(winreg.HKEY_CLASSES_ROOT, normalized, "URL Protocol")

    return {
        "scheme": normalized,
        "registered": command is not None,
        "friendly_name": friendly_name,
        "command": command,
        "url_protocol": url_protocol,
    }


def list_registered_uri_schemes(
    *,
    query: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    names = _list_subkeys(winreg.HKEY_CLASSES_ROOT, "")
    query_normalized = query.casefold() if query else None
    matches: list[dict[str, Any]] = []

    for name in names:
        if query_normalized and query_normalized not in name.casefold():
            continue
        command = _read_reg_value(
            winreg.HKEY_CLASSES_ROOT,
            f"{name}\\shell\\open\\command",
        )
        url_protocol = _read_reg_value(winreg.HKEY_CLASSES_ROOT, name, "URL Protocol")
        if command is None and url_protocol is None:
            continue
        matches.append(
            {
                "scheme": name,
                "friendly_name": _read_reg_value(winreg.HKEY_CLASSES_ROOT, name),
                "command": command,
                "url_protocol": url_protocol,
            }
        )
        if len(matches) >= limit:
            break

    return {
        "schemes": matches,
        "count": len(matches),
    }


def list_processes(
    *,
    name_filter: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    completed = subprocess.run(  # noqa: S603
        ["tasklist", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        check=True,
        encoding="utf-8",
        errors="replace",
    )
    rows: list[dict[str, Any]] = []
    query = name_filter.casefold() if name_filter else None
    for raw_line in completed.stdout.splitlines():
        if not raw_line.strip():
            continue
        columns = next(iter(json.loads(f"[{raw_line}]")), None)
        if columns is None:
            continue
        image_name, pid, session_name, session_num, mem_usage = columns
        if query and query not in image_name.casefold():
            continue
        rows.append(
            {
                "image_name": image_name,
                "pid": int(pid),
                "session_name": session_name,
                "session_num": session_num,
                "mem_usage": mem_usage,
            }
        )
        if len(rows) >= limit:
            break

    return {
        "processes": rows,
        "count": len(rows),
    }


@server.tool(name="launch_app_tool")
def launch_app_tool(
    executable: str,
    arguments: list[str] | None = None,
    cwd: str | None = None,
    wait_seconds: float = 0.0,
) -> dict[str, Any]:
    return launch_app(
        executable,
        arguments=arguments,
        cwd=cwd,
        wait_seconds=wait_seconds,
    )


@server.tool(name="open_uri_tool")
def open_uri_tool(
    uri: str,
    wait_seconds: float = 0.0,
) -> dict[str, Any]:
    return open_uri(uri, wait_seconds=wait_seconds)


@server.tool(name="query_uri_scheme_tool")
def query_uri_scheme_tool(
    scheme: str,
) -> dict[str, Any]:
    return query_uri_scheme(scheme)


@server.tool(name="list_registered_uri_schemes_tool")
def list_registered_uri_schemes_tool(
    query: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    return list_registered_uri_schemes(query=query, limit=limit)


@server.tool(name="list_processes_tool")
def list_processes_tool(
    name_filter: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    return list_processes(name_filter=name_filter, limit=limit)


if __name__ == "__main__":
    import sys

    if "--mcp" in sys.argv:
        server.run()
    else:
        print(
            "usage: python tools/desktop_control_tools.py --mcp\n"
            "This file is primarily intended to run as the desktop_control MCP server."
        )
