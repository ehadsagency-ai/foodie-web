#!/usr/bin/env python3
"""Fix CSS-breaking 'NN <unit>' artifacts injected by auto-typography.

French typography auto-formatters insert ASCII spaces or U+202F narrow
no-break spaces between numbers and units. While correct for prose
('5 % par an', '12 px de marge'), this is INVALID inside CSS, where:

    border-radius: 50 %        -> declaration dropped
    width: 100 %               -> declaration dropped
    border-radius: 2 em        -> dropped, no rounded corners
    gap: 1 em                  -> dropped, layout collapses
    transform: translateX(-50 %) -> keyframe value invalid

This script normalises r'(\\d+)[\\s\\u202f]+(<unit>)' to r'\\1\\2' ONLY
inside <style>...</style> blocks, style="..." attributes, and .css
files. It LEAVES INTACT the HTML body text (where French typography is
correct).

Covers all CSS Values & Units Level 4 absolute and relative units.

Usage :
  python3 scripts/fix_css_units.py            # dry-run report
  python3 scripts/fix_css_units.py --apply    # write
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

UNITS = ['%', 'px', 'em', 'rem', 'ex', 'ch', 'cap', 'ic', 'lh', 'rlh',
         'vh', 'vw', 'vi', 'vb', 'vmin', 'vmax',
         'svh', 'svw', 'lvh', 'lvw', 'dvh', 'dvw',
         'cqw', 'cqh', 'cqi', 'cqb', 'cqmin', 'cqmax',
         'pt', 'pc', 'cm', 'mm', 'Q', 'in',
         'deg', 'rad', 'grad', 'turn',
         's', 'ms',
         'Hz', 'kHz', 'dpi', 'dpcm', 'dppx', 'x', 'fr']

_units = '|'.join(re.escape(u) for u in sorted(UNITS, key=len, reverse=True))
NUM_SP_UNIT = re.compile(rf"(\d+(?:\.\d+)?)[\s ]+({_units})(?=[^a-zA-Z]|$)")
STYLE_BLOCK = re.compile(r"(<style[^>]*>)(.*?)(</style>)", re.DOTALL | re.IGNORECASE)
STYLE_ATTR = re.compile(r'(style\s*=\s*")([^"]*)(")', re.IGNORECASE)


def fix_css_segment(seg: str) -> tuple[str, int]:
    n = [0]
    def sub(m: re.Match) -> str:
        n[0] += 1
        return f"{m.group(1)}{m.group(2)}"
    return NUM_SP_UNIT.sub(sub, seg), n[0]


def fix_html(text: str) -> tuple[str, int]:
    total = [0]
    def fix_block(m):
        body, n = fix_css_segment(m.group(2))
        total[0] += n
        return m.group(1) + body + m.group(3)
    text = STYLE_BLOCK.sub(fix_block, text)
    def fix_attr(m):
        body, n = fix_css_segment(m.group(2))
        total[0] += n
        return m.group(1) + body + m.group(3)
    text = STYLE_ATTR.sub(fix_attr, text)
    return text, total[0]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Normalise CSS num-space-unit (% px em rem etc.)")
    ap.add_argument("--apply", action="store_true", help="Write changes")
    args = ap.parse_args(argv)

    repo = Path(__file__).resolve().parent.parent
    targets = []
    for p in repo.rglob("*.html"):
        if ".git" in p.parts or "scripts" in p.parts:
            continue
        targets.append(p)
    for p in repo.rglob("*.css"):
        if ".git" in p.parts:
            continue
        targets.append(p)

    total = 0
    files = []
    for p in targets:
        text = p.read_text(encoding="utf-8")
        if p.suffix == ".css":
            new, n = fix_css_segment(text)
        else:
            new, n = fix_html(text)
        if n == 0:
            continue
        files.append((str(p.relative_to(repo)), n))
        total += n
        if args.apply:
            p.write_text(new, encoding="utf-8")

    label = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{label}] {total} fixes in {len(files)} files:")
    for rel, n in sorted(files, key=lambda x: -x[1]):
        print(f"  {n:4d}  {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
