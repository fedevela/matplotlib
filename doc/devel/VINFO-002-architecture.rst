VINFO-002 Architecture Artifact
===============================

Scope
-----
Add a top-level public `matplotlib.version_info` contract, available via:

- `from matplotlib import version_info`
- `import matplotlib; matplotlib.version_info`

Requirement-to-architecture map
-------------------------------
- **GUID:** ``VINFO-002``
- **Canonical acceptance target:** expose a top-level `version_info` symbol without requiring private helper imports in user code.
- **Primary locus:** ``lib/matplotlib/__init__.py``
- **Verification locus:** ``lib/matplotlib/tests/test_version_info.py``

Ownership and placement
-----------------------
- The owning boundary is the top-level package module ``matplotlib`` namespace (`lib/matplotlib/__init__.py`).
- Version-source resolution (`_get_matplotlib_version`) stays within this module to prevent API users from coupling to private modules.
- Parsed version shape is represented by `_VersionInfo` (namedtuple) in the same module.

Boundary and contracts
----------------------
- **Public seam:** module attribute resolution through `__getattr__(name)`.
- **Contract:** when `name == "version_info"`, module returns `_VersionInfo` tuple `(major, minor, micro, releaselevel, serial)`.
- **Importability contract:** symbol must be discoverable by `from matplotlib import version_info` by normal import mechanism.
- **Module contract:** `matplotlib.version_info` must be present after standard `import matplotlib`.
- **Traceability contract:** value must derive from the same version source used by `__version__`.

Dependency direction
--------------------
- Outward from `lib/matplotlib/__init__.py` to:
  - `matplotlib._version.version`
  - `setuptools_scm.get_version` (SCM source path)
  - `_parse_version_info(version)` as a local parser
- No new inbound dependency from helpers into package import logic.
- `version_info` must remain an additive API and must not be routed through caller-side imports of private submodules.

Integration-seam skeleton
-------------------------
- Keep `version_info` branch inside existing `__getattr__(name)` decision lattice:
  - `__version__` branch: unchanged source-of-truth and cache behavior.
  - `version_info` branch: pull from cached `__version__` when present, otherwise call `_get_matplotlib_version`, then parse via `_parse_version_info`.
  - default `AttributeError` behavior for unknown attributes.
- Preserve invariant that `_VersionInfo` parsing is local and deterministic.

Structural readiness
--------------------
- Structural home is set (`lib/matplotlib/__init__.py`), with a clear seam for implementation (`__getattr__`).
- Boundaries and dependencies are explicit and source-of-truth remains inside package namespace.
- Artifact is requirements-linked and ready for Hod/Hod-like implementation without further placement work.
