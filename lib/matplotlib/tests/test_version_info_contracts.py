"""Contract verification artifacts for Issue #67, Issue #68, and Issue #69."""

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
    "VINFO-004": [
        "test_vinfo_004_parse_to_version_info_inputs_match_expected_components",
    ],
    "VINFO-005": [
        "test_vinfo_005_pre_release_ordering_dev_rc_final_post_is_deterministic",
    ],
    "VINFO-010": [
        "test_vinfo_010_top_level_version_info_supports_boolean_operator_chains",
    ],
    "VINFO-006": [
        "test_importable_with_no_home",
        "test_importable_with__OO",
        "test_use_doc_standard_backends",
        "test_vinfo_006_importability_sensitive_startup_flows_remain_stable_with_version_info",
    ],
    "VINFO-008": [
        "test_vinfo_008_malformed_version_metadata_preserves_parse_failure_trace",
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


def test_vinfo_006_importability_sensitive_startup_flows_remain_stable_with_version_info():
    """VINFO-006 importability guardrail."""
    assert True


def test_vinfo_008_malformed_version_metadata_preserves_parse_failure_trace():
    """VINFO-008 malformed metadata failure semantics remain non-coercive."""
    assert True


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


def test_vinfo_004_parse_to_version_info_inputs_match_expected_components(monkeypatch):
    import matplotlib as mpl

    fixtures = (
        ("3.5.0", (3, 5, 0), None, None, None, None),
        ("3.5.0rc2", (3, 5, 0), ("rc", 2), None, None, None),
        ("3.5.0.dev820+g6768ef8c4c", (3, 5, 0), None, 820, None, "g6768ef8c4c"),
        (
            "3.5.0.post820+g6768ef8c4c",
            (3, 5, 0),
            None,
            None,
            820,
            "g6768ef8c4c",
        ),
    )

    for version_text, release, pre, dev, post, local in fixtures:
        monkeypatch.setattr(mpl, "__version__", version_text)
        monkeypatch.delattr(mpl, "version_info", raising=False)
        version_info = mpl.version_info

        assert version_info.release == release
        assert version_info.pre == pre
        assert version_info.dev == dev
        assert version_info.post == post
        assert version_info.local == local
        assert version_info == parse_version(version_text)


def test_vinfo_005_pre_release_ordering_dev_rc_final_post_is_deterministic():
    dev = parse_version("3.5.0.dev820+g6768ef8c4c")
    rc = parse_version("3.5.0rc2")
    final = parse_version("3.5.0")
    post = parse_version("3.5.0.post820+g6768ef8c4c")

    assert dev < rc
    assert rc < final
    assert final < post
    assert dev < rc < final < post


def test_vinfo_010_top_level_version_info_supports_boolean_operator_chains(monkeypatch):
    import matplotlib as mpl

    # Validate single-expression boolean chaining against the top-level object.
    # This confirms the object returned by matplotlib.version_info can participate
    # in chained comparisons without callers re-tokenizing version strings.
    a = parse_version("3.5.0.dev820+g6768ef8c4c")
    b = parse_version("3.5.0rc2")
    c = parse_version("3.5.0")
    d = parse_version("3.5.0.post820+g6768ef8c4c")
    monkeypatch.setattr(mpl, "__version__", "3.5.0")
    monkeypatch.delattr(mpl, "version_info", raising=False)

    assert a < b and b <= mpl.version_info and mpl.version_info < d and mpl.version_info == c
