"""Patch table : per-file list of inserts (anchor + position + payload + sentinel).

Anchors are resolved with BeautifulSoup4.
Position : "after" inserts the payload as next sibling of anchor;
           "before" inserts as previous sibling;
           "prepend_into" inserts as first child of anchor;
           "append_into" inserts as last child of anchor.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from . import constants as C


@dataclass(frozen=True)
class Patch:
    """One sentinel-marked insert into a file."""

    sentinel_key: str
    payload: str  # raw HTML string, must contain the sentinel comment
    finder: Callable  # callable(soup) -> Tag | None
    position: str  # "after" | "before" | "prepend_into" | "append_into"
    description: str  # short human label for logging


# ---------------------------------------------------------------------------
# Anchor finders (BeautifulSoup callables)
# ---------------------------------------------------------------------------

def _find_h2_id(soup, anchor_id: str):
    return soup.find("h2", id=anchor_id)


def _find_legal_block(soup):
    """Return the last <div class='legal-block'> in the document."""
    blocks = soup.find_all("div", class_="legal-block")
    return blocks[-1] if blocks else None


def _find_role_sidebar(soup):
    return soup.find("aside", class_="role-sidebar")


# ---------------------------------------------------------------------------
# Per-file patch table
# ---------------------------------------------------------------------------

PATCHES: dict[str, list[Patch]] = {
    # FR — CGU : DSA art. 26 + Promesse Producteur V0
    "conditions-generales/index.html": [
        Patch(
            sentinel_key="dsa_art26",
            payload=C.DSA_ART26_FR,
            finder=lambda s: _find_h2_id(s, "signalement"),
            position="after",
            description="DSA art. 26 (FR) inserted after H2 #signalement",
        ),
        Patch(
            sentinel_key="promesse_producteur",
            payload=C.PROMESSE_PRODUCTEUR_FR,
            finder=lambda s: _find_h2_id(s, "commande"),
            position="after",
            description="Promesse Producteur V0 (FR) inserted after H2 #commande",
        ),
    ],
    # EN — Terms : DSA art. 26 + TVA + Promesse Producteur V0
    "terms/index.html": [
        Patch(
            sentinel_key="dsa_art26",
            payload=C.DSA_ART26_EN,
            finder=lambda s: _find_h2_id(s, "moderation"),
            position="after",
            description="DSA art. 26 (EN) inserted after H2 #moderation",
        ),
        Patch(
            sentinel_key="tva_293b",
            payload=C.TVA_293B_EN,
            finder=_find_legal_block,
            position="append_into",
            description="TVA 293 B (EN) appended to legal-block",
        ),
        Patch(
            sentinel_key="promesse_producteur",
            payload=C.PROMESSE_PRODUCTEUR_EN,
            finder=lambda s: _find_h2_id(s, "moderation"),
            position="before",
            description="Promesse Producteur V0 (EN) inserted before H2 #moderation",
        ),
    ],
    # FR — Politique de confidentialité : TVA
    "privacy-fr/index.html": [
        Patch(
            sentinel_key="tva_293b",
            payload=C.TVA_293B_FR,
            finder=_find_legal_block,
            position="append_into",
            description="TVA 293 B (FR) appended to legal-block",
        ),
    ],
    # EN — Privacy Policy : TVA + LCEN
    "privacy/index.html": [
        Patch(
            sentinel_key="lcen_6i2",
            payload=C.LCEN_6I2_EN,
            finder=_find_legal_block,
            position="append_into",
            description="LCEN 6.I.2 (EN) appended to legal-block",
        ),
        Patch(
            sentinel_key="tva_293b",
            payload=C.TVA_293B_EN,
            finder=_find_legal_block,
            position="append_into",
            description="TVA 293 B (EN) appended to legal-block",
        ),
    ],
    # Cookies (page bilingue : footer FR canonique) : TVA + LCEN
    "cookies/index.html": [
        Patch(
            sentinel_key="lcen_6i2",
            payload=C.LCEN_6I2_FR,
            finder=_find_legal_block,
            position="append_into",
            description="LCEN 6.I.2 (FR) appended to legal-block",
        ),
        Patch(
            sentinel_key="tva_293b",
            payload=C.TVA_293B_FR,
            finder=_find_legal_block,
            position="append_into",
            description="TVA 293 B (FR) appended to legal-block",
        ),
    ],
    # FR — Page rôle Producteur : Promesse Producteur V0 dans encadré sidebar
    "producteur/index.html": [
        Patch(
            sentinel_key="promesse_producteur",
            payload=C.PROMESSE_PRODUCTEUR_FR,
            finder=_find_role_sidebar,
            position="append_into",
            description="Promesse Producteur V0 (FR) appended to role-sidebar",
        ),
    ],
}
