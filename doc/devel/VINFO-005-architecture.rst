VINFO-005 Architecture Artifact
===============================

Scope
-----
Preserve import-time safety for version attribute exposure so existing
environment-sensitive import scenarios stay unchanged, while still exposing
``matplotlib.version_info`` through the established lazy top-level attribute
path.

Requirement-to-architecture map
-------------------------------
- **GUID:** ``VINFO-005``
- **Canonical verification targets:**
  - ``test_VINFO_005_importable_with__OO_version_initialization_remains_import_side_effect_free``
  - ``test_VINFO_005_importable_with_no_home_version_initialization_remains_home_free``
  - ``test_VINFO_005_doc_standard_backends_observations_unmodified_by_version_initialization``
- **Primary locus:** ``lib/matplotlib/__init__.py``
- **Verification locus:** ``lib/matplotlib/tests/test_version_info.py``

Ownership and placement
-----------------------
- Version exposure ownership remains with top-level package module:
  ``lib/matplotlib/__init__.py``.
- No new ownership is introduced; both source resolution and lazy materialization
  stay in this module:
  - ``_get_matplotlib_version``
  - ``__getattr__`` for ``"__version__"`` and ``"version_info"``
  - ``_parse_version_info`` and ``_VersionInfo`` as existing parse/compare units.
- Responsibility for preserving importability and configuration neutrality belongs to
  the same boundary that currently owns version logic; this avoids moving version
  policy across modules.

Boundary definition
-------------------
- **Public seam:** attribute lookup via ``matplotlib.__getattr__(name)``.
- **Private seam:** version source decision in ``_get_matplotlib_version``.
- **Environment-sensitive seam isolation:** version lookup must not cross into HOME,
  cache, config-dir, backend, or pyplot side-effect zones.
- **Import seam rule:** expensive or mutable environment setup paths remain gated to
  existing top-level import behavior outside the version branch.

Constraint translation from obligations
--------------------------------------
1. ``..._importable_with__OO...``  
   - Pressure: avoid new import-time side effects from exposing ``version_info``.
   - Home: ``__getattr__`` must stay lazy and only run on explicit attribute access.
   - Requirement: no new side effects may be introduced by version initialization.

2. ``..._no_home...``  
   - Pressure: no home-directory-dependent behavior in version initialization.
   - Home: ``_get_matplotlib_version`` and ``__getattr__`` must avoid calls to
     HOME-driven config helpers during version resolution.
   - Requirement: only existing version-source checks remain (SCM fallback path +
     packaged version constant).

3. ``...doc_standard_backends...``  
   - Pressure: preserve backend discovery assumptions used by doc build/import tests.
   - Home: keep backend selection state untouched by version attribute materialization.
   - Requirement: version attribute access is read-only, cache-only, and contracted
     through ``__version__`` reuse.

Contracts and invariants
------------------------
- **Importability contract:** module import should succeed without requiring access
  to HOME-dependent paths through the version path.
- **Side-effect contract:** attribute resolution for ``__version__`` and
  ``version_info`` may cache module-local globals only.
- **Source contract:** ``version_info`` materializes from the same version source as
  ``__version__`` by delegating to the existing logic.
- **Cache contract:** first version lookup may populate ``__version__``; subsequent
  ``version_info`` reads may rely on cached value and must not re-enter version
  resolution.

Dependency direction
--------------------
- Primary outward dependency edges remain:
  - ``lib/matplotlib/__init__.py`` -> ``setuptools_scm.get_version``
  - ``lib/matplotlib/__init__.py`` -> ``matplotlib._version.version``
  - ``lib/matplotlib/__init__.py`` -> ``Path(__file__)`` location checks
- No new edges are added for config home resolution, backend selection, or pyplot
  state from version path.
- Existing outward direction into validation helpers/tests in ``lib/matplotlib/tests``
  stays test-only.

Integration-seam skeleton
-------------------------
- Keep existing comment-based control points in-place:
  1. ``_get_matplotlib_version`` selects SCM-backed or fallback version string by
     `.git` metadata check.
  2. ``__getattr__`` handles only:
     - ``"__version__"`` -> cache and return lazy string
     - ``"version_info"`` -> source from cached or lazy ``__version__``, parse, cache tuple
     - else -> ``AttributeError``
- Maintain isolation: no backend imports/config writes/home resolution from these
  two branches.

Readiness status
---------------
- Changed artifact: ``doc/devel/VINFO-005-architecture.rst`` (new)
- Traceability status: complete for all three VINFO-005 canonical verification names.
- Structural readiness: implementation-ready; ownership, boundaries, dependency direction,
  and integration seams are explicitly defined for deterministic follow-through.
