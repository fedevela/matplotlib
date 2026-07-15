VINFO-001 Architecture Artifact
==============================

Scope
-----
Preserve ``matplotlib.__version__`` behavior and value/format while introducing a new
additive public ``version_info`` path.

Requirement-to-architecture map
-------------------------------
- **GUID:** ``VINFO-001``
- **Canonical contract:** keep ``matplotlib.__version__`` publicly available and unchanged in
  value/format; repeated reads before/after ``version_info`` access must remain stable and string-only.
- **Primary locus:** ``lib/matplotlib/__init__.py``
- **Existing verification locus:** ``lib/matplotlib/tests/test_version_info.py``

Ownership and placement
-----------------------
- ``matplotlib`` top-level API behavior is owned by ``lib/matplotlib/__init__.py``.
- Version source resolution remains within package public module namespace, not delegated to callers.
- ``__version__`` and future ``version_info`` logic stay in the same owning boundary to
  preserve import-time semantics and cache behavior.

Boundary definition
------------------
- **Public seam:** module attribute access via ``__getattr__(name)`` on ``matplotlib``.
- **Internal collaborators:**
  - ``matplotlib._version.version`` as fallback source.
  - ``setuptools_scm.get_version`` as SCM source.
  - filesystem path check for ``.git`` and ``.git/shallow`` to select source path.

Contracts and invariants
------------------------
- **Stability contract (for ``__version__``):** value must remain a string and identical across reads
  across the ``version_info`` path.
- **Source contract:** ``version_info`` must consume the same underlying version source as
  existing ``__version__`` resolution; no reformatting, replacement, or recasting of
  ``__version__``.
- **Failure contract:** dependency/import errors from current resolution path remain unchanged.

Dependency direction
--------------------
- Direction is outward from ``lib/matplotlib/__init__.py`` to:
  - ``setuptools_scm``
  - ``Path`` / ``.git`` detection
  - ``matplotlib._version``
- No inverse dependency from these collaborators into public-version semantics.

Integration-seam skeleton (implementation-ready)
-----------------------------------------------
- Introduce a version-introspection contract under ``matplotlib.__getattr__`` for two branches:
  1. ``name == "__version__"`` (legacy path).
  2. ``name == "version_info"`` (new path, additive only).
- The ``version_info`` branch must call the same source decision used by ``__version__`` and may be
  implemented by a non-mutating parser over the resolved source string.
- Cache point remains the module-level ``__version__`` symbol only.

Acceptance traceability
-----------------------
- ``lib/matplotlib/__init__.py``
  - ``__getattr__`` branching location maps to VINFO-001 obligations.
- ``lib/matplotlib/tests/test_version_info.py``
  - placeholder test names carry VINFO-001 requirement IDs.

Readiness note
--------------
This artifact is sufficient for implementation handoff because ownership, boundaries,
invariants, and dependency direction are explicitly defined without introducing
runtime behavior changes.
