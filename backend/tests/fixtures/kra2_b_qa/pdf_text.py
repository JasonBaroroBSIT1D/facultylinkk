"""Labeled PDF body text for KRA II Criterion B live QA (fictional test data only)."""

from __future__ import annotations

import uuid

QA_TAG = "KRA2-B-QA"


def qa_title(family_key: str) -> str:
    return f"[{QA_TAG}] {family_key} {uuid.uuid4().hex[:8]}"


PATENT_GRANT_SOLE = """
FICTIONAL — FOR SYSTEM TESTING ONLY
Patent Certificate

Title of Invention: QA Solar Desalination Module
Inventor(s): Jason Baroro
Patent No.: QA-PAT-G-{run}
Date of Grant: 2025-07-01
Intellectual Property Office of the Philippines
"""

PATENT_GRANT_CO = """
FICTIONAL — FOR SYSTEM TESTING ONLY
IPOPHL patent certificate

Invention title
QA Co-Invented Filtration Device
Inventor(s)
Jason Baroro; Maria Santos
Registration No.
QA-PAT-CO-{run}
Registration date
2025-07-02
"""

ANNEX_F_CONTRIBUTION = """
FICTIONAL — FOR SYSTEM TESTING ONLY
Certificate of Contribution Form — Intellectual Property (Annex F)
Percentage of Contribution: 40%
Name of Faculty Member: Jason Baroro
Project / Invention: QA Co-Invented Filtration Device
"""

COMM_LOCAL = """
FICTIONAL — FOR SYSTEM TESTING ONLY
Proof of commercialization — local market

Title of work
QA Licensed Water Pump Product
Authors / Faculty
Jason Baroro
Commercialization venue
Local distributor — Metro Manila
Publication / event date
2025-08-01
Patent reference
QA-COMM-PAT-{run}
"""

UM_SOLE = """
FICTIONAL — FOR SYSTEM TESTING ONLY
Utility Model Certificate of Registration

Invention title
QA Utility Model Valve Assembly
Inventor(s)
Jason Baroro
Registration No.
QA-UM-{run}
Registration date
2025-05-10
IPOPHL
"""

ID_SOLE = """
FICTIONAL — FOR SYSTEM TESTING ONLY
Industrial Design Certificate of Registration

Invention title
QA Industrial Design Handle Grip
Inventor(s)
Jason Baroro
Registration / application no.
QA-ID-{run}
Filing / event date
2025-05-15
Issuing organization
Intellectual Property Office of the Philippines (IPOPHL)
"""

SW_NEW_SOLE = """
FICTIONAL — FOR SYSTEM TESTING ONLY
Software copyright certificate

Software title
QA FacultyLink Attendance Module
Developer(s)
Jason Baroro
Copyright registration no.
QA-SW-{run}
Registration date
2025-03-01
Intellectual Property Office of the Philippines
"""

VARIETY_SOLE = """
FICTIONAL — FOR SYSTEM TESTING ONLY
Plant variety registration

Cultivar name
QA High-Yield Test Rice Line 9
Breeder(s)
Jason Baroro
Registration number
QA-VAR-{run}
Date of registration
2025-04-20
"""

FAMILY_TEXT: dict[str, str] = {
    "patent": PATENT_GRANT_SOLE,
    "patent_co": PATENT_GRANT_CO,
    "commercialization": COMM_LOCAL,
    "utility_model": UM_SOLE,
    "industrial_design": ID_SOLE,
    "software": SW_NEW_SOLE,
    "variety": VARIETY_SOLE,
}

FAMILY_INDICATORS: dict[str, str] = {
    "patent": "kra2-b-patent-g-sole",
    "patent_co": "kra2-b-patent-g-co",
    "commercialization": "kra2-b-comm-local",
    "utility_model": "kra2-b-um-sole",
    "industrial_design": "kra2-b-id-sole",
    "software": "kra2-b-sw-new-sole",
    "variety": "kra2-b-variety-sole",
}
