"""Post-apply verification.

Checks (each must pass for exit 0):
  1. DSA art. 26 sentinel : 2 occurrences (CGU FR + terms EN)
  2. TVA 293 B mention   : present on privacy-fr, privacy, cookies, terms
  3. LCEN 6.I.2 mention  : present on privacy and cookies
  4. Promesse Producteur sentinel : 3 occurrences (CGU FR, terms EN, producteur)
  5. BS4 parses every HTML cleanly
  6. No duplicate sentinel within a single file
  7. No 'Customer' regression (FR→Convive doctrine)
  8. No proscribed anglicisms (royalty, MVP, startup, launch, utilize, etc.)
"""
from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup

from .constants import SENTINELS

EXPECTED = {
    "dsa_art26": 2,           # conditions-generales + terms
    "promesse_producteur": 3, # conditions-generales + terms + producteur
}

LEGAL_PAGES_TVA = ["privacy-fr/index.html", "privacy/index.html",
                   "cookies/index.html", "terms/index.html"]
LEGAL_PAGES_LCEN = ["privacy/index.html", "cookies/index.html"]

ANGLICISMS_PATTERN = re.compile(
    r"\b(royalty|MVP|startup|launch|soft launch|utilize|hopefully|du coup|au final)\b",
    re.IGNORECASE,
)
CUSTOMER_PATTERN = re.compile(r"\bCustomer\b")

# Pages EN — anglicism audit skipped (English contractual register).
# Memory `feedback_ratio_v35_voix_editoriale`: 'Royalty/Royalties' in EN/DA
# contractual paragraphs are KEEP (standard legal term). Same logic for
# 'launch' as a technical metric label.
EN_ONLY_PAGES = {"terms/index.html", "privacy/index.html"}

# Broken elision after Customer→Convive rename (FR doctrine).
BROKEN_ELISION_PATTERN = re.compile(r"\b(?:[Ll]'|[Dd]')Convive\b")


def _all_html(repo_root: Path) -> list[Path]:
    return [
        p for p in repo_root.rglob("*.html")
        if ".git" not in p.parts and "scripts" not in p.parts
        and "styles" not in p.parts  # style refs are R&D, not in production
    ]


def verify(repo_root: Path, *, log=print) -> int:
    failures: list[str] = []
    html_files = _all_html(repo_root)

    # 1+4. Sentinel counts
    for key, expected_count in EXPECTED.items():
        sentinel = SENTINELS[key]
        count = sum(1 for p in html_files if sentinel in p.read_text(encoding="utf-8"))
        status = "✓" if count == expected_count else "✗"
        log(f"  {status} sentinel {sentinel}: {count} (expected {expected_count})")
        if count != expected_count:
            failures.append(f"sentinel {sentinel}: got {count}, expected {expected_count}")

    # 2. TVA on 4 pages
    for rel in LEGAL_PAGES_TVA:
        full = repo_root / rel
        text = full.read_text(encoding="utf-8")
        ok = "293 B" in text or "art. 293 B" in text
        status = "✓" if ok else "✗"
        log(f"  {status} TVA 293 B in {rel}")
        if not ok:
            failures.append(f"TVA 293 B missing in {rel}")

    # 3. LCEN on 2 pages
    for rel in LEGAL_PAGES_LCEN:
        full = repo_root / rel
        text = full.read_text(encoding="utf-8")
        ok = "6, I, 2°" in text or "6.I.2" in text
        status = "✓" if ok else "✗"
        log(f"  {status} LCEN 6.I.2 in {rel}")
        if not ok:
            failures.append(f"LCEN 6.I.2 missing in {rel}")

    # 5. BS4 sanity
    for p in html_files:
        try:
            BeautifulSoup(p.read_text(encoding="utf-8"), "lxml")
        except Exception as exc:
            failures.append(f"BS4 parse failed for {p}: {exc}")
            log(f"  ✗ BS4 parse failed: {p}")

    # 6. Duplicate sentinels
    for p in html_files:
        text = p.read_text(encoding="utf-8")
        for sentinel in SENTINELS.values():
            count = text.count(sentinel)
            if count > 1:
                failures.append(f"duplicate sentinel {sentinel} in {p} ({count}x)")
                log(f"  ✗ duplicate {sentinel} in {p.relative_to(repo_root)} ({count}x)")

    # 7. Customer residue (excluding HTML comments and code blocks)
    for p in html_files:
        text = p.read_text(encoding="utf-8")
        # strip <!-- comments --> and <code> blocks for the regex
        stripped = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        stripped = re.sub(r"<code[^>]*>.*?</code>", "", stripped, flags=re.DOTALL)
        if CUSTOMER_PATTERN.search(stripped):
            failures.append(f"'Customer' residue in {p.relative_to(repo_root)}")
            log(f"  ✗ 'Customer' residue in {p.relative_to(repo_root)}")

    # 8. Anglicisms (skip EN-only pages — English contractual register valid)
    for p in html_files:
        rel = str(p.relative_to(repo_root))
        if rel in EN_ONLY_PAGES:
            continue
        text = p.read_text(encoding="utf-8")
        # tolerate inside <code> and <!-- -->
        stripped = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        stripped = re.sub(r"<code[^>]*>.*?</code>", "", stripped, flags=re.DOTALL)
        for m in ANGLICISMS_PATTERN.finditer(stripped):
            term = m.group(0)
            failures.append(f"anglicisme '{term}' in {rel}")
            log(f"  ✗ anglicisme '{term}' in {rel}")

    # 9. Broken elision after Customer→Convive rename (FR doctrine).
    for p in html_files:
        text = p.read_text(encoding="utf-8")
        for m in BROKEN_ELISION_PATTERN.finditer(text):
            failures.append(f"élision cassée '{m.group(0)}' in {p.relative_to(repo_root)}")
            log(f"  ✗ élision cassée '{m.group(0)}' in {p.relative_to(repo_root)}")

    if failures:
        log(f"\n✗ {len(failures)} failure(s)")
        for f in failures:
            log(f"  - {f}")
        return 1

    log("\n✓ verify OK — all 8 checks passed")
    return 0
