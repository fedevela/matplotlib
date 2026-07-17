from io import BytesIO
import ast
import pickle
import weakref

import numpy as np
import pytest

import matplotlib as mpl
from matplotlib import cm
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


def test_mplal_001_multiple_subplots_serialize_after_align_labels():
    fig, axs = plt.subplots(2, 2)
    for ax in axs.flat:
        ax.set(xlabel="x", ylabel="y")
    fig.align_labels()

    pickle.dumps(fig)


def test_mplal_002_aligned_label_state_serializes_without_weakref_failure():
    fig, _ = plt.subplots(2, 1)
    fig.align_labels()

    state = fig._align_label_groups["x"].__getstate__()
    assert all(not isinstance(member, weakref.ReferenceType)
               for group in state for member in group)
    pickle.dumps(fig)


def test_mplal_003_serialized_aligned_label_figure_deserializes_usable():
    fig, _ = plt.subplots(2, 1)
    fig.align_labels()

    restored = pickle.loads(pickle.dumps(fig))

    restored.canvas.draw()
    assert len(restored.axes) == 2


def test_mplal_004_label_alignment_remains_effective_after_pickle_round_trip():
    fig, axs = plt.subplots(2, 2)
    for ax in axs.flat:
        ax.set(xlabel="x", ylabel="y")
    axs[0, 0].set_yticks([0], ["a long tick label"])
    axs[1, 0].set_yticks([0], ["0"])
    fig.align_labels()

    restored = pickle.loads(pickle.dumps(fig))
    restored_axs = restored.axes

    x_grouper = restored._align_label_groups["x"]
    y_grouper = restored._align_label_groups["y"]
    assert x_grouper.joined(restored_axs[0], restored_axs[1])
    assert y_grouper.joined(restored_axs[0], restored_axs[2])
    assert x_grouper.get_siblings(restored_axs[0]) == restored_axs[:2]
    assert y_grouper.get_siblings(restored_axs[0]) == restored_axs[::2]
    restored.canvas.draw()
    assert (restored_axs[0].yaxis.label.get_position()[0]
            == pytest.approx(restored_axs[2].yaxis.label.get_position()[0]))


def test_mplal_005_axes_data_and_label_text_remain_intact_after_round_trip():
    fig, axs = plt.subplots(2, 1)
    expected = []
    for i, ax in enumerate(axs):
        x = np.arange(3)
        y = x + i
        ax.plot(x, y)
        ax.set(xlabel=f"x label {i}", ylabel=f"y label {i}")
        expected.append((x, y, ax.get_xlabel(), ax.get_ylabel()))
    fig.align_labels()

    restored = pickle.loads(pickle.dumps(fig))

    assert len(restored.axes) == len(expected)
    for ax, (x, y, xlabel, ylabel) in zip(restored.axes, expected):
        assert len(ax.lines) == 1
        np.testing.assert_array_equal(ax.lines[0].get_xdata(), x)
        np.testing.assert_array_equal(ax.lines[0].get_ydata(), y)
        assert ax.get_xlabel() == xlabel
        assert ax.get_ylabel() == ylabel


def test_mplal_006_unaligned_figure_pickle_dumps_and_loads_without_exception():
    fig, ax = plt.subplots()
    ax.set(xlabel="x label", ylabel="y label")

    payload = pickle.dumps(fig)
    restored = pickle.loads(payload)

    assert isinstance(restored, mfigure.Figure)
    assert len(restored.axes) == 1


def test_mplal_006_deserialized_unaligned_figure_axes_data_labels_remain_usable():
    fig, axs = plt.subplots(2, 1)
    expected = []
    for i, ax in enumerate(axs):
        x = np.arange(4)
        y = x ** 2 + i
        ax.plot(x, y)
        ax.set(xlabel=f"x label {i}", ylabel=f"y label {i}")
        expected.append((x, y, ax.get_xlabel(), ax.get_ylabel()))

    assert all(list(group) == []
               for group in fig._align_label_groups.values())
    restored = pickle.loads(pickle.dumps(fig))

    assert len(restored.axes) == len(expected)
    assert all(list(group) == []
               for group in restored._align_label_groups.values())
    for ax, (x, y, xlabel, ylabel) in zip(restored.axes, expected):
        assert len(ax.lines) == 1
        np.testing.assert_array_equal(ax.lines[0].get_xdata(), x)
        np.testing.assert_array_equal(ax.lines[0].get_ydata(), y)
        assert ax.get_xlabel() == xlabel
        assert ax.get_ylabel() == ylabel
    restored.canvas.draw()


# MPLAL-007 / MPLAL-008 architecture contract: test_pickle owns the regression
# seam between Figure.align_labels() and the standard-library pickle round trip.
# Setup enters through pyplot's existing multi-subplot API; verification leaves
# through the restored Figure/Axes and canvas APIs.  Keep numeric samples on the
# test side of that seam so Figure serialization has no dependency on their
# values and requires no production adapter or alternate pickle entry point.


def test_mplal_007_aligned_multi_subplot_pickle_round_trip_returns_usable_figure():
    # MPLAL-007 ownership: this test owns the multi-subplot construction,
    # alignment call, pickle boundary, restored-Figure contract, and draw seam.
    # MPLAL-007 logic obligation:
    # GIVEN a Figure containing multiple labeled subplots,
    # WHEN align_labels() establishes the shared-label groups,
    # THEN serialize the Figure with pickle.dumps() and deserialize that payload
    # with pickle.loads(); allow either operation's exception to fail the test.
    # VERIFY the restored object is a Figure with the expected subplot count,
    # and draw its canvas to prove that the returned Figure remains usable.
    fig, axs = plt.subplots(2, 1)
    for i, ax in enumerate(axs):
        ax.set(xlabel=f"x label {i}", ylabel=f"y label {i}")
    fig.align_labels()

    payload = pickle.dumps(fig)
    restored = pickle.loads(payload)

    assert isinstance(restored, mfigure.Figure)
    assert len(restored.axes) == 2
    restored.canvas.draw()


def test_mplal_008_aligned_multi_subplot_pickle_round_trip_with_other_values_succeeds():
    # MPLAL-008 ownership: alternate values are injected by this test before
    # control crosses the same alignment/pickle seam owned above; production
    # Figure state must remain unaware of which deterministic samples were used.
    # MPLAL-008 logic obligation:
    # GIVEN deterministic x and y values distinct from the reported reproduction,
    # create multiple labeled subplots and plot those alternate values on each.
    # WHEN align_labels() is called, pickle.dumps() serializes the Figure, and
    # pickle.loads() restores it, allow any round-trip exception to fail the test.
    # VERIFY the restored Figure is usable and retains the expected axes and
    # alternate plotted values, demonstrating success is independent of the
    # reproduction's particular numeric values.
    x = np.array([-3.5, -0.25, 2.75, 8.5])
    ys = [
        np.array([7.25, -1.5, 12.75, 4.625]),
        np.array([-6.0, 3.125, 1.5, 9.75]),
    ]
    fig, axs = plt.subplots(2, 1)
    for i, (ax, y) in enumerate(zip(axs, ys)):
        ax.plot(x, y)
        ax.set(xlabel=f"alternate x {i}", ylabel=f"alternate y {i}")
    fig.align_labels()

    restored = pickle.loads(pickle.dumps(fig))

    assert isinstance(restored, mfigure.Figure)
    assert len(restored.axes) == len(ys)
    for ax, y in zip(restored.axes, ys):
        assert len(ax.lines) == 1
        np.testing.assert_array_equal(ax.lines[0].get_xdata(), x)
        np.testing.assert_array_equal(ax.lines[0].get_ydata(), y)
    restored.canvas.draw()


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
