from kra_configuration.kra2_indicator_pdf_verification import (
    KRA2_AGGREGATION_FORMULA,
    verification_summary,
)


def test_all_54_indicators_mapped():
    s = verification_summary()
    assert s["total"] == 54
    assert s.get("mismatchCount", 0) == 0


def test_aggregation_formula_documented():
    assert "min(criterion_a + criterion_b + criterion_c" in KRA2_AGGREGATION_FORMULA["formula"]
