"""Verbatim editorial texts for compliance inserts.

Each text is sentinel-marked so re-running --apply is idempotent.
Verbatim per Memory rules:
  - feedback_promesse_producteur_v0 (RÈGLE ABSOLUE 2026-05-05)
  - reference_marketplace_legal_doctrine
  - V3.5 cabinet d'avocats register
"""
from __future__ import annotations

SENTINELS: dict[str, str] = {
    "dsa_art26": "v3.5-dsa-art26",
    "tva_293b": "v3.5-tva-293b",
    "lcen_6i2": "v3.5-lcen-6i2",
    "promesse_producteur": "v3.5-promesse-producteur-v0",
}

# DSA art. 26 — Provenance disclosure (Regulation (EU) 2022/2065)
DSA_ART26_FR = """\
<!-- v3.5-dsa-art26 -->
<p><strong>Marqueur de provenance — article 26 du Règlement (UE) 2022/2065 (Digital Services Act).</strong> Conformément à l'article 26 du Digital Services Act, FOODIE identifie de manière claire, sans ambiguïté et en temps réel, l'identité de la personne morale au nom de laquelle chaque contenu, communication commerciale ou publication promotionnelle est diffusé. L'éditeur du service est <strong>la Maison E&amp;HADS Agency</strong> (E&amp;HADS Agency SASU, SIRET 932 700 271 00012, RCS Saintes). Toute communication issue de l'application porte la mention « Édité par la Maison E&amp;HADS Agency ». Tout contenu publié par un Producteur référencé porte la mention de son numéro SIRET et de sa raison sociale.</p>
"""

DSA_ART26_EN = """\
<!-- v3.5-dsa-art26 -->
<p><strong>Provenance disclosure — Article 26 of Regulation (EU) 2022/2065 (Digital Services Act).</strong> In accordance with Article 26 of the Digital Services Act, FOODIE clearly, unambiguously and in real time identifies the legal person on whose behalf each piece of content, commercial communication or promotional publication is disseminated. The publisher of the service is <strong>Maison E&amp;HADS Agency</strong> (E&amp;HADS Agency SASU, SIRET 932 700 271 00012, RCS Saintes, France). All communications originating from the application bear the notice "Published by Maison E&amp;HADS Agency". All content published by a referenced Producer bears the Producer's SIRET number and registered legal name.</p>
"""

# TVA art. 293 B (small business exemption) — short legal-block addendum
TVA_293B_FR = """\
<!-- v3.5-tva-293b -->
<em>Prix nets — TVA non applicable, art. 293 B du CGI.</em><br>
"""

TVA_293B_EN = """\
<!-- v3.5-tva-293b -->
<em>Net prices — VAT not applicable, French CGI art. 293 B (small business exemption).</em><br>
"""

# LCEN art. 6.I.2 (hosting intermediary status)
LCEN_6I2_FR = """\
<!-- v3.5-lcen-6i2 -->
<em>Hébergeur de mise en relation au sens de l'article 6, I, 2°, de la loi n° 2004-575 du 21 juin 2004 (LCEN).</em><br>
"""

LCEN_6I2_EN = """\
<!-- v3.5-lcen-6i2 -->
<em>Hosting intermediary within the meaning of article 6, I, 2° of French law n° 2004-575 of 21 June 2004 (LCEN) and article 14 of the EU e-Commerce Directive 2000/31/EC.</em><br>
"""

# Promesse Producteur V0 — verbatim per memory rule
# Anchor : Code de la consommation L. 122-25 + L. 132-1
PROMESSE_PRODUCTEUR_FR = """\
<!-- v3.5-promesse-producteur-v0 -->
<p class="promesse-producteur"><strong>Promesse Producteur V0 :</strong> en V0 (mise en relation pure, version actuellement publiée), <strong>cent pour cent du règlement va directement au Producteur</strong>, encaissé en main propre lors du retrait sur place. Aucun flux financier ne transite par l'application. <strong>Évolution V1 et au-delà :</strong> à l'introduction du paiement intégré, la part du Producteur restera <strong>majoritaire</strong> et publiée trimestriellement, accompagnée d'un audit par tiers indépendant. Cadre : art. L. 122-25 et L. 132-1 du Code de la consommation.</p>
"""

PROMESSE_PRODUCTEUR_EN = """\
<!-- v3.5-promesse-producteur-v0 -->
<p class="promesse-producteur"><strong>Producer Promise V0:</strong> in V0 (pure matchmaking, currently published version), <strong>one hundred percent of the payment goes directly to the Producer</strong>, collected in person at pickup. No financial flow transits through the application. <strong>V1 and beyond:</strong> when integrated payment is introduced, the Producer's share will remain <strong>majority</strong> and published quarterly, accompanied by an independent third-party audit. Framework: French Consumer Code art. L. 122-25 and L. 132-1.</p>
"""
