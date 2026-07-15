VINFO-004 Architecture Artifact
===============================

Scope
-----
Define structural placement for directly comparable ``matplotlib.version_info``:
all standard comparison operators and pre/post semantic ordering must be deterministic
for supported version forms.

Supported forms in scope:

- ``3.5.0``
- ``3.5.0rc2``
- ``3.5.0.dev820+g6768ef8c4c``
- ``3.5.0.post820+g6768ef8c4c``

Requirement-to-architecture map
-------------------------------
- **GUID:** ``VINFO-004``
- **Canonical verification targets:**
  - ``test_VINFO_004_version_info_comparison_operators_are_total_for_all_6_standard_operators``
  - ``test_VINFO_004_dev_release_is_semantically_before_final_and_reverse_check``
  - ``test_VINFO_004_candidate_is_before_final_and_post_release_is_after_final``
  - ``test_VINFO_004_compatibility_guard_version_info_ge_target_returns_deterministic_semantic_result``
- **Primary locus:** ``lib/matplotlib/__init__.py``
- **Verification locus:** ``lib/matplotlib/tests/test_version_info.py``

Ownership and placement
-----------------------
- ``matplotlib.version_info`` remains the external ownership boundary in
  ``lib/matplotlib/__init__.py`` via ``__getattr__`` lazy materialization.
- The comparison domain belongs to a dedicated private projection object created in
  the same module scope (the existing ``_VersionInfo`` declaration site).
- ``_parse_version_info(version)`` remains the sole parser boundary that preserves
  the ordering inputs used by comparators.
- Pseudocode-only implementation logic remains co-located with current comment
  loci (already present in ``__init__.py``) for VINFO-004.

Structure pressure translation
-----------------------------
1. **Deterministic six-operator behavior**
   - Pressure: operator surface completeness and deterministic return values.
   - Home: ``_VersionInfo`` comparison implementation in ``lib/matplotlib/__init__.py``.
   - Required seam: comparison protocol methods over normalized keys.

2. **Release precedence semantics (`dev` < `rc` < `final` < `post`)**
   - Pressure: ranking order must be encoded by key projection, not ad hoc
     operator branching.
   - Home: ``_VersionInfo`` key construction contract plus
     ``_parse_version_info`` releaselevel retention.

3. **Compatibility guard tuple handling**
   - Pressure: stable behavior for expressions like
     ``version_info >= (3, 5, 0)``.
   - Home: comparison normalization seam that translates supported tuple operands
   to canonical compare keys while preserving compatibility shape.

Boundary and contracts
----------------------
- **Public contract seam:** module attribute resolution for ``version_info`` in
  ``__getattr__(name)``.
- **Data contract:** ``_VersionInfo`` shape is
  ``(major, minor, micro, releaselevel, serial, local)`` with ``local`` as a
  deterministic tuple.
- **Ordering contract (structural):**
  - normalize both operands into a fixed comparison key,
  - compare lexicographically for ``< <= > >=``.
- **Value coercion contract (structural):**
  - RHS tuple of length 3 treated as final-level target for guard forms.
  - RHS that is not supported by this contract must not create undefined behavior
    from comparison entry points.

Dependency-direction notes
--------------------------
Dependency direction remains module-local:

- ``__getattr__`` -> ``_get_matplotlib_version`` / ``_parse_version_info`` -> compare
  contract helpers.
- No new outbound dependency for version comparison is introduced into public user
  call sites.
- Parsing still depends on ``packaging.version.parse_version`` and
  ``matplotlib._version.version`` indirectly through existing `_get_matplotlib_version`
  path.

Integration-seam skeleton
-------------------------
- Maintain public seam in ``__getattr__``:

  1. ``"version_info"`` resolves through existing version source logic.
  2. parse value once through ``_parse_version_info`` and cache in ``globals()``.
  3. return projection object implementing all six operators.

- Comparison seam for implementation phase 06:

  1. introduce internal key normalization routine for operands.
  2. define strict total-order rules for local key fields.
  3. ensure guard-form tuple targets are accepted as final-release keys.
  4. wire only operators required by ``VINFO-004``; leave unsupported RHS types
     with deterministic outcomes.

Readiness and completion
------------------------
- This artifact maps all currently-traceable VINFO-004 obligations to concrete
  module ownership, boundary seams, and dependency direction.
- Structural placement is stable and implementation-ready:
  - ``lib/matplotlib/__init__.py`` for behavior placement,
  - ``lib/matplotlib/tests/test_version_info.py`` for acceptance mapping.
