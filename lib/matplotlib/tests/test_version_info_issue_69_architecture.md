# Issue #69 Architecture Mapping (VINFO-006, VINFO-008)

## Canonical Requirement Trace

- `VINFO-006`: preserve import-time behavior while introducing top-level `version_info`.
- `VINFO-008`: preserve malformed metadata failure semantics without coercion/fallback.

## Requirement-to-Architecture Pressure Map

### VINFO-006 (Importability-sensitive startup flow)
- Pressure type: `boundary`
- Primary owner: `lib/matplotlib/__init__.py` (`__getattr__`)
- Integration scope:
  - `name == "version_info"` branch in module-level attribute fallback.
  - Existing import graph triggered by `matplotlib`/`matplotlib.pyplot` startup tests.
- Structural decision:
  - Keep `version_info` resolution in top-level module boundary only.
  - Preserve existing module side-effect sequence by lazy-resolving cache from `__version__` only when requested.

### VINFO-008 (Malformed-version failure semantics)
- Pressure type: `contract`
- Primary owner: `lib/matplotlib/__init__.py` (`__getattr__` -> `parse_version`)
- Integration scope:
  - `parse_version` call path for `version_info`.
  - No alternate module-level normalization/coercion path.
- Structural decision:
  - Maintain direct pass-through parse exception semantics.
  - Keep cache-write only on success.

## Ownership and Boundary Decisions

1. `matplotlib.__getattr__` owns top-level symbol resolution:
   - Input boundary: external symbol lookup (`__version__`, `version_info`).
   - Output boundary: cached symbol values in `globals()` (`__version__`, `version_info`).
   - Contract: deterministic lazy init, no import-surface reordering.

2. `lib/matplotlib/tests/test_matplotlib.py` owns startup/importability verification:
   - Boundary role: external behavior contract for importability under constrained runtimes.
   - No ownership of version parsing internals.

3. `lib/matplotlib/tests/test_version_info_contracts.py` owns requirement traceability:
   - Boundary role: requirement-indexed contract registry and behavior contracts.

## Dependency Direction

- `__getattr__(version_info)` must only depend inward on:
  - `globals()["__version__"]` if present, else `__getattr__("__version__")`.
  - `packaging.version.parse`.
- `test_matplotlib.py` and `test_version_info_contracts.py` depend outward on public `matplotlib` contract only.
- Failure-path tests must not introduce alternate parse or fallback dependencies.

## Integration Seams (Skeletons)

- Seam A: `matplotlib` top-level attribute fallback (`__getattr__`)
  - Input: symbol name (`"version_info"`).
  - Output: cached `packaging.version.Version` object.
  - Failure mode: raised parse exception bubbles unchanged.

- Seam B: importability test harness (subprocess)
  - Inputs: CLI/interpreter flags, temp env (`MPLCONFIGDIR`, `MPLBACKEND`), stripped docstrings (`-OO`).
  - Output: exit code 0.

- Seam C: malformed metadata harness
  - Input: forced mutation of version source and cache invalidation.
  - Output: deterministic exception propagation, no fallback return object.

## Completion Status

- Every traced obligation is assigned an owning file boundary.
- Contract and boundary mapping added in a repository-local architecture artifact.
- No production/runtime behavior changed in this phase.

