import os
import subprocess
import sys

import pytest

import matplotlib


@pytest.mark.skipif(
    os.name == "nt", reason="chmod() doesn't work as is on Windows")
@pytest.mark.skipif(os.name != "nt" and os.geteuid() == 0,
                    reason="chmod() doesn't work as root")
def test_tmpconfigdir_warning(tmpdir):
    """Test that a warning is emitted if a temporary configdir must be used."""
    mode = os.stat(tmpdir).st_mode
    try:
        os.chmod(tmpdir, 0)
        proc = subprocess.run(
            [sys.executable, "-c", "import matplotlib"],
            env={**os.environ, "MPLCONFIGDIR": str(tmpdir)},
            stderr=subprocess.PIPE, universal_newlines=True, check=True)
        assert "set the MPLCONFIGDIR" in proc.stderr
    finally:
        os.chmod(tmpdir, mode)


def test_importable_with_no_home(tmpdir):
    # VINFO-006 PSEUDOCODE:
    #   1) Launch a subprocess import of `matplotlib.pyplot`.
    #   2) Monkey-patch `pathlib.Path.home` to raise in-process errors.
    #   3) Force configdir to a temporary directory.
    #   4) Assert subprocess exit status is success (no unhandled import-time
    #      regression from `matplotlib.version_info` initialization).
    subprocess.run(
        [sys.executable, "-c",
         "import pathlib; pathlib.Path.home = lambda *args: 1/0; "
         "import matplotlib.pyplot"],
        env={**os.environ, "MPLCONFIGDIR": str(tmpdir)}, check=True)


def test_use_doc_standard_backends():
    """
    Test that the standard backends mentioned in the docstring of
    matplotlib.use() are the same as in matplotlib.rcsetup.
    """
    # VINFO-006 PSEUDOCODE:
    #   1) Parse standard-backend names from the `matplotlib.use` docstring.
    #   2) Split by lines and commas into normalized backend sets.
    #   3) Compare against `matplotlib.rcsetup.interactive_bk` and
    #      `matplotlib.rcsetup.non_interactive_bk`.
    #   4) Preserve existing behavior; only fail if the runtime import/docstring
    #      parsing contract is violated.
    def parse(key):
        backends = []
        for line in matplotlib.use.__doc__.split(key)[1].split('\n'):
            if not line.strip():
                break
            backends += [e.strip() for e in line.split(',') if e]
        return backends

    assert (set(parse('- interactive backends:\n')) ==
            set(matplotlib.rcsetup.interactive_bk))
    assert (set(parse('- non-interactive backends:\n')) ==
            set(matplotlib.rcsetup.non_interactive_bk))


def test_importable_with__OO():
    """
    When using -OO or export PYTHONOPTIMIZE=2, docstrings are discarded,
    this simple test may prevent something like issue #17970.
    """
    program = (
        "import matplotlib as mpl; "
        "import matplotlib.pyplot as plt; "
        "import matplotlib.cbook as cbook; "
        "import matplotlib.patches as mpatches"
    )
    # VINFO-006 PSEUDOCODE:
    #   1) Execute interpreter with `-OO` optimization and fixed backend env.
    #   2) Import core modules (`matplotlib`, `pyplot`, `cbook`, `patches`).
    #   3) Expect process exit code 0.
    #   4) Deterministic pass condition: no new import-time exception appears when
    #      docstrings are stripped, including during version symbol access.
    cmd = [sys.executable, "-OO", "-c", program]
    assert subprocess.call(cmd, env={**os.environ, "MPLBACKEND": ""}) == 0
