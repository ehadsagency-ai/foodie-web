"""Apply patches with sentinel-based idempotency — surgical edition.

Strategy : use BeautifulSoup4 only to LOCATE anchor positions in the
original source; then perform pure-string insertion at the found offsets.
This preserves all original formatting (indentation, self-closing styles,
attribute quoting, comments) and produces minimal unified diffs.

Modes :
  dry_run -> print unified diff per file, do not write
  apply   -> write file (with .bak.<timestamp> backup)

The same payload may be applied to multiple files. Each insert is
sentinel-marked so re-running --apply is a no-op once everything is in
place.
"""
from __future__ import annotations

import difflib
import shutil
import time
from pathlib import Path

from bs4 import BeautifulSoup

from .constants import SENTINELS
from .patches import PATCHES


def _sentinel_present(text: str, sentinel_key: str) -> bool:
    return SENTINELS[sentinel_key] in text


def _line_indent(text: str, line_start: int) -> str:
    """Return the leading whitespace of the line containing line_start."""
    line_end = text.find("\n", line_start)
    if line_end == -1:
        line_end = len(text)
    line = text[line_start:line_end]
    return line[: len(line) - len(line.lstrip())]


def _line_start_offset(text: str, offset: int) -> int:
    """Offset of the start of the line containing the given offset."""
    nl = text.rfind("\n", 0, offset)
    return nl + 1 if nl >= 0 else 0


def _next_line_offset(text: str, offset: int) -> int:
    """Offset just after the next newline at/after offset."""
    nl = text.find("\n", offset)
    return (nl + 1) if nl >= 0 else len(text)


def _indent_payload(payload: str, indent: str) -> str:
    """Indent each non-empty line of payload, preserve trailing newline."""
    lines = payload.splitlines(keepends=True)
    return "".join(indent + ln if ln.strip() else ln for ln in lines)


def _locate_anchor_offset(text: str, soup: BeautifulSoup, finder, position: str) -> int | None:
    """Find textual offset where to insert the payload.

    Strategy : we re-parse with html.parser (preserves source positions
    via sourceline/sourcepos), find the same anchor, and use sourceline
    to compute the offset in the *original* text.
    """
    # Re-parse with html.parser which records sourceline/sourcepos.
    soup_pos = BeautifulSoup(text, "html.parser")
    anchor = finder(soup_pos)
    if anchor is None:
        return None

    sourceline = getattr(anchor, "sourceline", None)
    if sourceline is None:
        return None

    # Walk through text counting newlines until we reach sourceline.
    cur = 0
    for _ in range(sourceline - 1):
        nl = text.find("\n", cur)
        if nl == -1:
            return None
        cur = nl + 1
    line_start = cur
    line_end = text.find("\n", line_start)
    if line_end == -1:
        line_end = len(text)
    line_text = text[line_start:line_end]

    if position == "after":
        # Find the closing tag of the anchor element and insert just after it.
        # For container elements (<h2>...</h2>), find matching close tag.
        # For self-closing or simple cases, end of line is enough.
        return _next_line_offset(text, line_end)
    if position == "before":
        return line_start
    if position == "prepend_into":
        # Insert just after the opening tag's > on this line.
        gt = text.find(">", line_start)
        if gt == -1:
            return None
        # Insert at the start of the next line (typical formatting).
        return _next_line_offset(text, gt)
    if position == "append_into":
        # Find closing tag matching the anchor's tag name. Naive but
        # sufficient for our targets (legal-block, role-sidebar are
        # well-formed simple containers).
        tag_name = anchor.name
        close_token = f"</{tag_name}>"
        # Search forward starting from anchor's line.
        idx = text.find(close_token, line_start)
        if idx == -1:
            return None
        return _line_start_offset(text, idx)
    return None


def apply_patches(
    repo_root: Path,
    *,
    dry_run: bool = True,
    only_file: str | None = None,
    log=print,
) -> dict[str, list[str]]:
    """Apply all patches in PATCHES table.

    Returns a result dict with 'applied', 'skipped', 'errors' lists.
    """
    result = {"applied": [], "skipped": [], "errors": []}

    targets = (
        {only_file: PATCHES[only_file]}
        if only_file and only_file in PATCHES
        else PATCHES
    )

    for rel_path, patches in targets.items():
        full_path = repo_root / rel_path
        if not full_path.is_file():
            result["errors"].append(f"{rel_path}: file not found")
            log(f"✗ {rel_path}: file not found")
            continue

        original = full_path.read_text(encoding="utf-8")
        current = original
        local_changes = 0

        # Re-parse with lxml fresh each iteration since text mutates;
        # alternative would be offset adjustment, but re-parsing is simpler.
        for patch in patches:
            if _sentinel_present(current, patch.sentinel_key):
                result["skipped"].append(f"{rel_path}:{patch.sentinel_key}")
                log(f"  SKIP {rel_path}: {patch.sentinel_key} already present")
                continue

            soup = BeautifulSoup(current, "lxml")
            offset = _locate_anchor_offset(current, soup, patch.finder, patch.position)
            if offset is None:
                msg = f"{rel_path}: anchor not found for {patch.sentinel_key}"
                result["errors"].append(msg)
                log(f"  ✗ {msg}")
                continue

            indent = _line_indent(current, _line_start_offset(current, offset))
            indented = _indent_payload(patch.payload, indent)
            # Ensure trailing newline so the next line stays clean.
            if not indented.endswith("\n"):
                indented += "\n"

            current = current[:offset] + indented + current[offset:]
            log(f"  ✓ {rel_path}: {patch.description}")
            result["applied"].append(f"{rel_path}:{patch.sentinel_key}")
            local_changes += 1

        if local_changes == 0:
            continue

        if dry_run:
            diff = "".join(
                difflib.unified_diff(
                    original.splitlines(keepends=True),
                    current.splitlines(keepends=True),
                    fromfile=f"a/{rel_path}",
                    tofile=f"b/{rel_path}",
                    n=3,
                )
            )
            log(diff if diff else f"  (no textual diff for {rel_path})")
        else:
            ts = time.strftime("%Y%m%d-%H%M%S")
            backup = full_path.with_suffix(full_path.suffix + f".bak.{ts}")
            shutil.copy2(full_path, backup)
            full_path.write_text(current, encoding="utf-8")
            log(f"    written ({local_changes} insert(s)) — backup: {backup.name}")

    return result
