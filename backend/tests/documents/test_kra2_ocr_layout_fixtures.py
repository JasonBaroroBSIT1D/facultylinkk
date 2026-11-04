"""Representative KRA II OCR layouts — per-field extraction accuracy."""

from __future__ import annotations

from documents.kra2_evidence.ocr_extraction import extract_fields_for_indicator

# Each fixture: id, indicator_id, text, expected field fragments (substring match).
LAYOUT_FIXTURES: list[dict] = [
    {
        "id": "journal_inline_colons",
        "indicator_id": "kra2-a-journal-sole",
        "text": """
Title: Machine Learning for Agriculture
Authors: Jason Baroro, Maria Santos
Journal: Journal of Applied Research
Published: March 15, 2024
DOI: 10.1234/jar.2024.001
""",
        "expected": {
            "outputTitle": "Machine Learning",
            "authorsLine": "Jason Baroro",
            "outputVenue": "Applied Research",
            "publicationDate": "2024",
            "publicationReference": "10.1234",
        },
    },
    {
        "id": "journal_fictional_labeled_lines",
        "indicator_id": "kra2-a-journal-sole",
        "text": """
FICTIONAL — FOR SYSTEM TESTING ONLY
Article title
Adaptive Learning Analytics in Introductory STEM Courses
Authors
Alex Rivera; Jamie Cruz
Journal
Journal of Fictional Education Research (TEST)
Publication date
2025-08-15
DOI
10.9999/fictional.kra2a.007
""",
        "expected": {
            "outputTitle": "Adaptive Learning",
            "authorsLine": "Alex Rivera",
            "outputVenue": "Fictional Education",
            "publicationDate": "2025-08-15",
            "publicationReference": "10.9999",
        },
    },
    {
        "id": "journal_table_pipes",
        "indicator_id": "kra2-a-journal-sole",
        "text": """
| Article title | Coastal Resilience Modeling |
| Authors | Dr. Lee; Dr. Kim |
| Journal | Pacific Science Quarterly |
| Publication date | 2024-11-01 |
| DOI | 10.5555/pacific.2024.001 |
""",
        "expected": {
            "outputTitle": "Coastal Resilience",
            "authorsLine": "Lee",
            "outputVenue": "Pacific Science",
            "publicationDate": "2024-11-01",
            "publicationReference": "10.5555",
        },
    },
    {
        "id": "patent_application_labels",
        "indicator_id": "kra2-b-patent-a-sole",
        "text": """
Invention title
Sample Innovation Device 01
Inventor(s)
Jason Baroro; Jamie Cruz
Registration / application no.
FAKE-IP-2025-00001
Filing / event date
2025-02-12
""",
        "expected": {
            "outputTitle": "Sample Innovation",
            "authorsLine": "Jason Baroro",
            "registrationNumber": "FAKE-IP-2025",
            "registrationDate": "2025-02-12",
        },
    },
    {
        "id": "book_chapter_labels",
        "indicator_id": "kra2-a-chapter-sole",
        "text": """
Book title
Advanced Methods in Data Science
Chapter title
Bayesian Methods for Small Samples
Authors
Jordan Reyes
Publisher
Academic Press Examples
Publication date
June 3, 2023
ISBN 978-0-123456-78-9
""",
        "expected": {
            "outputTitle": "Bayesian Methods",
            "authorsLine": "Jordan Reyes",
            "outputVenue": "Academic Press",
            "publicationDate": "2023",
        },
    },
    {
        "id": "creative_exhibition_labels",
        "indicator_id": "kra2-c-music-comp-sole",
        "text": """
Title of creative work
Urban Light Installations (TEST)
Author(s) / creator(s)
Jamie Cruz
Exhibition venue
Metro Art Hall (TEST)
Exhibition date
2025-04-12
""",
        "expected": {
            "outputTitle": "Urban Light",
            "authorsLine": "Jamie Cruz",
            "outputVenue": "Metro Art",
            "publicationDate": "2025-04-12",
        },
    },
    {
        "id": "citation_notice",
        "indicator_id": "kra2-a-cite",
        "text": """
Cited work: Neural Networks in Education
Citation context: Cited in Annual Review of Learning Technology, 2025
DOI: 10.7777/cite.2025.001
""",
        "expected": {
            "outputTitle": "Neural Networks",
            "publicationReference": "10.7777",
        },
    },
]


def _field_hit_rate() -> dict[str, float]:
    totals: dict[str, int] = {}
    hits: dict[str, int] = {}
    for fx in LAYOUT_FIXTURES:
        fields = extract_fields_for_indicator(fx["text"], fx["indicator_id"])
        for key, needle in fx["expected"].items():
            totals[key] = totals.get(key, 0) + 1
            val = (fields.get(key) or "").strip()
            if needle.lower() in val.lower():
                hits[key] = hits.get(key, 0) + 1
    return {k: hits.get(k, 0) / totals[k] for k in totals}


def test_layout_fixtures_minimum_accuracy():
    rates = _field_hit_rate()
    assert rates.get("outputTitle", 0) >= 0.8, rates
    assert rates.get("authorsLine", 0) >= 0.75, rates
    assert rates.get("publicationDate", 0) >= 0.75, rates


def test_each_layout_fixture_individually():
    for fx in LAYOUT_FIXTURES:
        fields = extract_fields_for_indicator(fx["text"], fx["indicator_id"])
        for key, needle in fx["expected"].items():
            val = (fields.get(key) or "").strip()
            assert needle.lower() in val.lower(), f"{fx['id']} missing {key}: got {val!r}"
