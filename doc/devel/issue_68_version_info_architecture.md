# Issue #68 Architecture Artifact: `version_info` comparable ordering semantics

Status: Architecture phase complete.
Canonical requirements: `VINFO-004`, `VINFO-005`, `VINFO-010`.

## Requirement-to-architecture map

- `VINFO-004` (fixture-component conformance):
  - Pressure: parsed top-level version objects must expose the expected token families for stable, rc, dev, and post-release strings.
  - Placement: `lib/matplotlib/__init__.py`, `name == "version_info"` branch in `__getattr__`.
  - Contract boundary: parsing remains a pure transformation from resolved `__version__` to `packaging.version.Version`.

- `VINFO-005` (ordering determinism):
  - Pressure: pre-release family ordering must be deterministic as `dev < rc < final < post`, with malformed versions surfacing parse failures.
  - Placement: same `__getattr__` branch in `lib/matplotlib/__init__.py`.
  - Contract boundary: ordering behavior is owned by `parse_version` comparator semantics, not caller-side token parsing.

- `VINFO-010` (chainable boolean comparison):
  - Pressure: `version_info` must be directly usable in single boolean expression chains (`a < b <= c > d`) without caller tokenization.
  - Placement: `lib/matplotlib/__init__.py`, memoized `version_info` object in module globals; test seam in `lib/matplotlib/tests/test_version_info_contracts.py`.
  - Contract boundary: chainability is provided by object identity/stability plus true Version comparability.

## Ownership and boundaries

- Public API boundary: `lib/matplotlib/__init__.py`
  - Owns top-level version symbols (`__version__`, `version_info`) via `__getattr__`.
  - Owns the `version_info` memoization contract and cache lifecycle.

- Version source boundary:
  - `version_info` MUST derive from resolved top-level `__version__` text.
  - Dependency direction remains one-way: `__version__` -> `version_info`.
  - No alternate parser entry points are introduced.

- Parser boundary:
  - Parsing remains delegated to `packaging.version.parse` (`parse_version` import in `matplotlib.__init__`).
  - Boundary prevents local parsing code or post-processing in this issue.

## Dependency-direction notes

1. `__getattr__("__version__")` resolves version source and string shape.
2. `__getattr__("version_info")` reads cached `version_info` or parses `__version__` once through `parse_version`.
3. Result is stored in module globals and reused for all subsequent `version_info` reads.
4. Contract tests (`lib/matplotlib/tests/test_version_info_contracts.py`) consume the symbol through the public API and assert comparability.

## Interface / contract skeletons

- Top-level contract:
  - `matplotlib.version_info` is a module attribute (`Version`-like object) that supports standard rich comparisons (`<`, `<=`, `>`, `>=`, `==`).

- Integration seam:
  - Use `matplotlib.version_info` as a first-class comparator input in all higher-level ordering checks.
  - Keep comparison operations in callers single-expression-friendly by avoiding pre-split token checks.

## Structural integration points

- `lib/matplotlib/__init__.py`
  - Existing `__getattr__` branch for `version_info` is the unique construction seam.
  - Cache and return path is the integration point for deterministic reads.

- `lib/matplotlib/tests/test_version_info_contracts.py`
  - `VINFO_CONTRACT_MAP` already binds VINFO-004/005/010 to tests.
  - Placeholder contract tests preserve phase boundary until implementation phase.

## Completion assessment

- All three traced obligations are assigned to explicit loci and module boundaries.
- Dependency direction is explicit and acyclic for this scope.
- This file is a concrete architecture artifact; it is now requirement-traceable and implementation-ready.
