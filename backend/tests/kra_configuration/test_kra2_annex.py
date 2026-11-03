from kra_configuration.kra2_annex import (
    CRITERION_A_ID,
    KRA2_ID,
    criterion_id_for_indicator,
    indicator_metadata,
    is_kra2_indicator,
    published_kra2_indicator_points,
)


def test_kra2_indicator_detection():
    assert is_kra2_indicator("kra2-a-journal-sole")
    assert criterion_id_for_indicator("kra2-a-journal-sole") == CRITERION_A_ID
    assert not is_kra2_indicator("kra1-c-adviser-sp")


def test_published_points_from_settings():
    settings = {"indicators": {"kra2-a-journal-sole": {"points": 50, "maxPoints": 50}}}
    assert published_kra2_indicator_points("kra2-a-journal-sole", settings) == 50.0


def test_kra2_constants():
    assert KRA2_ID == "kra2"


def test_indicator_metadata_journal():
    meta = indicator_metadata("kra2-a-journal-co")
    assert meta is not None
    assert meta["contribution"] == "declared"
    assert meta["outputFamily"] == "journal"
