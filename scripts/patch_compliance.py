#!/usr/bin/env python3
"""Idempotent compliance patcher for foodie-web (lamaisonfoodie.fr).

Inserts V3.5 doctrine + DSA art. 26 + LCEN 6.I.2 + TVA 293 B + Promesse
Producteur V0 verbatim across legal HTML pages. Sentinel-based: re-run
of --apply is a no-op once everything is in place.

Modes :
  python3 scripts/patch_compliance.py            # dry-run (default)
  python3 scripts/patch_compliance.py --apply    # writes, with .bak.<ts>
  python3 scripts/patch_compliance.py --verify   # post-apply audit (exit 0/1)
  python3 scripts/patch_compliance.py --file <p> # debug single file

Repo root is auto-detected (parent of this script's parent).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# When run as a script, ensure local imports work.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from compliance.runner import apply_patches
from compliance.verify import verify


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Apply V3.5 doctrine + legal disclosures to foodie-web HTML"
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Write changes to disk (default: dry-run)",
    )
    parser.add_argument(
        "--verify", action="store_true",
        help="Run post-apply audits (exit 0 = green-light commit)",
    )
    parser.add_argument(
        "--file", type=str, default=None,
        help="Only process this relative path (e.g. terms/index.html)",
    )
    args = parser.parse_args(argv)

    repo_root = _HERE.parent

    if args.verify:
        return verify(repo_root)

    print(f"  repo: {repo_root}")
    print(f"  mode: {'APPLY (writes)' if args.apply else 'DRY-RUN'}")
    if args.file:
        print(f"  file: {args.file}")
    print()

    result = apply_patches(
        repo_root,
        dry_run=not args.apply,
        only_file=args.file,
    )

    print()
    print(f"  applied : {len(result['applied'])}")
    print(f"  skipped : {len(result['skipped'])}")
    print(f"  errors  : {len(result['errors'])}")

    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
