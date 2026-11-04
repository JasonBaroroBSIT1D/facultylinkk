"""OCR parser routing for Criterion C creative-work families."""

from __future__ import annotations

import pytest

from documents.kra2_evidence.ocr_extraction import extract_fields_for_indicator

SAMPLES = {
    "kra2-c-acting": """
Title of performance
Hamlet (Guest Role)
Performer
Maria Santos
Performance venue
Cultural Center of the Philippines
Date of performance
March 15, 2025
""",
    "kra2-c-novel-sole": """
Title of literary work
The River Between
Author
Juan Dela Cruz
Publisher
University Press
Publication date
January 10, 2024
""",
    "kra2-c-film": """
Film title
Short Film Project
Director
Ana Reyes
Festival
Cinemalaya Independent Film Festival
Screening date
August 5, 2025
""",
    "kra2-c-visual": """
Title of artwork
Sunrise Over Laguna
Artist
Pedro Artista
Gallery
National Museum of Fine Arts
Exhibition date
June 1, 2025
""",
    "kra2-c-music-comp-sole": """
Title of composition
Suite for Strings
Composer
Lea Musika
Venue
Philippine Philharmonic Orchestra
Date
December 12, 2024
""",
}


@pytest.mark.parametrize("indicator_id,sample_key", [
    ("kra2-c-acting", "kra2-c-acting"),
    ("kra2-c-novel-sole", "kra2-c-novel-sole"),
    ("kra2-c-film", "kra2-c-film"),
    ("kra2-c-visual", "kra2-c-visual"),
    ("kra2-c-music-comp-sole", "kra2-c-music-comp-sole"),
    ("kra2-c-directing", "kra2-c-acting"),
    ("kra2-c-poetry", "kra2-c-novel-sole"),
    ("kra2-c-arch-design", "kra2-c-visual"),
    ("kra2-c-music-prod-sole", "kra2-c-music-comp-sole"),
])
def test_criterion_c_ocr_extracts_core_fields(indicator_id: str, sample_key: str):
    text = SAMPLES[sample_key]
    fields = extract_fields_for_indicator(text, indicator_id)
    assert fields.get("outputTitle")
    assert fields.get("authorsLine")
    assert fields.get("outputVenue")
    assert fields.get("publicationDate")
    assert "publicationReference" not in fields
    assert "registrationNumber" not in fields


def test_invention_heading_not_used_as_creative_title():
    text = """
Invention Title
Widget Patent Application
Title of performance
Actual Play Name
Performer
Jane Doe
Performance venue
City Theater
Date of performance
May 1, 2025
"""
    fields = extract_fields_for_indicator(text, "kra2-c-acting")
    title = (fields.get("outputTitle") or "").casefold()
    assert "invention" not in title
    assert "widget" not in title or "actual" in title
