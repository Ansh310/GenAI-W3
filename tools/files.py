import os
import glob
import difflib

WORKSPACE_ROOT = os.path.abspath(
    os.environ.get("WORKSPACE_ROOT", ".")
)

MAX_READ_CHARS = 12_000


def resolve_path(path: str) -> str:
    """
    Prevent access outside workspace.
    """

    full_path = os.path.abspath(
        os.path.join(WORKSPACE_ROOT, path)
    )

    if not full_path.startswith(WORKSPACE_ROOT):
        raise ValueError(
            f"Path escapes workspace: {path}"
        )

    return full_path


def read_file(
    path: str,
    start_line: int = 1,
    read_lines: int = 200,
) -> dict:
    try:
        full_path = resolve_path(path)

        with open(
            full_path,
            "r",
            encoding="utf-8",
        ) as f:
            lines = f.readlines()

        start_idx = max(0, start_line - 1)
        end_idx = start_idx + read_lines

        chunk = lines[start_idx:end_idx]

        numbered = [
            f"{i}: {line.rstrip()}"
            for i, line in enumerate(
                chunk,
                start=start_line,
            )
        ]

        content = "\n".join(numbered)

        if len(content) > MAX_READ_CHARS:
            content = content[:MAX_READ_CHARS]

        return {
            "path": path,
            "content": content,
            "start_line": start_line,
            "end_line": start_line + len(chunk) - 1,
            "has_more": end_idx < len(lines),
        }

    except Exception as e:
        return {"error": str(e)}


def write_file(
    path: str,
    content: str,
) -> dict:
    try:
        full_path = resolve_path(path)

        os.makedirs(
            os.path.dirname(full_path),
            exist_ok=True,
        )

        with open(
            full_path,
            "w",
            encoding="utf-8",
        ) as f:
            f.write(content)

        return {
            "success": True,
            "path": path,
            "bytes_written": len(content),
        }

    except Exception as e:
        return {"error": str(e)}


def edit_file(
    path: str,
    operation: str,
    start_line: int,
    end_line: int | None = None,
    content: str | None = None,
) -> dict:

    try:
        full_path = resolve_path(path)

        with open(
            full_path,
            "r",
            encoding="utf-8",
        ) as f:
            original_lines = f.readlines()

        lines = original_lines[:]

        start_idx = max(0, start_line - 1)

        if operation == "replace":

            if end_line is None:
                return {
                    "error": "end_line required"
                }

            replacement = (
                content.splitlines(
                    keepends=True
                )
                if content
                else []
            )

            lines[start_idx:end_line] = replacement

        elif operation == "delete":

            if end_line is None:
                return {
                    "error": "end_line required"
                }

            del lines[start_idx:end_line]

        elif operation == "append":

            if content:
                lines.extend(
                    content.splitlines(
                        keepends=True
                    )
                )

        else:
            return {
                "error":
                f"Unknown operation: {operation}"
            }

        with open(
            full_path,
            "w",
            encoding="utf-8",
        ) as f:
            f.writelines(lines)

        diff = "\n".join(
            difflib.unified_diff(
                original_lines,
                lines,
                fromfile="before",
                tofile="after",
                lineterm="",
            )
        )

        return {
            "success": True,
            "operation": operation,
            "path": path,
            "diff": diff[:8000],
        }

    except Exception as e:
        return {"error": str(e)}


def list_files(
    path: str = ".",
    pattern: str = "*",
) -> dict:

    try:
        root = resolve_path(path)

        matches = glob.glob(
            os.path.join(
                root,
                "**",
                pattern,
            ),
            recursive=True,
        )

        files = [
            os.path.relpath(
                f,
                WORKSPACE_ROOT,
            )
            for f in matches
        ]

        return {
            "files": sorted(files)
        }

    except Exception as e:
        return {"error": str(e)}
    

