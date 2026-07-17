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


def test_mpl_007_version_read_retains_meaning_and_value_format():
    """MPL-007: reading __version__ preserves its meaning and value format."""
    version_before = mpl.__version__

    mpl.__version_info__

    assert isinstance(version_before, str)
    assert mpl.__version__ == version_before
