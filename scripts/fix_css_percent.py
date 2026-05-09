#!/usr/bin/env python3
"""Fix CSS-breaking '<num> %' artifacts injected by auto-typography.

Some recent edits introduced ` %` (ASCII space) and `\\u202f%` (narrow
no-break space) between numbers and percent signs. In French prose this
is correct typography (« 5 % par an »), but in CSS it is invalid:

    border-radius: 50 %       -> declaration dropped
    width: 100\\u202f%         -> declaration dropped
    transform: translateX(-50 %) -> keyframe value invalid

This script normalises `<num>[\\s\\u202f]+%` to `<num>%` ONLY inside:
  - <style>...</style> blocks
  - style="..." attributes
  - .css files

It LEAVES INTACT the HTML body text (where French typography is correct).

Usage :
  python3 scripts/fix_css_percent.py            # dry-run report
  python3 scripts/fix_css_percent.py --apply    # write
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Match: digits, optional decimal, ASCII space or narrow-no-break space, then %
_NUM_SPACE_PCT = re.compile(r"(\d+(?:\.\d+)?)[\s ]+%")
_STYLE_BLOCK = re.compile(r"(<style[^>]*>)(.*?)(</style>)", re.DOTALL | re.IGNORECASE)
_STYLE_ATTR = re.compile(r'(style\s*=\s*")([^"]*)(")', re.IGNORECASE)


def fix_css_segment(segment: str) -> tuple[str, int]:
    """Replace all <num>[\\s\\u202f]+% with <num>% in a CSS string."""
    count = 0

    def _sub(m: re.Match) -> str:
        nonlocal count
        count += 1
        return f"{m.group(1)}%"

    return _NUM_SPACE_PCT.sub(_sub, segment), count


def fix_html(text: str) -> tuple[str, int]:
    total = 0

    def _fix_style_block(m: re.Match) -> str:
        nonlocal total
        body, n = fix_css_segment(m.group(2))
        total += n
        return m.group(1) + body + m.group(3)

    text = _STYLE_BLOCK.sub(_fix_style_block, text)

    def _fix_style_attr(m: re.Match) -> str:
        nonlocal total
        body, n = fix_css_segment(m.group(2))
        total += n
        return m.group(1) + body + m.group(3)

    text = _STYLE_ATTR.sub(_fix_style_attr, text)
    return text, total


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalise CSS num-space-percent")
    parser.add_argument("--apply", action="store_true", help="Write changes")
    args = parser.parse_args(argv)

    repo = Path(__file__).resolve().parent.parent
    targets: list[Path] = []
    for p in repo.rglob("*.html"):
        if ".git" in p.parts or "scripts" in p.parts:
            continue
        targets.append(p)
    for p in repo.rglob("*.css"):
        if ".git" in p.parts:
            continue
        targets.append(p)

    grand_total = 0
    files_touched: list[tuple[str, int]] = []

    for p in targets:
        text = p.read_text(encoding="utf-8")
        if p.suffix == ".css":
            new_text, n = fix_css_segment(text)
        else:
            new_text, n = fix_html(text)
        if n == 0:
            continue
        files_touched.append((str(p.relative_to(repo)), n))
        grand_total += n
        if args.apply:
            p.write_text(new_text, encoding="utf-8")

    label = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{label}] {grand_total} fix(es) across {len(files_touched)} file(s):")
    for rel, n in sorted(files_touched, key=lambda x: -x[1]):
        print(f"  {n:4d}  {rel}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
