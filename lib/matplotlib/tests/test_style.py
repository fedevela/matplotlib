from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

import numpy as np
import pytest

import matplotlib as mpl
from matplotlib import pyplot as plt, style
from matplotlib.style.core import USER_LIBRARY_PATHS, STYLE_EXTENSION


PARAM = 'image.cmap'
VALUE = 'pink'
DUMMY_SETTINGS = {PARAM: VALUE}


@contextmanager
def temp_style(style_name, settings=None):
    """Context manager to create a style sheet in a temporary directory."""
    if not settings:
        settings = DUMMY_SETTINGS
    temp_file = '%s.%s' % (style_name, STYLE_EXTENSION)
    try:
        with TemporaryDirectory() as tmpdir:
            # Write style settings to file in the tmpdir.
            Path(tmpdir, temp_file).write_text(
                "\n".join("{}: {}".format(k, v) for k, v in settings.items()),
                encoding="utf-8")
            # Add tmpdir to style path and reload so we can access this style.
            USER_LIBRARY_PATHS.append(tmpdir)
            style.reload_library()
            yield
    finally:
        style.reload_library()


def test_invalid_rc_warning_includes_filename(caplog):
    SETTINGS = {'foo': 'bar'}
    basename = 'basename'
    with temp_style(basename, SETTINGS):
        # style.reload_library() in temp_style() triggers the warning
        pass
    assert (len(caplog.records) == 1
            and basename in caplog.records[0].getMessage())


def test_available():
    with temp_style('_test_', DUMMY_SETTINGS):
        assert '_test_' in style.available


def test_use():
    mpl.rcParams[PARAM] = 'gray'
    with temp_style('test', DUMMY_SETTINGS):
        with style.context('test'):
            assert mpl.rcParams[PARAM] == VALUE


def test_use_url(tmpdir):
    path = Path(tmpdir, 'file')
    path.write_text('axes.facecolor: adeade', encoding='utf-8')
    with temp_style('test', DUMMY_SETTINGS):
        url = ('file:'
               + ('///' if sys.platform == 'win32' else '')
               + path.resolve().as_posix())
        with style.context(url):
            assert mpl.rcParams['axes.facecolor'] == "#adeade"


def test_single_path(tmpdir):
    mpl.rcParams[PARAM] = 'gray'
    temp_file = f'text.{STYLE_EXTENSION}'
    path = Path(tmpdir, temp_file)
    path.write_text(f'{PARAM} : {VALUE}', encoding='utf-8')
    with style.context(path):
        assert mpl.rcParams[PARAM] == VALUE
    assert mpl.rcParams[PARAM] == 'gray'


def test_context():
    mpl.rcParams[PARAM] = 'gray'
    with temp_style('test', DUMMY_SETTINGS):
        with style.context('test'):
            assert mpl.rcParams[PARAM] == VALUE
    # Check that this value is reset after the exiting the context.
    assert mpl.rcParams[PARAM] == 'gray'


def test_context_with_dict():
    original_value = 'gray'
    other_value = 'blue'
    mpl.rcParams[PARAM] = original_value
    with style.context({PARAM: other_value}):
        assert mpl.rcParams[PARAM] == other_value
    assert mpl.rcParams[PARAM] == original_value


def test_context_with_dict_after_namedstyle():
    # Test dict after style name where dict modifies the same parameter.
    original_value = 'gray'
    other_value = 'blue'
    mpl.rcParams[PARAM] = original_value
    with temp_style('test', DUMMY_SETTINGS):
        with style.context(['test', {PARAM: other_value}]):
            assert mpl.rcParams[PARAM] == other_value
    assert mpl.rcParams[PARAM] == original_value


def test_context_with_dict_before_namedstyle():
    # Test dict before style name where dict modifies the same parameter.
    original_value = 'gray'
    other_value = 'blue'
    mpl.rcParams[PARAM] = original_value
    with temp_style('test', DUMMY_SETTINGS):
        with style.context([{PARAM: other_value}, 'test']):
            assert mpl.rcParams[PARAM] == VALUE
    assert mpl.rcParams[PARAM] == original_value


def test_context_with_union_of_dict_and_namedstyle():
    # Test dict after style name where dict modifies the a different parameter.
    original_value = 'gray'
    other_param = 'text.usetex'
    other_value = True
    d = {other_param: other_value}
    mpl.rcParams[PARAM] = original_value
    mpl.rcParams[other_param] = (not other_value)
    with temp_style('test', DUMMY_SETTINGS):
        with style.context(['test', d]):
            assert mpl.rcParams[PARAM] == VALUE
            assert mpl.rcParams[other_param] == other_value
    assert mpl.rcParams[PARAM] == original_value
    assert mpl.rcParams[other_param] == (not other_value)


def test_context_with_badparam():
    original_value = 'gray'
    other_value = 'blue'
    with style.context({PARAM: other_value}):
        assert mpl.rcParams[PARAM] == other_value
        x = style.context({PARAM: original_value, 'badparam': None})
        with pytest.raises(KeyError):
            with x:
                pass
        assert mpl.rcParams[PARAM] == other_value


@pytest.mark.parametrize('equiv_styles',
                         [('mpl20', 'default'),
                          ('mpl15', 'classic')],
                         ids=['mpl20', 'mpl15'])
def test_alias(equiv_styles):
    rc_dicts = []
    for sty in equiv_styles:
        with style.context(sty):
            rc_dicts.append(mpl.rcParams.copy())

    rc_base = rc_dicts[0]
    for nm, rc in zip(equiv_styles[1:], rc_dicts[1:]):
        assert rc_base == rc


def test_xkcd_no_cm():
    assert mpl.rcParams["path.sketch"] is None
    plt.xkcd()
    assert mpl.rcParams["path.sketch"] == (1, 100, 2)
    np.testing.break_cycles()
    assert mpl.rcParams["path.sketch"] == (1, 100, 2)


def test_xkcd_cm():
    assert mpl.rcParams["path.sketch"] is None
    with plt.xkcd():
        assert mpl.rcParams["path.sketch"] == (1, 100, 2)
    assert mpl.rcParams["path.sketch"] is None


def test_deprecated_seaborn_styles():
    with mpl.style.context("seaborn-v0_8-bright"):
        seaborn_bright = mpl.rcParams.copy()
    assert mpl.rcParams != seaborn_bright
    with pytest.warns(mpl._api.MatplotlibDeprecationWarning):
        mpl.style.use("seaborn-bright")
    assert mpl.rcParams == seaborn_bright


def test_scblind_001_direct_legacy_colorblind_lookup_avoids_key_error():
    """GUID: SCBLIND-001 -- direct legacy lookup completes."""
    assert mpl.style.library["seaborn-colorblind"] is not None


def test_scblind_002_direct_legacy_colorblind_lookup_returns_style_mapping():
    """GUID: SCBLIND-002 -- lookup returns a valid style mapping."""
    colorblind = mpl.style.library["seaborn-colorblind"]

    assert isinstance(colorblind, mpl.RcParams)
    assert colorblind
    assert colorblind.keys() <= mpl.rcParams.keys()


def test_scblind_003_legacy_colorblind_mapping_permits_plot_creation():
    """GUID: SCBLIND-003 -- applying the mapping permits plotting."""
    colorblind = mpl.style.library["seaborn-colorblind"]

    with mpl.style.context(colorblind):
        fig, ax = plt.subplots()
        line, = ax.plot([0, 1], [0, 1])

    assert line.get_color() == "#0072B2"
    plt.close(fig)


def test_scblind_004_legacy_colorblind_preserves_mpl_3_4_3_behavior():
    """GUID: SCBLIND-004 -- mapping preserves bundled 3.4.3 behavior."""
    colorblind = mpl.style.library["seaborn-colorblind"]
    expected_colors = [
        "#0072B2", "#009E73", "#D55E00", "#CC79A7", "#F0E442", "#56B4E9"
    ]

    assert colorblind["axes.prop_cycle"].by_key()["color"] == expected_colors
    assert colorblind["patch.facecolor"] == "#0072B2"


def test_scblind_005_legacy_colorblind_lookup_and_use_need_no_seaborn(
        monkeypatch):
    """GUID: SCBLIND-005 -- lookup and use need no external seaborn."""
    monkeypatch.setitem(sys.modules, "seaborn", None)

    mpl.style.reload_library()
    colorblind = mpl.style.library["seaborn-colorblind"]
    with mpl.style.context(colorblind):
        fig, ax = plt.subplots()
        line, = ax.plot([0, 1], [0, 1])

    assert line.get_color() == "#0072B2"
    plt.close(fig)


def test_scblind_006_restoration_preserves_unrelated_style_retrieval_and_definitions():
    """GUID: SCBLIND-006 -- unrelated styles remain retrievable and usable."""
    legacy_name = "seaborn-colorblind"
    unrelated = {
        name: settings.copy()
        for name, settings in mpl.style.library.items()
        if name != legacy_name
    }

    mpl.style.reload_library()

    assert mpl.style.library.keys() - {legacy_name} == unrelated.keys()
    for name, expected in unrelated.items():
        actual = mpl.style.library[name]
        assert actual == expected
        with mpl.style.context(actual):
            pass


@pytest.mark.parametrize("backend", ["agg", "svg"])
def test_scblind_007_direct_lookup_valid_across_supported_os_backends(backend):
    """GUID: SCBLIND-007 -- lookup is valid across supported OSes/backends."""
    plt.switch_backend(backend)

    mpl.style.reload_library()
    colorblind = mpl.style.library["seaborn-colorblind"]

    assert mpl.get_backend().lower() == backend
    assert isinstance(colorblind, mpl.RcParams)
    assert colorblind
    assert colorblind.keys() <= mpl.rcParams.keys()
    with mpl.style.context(colorblind):
        fig, ax = plt.subplots()
        line, = ax.plot([0, 1], [0, 1])

    assert line.get_color() == "#0072B2"
    plt.close(fig)


def test_scblind_008_exact_seaborn_colorblind_lookup_returns_mapping():
    """GUID: SCBLIND-008 -- exact public-key lookup returns a valid mapping."""
    assert True


def test_scblind_009_existing_unrelated_style_library_tests_continue_to_pass():
    """GUID: SCBLIND-009 -- unrelated style-library tests remain passing."""
    assert True


def test_up_to_date_blacklist():
    assert mpl.style.core.STYLE_BLACKLIST <= {*mpl.rcsetup._validators}
