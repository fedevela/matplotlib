import subprocess
import sys

from packaging.version import Version, parse as parse_version

import matplotlib as mpl


def test_mpl_001_import_exposes_comparable_version_alongside_version():
    """MPL-001: importing matplotlib exposes both top-level version values."""
    assert isinstance(mpl.__version_info__, Version)
    assert isinstance(mpl.__version__, str)
    assert mpl.__version_info__ >= Version("0")


def test_mpl_002_inspection_finds_exactly_one_new_comparable_version():
    """MPL-002: inspection finds one new comparable version value."""
    mpl.__version_info__

    comparable_version_names = {
        name for name, value in vars(mpl).items()
        if isinstance(value, Version) and name.startswith("__version")
    }

    assert comparable_version_names == {"__version_info__"}


def test_mpl_003_versions_identify_same_release_when_interpreted():
    """MPL-003: interpreted top-level version values identify one release."""
    assert mpl.__version_info__ == parse_version(mpl.__version__)


def test_mpl_004_comparing_3_10_and_3_9_orders_3_10_as_newer():
    """MPL-004: direct comparison orders 3.10 as newer than 3.9."""
    assert parse_version("3.10") > parse_version("3.9")


def test_mpl_005_release_conversion_preserves_prerelease_dev_post_identity():
    """MPL-005: conversion preserves prerelease, dev, and post identity."""
    alpha = parse_version("3.10.0a1")
    beta = parse_version("3.10.0b2")
    candidate = parse_version("3.10.0rc3")
    development = parse_version("3.10.0.dev3")
    postrelease = parse_version("3.10.0.post4")

    assert alpha.pre == ("a", 1)
    assert beta.pre == ("b", 2)
    assert candidate.pre == ("rc", 3)
    assert development.dev == 3
    assert postrelease.post == 4
    assert len({alpha, beta, candidate, development, postrelease}) == 5


def test_mpl_006_dev_prerelease_final_post_values_follow_release_order():
    """MPL-006: dev, prerelease, final, and post values order correctly."""
    ordered_releases = [
        "3.10.0.dev1",
        "3.10.0.dev2",
        "3.10.0a1.dev1",
        "3.10.0a1",
        "3.10.0a2",
        "3.10.0b1",
        "3.10.0rc1",
        "3.10.0rc2",
        "3.10.0",
        "3.10.0.post1",
        "3.10.0.post2",
    ]
    comparable_releases = list(map(parse_version, ordered_releases))

    assert comparable_releases == sorted(comparable_releases)
    assert len(set(comparable_releases)) == len(comparable_releases)


def test_mpl_007_version_read_retains_meaning_and_value_format():
    """MPL-007: reading __version__ preserves its meaning and value format."""
    version_before = mpl.__version__

    mpl.__version_info__

    assert isinstance(version_before, str)
    assert mpl.__version__ == version_before


def test_mpl_008_existing_import_without_new_value_still_succeeds():
    """MPL-008: an existing import remains successful without the new value."""
    subprocess.run(
        [sys.executable, "-c", "import matplotlib as mpl; "
         "assert '__version_info__' not in vars(mpl)"],
        check=True)


def test_mpl_008_version_reporting_without_new_value_still_succeeds():
    """MPL-008: established version reporting remains successful unchanged."""
    subprocess.run(
        [sys.executable, "-c", "import matplotlib as mpl; "
         "assert isinstance(mpl.__version__, str); "
         "assert mpl.__version__; "
         "assert '__version_info__' not in vars(mpl)"],
        check=True)
