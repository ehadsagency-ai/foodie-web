#!/usr/bin/env python3
"""Fix CSS-breaking artifacts injected by French typography auto-formatters.

Two categories of corruption are handled in a single pass:

1. NBSP-IN-CSS : ANY occurrence of U+202F (NARROW NO-BREAK SPACE) or
   U+00A0 (NO-BREAK SPACE) inside CSS. The CSS Syntax Module Level 3
   recognises ONLY U+0009, U+000A, U+000C, U+000D and U+0020 as
   whitespace. Any other space-like Unicode codepoint causes the
   declaration to be DROPPED. Auto-formatters typically pepper CSS
   with U+202F before semicolons after applying French typography rules
   to *the entire file* :

       display:grid<U+202F>;          -> declaration dropped, no grid
       grid-template-columns:1.4fr 1fr<U+202F>; -> dropped, no columns

   Fix: replace every U+202F and U+00A0 inside CSS contexts with
   regular ASCII space U+0020.

2. NUM-SPACE-UNIT : ASCII space between a number and its unit. Correct
   for prose ('5 % par an'), invalid in CSS:

       border-radius: 50 %        -> declaration dropped
       gap: 1 em                  -> dropped, layout collapses
       transform: translateX(-50 %) -> keyframe value invalid

   Fix: tighten 'NN <unit>' back to 'NN<unit>' for all units in the
   CSS Values & Units Level 4 catalogue.

Both fixes target the same scope:
  - <style>...</style> blocks
  - style="..." attributes
  - .css files

HTML body text is LEFT INTACT (French typography is correct there).

Usage :
  python3 scripts/fix_css_units.py            # dry-run report
  python3 scripts/fix_css_units.py --apply    # write
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

# CSS Values & Units Level 4
UNITS = ['%', 'px', 'em', 'rem', 'ex', 'ch', 'cap', 'ic', 'lh', 'rlh',
         'vh', 'vw', 'vi', 'vb', 'vmin', 'vmax',
         'svh', 'svw', 'lvh', 'lvw', 'dvh', 'dvw',
         'cqw', 'cqh', 'cqi', 'cqb', 'cqmin', 'cqmax',
         'pt', 'pc', 'cm', 'mm', 'Q', 'in',
         'deg', 'rad', 'grad', 'turn',
         's', 'ms',
         'Hz', 'kHz', 'dpi', 'dpcm', 'dppx', 'x', 'fr']

_units = '|'.join(re.escape(u) for u in sorted(UNITS, key=len, reverse=True))
# After NBSP→space normalisation, num-unit gaps appear as U+0020.
NUM_SP_UNIT = re.compile(rf"(\d+(?:\.\d+)?) +({_units})(?=[^a-zA-Z]|$)")
STYLE_BLOCK = re.compile(r"(<style[^>]*>)(.*?)(</style>)", re.DOTALL | re.IGNORECASE)
STYLE_ATTR = re.compile(r'(style\s*=\s*")([^"]*)(")', re.IGNORECASE)

# Unicode codepoints that look like whitespace but are NOT recognised
# by the CSS Syntax Module Level 3 — they make declarations invalid.
NBSP_TARGETS = [' ', ' ']


def fix_css_segment(seg: str) -> tuple[str, int]:
    """Return (cleaned_segment, count_of_fixes)."""
    n = 0
    # Pass 1 : neutralise non-CSS whitespace.
    for nbsp in NBSP_TARGETS:
        n += seg.count(nbsp)
        seg = seg.replace(nbsp, ' ')
    # Pass 2 : tighten num-space-unit (now that all spaces are ASCII).
    def _sub(m: re.Match) -> str:
        nonlocal n
        n += 1
        return f"{m.group(1)}{m.group(2)}"
    seg = NUM_SP_UNIT.sub(_sub, seg)
    return seg, n


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
