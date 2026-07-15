# Issue #67 Architecture Artifact: Top-level `version_info` exposure

Status: Architecture phase complete-in-progress for implementation handoff.
Canonical requirements: `VINFO-001`, `VINFO-002`, `VINFO-003`, `VINFO-007`.

## Requirement-to-architecture map

- `VINFO-001` (exposure):
  - Pressure: public top-level API surface must own a comparable `version_info` symbol as a true module attribute.
  - Placement: module attribute boundary in `lib/matplotlib/__init__.py`.
  - Contract location: `__getattr__` lazy attribute branch.

- `VINFO-002` (determinism/repeatability):
  - Pressure: `version_info` must be derived from the same `__version__` input and be stable per import-time version string.
  - Placement: `lib/matplotlib/__init__.py` with memoization/caching in module state when constructed from `__version__`.
  - Contract location: shared derivation path in `__getattr__`.

- `VINFO-003` (format compatibility):
  - Pressure: preserve existing `matplotlib.__version__` value/format contract.
  - Placement: keep current `__getattr__` branch as single source of truth for `__version__` resolution.
  - Boundary: `version_info` must depend on resolved `__version__` instead of introducing alternate version formatting.

- `VINFO-007` (single parse source):
  - Pressure: no parallel parser path for top-level comparable object creation.
  - Placement: package parser boundary remains `packaging.version.parse` as already imported in `lib/matplotlib/__init__.py`.
  - Contract location: all version comparisons continue to use `parse_version(...)` calls in module scope / attribute resolution path.

## Ownership and seams

- `matplotlib` package public boundary: `lib/matplotlib/__init__.py`
  - Owns API symbol exposure (`__version__`, `version_info`) via `__getattr__`.
  - Owns attribute-level dependency routing and lazy behavior.

- Version source seam:
  - Upstream source remains the `__version__` lazy branch and `_version.version` fallback.
  - `version_info` construction must have a one-way dependency on this resolved string.

- Parsing seam:
  - Use existing imported helper `parse_version` only.
  - No new local parser helper may be introduced in this issue surface.

## Dependency direction

1. `version_info` construction depends on `__version__`.
2. `__version__` construction depends on `setuptools_scm` + `_version.version`.
3. `version_info` comparison uses `packaging.version.parse` result objects.

Inverted dependency from parsing to raw string formatting is explicitly forbidden.

## Integration skeleton (implementation-ready)

- Add module-private cache state in `lib/matplotlib/__init__.py` for resolved version info.
- Add a deterministic branch in `__getattr__` for `name == "version_info"` that:
  - resolves `__version__` first,
  - parses once with `parse_version(__version__)`,
  - caches and returns the parsed object.
- Do not alter `__version__` branch semantics.

## Traceability

- Test contract map anchor already exists in:
  - `lib/matplotlib/tests/test_version_info_contracts.py` as `VINFO_CONTRACT_MAP`.
- This artifact references the same requirement IDs and maps each to a structural place.

## Completion assessment

- All four obligations now have explicit architectural homes.
- Structural owner/seam/dependency are documented.
- This file is a concrete architecture artifact update and is requirement-traceable.
