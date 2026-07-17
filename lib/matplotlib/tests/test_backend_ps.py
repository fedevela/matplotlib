from collections import Counter
from pathlib import Path
import io
import re
import tempfile

import numpy as np
import pytest

from matplotlib import cbook, path, patheffects, font_manager as fm
from matplotlib._api import MatplotlibDeprecationWarning
from matplotlib.figure import Figure
from matplotlib.patches import Ellipse
from matplotlib.testing._markers import needs_ghostscript, needs_usetex
from matplotlib.testing.decorators import check_figures_equal, image_comparison
import matplotlib as mpl
import matplotlib.collections as mcollections
import matplotlib.pyplot as plt


# This tests tends to hit a TeX cache lock on AppVeyor.
@pytest.mark.flaky(reruns=3)
@pytest.mark.parametrize('orientation', ['portrait', 'landscape'])
@pytest.mark.parametrize('format, use_log, rcParams', [
    ('ps', False, {}),
    ('ps', False, {'ps.usedistiller': 'ghostscript'}),
    ('ps', False, {'ps.usedistiller': 'xpdf'}),
    ('ps', False, {'text.usetex': True}),
    ('eps', False, {}),
    ('eps', True, {'ps.useafm': True}),
    ('eps', False, {'text.usetex': True}),
], ids=[
    'ps',
    'ps with distiller=ghostscript',
    'ps with distiller=xpdf',
    'ps with usetex',
    'eps',
    'eps afm',
    'eps with usetex'
])
def test_savefig_to_stringio(format, use_log, rcParams, orientation):
    mpl.rcParams.update(rcParams)

    fig, ax = plt.subplots()

    with io.StringIO() as s_buf, io.BytesIO() as b_buf:

        if use_log:
            ax.set_yscale('log')

        ax.plot([1, 2], [1, 2])
        title = "Déjà vu"
        if not mpl.rcParams["text.usetex"]:
            title += " \N{MINUS SIGN}\N{EURO SIGN}"
        ax.set_title(title)
        allowable_exceptions = []
        if rcParams.get("ps.usedistiller"):
            allowable_exceptions.append(mpl.ExecutableNotFoundError)
        if rcParams.get("text.usetex"):
            allowable_exceptions.append(RuntimeError)
        if rcParams.get("ps.useafm"):
            allowable_exceptions.append(MatplotlibDeprecationWarning)
        try:
            fig.savefig(s_buf, format=format, orientation=orientation)
            fig.savefig(b_buf, format=format, orientation=orientation)
        except tuple(allowable_exceptions) as exc:
            pytest.skip(str(exc))

        assert not s_buf.closed
        assert not b_buf.closed
        s_val = s_buf.getvalue().encode('ascii')
        b_val = b_buf.getvalue()

        # Strip out CreationDate: ghostscript and cairo don't obey
        # SOURCE_DATE_EPOCH, and that environment variable is already tested in
        # test_determinism.
        s_val = re.sub(b"(?<=\n%%CreationDate: ).*", b"", s_val)
        b_val = re.sub(b"(?<=\n%%CreationDate: ).*", b"", b_val)

        assert s_val == b_val.replace(b'\r\n', b'\n')


def test_patheffects():
    mpl.rcParams['path.effects'] = [
        patheffects.withStroke(linewidth=4, foreground='w')]
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3])
    with io.BytesIO() as ps:
        fig.savefig(ps, format='ps')


@needs_usetex
@needs_ghostscript
def test_tilde_in_tempfilename(tmpdir):
    # Tilde ~ in the tempdir path (e.g. TMPDIR, TMP or TEMP on windows
    # when the username is very long and windows uses a short name) breaks
    # latex before https://github.com/matplotlib/matplotlib/pull/5928
    base_tempdir = Path(tmpdir, "short-1")
    base_tempdir.mkdir()
    # Change the path for new tempdirs, which is used internally by the ps
    # backend to write a file.
    with cbook._setattr_cm(tempfile, tempdir=str(base_tempdir)):
        # usetex results in the latex call, which does not like the ~
        mpl.rcParams['text.usetex'] = True
        plt.plot([1, 2, 3, 4])
        plt.xlabel(r'\textbf{time} (s)')
        # use the PS backend to write the file...
        plt.savefig(base_tempdir / 'tex_demo.eps', format="ps")


@image_comparison(["empty.eps"])
def test_transparency():
    fig, ax = plt.subplots()
    ax.set_axis_off()
    ax.plot([0, 1], color="r", alpha=0)
    ax.text(.5, .5, "foo", color="r", alpha=0)


@needs_usetex
@image_comparison(["empty.eps"])
def test_transparency_tex():
    mpl.rcParams['text.usetex'] = True
    fig, ax = plt.subplots()
    ax.set_axis_off()
    ax.plot([0, 1], color="r", alpha=0)
    ax.text(.5, .5, "foo", color="r", alpha=0)


def test_bbox():
    fig, ax = plt.subplots()
    with io.BytesIO() as buf:
        fig.savefig(buf, format='eps')
        buf = buf.getvalue()

    bb = re.search(b'^%%BoundingBox: (.+) (.+) (.+) (.+)$', buf, re.MULTILINE)
    assert bb
    hibb = re.search(b'^%%HiResBoundingBox: (.+) (.+) (.+) (.+)$', buf,
                     re.MULTILINE)
    assert hibb

    for i in range(1, 5):
        # BoundingBox must use integers, and be ceil/floor of the hi res.
        assert b'.' not in bb.group(i)
        assert int(bb.group(i)) == pytest.approx(float(hibb.group(i)), 1)


@needs_usetex
def test_failing_latex():
    """Test failing latex subprocess call"""
    mpl.rcParams['text.usetex'] = True
    # This fails with "Double subscript"
    plt.xlabel("$22_2_2$")
    with pytest.raises(RuntimeError):
        plt.savefig(io.BytesIO(), format="ps")


@needs_usetex
def test_partial_usetex(caplog):
    caplog.set_level("WARNING")
    plt.figtext(.1, .1, "foo", usetex=True)
    plt.figtext(.2, .2, "bar", usetex=True)
    plt.savefig(io.BytesIO(), format="ps")
    record, = caplog.records  # asserts there's a single record.
    assert "as if usetex=False" in record.getMessage()


@needs_usetex
def test_usetex_preamble(caplog):
    mpl.rcParams.update({
        "text.usetex": True,
        # Check that these don't conflict with the packages loaded by default.
        "text.latex.preamble": r"\usepackage{color,graphicx,textcomp}",
    })
    plt.figtext(.5, .5, "foo")
    plt.savefig(io.BytesIO(), format="ps")


@image_comparison(["useafm.eps"])
def test_useafm():
    mpl.rcParams["ps.useafm"] = True
    fig, ax = plt.subplots()
    ax.set_axis_off()
    ax.axhline(.5)
    ax.text(.5, .5, "qk")


@image_comparison(["type3.eps"])
def test_type3_font():
    plt.figtext(.5, .5, "I/J")


@image_comparison(["coloredhatcheszerolw.eps"])
def test_colored_hatch_zero_linewidth():
    ax = plt.gca()
    ax.add_patch(Ellipse((0, 0), 1, 1, hatch='/', facecolor='none',
                         edgecolor='r', linewidth=0))
    ax.add_patch(Ellipse((0.5, 0.5), 0.5, 0.5, hatch='+', facecolor='none',
                         edgecolor='g', linewidth=0.2))
    ax.add_patch(Ellipse((1, 1), 0.3, 0.8, hatch='\\', facecolor='none',
                         edgecolor='b', linewidth=0))
    ax.set_axis_off()


@check_figures_equal(extensions=["eps"])
def test_text_clip(fig_test, fig_ref):
    ax = fig_test.add_subplot()
    # Fully clipped-out text should not appear.
    ax.text(0, 0, "hello", transform=fig_test.transFigure, clip_on=True)
    fig_ref.add_subplot()


@needs_ghostscript
def test_d_glyph(tmp_path):
    # Ensure that we don't have a procedure defined as /d, which would be
    # overwritten by the glyph definition for "d".
    fig = plt.figure()
    fig.text(.5, .5, "def")
    out = tmp_path / "test.eps"
    fig.savefig(out)
    mpl.testing.compare.convert(out, cache=False)  # Should not raise.


@image_comparison(["type42_without_prep.eps"], style='mpl20')
def test_type42_font_without_prep():
    # Test whether Type 42 fonts without prep table are properly embedded
    mpl.rcParams["ps.fonttype"] = 42
    mpl.rcParams["mathtext.fontset"] = "stix"

    plt.figtext(0.5, 0.5, "Mass $m$")


@pytest.mark.parametrize('fonttype', ["3", "42"])
def test_fonttype(fonttype):
    mpl.rcParams["ps.fonttype"] = fonttype
    fig, ax = plt.subplots()

    ax.text(0.25, 0.5, "Forty-two is the answer to everything!")

    buf = io.BytesIO()
    fig.savefig(buf, format="ps")

    test = b'/FontType ' + bytes(f"{fonttype}", encoding='utf-8') + b' def'

    assert re.search(test, buf.getvalue(), re.MULTILINE)


def test_linedash():
    """Test that dashed lines do not break PS output"""
    fig, ax = plt.subplots()

    ax.plot([0, 1], linestyle="--")

    buf = io.BytesIO()
    fig.savefig(buf, format="ps")

    assert buf.tell() > 0


def test_no_duplicate_definition():

    fig = Figure()
    axs = fig.subplots(4, 4, subplot_kw=dict(projection="polar"))
    for ax in axs.flat:
        ax.set(xticks=[], yticks=[])
        ax.plot([1, 2])
    fig.suptitle("hello, world")

    buf = io.StringIO()
    fig.savefig(buf, format='eps')
    buf.seek(0)

    wds = [ln.partition(' ')[0] for
           ln in buf.readlines()
           if ln.startswith('/')]

    assert max(Counter(wds).values()) == 1


# MPLPS-001, MPLPS-002, MPLPS-008, MPLPS-009 architecture:
# These existing backend-test loci own the artist-to-EPS integration contract.
# Their fixture boundary starts at Figure (not pyplot), crosses Figure.savefig,
# and observes the generated EPS stream; renderer run assembly remains private
# to backend_ps and therefore needs no test-facing adapter or public contract.
def _save_artist_text_as_eps(kind, text):
    fig = Figure()
    ax = fig.subplots()
    ax.set_axis_off()
    if kind == "annotation":
        artist = ax.annotate(text, (.5, .5))
    else:
        artist = ax.set_title(text)
    output = io.StringIO()
    fig.savefig(output, format="eps")
    return artist, output.getvalue()


def _assert_eps_contains_text(output, text):
    glyph_names = re.findall(r"/[\w.]+ glyphshow", output)
    expected = [f"/{'space' if char == ' ' else char} glyphshow"
                for char in text]
    assert any(glyph_names[start:start + len(expected)] == expected
               for start in range(len(glyph_names) - len(expected) + 1))


def test_mplps_001_direct_figure_annotation_leading_blank_eps_retains_label():
    """MPLPS-001: EPS saves without TypeError and retains ``Lower label``."""
    # MPLPS-001 pseudocode:
    # GIVEN a directly constructed Figure with axes
    # AND an annotation whose text is "\nLower label"
    # WHEN the Figure saves to an in-memory EPS destination
    # THEN saving completes without TypeError
    # AND decoded EPS output contains "Lower label".
    _, output = _save_artist_text_as_eps("annotation", "\nLower label")

    _assert_eps_contains_text(output, "Lower label")


def test_mplps_002_direct_figure_title_leading_blank_eps_retains_title():
    """MPLPS-002: EPS saves without error and retains ``Lower title``."""
    # MPLPS-002 pseudocode:
    # GIVEN a directly constructed Figure with axes
    # AND the axes title is "\nLower title"
    # WHEN the Figure saves to an in-memory EPS destination
    # THEN saving completes without error
    # AND decoded EPS output contains "Lower title".
    _, output = _save_artist_text_as_eps("title", "\nLower title")

    _assert_eps_contains_text(output, "Lower title")


@pytest.mark.parametrize("kind", ["annotation", "title"])
def test_mplps_008_annotation_title_semantics_change_only_for_empty_line_fix(
        kind):
    """MPLPS-008: Baseline artist semantics remain otherwise unchanged."""
    # MPLPS-008 pseudocode:
    # FOR EACH artist kind in annotation and axes title:
    #   CAPTURE observable EPS behavior for ordinary non-empty text.
    #   EXERCISE the corresponding leading-empty-line text.
    #   VERIFY artist semantics and non-empty-line rendering follow the same
    #   existing path, with only the empty-line failure removed.
    text = f"Lower {kind}"
    ordinary_artist, ordinary_output = _save_artist_text_as_eps(kind, text)
    leading_artist, leading_output = _save_artist_text_as_eps(kind, f"\n{text}")

    assert ordinary_artist.get_text() == text
    assert leading_artist.get_text() == f"\n{text}"
    _assert_eps_contains_text(ordinary_output, text)
    _assert_eps_contains_text(leading_output, text)


def test_mplps_009_direct_figure_leading_blank_eps_regression_retains_text():
    """MPLPS-009: Regression saves EPS and checks text after the empty line."""
    # MPLPS-009 pseudocode:
    # BUILD the regression fixture from Figure directly, without pyplot.
    # ADD leading-empty-line annotation and title text to its axes.
    # SAVE through the EPS backend into memory.
    # IF saving raises, fail with the backend exception.
    # OTHERWISE verify each non-empty trailing line occurs in EPS output.
    fig = Figure()
    ax = fig.subplots()
    ax.set_axis_off()
    ax.annotate("\nLower label", (.5, .5))
    ax.set_title("\nLower title")
    output = io.StringIO()

    fig.savefig(output, format="eps")

    _assert_eps_contains_text(output.getvalue(), "Lower label")
    _assert_eps_contains_text(output.getvalue(), "Lower title")


@image_comparison(["multi_font_type3.eps"], tol=0.51)
def test_multi_font_type3():
    fp = fm.FontProperties(family=["WenQuanYi Zen Hei"])
    if Path(fm.findfont(fp)).name != "wqy-zenhei.ttc":
        pytest.skip("Font may be missing")

    plt.rc('font', family=['DejaVu Sans', 'WenQuanYi Zen Hei'], size=27)
    plt.rc('ps', fonttype=3)

    fig = plt.figure()
    fig.text(0.15, 0.475, "There are 几个汉字 in between!")


@image_comparison(["multi_font_type42.eps"], tol=1.6)
def test_multi_font_type42():
    fp = fm.FontProperties(family=["WenQuanYi Zen Hei"])
    if Path(fm.findfont(fp)).name != "wqy-zenhei.ttc":
        pytest.skip("Font may be missing")

    plt.rc('font', family=['DejaVu Sans', 'WenQuanYi Zen Hei'], size=27)
    plt.rc('ps', fonttype=42)

    fig = plt.figure()
    fig.text(0.15, 0.475, "There are 几个汉字 in between!")


@image_comparison(["scatter.eps"])
def test_path_collection():
    rng = np.random.default_rng(19680801)
    xvals = rng.uniform(0, 1, 10)
    yvals = rng.uniform(0, 1, 10)
    sizes = rng.uniform(30, 100, 10)
    fig, ax = plt.subplots()
    ax.scatter(xvals, yvals, sizes, edgecolor=[0.9, 0.2, 0.1], marker='<')
    ax.set_axis_off()
    paths = [path.Path.unit_regular_polygon(i) for i in range(3, 7)]
    offsets = rng.uniform(0, 200, 20).reshape(10, 2)
    sizes = [0.02, 0.04]
    pc = mcollections.PathCollection(paths, sizes, zorder=-1,
                                     facecolors='yellow', offsets=offsets)
    ax.add_collection(pc)
    ax.set_xlim(0, 1)
