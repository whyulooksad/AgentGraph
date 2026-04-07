# Skill: play_music

## Purpose

Use this skill when the user wants the desktop agent to play a song in a desktop music application.

## Execution Rules

1. Identify the target music application and resolve its executable path.
2. Check whether the application exposes a URI scheme, protocol handler, or command-line entry that can open or play content directly.
3. If a direct playback URI or command is available, use it and then verify whether the target process is running as expected.
4. If only application launch is available, launch the application and report clearly that direct song playback control is still missing.
5. If no usable protocol or command is available, stop and report the missing control capability explicitly.

## Constraints

- Do not guess application paths.
- Do not claim playback success without an explicit verification step.
- Prefer `query_uri_scheme`, `list_registered_uri_schemes`, `open_uri`, `launch_app`, and `list_processes`.
- Prefer factual status updates over narrative explanations.
- Keep the final answer concise and execution-oriented.
