# Issue #70 Architecture Artifact: `VINFO-009` scope discipline for top-level version exposure

Status: Architecture phase complete.
Canonical requirement: `VINFO-009`.

## Requirement-to-architecture map

- `VINFO-009` (scope discipline and no dependency/release edits):
  - Pressure A:
    - Top-level API behavior for version exposure must be owned by `matplotlib` import/startup boundary only.
    - Placement: `lib/matplotlib/__init__.py` via existing `__getattr__` path for `__version__` and `version_info`.
    - Contract boundary: callers observe `matplotlib.__version__`, `matplotlib.version_info`, and related lazy parse behavior through public module state.
  - Pressure B:
    - No new third-party versioning dependency and no release/build pipeline-file edits.
    - Placement: repository-level policy boundary under change control for packaging/release metadata and pipeline config.
    - Contract boundary: edits are restricted to contract/verification surfaces in tests and architecture artifacts only.

## Ownership and boundaries

1. API seam owner: `lib/matplotlib/__init__.py`
  - Owns top-level symbol exposure and lazy memoization behavior for `__version__` and `version_info`.
  - Boundary:
    - Input: module-level symbol lookup (`"__version__"`, `"version_info"`).
    - Output: module globals cache values and comparability semantics.
  - Rationale:
    - `VINFO-009` must only constrain what is already in scope here; no new module owners are introduced.

2. Traceability owner: `lib/matplotlib/tests/test_version_info_contracts.py`
  - Owns requirement binding and acceptance checks for import-time scope and policy compliance.
  - Boundary:
    - Input: top-level public `matplotlib` contract and repository file-diff policy assumptions.
    - Output: deterministic contract placeholders and mapping entries in `VINFO_CONTRACT_MAP`.

3. Repository policy boundary:
  - No ownership transfer to dependency or release pipeline configuration files for this issue.
  - Forbidden surfaces are explicitly out-of-scope:
    - dependency management (`requirements*.txt`, `pyproject.toml`, `setup.py`, `setup.cfg`),
    - release/pipeline workflows (`.github/workflows`, `ci/*`, `ci-*.yml`, `azure-pipelines.yml`).

## Dependency direction

- Allowed inward dependency:
  - `matplotlib.version_info` behavior remains one-way from resolved `matplotlib.__version__` through existing `parse_version`.
- Forbidden dependency direction:
  - No new package dependency path from `version_info` logic to third-party version-semantics packages beyond current `packaging.version.parse`.
  - No dependency from implementation phase to release pipeline state or packaging metadata.

## Integration-seam skeletons

- Seam A: import/startup seam (`import matplotlib`)
  - Observability point:
    - module attribute first access for `__version__` and `version_info` at import-time and lazy read sites.
  - Transition:
    - On valid flow, symbols remain resolved through existing top-level pathway only.

- Seam B: contract gating seam (`test_version_info_contracts.py`)
  - Inputs:
    - `VINFO-009` contract test names
    - `VINFO_CONTRACT_MAP` entries
    - file-scope policy assertions (placeholder pass-through in current phase)
  - Output:
    - requirement traceability and a stable gate for implementation handoff.

- Seam C: release/pipeline guard seam (non-edit seam)
  - Policy interface:
    - no changes are routed to dependency declarations or build/release scripts.
  - Failure transition:
    - Any attempt to alter forbidden files must fail issue scoping in review by changing this artifact and trace map.

## Structural completion check

- Requirement obligation is mapped to explicit owners and boundaries.
- Dependency direction is explicit and restricted to existing top-level version semantics.
- A concrete architecture artifact was created and remains requirement-traceable to `VINFO-009`.
- The artifact keeps scope constrained to API/startup contracts and import-time structure.
