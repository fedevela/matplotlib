"""Regression coverage for VINFO-001 and VINFO-002 version information contracts."""

import importlib

import matplotlib as mpl


VINFO_REQUIREMENT_VERIFICATIONS = {
    "VINFO-001": [
        "VINFO-001_read_stability_before_after_version_info_access",
        "VINFO-001_version_source_contract_for_version_info_path",
    ],
    "VINFO-002": [
        "VINFO-002_top_level_import_from_matplotlib_version_info_matches_module_version_info",
        "VINFO-002_standard_import_module_exposes_version_info_without_private_imports",
    ],
    "VINFO-003": [
        "VINFO-003_supported_version_forms_parse_to_deterministic_fields",
        "VINFO-003_version_info_fields_stable_across_version_form_reparsing",
        "VINFO-003_supported_version_forms_with_local_metadata_are_order_stable",
    ],
}


def test_VINFO_001_read_stability_before_after_version_info_access():
    """
    Requirement VINFO-001:
    When module import has cached or computed __version__, repeated reads
    before and after version_info access remain stable and string-typed.
    """
    version_before = mpl.__version__
    assert isinstance(version_before, str)

    version_info = mpl.version_info
    assert isinstance(version_info, tuple)

    assert isinstance(mpl.__version__, str)
    assert version_before == mpl.__version__
    assert version_info == mpl.version_info


def test_VINFO_001_version_source_contract_for_version_info_path(monkeypatch):
    """
    Requirement VINFO-001:
    __version__ remains sourced from the existing version source used by current
    module behavior rather than replacing it with a different formatted value.
    """
    original_version = mpl.__version__
    fake_version = "3.10.4rc2"

    monkeypatch.setattr(mpl, "_get_matplotlib_version", lambda: fake_version)
    monkeypatch.delitem(mpl.__dict__, "__version__", raising=False)

    version_info = mpl.version_info
    assert mpl.__version__ == fake_version
    assert isinstance(version_info, tuple)
    assert version_info.major == 3
    assert version_info.minor == 10
    assert version_info.micro == 4
    assert version_info.releaselevel == "candidate"
    assert version_info.serial == 2

    monkeypatch.setitem(mpl.__dict__, "__version__", original_version)


def test_VINFO_002_top_level_import_from_matplotlib_version_info_matches_module_version_info():
    """
    Requirement VINFO-002:
    Direct `from matplotlib import version_info` resolves against the
    package namespace and represents the same top-level value as
    `matplotlib.version_info`.
    """
    from matplotlib import version_info as imported_version_info

    assert imported_version_info == mpl.version_info
    assert imported_version_info is mpl.version_info


def test_VINFO_002_standard_import_module_exposes_version_info_without_private_imports():
    """
    Requirement VINFO-002:
    A standard `import matplotlib` exposes `version_info` on the module object
    without requiring private helper module imports in user-facing code.
    """
    assert hasattr(mpl, "version_info")
    assert "version_info" in mpl.__dict__
    assert isinstance(mpl.version_info, tuple)


def test_VINFO_003_supported_version_forms_parse_to_deterministic_fields():
    """
    Requirement VINFO-003:
    Parse forms in {3.5.0, 3.5.0rc2, 3.5.0.dev820+g6768ef8c4c,
    3.5.0.post820+g6768ef8c4c} into a stable and deterministic structure.
    """
    versions = {
        "3.5.0": {
            "expected": (3, 5, 0, "final", 0, ()),
        },
        "3.5.0rc2": {
            "expected": (3, 5, 0, "candidate", 2, ()),
        },
        "3.5.0.dev820+g6768ef8c4c": {
            "expected": (3, 5, 0, "development", 820, ("g6768ef8c4c",)),
        },
        "3.5.0.post820+g6768ef8c4c": {
            "expected": (3, 5, 0, "post", 820, ("g6768ef8c4c",)),
        },
    }

    for version, expected in versions.items():
        old_getter = mpl._get_matplotlib_version
        try:
            mpl._get_matplotlib_version = lambda version=version: version
            mpl.__dict__.pop("__version__", None)
            mpl.__dict__.pop("version_info", None)
            info = mpl.version_info
            assert info == expected["expected"]
        finally:
            mpl._get_matplotlib_version = old_getter


def test_VINFO_003_version_info_fields_stable_across_version_form_reparsing():
    """
    Requirement VINFO-003:
    Repeated parsing of supported version forms across controlled reload flows
    produces stable major/minor/patch and pre/post/dev/local fields.
    """
    versions = (
        "3.5.0",
        "3.5.0rc2",
        "3.5.0.dev820+g6768ef8c4c",
        "3.5.0.post820+g6768ef8c4c",
    )

    for version in versions:
        old_getter = mpl._get_matplotlib_version
        try:
            # Force a fresh attribute path and reparse in-place twice.
            mpl._get_matplotlib_version = lambda version=version: version
            mpl.__dict__.pop("version_info", None)
            mpl.__dict__.pop("__version__", None)
            first = mpl.version_info

            # Simulate an isolated reload path by reconstructing module state.
            importlib.reload(mpl)
            mpl._get_matplotlib_version = lambda version=version: version
            mpl.__dict__.pop("version_info", None)
            mpl.__dict__.pop("__version__", None)
            second = mpl.version_info

            assert first == second
            assert (
                first.major,
                first.minor,
                first.micro,
                first.releaselevel,
                first.serial,
                first.local,
            ) == (
                second.major,
                second.minor,
                second.micro,
                second.releaselevel,
                second.serial,
                second.local,
            )
        finally:
            mpl._get_matplotlib_version = old_getter
            # Return to imported module state used by other tests.
            mpl.__dict__.pop("__version__", None)
            mpl.__dict__.pop("version_info", None)


def test_VINFO_003_supported_version_forms_with_local_metadata_are_order_stable():
    """
    Requirement VINFO-003:
    Local metadata suffixes such as +g... are represented deterministically and do
    not produce non-deterministic field order.
    """
    version = "3.5.0.dev820+g6768ef8c4c"
    old_getter = mpl._get_matplotlib_version

    try:
        mpl._get_matplotlib_version = lambda: version
        mpl.__dict__.pop("__version__", None)
        mpl.__dict__.pop("version_info", None)
        first = mpl.version_info

        mpl.__dict__.pop("__version__", None)
        mpl.__dict__.pop("version_info", None)
        second = mpl.version_info

        assert first.local == ("g6768ef8c4c",)
        assert second.local == ("g6768ef8c4c",)
        assert first.local == second.local
    finally:
        mpl._get_matplotlib_version = old_getter
        mpl.__dict__.pop("__version__", None)
        mpl.__dict__.pop("version_info", None)
