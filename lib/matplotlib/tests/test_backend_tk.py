import functools
import importlib
import os
import platform
import subprocess
import sys

import pytest

from matplotlib import _c_internal_utils
from matplotlib.testing import subprocess_run_helper


_test_timeout = 60  # A reasonably safe value for slower architectures.


def _isolated_tk_test(success_count, func=None):
    """
    A decorator to run *func* in a subprocess and assert that it prints
    "success" *success_count* times and nothing on stderr.

    TkAgg tests seem to have interactions between tests, so isolate each test
    in a subprocess. See GH#18261
    """

    if func is None:
        return functools.partial(_isolated_tk_test, success_count)

    if "MPL_TEST_ESCAPE_HATCH" in os.environ:
        # set in subprocess_run_helper() below
        return func

    @pytest.mark.skipif(
        not importlib.util.find_spec('tkinter'),
        reason="missing tkinter"
    )
    @pytest.mark.skipif(
        sys.platform == "linux" and not _c_internal_utils.display_is_valid(),
        reason="$DISPLAY and $WAYLAND_DISPLAY are unset"
    )
    @functools.wraps(func)
    def test_func():
        # even if the package exists, may not actually be importable this can
        # be the case on some CI systems.
        pytest.importorskip('tkinter')
        try:
            proc = subprocess_run_helper(
                func, timeout=_test_timeout, extra_env=dict(
                    MPLBACKEND="TkAgg", MPL_TEST_ESCAPE_HATCH="1"))
        except subprocess.TimeoutExpired:
            pytest.fail("Subprocess timed out")
        except subprocess.CalledProcessError as e:
            pytest.fail("Subprocess failed to test intended behavior\n"
                        + str(e.stderr))
        else:
            # macOS may actually emit irrelevant errors about Accelerated
            # OpenGL vs. software OpenGL, or some permission error on Azure, so
            # suppress them.
            # Asserting stderr first (and printing it on failure) should be
            # more helpful for debugging that printing a failed success count.
            ignored_lines = ["OpenGL", "CFMessagePort: bootstrap_register",
                             "/usr/include/servers/bootstrap_defs.h"]
            assert not [line for line in proc.stderr.splitlines()
                        if all(msg not in line for msg in ignored_lines)]
            assert proc.stdout.count("success") == success_count

    return test_func


@pytest.mark.backend('TkAgg', skip_on_importerror=True)
@_isolated_tk_test(success_count=1)
def test_input_006_tkagg_clear_rebuild_redraw_recreated_widget_invokes_callback():
    """GUID: INPUT-006 - TkAgg preserves recreated-widget interaction."""
    import matplotlib.pyplot as plt
    from matplotlib.widgets import Button, RangeSlider

    fig = plt.figure(figsize=(4, 3))
    state = {"button_clicks": [], "rebuilds": 0, "widgets": []}

    def rebuild():
        fig.clear()
        slider = RangeSlider(
            fig.add_axes([.1, .55, .8, .2]), "", 0, 1,
            valinit=(.2, .8))
        button = Button(fig.add_axes([.4, .15, .2, .2]), "Button")
        slider.on_changed(changed)
        button.on_clicked(state["button_clicks"].append)
        state.update(slider=slider, button=button)
        state["widgets"].append((slider, button))
        state["rebuilds"] += 1
        fig.canvas.draw()

    def changed(values):
        rebuild()

    def click(widget, xy):
        x, y = widget.ax.transData.transform(xy)
        tk_y = fig.bbox.height - y
        tk_canvas.event_generate(
            "<ButtonPress-1>", x=round(x), y=round(tk_y))
        tk_canvas.event_generate(
            "<ButtonRelease-1>", x=round(x), y=round(tk_y))
        tk_canvas.update()

    rebuild()
    fig.canvas.manager.show()
    tk_canvas = fig.canvas.get_tk_widget()
    tk_canvas.update()

    original_slider = state["slider"]
    click(original_slider, (.35, .5))
    recreated_button = state["button"]
    click(recreated_button, (.5, .5))

    assert state["rebuilds"] == 2
    assert len(state["button_clicks"]) == 1
    assert original_slider.ax not in fig.axes
    assert fig.canvas.mouse_grabber is None
    plt.close(fig)
    print("success")


@_isolated_tk_test(success_count=6)  # len(bad_boxes)
def test_blit():
    import matplotlib.pyplot as plt
    import numpy as np
    import matplotlib.backends.backend_tkagg  # noqa
    from matplotlib.backends import _backend_tk, _tkagg

    fig, ax = plt.subplots()
    photoimage = fig.canvas._tkphoto
    data = np.ones((4, 4, 4))
    height, width = data.shape[:2]
    dataptr = (height, width, data.ctypes.data)
    # Test out of bounds blitting.
    bad_boxes = ((-1, 2, 0, 2),
                 (2, 0, 0, 2),
                 (1, 6, 0, 2),
                 (0, 2, -1, 2),
                 (0, 2, 2, 0),
                 (0, 2, 1, 6))
    for bad_box in bad_boxes:
        try:
            _tkagg.blit(
                photoimage.tk.interpaddr(), str(photoimage), dataptr, 0,
                (0, 1, 2, 3), bad_box)
        except ValueError:
            print("success")

    # Test blitting to a destroyed canvas.
    plt.close(fig)
    _backend_tk.blit(photoimage, data, (0, 1, 2, 3))


@_isolated_tk_test(success_count=1)
def test_figuremanager_preserves_host_mainloop():
    import tkinter
    import matplotlib.pyplot as plt
    success = []

    def do_plot():
        plt.figure()
        plt.plot([1, 2], [3, 5])
        plt.close()
        root.after(0, legitimate_quit)

    def legitimate_quit():
        root.quit()
        success.append(True)

    root = tkinter.Tk()
    root.after(0, do_plot)
    root.mainloop()

    if success:
        print("success")


@pytest.mark.skipif(platform.python_implementation() != 'CPython',
                    reason='PyPy does not support Tkinter threading: '
                           'https://foss.heptapod.net/pypy/pypy/-/issues/1929')
@pytest.mark.flaky(reruns=3)
@_isolated_tk_test(success_count=1)
def test_figuremanager_cleans_own_mainloop():
    import tkinter
    import time
    import matplotlib.pyplot as plt
    import threading
    from matplotlib.cbook import _get_running_interactive_framework

    root = tkinter.Tk()
    plt.plot([1, 2, 3], [1, 2, 5])

    def target():
        while not 'tk' == _get_running_interactive_framework():
            time.sleep(.01)
        plt.close()
        if show_finished_event.wait():
            print('success')

    show_finished_event = threading.Event()
    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    plt.show(block=True)  # Testing if this function hangs.
    show_finished_event.set()
    thread.join()


@pytest.mark.backend('TkAgg', skip_on_importerror=True)
@pytest.mark.flaky(reruns=3)
@_isolated_tk_test(success_count=0)
def test_never_update():
    import tkinter
    del tkinter.Misc.update
    del tkinter.Misc.update_idletasks

    import matplotlib.pyplot as plt
    fig = plt.figure()
    plt.show(block=False)

    plt.draw()  # Test FigureCanvasTkAgg.
    fig.canvas.toolbar.configure_subplots()  # Test NavigationToolbar2Tk.
    # Test FigureCanvasTk filter_destroy callback
    fig.canvas.get_tk_widget().after(100, plt.close, fig)

    # Check for update() or update_idletasks() in the event queue, functionally
    # equivalent to tkinter.Misc.update.
    plt.show(block=True)

    # Note that exceptions would be printed to stderr; _isolated_tk_test
    # checks them.


@_isolated_tk_test(success_count=2)
def test_missing_back_button():
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

    class Toolbar(NavigationToolbar2Tk):
        # Only display the buttons we need.
        toolitems = [t for t in NavigationToolbar2Tk.toolitems if
                     t[0] in ('Home', 'Pan', 'Zoom')]

    fig = plt.figure()
    print("success")
    Toolbar(fig.canvas, fig.canvas.manager.window)  # This should not raise.
    print("success")


@pytest.mark.backend('TkAgg', skip_on_importerror=True)
@_isolated_tk_test(success_count=1)
def test_canvas_focus():
    import tkinter as tk
    import matplotlib.pyplot as plt
    success = []

    def check_focus():
        tkcanvas = fig.canvas.get_tk_widget()
        # Give the plot window time to appear
        if not tkcanvas.winfo_viewable():
            tkcanvas.wait_visibility()
        # Make sure the canvas has the focus, so that it's able to receive
        # keyboard events.
        if tkcanvas.focus_lastfor() == tkcanvas:
            success.append(True)
        plt.close()
        root.destroy()

    root = tk.Tk()
    fig = plt.figure()
    plt.plot([1, 2, 3])
    root.after(0, plt.show)
    root.after(100, check_focus)
    root.mainloop()

    if success:
        print("success")


@_isolated_tk_test(success_count=2)
def test_embedding():
    import tkinter as tk
    from matplotlib.backends.backend_tkagg import (
        FigureCanvasTkAgg, NavigationToolbar2Tk)
    from matplotlib.backend_bases import key_press_handler
    from matplotlib.figure import Figure

    root = tk.Tk()

    def test_figure(master):
        fig = Figure()
        ax = fig.add_subplot()
        ax.plot([1, 2, 3])

        canvas = FigureCanvasTkAgg(fig, master=master)
        canvas.draw()
        canvas.mpl_connect("key_press_event", key_press_handler)
        canvas.get_tk_widget().pack(expand=True, fill="both")

        toolbar = NavigationToolbar2Tk(canvas, master, pack_toolbar=False)
        toolbar.pack(expand=True, fill="x")

        canvas.get_tk_widget().forget()
        toolbar.forget()

    test_figure(root)
    print("success")

    # Test with a dark button color. Doesn't actually check whether the icon
    # color becomes lighter, just that the code doesn't break.

    root.tk_setPalette(background="sky blue", selectColor="midnight blue",
                       foreground="white")
    test_figure(root)
    print("success")
