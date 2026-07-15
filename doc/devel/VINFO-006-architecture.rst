VINFO-006 Architecture Artifact
===============================

Scope
-----
Scope the version API change to the two version-introspection points:
`__version__` and `version_info` only, with no new unrelated top-level version
utilities exported from `matplotlib`.

Requirement-to-architecture map
-------------------------------
- **GUID:** ``VINFO-006``
- **Canonical acceptance targets:**
  - ``test_VINFO_006_top_level_version_additions_limited_to_version_scope_symbols``
  - ``test_VINFO_006_version_info_import_path_and_diff_scope_without_unrelated_new_exports``
- **Primary locus:** ``lib/matplotlib/__init__.py``
- **Verification locus:** ``lib/matplotlib/tests/test_version_info.py``

Ownership and placement
-----------------------
- Public version-surface ownership remains in the top-level package module
  ``lib/matplotlib/__init__.py``.
- `__version__` remains legacy ownership in the same module; `version_info`
  is additive ownership in that same module via lazy attribute materialization.
- No ownership is added in `matplotlib._version`, helper/parser, or any other
  top-level module for new public symbols.

Boundary definition
-------------------
- **Public boundary seam:** module attribute access through
  ``matplotlib.__getattr__(name)``.
- **Allowed public version-surface exports:** exactly the set
  ``{"__version__", "version_info"}``.
- **Default seam behavior:** all other names must follow fail-fast semantics
  through existing `AttributeError` behavior.

Dependency-direction notes
-------------------------
- Direction is inward-to-local within `lib/matplotlib/__init__.py`:
  - ``__getattr__`` depends on ``_get_matplotlib_version`` (version source).
  - ``__getattr__`` depends on ``_parse_version_info`` (projection for
    ``version_info``).
  - No dependency is introduced from private helpers back into module export
    surface.
- No new external modules are introduced by this requirement; existing version
  source collaborators remain unchanged (`setuptools_scm`, `matplotlib._version`).

Structural pressures and home assignment
---------------------------------------
1. **Scope-pressure:** prevent API fan-out beyond version introspection.
   - Home: ``__getattr__`` decision lattice in ``lib/matplotlib/__init__.py``.
   - Control: `if name` only accepts `"__version__"` and `"version_info"`.
2. **Export-surface pressure:** preserve existing top-level exports and avoid any
   new helper symbols.
   - Home: `__getattr__` return paths, no helper assignment except
     `__version__` and cached `version_info` in `globals()`.
3. **Import-semantics pressure:** keep `from matplotlib import version_info` and
   `matplotlib.version_info` equivalent and sourced from the same version path.
   - Home: existing `version_info` branch in ``__getattr__``.
4. **Diff-contract pressure:** top-level export diff for the patch should include
   only `version_info` addition.
   - Home: module-level attribute policy and test scope in
     ``lib/matplotlib/tests/test_version_info.py``.

Integration-seam skeleton
-------------------------
- In `lib/matplotlib/__init__.py`:
  1. `name == "__version__"`: existing lazy computation + cache of `__version__`.
  2. `name == "version_info"`:
     - read cached `__version__` if available,
     - otherwise compute via `_get_matplotlib_version`,
     - parse once through `_parse_version_info`,
     - cache and return `version_info`.
  3. else: raise `AttributeError` and do not add any top-level version utility
     symbols.

Readiness status
----------------
- Added artifact: ``doc/devel/VINFO-006-architecture.rst``.
- Traceability coverage: each structural pressure is bound to a concrete file and
  existing VINFO-006 verification names.
- Structural readiness: module ownership, boundaries, dependencies, and seam
  behavior are explicit and implementation-ready.
