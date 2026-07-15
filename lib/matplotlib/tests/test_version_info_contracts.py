"""Contract verification artifacts for Issue #67 version info compatibility."""

from packaging.version import parse as parse_version


VINFO_CONTRACT_MAP = {
    "VINFO-001": [
        "test_vinfo_001_import_side_effects_expose_top_level_matplotlib_version_info_symbol",
    ],
    "VINFO-002": [
        "test_vinfo_002_version_info_stable_under_repeated_same_version_source_reads",
    ],
    "VINFO-003": [
        "test_vinfo_003_version_info_construction_preserves_top_level_version_string_contract",
    ],
    "VINFO-007": [
        "test_vinfo_007_version_info_construction_reuses_existing_top_level_parse_helper",
    ],
}


def test_vinfo_001_import_side_effects_expose_top_level_matplotlib_version_info_symbol():
    import matplotlib as mpl

    assert hasattr(mpl, "version_info")
    assert mpl.version_info == mpl.version_info
    assert mpl.version_info <= mpl.version_info
    assert mpl.version_info >= mpl.version_info
    assert not (mpl.version_info < mpl.version_info)
    assert not (mpl.version_info > mpl.version_info)
    assert mpl.version_info < parse_version("9999")


def test_vinfo_002_version_info_stable_under_repeated_same_version_source_reads():
    import matplotlib as mpl

    first_read = mpl.version_info
    second_read = mpl.version_info

    assert first_read == second_read


def test_vinfo_003_version_info_construction_preserves_top_level_version_string_contract():
    import matplotlib as mpl

    raw_version = mpl.__version__
    _ = mpl.version_info

    assert mpl.__version__ == raw_version
    assert isinstance(raw_version, str)
    assert parse_version(raw_version) == parse_version(mpl.__version__)


def test_vinfo_007_version_info_construction_reuses_existing_top_level_parse_helper(
    monkeypatch,
):
    import matplotlib as mpl

    parse_calls = []

    def tracked_parse(version_text):
        parse_calls.append(version_text)
        return parse_version(version_text)

    monkeypatch.setattr(mpl, "parse_version", tracked_parse)
    monkeypatch.delattr(mpl, "version_info", raising=False)
    version_info = mpl.version_info

    assert parse_calls == [mpl.__version__]
    assert version_info == parse_version(mpl.__version__)
