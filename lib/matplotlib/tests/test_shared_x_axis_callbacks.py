"""Tests for callback notification across shared x-axes."""

import matplotlib.pyplot as plt


def test_XLIM_001_emitted_shared_change_notifies_each_affected_axis_once():
    """GUID: XLIM-001 - Each affected shared axis emits exactly once."""
    _, axes = plt.subplots(2, sharex=True)
    events = []
    for ax in axes:
        ax.callbacks.connect("xlim_changed", events.append)

    axes[0].set_xlim(2, 5)

    assert events.count(axes[0]) == 1
    assert events.count(axes[1]) == 1


def test_XLIM_002_emitted_shared_change_synchronizes_affected_limits():
    """GUID: XLIM-002 - Affected shared axes end with equal x-limits."""
    _, axes = plt.subplots(3, sharex=True)

    axes[1].set_xlim(-2, 8)

    assert all(ax.get_xlim() == (-2, 8) for ax in axes)


def test_XLIM_003_emitted_shared_change_terminates_without_recursion(
        monkeypatch):
    """GUID: XLIM-003 - Propagation terminates without cycles or reapplication."""
    _, axes = plt.subplots(3, sharex=True)
    calls = []
    for ax in axes:
        original = ax.xaxis._set_lim

        def record(*args, _ax=ax, _original=original, **kwargs):
            calls.append((_ax, kwargs["emit"]))
            return _original(*args, **kwargs)

        monkeypatch.setattr(ax.xaxis, "_set_lim", record)

    axes[0].set_xlim(1, 4)

    assert calls.count((axes[0], True)) == 1
    assert all(calls.count((ax, False)) == 1 for ax in axes[1:])
    assert len(calls) == 3


def test_XLIM_004_changed_callback_receives_its_reporting_axis():
    """GUID: XLIM-004 - Each callback receives the axis it reports."""
    _, axes = plt.subplots(2, sharex=True)
    reported = []
    for ax in axes:
        ax.callbacks.connect(
            "xlim_changed", lambda changed, expected=ax:
            reported.append((changed, expected)))

    axes[0].set_xlim(2, 5)

    assert len(reported) == 2
    assert all(changed is expected for changed, expected in reported)


def test_XLIM_005_indirect_axis_is_synchronized_before_callback():
    """GUID: XLIM-005 - Indirect limits are synchronized before notification."""
    _, axes = plt.subplots(2, sharex=True)
    observed_limits = []
    axes[1].callbacks.connect(
        "xlim_changed", lambda changed: observed_limits.append(
            changed.get_xlim()))

    axes[0].set_xlim(-3, 6)

    assert observed_limits == [(-3, 6)]


def test_XLIM_006_emitting_initiator_retains_direct_notification():
    """GUID: XLIM-006 - The initiating axis retains direct notification."""
    _, axes = plt.subplots(2, sharex=True)
    events = []
    axes[1].callbacks.connect("xlim_changed", events.append)

    axes[1].set_xlim(4, 9)

    assert events == [axes[1]]


def test_XLIM_007_emitted_shared_change_leaves_outside_axis_unchanged():
    """GUID: XLIM-007 - Outside axes neither change nor emit notification."""
    fig = plt.figure()
    shared = [fig.add_subplot(221)]
    shared.append(fig.add_subplot(222, sharex=shared[0]))
    outside = fig.add_subplot(223)
    outside.set_xlim(10, 20, emit=False)
    events = []
    outside.callbacks.connect("xlim_changed", events.append)

    shared[0].set_xlim(-1, 1)

    assert all(ax.get_xlim() == (-1, 1) for ax in shared)
    assert outside.get_xlim() == (10, 20)
    assert events == []


def test_XLIM_008_direct_change_with_emit_false_suppresses_callback():
    """GUID: XLIM-008 - Direct emit=False retains callback suppression."""
    _, ax = plt.subplots()
    events = []
    ax.callbacks.connect("xlim_changed", events.append)

    ax.set_xlim(3, 7, emit=False)

    assert ax.get_xlim() == (3, 7)
    assert events == []


def test_shared_y_axis_callback_notifies_each_affected_axis():
    _, axes = plt.subplots(2, sharey=True)
    events = []
    for ax in axes:
        ax.callbacks.connect("ylim_changed", events.append)

    axes[0].set_ylim(2, 5)

    assert events == [axes[0], axes[1]]
