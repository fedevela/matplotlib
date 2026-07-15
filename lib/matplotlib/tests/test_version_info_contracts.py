"""Contract verification artifacts for Issue #67, Issue #68, Issue #69, and Issue #70."""

import os
import subprocess
import sys

import pytest
from packaging.version import InvalidVersion, parse as parse_version


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
    "VINFO-009": [
        "test_vinfo_009_version_exposure_scoped_to_top_level_api_and_import_time",
        "test_vinfo_009_no_dependency_or_release_pipeline_file_edits",
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


def test_vinfo_006_importability_sensitive_startup_flows_remain_stable_with_version_info(
    tmpdir,
):
    """VINFO-006 importability guardrail."""
    import matplotlib as mpl

    assert hasattr(mpl, "version_info")
    assert mpl.version_info == mpl.version_info

    no_home_cmd = [
        sys.executable,
        "-c",
        (
            "import pathlib, matplotlib as mpl; "
            "pathlib.Path.home = "
            "lambda *args: (_ for _ in ()).throw(ZeroDivisionError('home')); "
            "_ = mpl.version_info; import matplotlib.pyplot"
        ),
    ]
    proc = subprocess.run(
        no_home_cmd,
        env={**os.environ, "MPLCONFIGDIR": str(tmpdir)},
        check=False,
    )
    assert proc.returncode == 0

    oo_cmd = [
        sys.executable,
        "-OO",
        "-c",
        (
            "import matplotlib as mpl; "
            "_ = mpl.version_info; "
            "import matplotlib.pyplot as plt; "
            "import matplotlib.cbook as cbook; "
            "import matplotlib.patches as mpatches"
        ),
    ]
    proc = subprocess.run(oo_cmd, env={**os.environ, "MPLBACKEND": ""}, check=False)
    assert proc.returncode == 0

    assert mpl.version_info == parse_version(mpl.__version__)

    def parse_backends(key):
        backends = []
        for line in mpl.use.__doc__.split(key)[1].split("\n"):
            if not line.strip():
                break
            backends += [e.strip() for e in line.split(",") if e]
        return backends

    assert set(parse_backends("- interactive backends:\n")) == set(
        mpl.rcsetup.interactive_bk
    )
    assert set(parse_backends("- non-interactive backends:\n")) == set(
        mpl.rcsetup.non_interactive_bk
    )


def test_vinfo_008_malformed_version_metadata_preserves_parse_failure_trace(monkeypatch):
    """VINFO-008 malformed metadata failure semantics remain non-coercive."""
    import matplotlib as mpl

    malformed_version = "not-a-version"
    monkeypatch.setattr(mpl, "__version__", malformed_version)
    # Force a malformed version source through the parsing path.
    monkeypatch.delattr(mpl, "version_info", raising=False)

    with pytest.raises(
        InvalidVersion,
        match=r"Invalid version: 'not-a-version'",
    ):
        _ = mpl.version_info

    assert "version_info" not in mpl.__dict__


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


def test_vinfo_009_version_exposure_scoped_to_top_level_api_and_import_time():
    """VINFO-009 scope gate: top-level version exposure remains import/startup-only."""
    import json
    import subprocess
    import textwrap

    probe = textwrap.dedent(
        """
        import json
        import sys
        import matplotlib as mpl

        pre_version_modules = set(sys.modules)
        parsed = str(mpl.version_info)  # may raise if __version__ contract is broken
        post_version_modules = set(sys.modules)
        _ = mpl.version_info
        repeat_modules = set(sys.modules)

        report = {
            "has_version": hasattr(mpl, "version_info"),
            "has_version_attr_string": hasattr(mpl, "__version__"),
            "has_parse_helper": hasattr(mpl, "parse_version"),
            "version_roundtrip": parsed == str(mpl.__version__),
            "top_level_version_surface": sorted(
                name for name in mpl.__dict__ if name in {"__version__", "version_info"}
            ),
            "no_growth_after_cache": len(repeat_modules - post_version_modules),
            "version_import_delta": len(post_version_modules - pre_version_modules),
        }
        print(json.dumps(report))
        """
    )
    proc = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=str(os.getcwd()),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout.strip())

    assert payload["has_version"]
    assert payload["has_version_attr_string"]
    assert payload["has_parse_helper"]
    assert payload["version_roundtrip"]
    assert set(payload["top_level_version_surface"]) == {"__version__", "version_info"}
    assert payload["no_growth_after_cache"] == 0
    assert payload["version_import_delta"] > 0


def test_vinfo_009_no_dependency_or_release_pipeline_file_edits():
    """VINFO-009 scope gate: no external dependency or release-pipeline files are edited."""
    import re

    base_cmd = ["git", "rev-parse", "--verify", "HEAD~1"]
    if subprocess.call(base_cmd, cwd=str(os.getcwd()), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL):
        pytest.skip("VINFO-009 scope gate requires git history to identify file-surface edits.")

    diff = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~1"],
        cwd=str(os.getcwd()),
        capture_output=True,
        text=True,
        check=False,
    )
    assert diff.returncode == 0

    changed_paths = [path.strip().replace("\\", "/") for path in diff.stdout.splitlines() if path.strip()]

    forbidden_dependency_patterns = (
        r"(?:^|/)pyproject\.toml$",
        r"(?:^|/)setup\.py$",
        r"(?:^|/)setup\.cfg$",
        r"(?:^|/)requirements(?:-[^/\\]+)?\.txt$",
        r"(?:^|/)requirements?/.*\.txt$",
        r"(?:^|/)Pipfile(?:\.lock)?$",
        r"(?:^|/)poetry\.lock$",
        r"(?:^|/)environment(?:-.*)?\.ya?ml$",
    )

    forbidden_pipeline_patterns = (
        r"(?:^|/)\.github/workflows/.*",
        r"(?:^|/)\.github/actions/.*",
        r"(?:^|/)\.github/[^/]*release[^/]*/?.*",
        r"(?:^|/)\.github/[^/]*packaging[^/]*/?.*",
        r"(?:^|/)\.travis\.yml$",
        r"(?:^|/)azure-pipelines\.ya?ml$",
        r"(?:^|/)\.circleci/.*",
        r"(?:^|/)tox\.ini$",
        r"(?:^|/)nox\.ini$",
        r"(?:^|/)conda/.*",
        r"(?:^|/)ci/.*",
        r"(?:^|/)packaging/.*",
    )

    forbidden = {
        path
        for path in changed_paths
        for pattern in (*forbidden_dependency_patterns, *forbidden_pipeline_patterns)
        if re.match(pattern, path)
    }

    assert not forbidden, f"VINFO-009 violation (scope-expanded files): {sorted(forbidden)}"
