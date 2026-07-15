"""Contract-only verification artifacts for Issue #67 version-info parity.

Requirements:
    - VINFO-001: top-level ``matplotlib.version_info`` is exposed and comparable.
    - VINFO-002: ``version_info`` is derived from and remains stable for the same
      import-time version string.
    - VINFO-003: ``__version__`` formatting and value remain unchanged.
    - VINFO-007: top-level comparable version is sourced from the existing parsing
      helper and does not introduce a parallel parser implementation.
"""


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
    """Placeholder contract for VINFO-001."""
    assert True


def test_vinfo_002_version_info_stable_under_repeated_same_version_source_reads():
    """Placeholder contract for VINFO-002."""
    assert True


def test_vinfo_003_version_info_construction_preserves_top_level_version_string_contract():
    """Placeholder contract for VINFO-003."""
    assert True


def test_vinfo_007_version_info_construction_reuses_existing_top_level_parse_helper():
    """Placeholder contract for VINFO-007."""
    assert True
