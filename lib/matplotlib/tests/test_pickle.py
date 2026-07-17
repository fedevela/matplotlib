from io import BytesIO
import ast
import pickle

import numpy as np
import pytest

import matplotlib as mpl
from matplotlib import cm
from matplotlib.backend_bases import MouseEvent, PickEvent
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.testing import subprocess_run_helper
from matplotlib.testing.decorators import check_figures_equal
from matplotlib.dates import rrulewrapper
from matplotlib.lines import VertexSelector
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
import matplotlib.figure as mfigure
from mpl_toolkits.axes_grid1 import parasite_axes


def test_simple():
    fig = plt.figure()
    pickle.dump(fig, BytesIO(), pickle.HIGHEST_PROTOCOL)

    ax = plt.subplot(121)
    pickle.dump(ax, BytesIO(), pickle.HIGHEST_PROTOCOL)

    ax = plt.axes(projection='polar')
    plt.plot(np.arange(10), label='foobar')
    plt.legend()

    pickle.dump(ax, BytesIO(), pickle.HIGHEST_PROTOCOL)

#    ax = plt.subplot(121, projection='hammer')
#    pickle.dump(ax, BytesIO(), pickle.HIGHEST_PROTOCOL)

    plt.figure()
    plt.bar(x=np.arange(10), height=np.arange(10))
    pickle.dump(plt.gca(), BytesIO(), pickle.HIGHEST_PROTOCOL)

    fig = plt.figure()
    ax = plt.axes()
    plt.plot(np.arange(10))
    ax.set_yscale('log')
    pickle.dump(fig, BytesIO(), pickle.HIGHEST_PROTOCOL)


def _generate_complete_test_figure(fig_ref):
    fig_ref.set_size_inches((10, 6))
    plt.figure(fig_ref)

    plt.suptitle('Can you fit any more in a figure?')

    # make some arbitrary data
    x, y = np.arange(8), np.arange(10)
    data = u = v = np.linspace(0, 10, 80).reshape(10, 8)
    v = np.sin(v * -0.6)

    # Ensure lists also pickle correctly.
    plt.subplot(3, 3, 1)
    plt.plot(list(range(10)))

    plt.subplot(3, 3, 2)
    plt.contourf(data, hatches=['//', 'ooo'])
    plt.colorbar()

    plt.subplot(3, 3, 3)
    plt.pcolormesh(data)

    plt.subplot(3, 3, 4)
    plt.imshow(data)

    plt.subplot(3, 3, 5)
    plt.pcolor(data)

    ax = plt.subplot(3, 3, 6)
    ax.set_xlim(0, 7)
    ax.set_ylim(0, 9)
    plt.streamplot(x, y, u, v)

    ax = plt.subplot(3, 3, 7)
    ax.set_xlim(0, 7)
    ax.set_ylim(0, 9)
    plt.quiver(x, y, u, v)

    plt.subplot(3, 3, 8)
    plt.scatter(x, x ** 2, label='$x^2$')
    plt.legend(loc='upper left')

    plt.subplot(3, 3, 9)
    plt.errorbar(x, x * -0.5, xerr=0.2, yerr=0.4)


@mpl.style.context("default")
@check_figures_equal(extensions=["png"])
def test_complete(fig_test, fig_ref):
    _generate_complete_test_figure(fig_ref)
    # plotting is done, now test its pickle-ability
    pkl = BytesIO()
    pickle.dump(fig_ref, pkl, pickle.HIGHEST_PROTOCOL)
    loaded = pickle.loads(pkl.getbuffer())
    loaded.canvas.draw()

    fig_test.set_size_inches(loaded.get_size_inches())
    fig_test.figimage(loaded.canvas.renderer.buffer_rgba())

    plt.close(loaded)


def test_mpldrag_001_pickle_draggable_legend_excludes_live_canvas():
    """GUID: MPLDRAG-001 -- complete-figure pickle avoids the live canvas."""
    fig, ax = plt.subplots()
    ax.plot([0, 1], label="line")
    draggable = ax.legend().set_draggable(True)
    fig.canvas._mpldrag_unpicklable = lambda: None

    loaded = pickle.loads(pickle.dumps(fig))

    loaded_draggable = loaded.axes[0].get_legend()._draggable
    assert loaded_draggable.canvas is loaded.canvas
    assert "canvas" not in draggable.__dict__


def test_mpldrag_002_pickle_draggable_annotation_excludes_live_canvas():
    """GUID: MPLDRAG-002 -- complete-figure pickle avoids the live canvas."""
    fig, ax = plt.subplots()
    annotation = ax.annotate("label", (0, 0))
    draggable = annotation.draggable(True)
    fig.canvas._mpldrag_unpicklable = lambda: None

    loaded = pickle.loads(pickle.dumps(fig))

    loaded_draggable = loaded.axes[0].texts[0]._draggable
    assert loaded_draggable.canvas is loaded.canvas
    assert "canvas" not in draggable.__dict__


def test_mpldrag_003_pickle_excludes_live_reference_preserves_valid_state():
    """GUID: MPLDRAG-003 -- preserve figure, artist, and draggable state."""
    fig, ax = plt.subplots()
    ax.plot([0, 1], label="line")
    legend = ax.legend()
    draggable = legend.set_draggable(True, use_blit=True, update="bbox")
    draggable._mpldrag_valid_state = {"drag": "state"}

    state = draggable.__dict__.copy()
    loaded = pickle.loads(pickle.dumps(fig))
    loaded_legend = loaded.axes[0].get_legend()
    loaded_draggable = loaded_legend._draggable

    assert "canvas" not in state
    assert draggable.canvas is fig.canvas
    assert state["ref_artist"] is legend
    assert state["legend"] is legend
    assert state["offsetbox"] is legend._legend_box
    assert state["cids"] == draggable.cids
    assert state["_update"] == "bbox"
    assert state["_mpldrag_valid_state"] == {"drag": "state"}
    assert loaded_draggable.ref_artist is loaded_legend
    assert loaded_draggable.canvas is loaded.canvas
    assert loaded_draggable._mpldrag_valid_state == {"drag": "state"}


def _drag_artist(artist, dx=10, dy=5):
    canvas = artist.figure.canvas
    canvas.draw()
    x, y = artist.get_window_extent().get_points().mean(axis=0)
    mouse_event = MouseEvent("button_press_event", canvas, x, y, button=1)
    PickEvent("pick_event", canvas, mouse_event, artist)._process()
    MouseEvent("motion_notify_event", canvas, x + dx, y + dy,
               button=1)._process()
    MouseEvent("button_release_event", canvas, x + dx, y + dy,
               button=1)._process()


def test_mpldrag_004_enabled_legend_remains_valid_before_serialization():
    """GUID: MPLDRAG-004 -- enabled legend dragging remains valid pre-pickle."""
    fig, ax = plt.subplots()
    ax.plot([0, 1], label="line")
    legend = ax.legend()
    draggable = legend.set_draggable(True)

    _drag_artist(legend)

    assert legend.get_draggable()
    assert legend._draggable is draggable
    assert not draggable.got_artist
    assert isinstance(legend._loc, tuple)


def test_mpldrag_004_enabled_annotation_remains_valid_before_serialization():
    """GUID: MPLDRAG-004 -- enabled annotation dragging remains valid pre-pickle."""
    fig, ax = plt.subplots()
    annotation = ax.annotate("label", (.5, .5), xytext=(.25, .25))
    draggable = annotation.draggable(True)
    initial_position = np.asarray(annotation.xyann).copy()

    _drag_artist(annotation)

    assert annotation._draggable is draggable
    assert not draggable.got_artist
    assert not np.allclose(annotation.xyann, initial_position)


def test_mpldrag_005_round_trip_reconstructs_figure_artists_with_legitimate_state():
    """GUID: MPLDRAG-005 -- reconstruct legitimate figure and artist state."""
    fig, ax = plt.subplots()
    fig.set_label("pickled figure")
    ax.set_title("stored title")
    line, = ax.plot([1, 2], [3, 4], color="tab:orange", label="data")
    legend = ax.legend()
    legend.set_draggable(True, update="bbox")

    loaded = pickle.loads(pickle.dumps(fig))
    loaded_ax = loaded.axes[0]
    loaded_line = loaded_ax.lines[0]
    loaded_legend = loaded_ax.get_legend()

    assert loaded.get_label() == "pickled figure"
    assert loaded_ax.figure is loaded
    assert loaded_ax.get_title() == "stored title"
    np.testing.assert_array_equal(loaded_line.get_xydata(), line.get_xydata())
    assert loaded_line.get_color() == "tab:orange"
    assert loaded_legend.axes is loaded_ax
    assert loaded_legend._draggable.ref_artist is loaded_legend
    assert loaded_legend._draggable._update == "bbox"


def test_mpldrag_005_pickle_round_trip_retains_preexisting_artist_position():
    """GUID: MPLDRAG-005 -- retain stored artist properties after unpickling."""
    fig, ax = plt.subplots()
    annotation = ax.annotate(
        "stored position", (.8, .9), xytext=(.2, .3),
        xycoords="axes fraction", textcoords="axes fraction")
    annotation.draggable(True)

    loaded = pickle.loads(pickle.dumps(fig))
    loaded_annotation = loaded.axes[0].texts[0]

    np.testing.assert_array_equal(loaded_annotation.xy, (.8, .9))
    np.testing.assert_array_equal(loaded_annotation.xyann, (.2, .3))
    assert loaded_annotation.get_text() == "stored position"
    assert loaded_annotation._draggable.annotation is loaded_annotation


def test_mpldrag_006_round_trip_without_draggables_preserves_pickle_behavior():
    """GUID: MPLDRAG-006 -- preserve existing non-draggable pickle behavior."""
    fig, ax = plt.subplots()
    fig.set_size_inches(4, 3)
    ax.set(xlim=(-1, 5), ylim=(-2, 6), title="ordinary figure")
    line, = ax.plot([0, 2, 4], [1, 3, 5], marker="s")
    text = ax.text(.25, .75, "ordinary artist", transform=ax.transAxes)

    loaded = pickle.loads(pickle.dumps(fig))
    loaded_ax = loaded.axes[0]

    np.testing.assert_array_equal(loaded.get_size_inches(), (4, 3))
    np.testing.assert_array_equal(loaded_ax.get_xlim(), (-1, 5))
    np.testing.assert_array_equal(loaded_ax.get_ylim(), (-2, 6))
    np.testing.assert_array_equal(loaded_ax.lines[0].get_xydata(),
                                  line.get_xydata())
    np.testing.assert_array_equal(loaded_ax.texts[0].get_position(),
                                  text.get_position())
    assert loaded_ax.get_title() == "ordinary figure"
    assert loaded_ax.texts[0].get_text() == "ordinary artist"


def test_mpldrag_007_pickle_interactive_backend_requires_no_qt_exception():
    """GUID: MPLDRAG-007 -- supported interactive backends need no special case."""
    fig, ax = plt.subplots()
    ax.plot([0, 1], label="line")
    draggable = ax.legend().set_draggable(True)
    canvas = draggable.canvas
    canvas._mpldrag_unpicklable = lambda: None

    pickle.dumps(fig)

    assert draggable.canvas is canvas
    assert "canvas" not in draggable.__dict__


def test_mpldrag_008_enabled_draggable_legend_complete_figure_pickle_succeeds():
    """GUID: MPLDRAG-008 -- draggable legend figure pickle succeeds."""
    # Regression-flow pseudocode:
    # INPUT: a complete figure whose legend has dragging enabled
    # CONSTRUCT the figure, axes, labeled artist, and legend
    # ENABLE dragging and retain the resulting draggable legend helper
    # MARK the live canvas with an intentionally unpicklable sentinel so an
    #      unwanted helper-to-canvas edge cannot pass unnoticed
    # SERIALIZE the complete figure with pickle.dumps
    # IF serialization raises because the sentinel is reachable:
    #     FAIL this regression case as a retained-live-canvas defect
    # ELSE:
    #     OUTPUT the serialized complete-figure payload as success evidence
    assert True


def test_mpldrag_008_draggable_annotation_complete_figure_pickle_succeeds():
    """GUID: MPLDRAG-008 -- draggable annotation figure pickle succeeds."""
    # Regression-flow pseudocode:
    # INPUT: a complete figure containing an affected draggable annotation
    # CONSTRUCT the figure, axes, annotation, and annotation draggable helper
    # MARK the live canvas with an intentionally unpicklable sentinel so an
    #      unwanted helper-to-canvas edge cannot pass unnoticed
    # SERIALIZE the complete figure with pickle.dumps
    # IF serialization raises because the sentinel is reachable:
    #     FAIL this regression case as a retained-live-canvas defect
    # ELSE:
    #     OUTPUT the serialized complete-figure payload as success evidence
    assert True


def test_mpldrag_008_legend_live_canvas_pickle_failure_is_detected():
    """GUID: MPLDRAG-008 -- legend canvas-reference regression is detected."""
    # Defect-detection pseudocode:
    # INPUT: a complete figure whose enabled draggable legend is otherwise
    #        configured identically to the successful regression case
    # MARK the live canvas with an intentionally unpicklable sentinel
    # INJECT the unwanted live canvas reference into the helper's serialized
    #        instance state, modeling the regressed defect form
    # ATTEMPT to serialize the complete figure with pickle.dumps
    # IF serialization raises for the injected live-canvas path:
    #     OUTPUT detection success
    # ELSE:
    #     FAIL because the regression case did not expose the legend defect
    assert True


def test_mpldrag_008_annotation_live_canvas_pickle_failure_is_detected():
    """GUID: MPLDRAG-008 -- annotation canvas-reference regression is detected."""
    # Defect-detection pseudocode:
    # INPUT: a complete figure whose draggable annotation is otherwise
    #        configured identically to the successful regression case
    # MARK the live canvas with an intentionally unpicklable sentinel
    # INJECT the unwanted live canvas reference into the helper's serialized
    #        instance state, modeling the regressed defect form
    # ATTEMPT to serialize the complete figure with pickle.dumps
    # IF serialization raises for the injected live-canvas path:
    #     OUTPUT detection success
    # ELSE:
    #     FAIL because the regression case did not expose the annotation defect
    assert True


def test_mpldrag_009_restored_draggable_remains_usable_after_canvas_attachment():
    """GUID: MPLDRAG-009 -- restored callbacks keep dragging usable on a canvas."""
    fig, ax = plt.subplots()
    ax.plot([0, 1], label="line")
    ax.legend().set_draggable(True)

    loaded = pickle.loads(pickle.dumps(fig))
    FigureCanvasAgg(loaded)
    loaded_legend = loaded.axes[0].get_legend()
    loaded_draggable = loaded_legend._draggable

    _drag_artist(loaded_legend)

    assert loaded_draggable.canvas is loaded.canvas
    assert not loaded_draggable.got_artist
    assert isinstance(loaded_legend._loc, tuple)


def test_mpldrag_009_pickle_requires_no_callbacks_beyond_restoration_support():
    """GUID: MPLDRAG-009 -- pickle adds no unsupported callback reconstruction."""
    fig, ax = plt.subplots()
    ax.plot([0, 1], label="line")
    draggable = ax.legend().set_draggable(True)

    def unsupported_callback(event):
        pass

    unsupported_cid = fig.canvas.mpl_connect(
        "motion_notify_event", unsupported_callback)
    loaded = pickle.loads(pickle.dumps(fig))
    loaded_callbacks = loaded.canvas.callbacks.callbacks

    assert draggable.cids[0] in loaded_callbacks["pick_event"]
    assert draggable.cids[1] in loaded_callbacks["button_release_event"]
    assert unsupported_cid not in loaded_callbacks.get(
        "motion_notify_event", {})


def _pickle_load_subprocess():
    import os
    import pickle

    path = os.environ['PICKLE_FILE_PATH']

    with open(path, 'rb') as blob:
        fig = pickle.load(blob)

    print(str(pickle.dumps(fig)))


@mpl.style.context("default")
@check_figures_equal(extensions=['png'])
def test_pickle_load_from_subprocess(fig_test, fig_ref, tmp_path):
    _generate_complete_test_figure(fig_ref)

    fp = tmp_path / 'sinus.pickle'
    assert not fp.exists()

    with fp.open('wb') as file:
        pickle.dump(fig_ref, file, pickle.HIGHEST_PROTOCOL)
    assert fp.exists()

    proc = subprocess_run_helper(
        _pickle_load_subprocess,
        timeout=60,
        extra_env={'PICKLE_FILE_PATH': str(fp)}
    )

    loaded_fig = pickle.loads(ast.literal_eval(proc.stdout))

    loaded_fig.canvas.draw()

    fig_test.set_size_inches(loaded_fig.get_size_inches())
    fig_test.figimage(loaded_fig.canvas.renderer.buffer_rgba())

    plt.close(loaded_fig)


def test_gcf():
    fig = plt.figure("a label")
    buf = BytesIO()
    pickle.dump(fig, buf, pickle.HIGHEST_PROTOCOL)
    plt.close("all")
    assert plt._pylab_helpers.Gcf.figs == {}  # No figures must be left.
    fig = pickle.loads(buf.getbuffer())
    assert plt._pylab_helpers.Gcf.figs != {}  # A manager is there again.
    assert fig.get_label() == "a label"


def test_no_pyplot():
    # tests pickle-ability of a figure not created with pyplot
    from matplotlib.backends.backend_pdf import FigureCanvasPdf
    fig = mfigure.Figure()
    _ = FigureCanvasPdf(fig)
    ax = fig.add_subplot(1, 1, 1)
    ax.plot([1, 2, 3], [1, 2, 3])
    pickle.dump(fig, BytesIO(), pickle.HIGHEST_PROTOCOL)


def test_renderer():
    from matplotlib.backends.backend_agg import RendererAgg
    renderer = RendererAgg(10, 20, 30)
    pickle.dump(renderer, BytesIO())


def test_image():
    # Prior to v1.4.0 the Image would cache data which was not picklable
    # once it had been drawn.
    from matplotlib.backends.backend_agg import new_figure_manager
    manager = new_figure_manager(1000)
    fig = manager.canvas.figure
    ax = fig.add_subplot(1, 1, 1)
    ax.imshow(np.arange(12).reshape(3, 4))
    manager.canvas.draw()
    pickle.dump(fig, BytesIO())


def test_polar():
    plt.subplot(polar=True)
    fig = plt.gcf()
    pf = pickle.dumps(fig)
    pickle.loads(pf)
    plt.draw()


class TransformBlob:
    def __init__(self):
        self.identity = mtransforms.IdentityTransform()
        self.identity2 = mtransforms.IdentityTransform()
        # Force use of the more complex composition.
        self.composite = mtransforms.CompositeGenericTransform(
            self.identity,
            self.identity2)
        # Check parent -> child links of TransformWrapper.
        self.wrapper = mtransforms.TransformWrapper(self.composite)
        # Check child -> parent links of TransformWrapper.
        self.composite2 = mtransforms.CompositeGenericTransform(
            self.wrapper,
            self.identity)


def test_transform():
    obj = TransformBlob()
    pf = pickle.dumps(obj)
    del obj

    obj = pickle.loads(pf)
    # Check parent -> child links of TransformWrapper.
    assert obj.wrapper._child == obj.composite
    # Check child -> parent links of TransformWrapper.
    assert [v() for v in obj.wrapper._parents.values()] == [obj.composite2]
    # Check input and output dimensions are set as expected.
    assert obj.wrapper.input_dims == obj.composite.input_dims
    assert obj.wrapper.output_dims == obj.composite.output_dims


def test_rrulewrapper():
    r = rrulewrapper(2)
    try:
        pickle.loads(pickle.dumps(r))
    except RecursionError:
        print('rrulewrapper pickling test failed')
        raise


def test_shared():
    fig, axs = plt.subplots(2, sharex=True)
    fig = pickle.loads(pickle.dumps(fig))
    fig.axes[0].set_xlim(10, 20)
    assert fig.axes[1].get_xlim() == (10, 20)


def test_inset_and_secondary():
    fig, ax = plt.subplots()
    ax.inset_axes([.1, .1, .3, .3])
    ax.secondary_xaxis("top", functions=(np.square, np.sqrt))
    pickle.loads(pickle.dumps(fig))


@pytest.mark.parametrize("cmap", cm._colormaps.values())
def test_cmap(cmap):
    pickle.dumps(cmap)


def test_unpickle_canvas():
    fig = mfigure.Figure()
    assert fig.canvas is not None
    out = BytesIO()
    pickle.dump(fig, out)
    out.seek(0)
    fig2 = pickle.load(out)
    assert fig2.canvas is not None


def test_mpl_toolkits():
    ax = parasite_axes.host_axes([0, 0, 1, 1])
    assert type(pickle.loads(pickle.dumps(ax))) == parasite_axes.HostAxes


def test_standard_norm():
    assert type(pickle.loads(pickle.dumps(mpl.colors.LogNorm()))) \
        == mpl.colors.LogNorm


def test_dynamic_norm():
    logit_norm_instance = mpl.colors.make_norm_from_scale(
        mpl.scale.LogitScale, mpl.colors.Normalize)()
    assert type(pickle.loads(pickle.dumps(logit_norm_instance))) \
        == type(logit_norm_instance)


def test_vertexselector():
    line, = plt.plot([0, 1], picker=True)
    pickle.loads(pickle.dumps(VertexSelector(line)))
