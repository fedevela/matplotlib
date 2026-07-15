"""Regression coverage for VINFO-001 and VINFO-002 version information contracts."""

import importlib
import os
import subprocess
import sys

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
    "VINFO-004": [
        "VINFO-004_version_info_comparison_operators_are_total_for_all_6_standard_operators",
        "VINFO-004_dev_release_is_semantically_before_final_and_reverse_check",
        "VINFO-004_candidate_is_before_final_and_post_release_is_after_final",
        "VINFO-004_compatibility_guard_version_info_ge_target_returns_deterministic_semantic_result",
    ],
    "VINFO-005": [
        "VINFO-005_importable_with__OO_version_initialization_remains_import_side_effect_free",
        "VINFO-005_importable_with_no_home_version_initialization_remains_home_free",
        "VINFO-005_doc_standard_backends_observations_unmodified_by_version_initialization",
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


def test_VINFO_004_version_info_comparison_operators_are_total_for_all_6_standard_operators():
    """
    Requirement VINFO-004:
    Validate that all comparison operators `<`, `<=`, `>`, `>=`, `==`, `!=` are
    covered by a traceability artifact for supported version tuple comparisons.
    """
    versions = (
        "3.5.0.dev820+g6768ef8c4c",
        "3.5.0rc2",
        "3.5.0",
        "3.5.0.post820+g6768ef8c4c",
    )

    old_getter = mpl._get_matplotlib_version
    infos = []
    try:
        for version in versions:
            mpl._get_matplotlib_version = lambda version=version: version
            mpl.__dict__.pop("__version__", None)
            mpl.__dict__.pop("version_info", None)
            infos.append(mpl.version_info)

        assert infos[0] < infos[1] < infos[2] < infos[3]
        assert infos[3] > infos[0]
        assert infos[2] == infos[2]
        assert infos[1] != infos[3]
        assert not (infos[2] <= infos[1])
        assert infos[1] <= infos[1]
        assert not (infos[0] >= infos[3])
        assert infos[2] >= infos[2]
    finally:
        mpl._get_matplotlib_version = old_getter
        mpl.__dict__.pop("__version__", None)
        mpl.__dict__.pop("version_info", None)


def test_VINFO_004_dev_release_is_semantically_before_final_and_reverse_check():
    """
    Requirement VINFO-004:
    Encode the semantic expectation that `dev` precedes `final` and that
    reverse comparison against `final` is consistent under that ordering.
    """
    old_getter = mpl._get_matplotlib_version

    try:
        mpl._get_matplotlib_version = lambda: "3.5.0.dev820+g6768ef8c4c"
        mpl.__dict__.pop("__version__", None)
        mpl.__dict__.pop("version_info", None)
        dev_version = mpl.version_info

        mpl._get_matplotlib_version = lambda: "3.5.0"
        mpl.__dict__.pop("__version__", None)
        mpl.__dict__.pop("version_info", None)
        final_version = mpl.version_info

        assert dev_version < final_version
        assert not final_version < dev_version
        assert final_version > dev_version
        assert not (dev_version >= final_version)
        assert not (final_version <= dev_version)
    finally:
        mpl._get_matplotlib_version = old_getter
        mpl.__dict__.pop("__version__", None)
        mpl.__dict__.pop("version_info", None)


def test_VINFO_004_candidate_is_before_final_and_post_release_is_after_final():
    """
    Requirement VINFO-004:
    Encode the semantic expectation that `candidate` precedes `final` and `post`
    follows `final` for compatible quick-release checks.
    """
    old_getter = mpl._get_matplotlib_version

    try:
        mpl._get_matplotlib_version = lambda: "3.5.0rc2"
        mpl.__dict__.pop("__version__", None)
        mpl.__dict__.pop("version_info", None)
        rc_version = mpl.version_info

        mpl._get_matplotlib_version = lambda: "3.5.0"
        mpl.__dict__.pop("__version__", None)
        mpl.__dict__.pop("version_info", None)
        final_version = mpl.version_info

        mpl._get_matplotlib_version = lambda: "3.5.0.post820+g6768ef8c4c"
        mpl.__dict__.pop("__version__", None)
        mpl.__dict__.pop("version_info", None)
        post_version = mpl.version_info

        assert rc_version < final_version
        assert final_version > rc_version
        assert final_version < post_version
        assert post_version > final_version
        assert rc_version < (3, 5, 0)
        assert (3, 5, 0) < post_version
    finally:
        mpl._get_matplotlib_version = old_getter
        mpl.__dict__.pop("__version__", None)
        mpl.__dict__.pop("version_info", None)


def test_VINFO_004_compatibility_guard_version_info_ge_target_returns_deterministic_semantic_result():
    """
    Requirement VINFO-004:
    Encode the quick-compatibility guard contract for
    `matplotlib.version_info >= (3, 5, 0)` using supported final/minor forms.
    """
    expectations = {
        "3.5.0": True,
        "3.5.0rc2": False,
        "3.5.0.dev820+g6768ef8c4c": False,
        "3.5.0.post820+g6768ef8c4c": True,
    }

    old_getter = mpl._get_matplotlib_version

    try:
        for version, expected in expectations.items():
            mpl._get_matplotlib_version = lambda version=version: version
            mpl.__dict__.pop("__version__", None)
            mpl.__dict__.pop("version_info", None)
            assert (mpl.version_info >= (3, 5, 0)) is expected
    finally:
        mpl._get_matplotlib_version = old_getter
        mpl.__dict__.pop("__version__", None)
        mpl.__dict__.pop("version_info", None)


def _parse_doc_standard_backends_from_use_doc():
    def parse(key):
        backends = []
        for line in mpl.use.__doc__.split(key)[1].split("\n"):
            if not line.strip():
                break
            backends += [entry.strip() for entry in line.split(",") if entry]
        return set(backends)

    return (
        parse("- interactive backends:\n"),
        parse("- non-interactive backends:\n"),
    )


def test_VINFO_005_importable_with__OO_version_initialization_remains_import_side_effect_free():
    """
    VINFO-005:
    When importing under -OO, version initialization must not alter the existing
    import flow for docstring-stripped optimization runs.
    """
    program = (
        "import matplotlib as mpl\n"
        "_ = mpl.version_info\n"
        "import matplotlib.pyplot as plt\n"
        "import matplotlib.cbook as cbook\n"
        "import matplotlib.patches as mpatches\n"
        "assert isinstance(mpl.version_info, tuple)\n"
        "assert isinstance(mpl.__version__, str)\n"
    )
    cmd = [sys.executable, "-OO", "-c", program]
    proc = subprocess.run(
        cmd,
        env={**os.environ, "MPLBACKEND": ""},
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == ""


def test_VINFO_005_importable_with_no_home_version_initialization_remains_home_free(tmp_path):
    """
    VINFO-005:
    Version initialization must remain HOME-safe and cannot require
    Path.home() in constrained HOME-resolution environments.
    """
    program = (
        "import pathlib\n"
        "pathlib.Path.home = lambda *args: (_ for _ in ()).throw(RuntimeError('HOME used'))\n"
        "import matplotlib as mpl\n"
        "assert isinstance(mpl.version_info, tuple)\n"
        "assert isinstance(mpl.__version__, str)\n"
    )
    cmd = [sys.executable, "-c", program]
    proc = subprocess.run(cmd, env={**os.environ, "MPLCONFIGDIR": str(tmp_path)}, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == ""


def test_VINFO_005_doc_standard_backends_observations_unmodified_by_version_initialization():
    """
    VINFO-005:
    Accessing version metadata before reading `matplotlib.use()` docstring-backed
    backend lists must not alter documented backend discovery behavior.
    """
    saved_version = mpl.__dict__.get("__version__")
    saved_version_info = mpl.__dict__.get("version_info")
    try:
        mpl.__dict__.pop("__version__", None)
        mpl.__dict__.pop("version_info", None)

        before = _parse_doc_standard_backends_from_use_doc()
        _ = mpl.version_info
        after = _parse_doc_standard_backends_from_use_doc()

        assert before == after
        assert after[0] == set(mpl.rcsetup.interactive_bk)
        assert after[1] == set(mpl.rcsetup.non_interactive_bk)
    finally:
        if saved_version is None:
            mpl.__dict__.pop("__version__", None)
        else:
            mpl.__dict__["__version__"] = saved_version
        if saved_version_info is None:
            mpl.__dict__.pop("version_info", None)
        else:
            mpl.__dict__["version_info"] = saved_version_info
