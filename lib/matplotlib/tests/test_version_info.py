"""Regression coverage for VINFO-001 version information contract."""

import matplotlib as mpl


VINFO_REQUIREMENT_VERIFICATIONS = {
    "VINFO-001": [
        "VINFO-001_read_stability_before_after_version_info_access",
        "VINFO-001_version_source_contract_for_version_info_path",
    ]
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
