"""ripgrep wrapper. Uses --json output for structured parsing."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .languages import RIPGREP_TYPE
from .models import CodeLocation, SearchHit


class RipgrepError(RuntimeError):
    pass


def search(
    project_root: Path,
    pattern: str,
    *,
    fixed_string: bool = False,
    glob: str | None = None,
    language: str | None = None,
    limit: int = 50,
    case_sensitive: bool = True,
) -> tuple[list[SearchHit], bool]:
    """Run ripgrep and return (hits, truncated).

    Args:
        pattern: Regex (or literal if fixed_string=True).
        glob: Path glob (e.g. "src/**/*.java").
        language: Filter by language using rg --type.
        limit: Max hits to return.
        truncated: True if rg produced more matches than limit.
    """
    cmd = ["rg", "--json", "--no-heading"]
    if fixed_string:
        cmd.append("--fixed-strings")
    if not case_sensitive:
        cmd.append("--ignore-case")
    if glob:
        cmd.extend(["--glob", glob])
    if language:
        rg_type = RIPGREP_TYPE.get(language)
        if rg_type:
            cmd.extend(["--type", rg_type])
    # Read up to limit+1 to detect truncation
    cmd.extend(["--max-count", str(limit + 1)])
    cmd.append(pattern)
    cmd.append(str(project_root))

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except FileNotFoundError as e:
        raise RipgrepError("ripgrep (rg) is not installed or not on PATH") from e
    except subprocess.TimeoutExpired as e:
        raise RipgrepError("ripgrep timed out after 30s") from e

    # rg returns 1 when no matches — that's not an error
    if proc.returncode not in (0, 1):
        raise RipgrepError(
            f"ripgrep failed (exit {proc.returncode}): {proc.stderr.strip()[:500]}"
        )

    hits: list[SearchHit] = []
    for line in proc.stdout.splitlines():
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "match":
            continue
        data = event["data"]
        path = data["path"].get("text") or data["path"].get("bytes", "")
        try:
            rel_path = str(Path(path).relative_to(project_root))
        except ValueError:
            rel_path = path
        line_no = data["line_number"]
        line_text = (data["lines"].get("text") or "").rstrip("\n")

        # The first submatch (if any) is the canonical match span
        submatches = data.get("submatches") or []
        match_text = submatches[0]["match"]["text"] if submatches else None
        column = (submatches[0]["start"] + 1) if submatches else None

        hits.append(
            SearchHit(
                location=CodeLocation(
                    file_path=rel_path,
                    line=line_no,
                    column=column,
                ),
                line_text=line_text.strip(),
                match_text=match_text,
            )
        )

    truncated = len(hits) > limit
    return hits[:limit], truncated
