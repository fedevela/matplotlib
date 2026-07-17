"""
Core functions and attributes for the matplotlib style library:

``use``
    Select style sheet to override the current matplotlib settings.
``context``
    Context manager to use a style sheet temporarily.
``available``
    List available style sheets.
``library``
    A dictionary of style names and matplotlib settings.
"""

import contextlib
import logging
import os
from pathlib import Path
import re
import warnings

import matplotlib as mpl
from matplotlib import _api, _docstring, rc_params_from_file, rcParamsDefault

_log = logging.getLogger(__name__)

__all__ = ['use', 'context', 'available', 'library', 'reload_library']


@_api.caching_module_getattr  # module-level deprecations
class __getattr__:
    STYLE_FILE_PATTERN = _api.deprecated("3.5", obj_type="")(property(
        lambda self: re.compile(r'([\S]+).%s$' % STYLE_EXTENSION)))


BASE_LIBRARY_PATH = os.path.join(mpl.get_data_path(), 'stylelib')
# Users may want multiple library paths, so store a list of paths.
USER_LIBRARY_PATHS = [os.path.join(mpl.get_configdir(), 'stylelib')]
STYLE_EXTENSION = 'mplstyle'
# A list of rcParams that should not be applied from styles
STYLE_BLACKLIST = {
    'interactive', 'backend', 'webagg.port', 'webagg.address',
    'webagg.port_retries', 'webagg.open_in_browser', 'backend_fallback',
    'toolbar', 'timezone', 'figure.max_open_warning',
    'figure.raise_window', 'savefig.directory', 'tk.window_focus',
    'docstring.hardcopy', 'date.epoch'}


def _remove_blacklisted_style_params(d, warn=True):
    o = {}
    for key in d:  # prevent triggering RcParams.__getitem__('backend')
        if key in STYLE_BLACKLIST:
            if warn:
                _api.warn_external(
                    f"Style includes a parameter, {key!r}, that is not "
                    "related to style.  Ignoring this parameter.")
        else:
            o[key] = d[key]
    return o


def _apply_style(d, warn=True):
    mpl.rcParams.update(_remove_blacklisted_style_params(d, warn=warn))


@_docstring.Substitution(
    "\n".join(map("- {}".format, sorted(STYLE_BLACKLIST, key=str.lower)))
)
def use(style):
    """
    Use Matplotlib style settings from a style specification.

    The style name of 'default' is reserved for reverting back to
    the default style settings.

    .. note::

       This updates the `.rcParams` with the settings from the style.
       `.rcParams` not defined in the style are kept.

    Parameters
    ----------
    style : str, dict, Path or list
        A style specification. Valid options are:

        +------+-------------------------------------------------------------+
        | str  | The name of a style or a path/URL to a style file. For a    |
        |      | list of available style names, see `.style.available`.      |
        +------+-------------------------------------------------------------+
        | dict | Dictionary with valid key/value pairs for                   |
        |      | `matplotlib.rcParams`.                                      |
        +------+-------------------------------------------------------------+
        | Path | A path-like object which is a path to a style file.         |
        +------+-------------------------------------------------------------+
        | list | A list of style specifiers (str, Path or dict) applied from |
        |      | first to last in the list.                                  |
        +------+-------------------------------------------------------------+

    Notes
    -----
    The following `.rcParams` are not related to style and will be ignored if
    found in a style specification:

    %s
    """
    if isinstance(style, (str, Path)) or hasattr(style, 'keys'):
        # If name is a single str, Path or dict, make it a single element list.
        styles = [style]
    else:
        styles = style

    style_alias = {'mpl20': 'default', 'mpl15': 'classic'}

    def fix_style(s):
        if isinstance(s, str):
            s = style_alias.get(s, s)
            if s in [
                "seaborn",
                "seaborn-bright",
                "seaborn-colorblind",
                "seaborn-dark",
                "seaborn-darkgrid",
                "seaborn-dark-palette",
                "seaborn-deep",
                "seaborn-muted",
                "seaborn-notebook",
                "seaborn-paper",
                "seaborn-pastel",
                "seaborn-poster",
                "seaborn-talk",
                "seaborn-ticks",
                "seaborn-white",
                "seaborn-whitegrid",
            ]:
                _api.warn_deprecated(
                    "3.6", message="The seaborn styles shipped by Matplotlib "
                    "are deprecated since %(since)s, as they no longer "
                    "correspond to the styles shipped by seaborn. However, "
                    "they will remain available as 'seaborn-v0_8-<style>'. "
                    "Alternatively, directly use the seaborn API instead.")
                s = s.replace("seaborn", "seaborn-v0_8")
        return s

    for style in map(fix_style, styles):
        if not isinstance(style, (str, Path)):
            _apply_style(style)
        elif style == 'default':
            # Deprecation warnings were already handled when creating
            # rcParamsDefault, no need to reemit them here.
            with _api.suppress_matplotlib_deprecation_warning():
                _apply_style(rcParamsDefault, warn=False)
        elif style in library:
            _apply_style(library[style])
        else:
            try:
                rc = rc_params_from_file(style, use_default_template=False)
                _apply_style(rc)
            except IOError as err:
                raise IOError(
                    "{!r} not found in the style library and input is not a "
                    "valid URL or path; see `style.available` for list of "
                    "available styles".format(style)) from err


@contextlib.contextmanager
def context(style, after_reset=False):
    """
    Context manager for using style settings temporarily.

    Parameters
    ----------
    style : str, dict, Path or list
        A style specification. Valid options are:

        +------+-------------------------------------------------------------+
        | str  | The name of a style or a path/URL to a style file. For a    |
        |      | list of available style names, see `.style.available`.      |
        +------+-------------------------------------------------------------+
        | dict | Dictionary with valid key/value pairs for                   |
        |      | `matplotlib.rcParams`.                                      |
        +------+-------------------------------------------------------------+
        | Path | A path-like object which is a path to a style file.         |
        +------+-------------------------------------------------------------+
        | list | A list of style specifiers (str, Path or dict) applied from |
        |      | first to last in the list.                                  |
        +------+-------------------------------------------------------------+

    after_reset : bool
        If True, apply style after resetting settings to their defaults;
        otherwise, apply style on top of the current settings.
    """
    with mpl.rc_context():
        if after_reset:
            mpl.rcdefaults()
        use(style)
        yield


@_api.deprecated("3.5")
def load_base_library():
    """Load style library defined in this package."""
    library = read_style_directory(BASE_LIBRARY_PATH)
    return library


@_api.deprecated("3.5")
def iter_user_libraries():
    for stylelib_path in USER_LIBRARY_PATHS:
        stylelib_path = os.path.expanduser(stylelib_path)
        if os.path.exists(stylelib_path) and os.path.isdir(stylelib_path):
            yield stylelib_path


def update_user_library(library):
    """Update style library with user-defined rc files."""
    for stylelib_path in map(os.path.expanduser, USER_LIBRARY_PATHS):
        styles = read_style_directory(stylelib_path)
        update_nested_dict(library, styles)
    return library


def read_style_directory(style_dir):
    """Return dictionary of styles defined in *style_dir*."""
    styles = dict()
    for path in Path(style_dir).glob(f"*.{STYLE_EXTENSION}"):
        with warnings.catch_warnings(record=True) as warns:
            styles[path.stem] = rc_params_from_file(
                path, use_default_template=False)
        for w in warns:
            _log.warning('In %s: %s', path, w.message)
    return styles


def update_nested_dict(main_dict, new_dict):
    """
    Update nested dict (only level of nesting) with new values.

    Unlike `dict.update`, this assumes that the values of the parent dict are
    dicts (or dict-like), so you shouldn't replace the nested dict if it
    already exists. Instead you should update the sub-dict.
    """
    # update named styles specified by user
    for name, rc_dict in new_dict.items():
        main_dict.setdefault(name, {}).update(rc_dict)
    return main_dict


# Load style library
# ==================
# SCBLIND-001..005 architecture contract:
#
# * Value ownership remains with the bundled
#   ``stylelib/seaborn-v0_8-colorblind.mplstyle`` artifact; the legacy name is
#   only a second library key for that internal style mapping.  [SCBLIND-002,
#   SCBLIND-004, SCBLIND-005]
# * ``reload_library`` is the sole publication seam for
#   ``library["seaborn-colorblind"]``.  Compatibility therefore depends inward
#   on ``_base_library["seaborn-v0_8-colorblind"]``, never outward on seaborn or
#   on a user style directory.  [SCBLIND-001, SCBLIND-004, SCBLIND-005]
# * The published value retains the existing style-mapping boundary consumed by
#   ``use`` and ``_apply_style``; plotting owns no compatibility-specific path.
#   [SCBLIND-002, SCBLIND-003]
# * Verification ownership remains in the SCBLIND tests in
#   ``matplotlib/tests/test_style.py``.  No new public symbol or adapter is
#   required for this integration seam.  [SCBLIND-001..005]
#
# SCBLIND-006..007 architecture contract:
#
# * ``reload_library`` owns the sole compatibility-key write, after the normal
#   bundled- and user-style assembly boundary.  That write may affect only
#   ``library["seaborn-colorblind"]``; unrelated keys and their parsed mapping
#   objects remain owned by the existing assembly flow.  [SCBLIND-006]
# * Parsing and validation remain owned by ``read_style_directory`` and
#   ``rc_params_from_file``.  The compatibility entry depends inward on the
#   already-validated bundled ``seaborn-v0_8-colorblind`` mapping and introduces
#   no operating-system, backend, or backend-state dependency.  [SCBLIND-007]
# * Direct retrieval continues through the existing ``library`` mapping
#   contract.  No platform adapter, backend hook, new public symbol, or second
#   publication path belongs between ``reload_library`` and consumers.
#   [SCBLIND-007]
# * Verification of preservation and environmental independence remains at the
#   existing SCBLIND-006 and SCBLIND-007 loci in
#   ``matplotlib/tests/test_style.py``.  [SCBLIND-006, SCBLIND-007]
_base_library = read_style_directory(BASE_LIBRARY_PATH)
library = None
available = []


def reload_library():
    """Reload the style library."""
    # SCBLIND-001..005 -- legacy colorblind compatibility pseudocode:
    #
    # INPUT:
    #   bundled_styles := styles parsed from Matplotlib's packaged stylelib
    #   compatibility_key := "seaborn-colorblind"
    #   reference_style := bundled Matplotlib 3.4.3 colorblind configuration
    #
    # FLOW:
    #   1. Build the normal style library from bundled_styles and user styles.
    #   2. Resolve reference_style exclusively from Matplotlib's bundled data;
    #      do not import, query, or otherwise depend on seaborn.  [SCBLIND-005]
    #   3. If the bundled reference cannot be resolved or is not a valid
    #      Matplotlib rc-parameter mapping, fail library reload through the
    #      existing style-loading error path; do not publish a partial entry.
    #      [SCBLIND-002, SCBLIND-004]
    #   4. Otherwise, expose reference_style under compatibility_key so an
    #      exact library lookup returns the mapping without KeyError and with
    #      the bundled 3.4.3 colorblind values unchanged.  [SCBLIND-001,
    #      SCBLIND-002, SCBLIND-004]
    #   5. Hand the returned mapping to the existing style-application flow;
    #      accepted rc parameters transition into active rcParams, after which
    #      ordinary plot creation proceeds.  Any invalid parameter follows the
    #      existing Matplotlib style-validation failure path.  [SCBLIND-003]
    #
    # OUTPUT:
    #   library[compatibility_key] is a bundled, valid, directly applicable
    #   style mapping after every reload, independent of seaborn installation.
    #
    # SCBLIND-006 -- unrelated-style preservation pseudocode:
    #
    # INPUT:
    #   ordinary_library := the library produced by the existing bundled- and
    #                       user-style loading flow
    #   unrelated_entries := every ordinary_library entry whose key is not
    #                        "seaborn-colorblind"
    #
    # FLOW:
    #   1. Complete the ordinary loading flow before publishing the legacy
    #      entry; retain every unrelated key and its parsed style mapping.
    #   2. Add or replace only ordinary_library["seaborn-colorblind"]; do not
    #      remove, reparse, replace, or mutate any unrelated entry.
    #   3. Preserve the invariant that each unrelated key remains directly
    #      retrievable and yields the same usable style definition it held
    #      immediately before legacy-entry publication.
    #   4. If ordinary style loading fails, follow its existing failure path
    #      before publication; never repair that failure by altering an
    #      unrelated style.
    #
    # OUTPUT:
    #   ordinary_library plus exactly the compatibility-key publication, with
    #   all unrelated definitions preserved.
    #
    # SCBLIND-007 -- environment-independent lookup pseudocode:
    #
    # INPUT:
    #   compatibility_key := "seaborn-colorblind"
    #   bundled_colorblind := ordinary_library["seaborn-v0_8-colorblind"]
    #
    # FLOW:
    #   1. Resolve bundled_colorblind without consulting the operating system,
    #      active plotting backend, or backend-specific state.
    #   2. Require the resolved value to have passed the ordinary Matplotlib
    #      rc-parameter parsing and validation flow.
    #   3. If resolution or validation fails, propagate the existing
    #      style-loading failure and do not publish an invalid legacy entry.
    #   4. Otherwise publish the validated mapping under compatibility_key;
    #      supported environments take this same branch because no OS or
    #      backend discriminator participates in the decision.
    #   5. Hand direct lookup consumers the mapping through the existing
    #      library interface, with no environment-specific adapter.
    #
    # OUTPUT:
    #   library[compatibility_key] directly retrieves a valid Matplotlib style
    #   mapping on every supported operating system and plotting backend.
    global library
    library = update_user_library(_base_library)
    library["seaborn-colorblind"] = library["seaborn-v0_8-colorblind"]
    available[:] = sorted(library.keys())


reload_library()
