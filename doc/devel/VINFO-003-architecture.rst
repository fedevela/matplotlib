VINFO-003 Architecture Artifact
===============================

Scope
-----
Parse supported `__version__` forms into deterministic comparable structure for
`version_info`, including stable handling of local metadata suffixes.

Supported forms in scope:

- ``3.5.0``
- ``3.5.0rc2``
- ``3.5.0.dev820+g6768ef8c4c``
- ``3.5.0.post820+g6768ef8c4c``

Requirement-to-architecture map
-------------------------------
- **GUID:** ``VINFO-003``
- **Canonical verification targets:**
  - ``test_VINFO_003_supported_version_forms_parse_to_deterministic_fields``
  - ``test_VINFO_003_version_info_fields_stable_across_version_form_reparsing``
  - ``test_VINFO_003_supported_version_forms_with_local_metadata_are_order_stable``
- **Primary locus:** ``lib/matplotlib/__init__.py``
- **Verification locus:** ``lib/matplotlib/tests/test_version_info.py``

Ownership and placement
-----------------------
- Parsing ownership remains in `matplotlib` package namespace (`lib/matplotlib/__init__.py`), not in any public helper module.
- `_parse_version_info` is the owned parser entry point for all supported forms used by `version_info`.
- `_VersionInfo` is the public projection boundary for parse outputs that `version_info` can expose.
- `__getattr__(name)` remains the owning boundary for lazy attribute materialization and caching.

Boundary and contracts
----------------------
- **Public seam:** module attribute resolution through `matplotlib.__getattr__(name)`.
- **Source boundary:** `version_info` resolves the same source string as `__version__`:
  - cached ``__version__`` first,
  - otherwise `_get_matplotlib_version`.
- **Cache boundary:** parsed value is memoized by storing it in `globals()["version_info"]` after first parse.
- **Reload boundary:** interpreter-level module reload re-initializes module globals, so reparsing must deterministically reconstruct the same structure from the same source string.

Parser contracts (structural)
-----------------------------
- `_parse_version_info(version)` is responsible for:
  - reading deterministic release components from supported forms,
  - applying branch priority ``pre`` → ``dev`` → ``post`` → final,
  - generating a stable `(major, minor, micro, releaselevel, serial, local)` shape,
  - deterministically normalizing local suffix order when present (e.g. split on ``.`` into an explicit stable sequence).
- No general normalization beyond the supported forms list.

Dependency-direction notes
--------------------------
- Internal dependencies in `__init__.py` flow outward to:
  - `packaging.version.parse_version`,
  - `_version.version`,
  - `setuptools_scm.get_version` via `_get_matplotlib_version`.
- `version_info` must never introduce new inbound dependencies into `matplotlib.__init__`.

Integration-seam skeleton
-------------------------
- Keep parse and version exposure within existing lattice:
  - `if name == "__version__":` keep source + cache behavior.
  - `elif name == "version_info":` source/version resolution, parse, cache, return.
  - `else:` raise `AttributeError`.
- `version_info` must always be derived from the same parsed source path as `__version__`.

Readiness
---------
- This file provides stable owner, contract, dependency, and seam placement for `VINFO-003`.
- Once tests are implemented, these structure-level decisions are implementation-ready and keep behavior changes localized.
