# Build 0519 ROM audit evidence

This directory contains the durable machine-readable evidence and visualizations for:

- `docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0035_build0519_rom_audit.md`
- ROM SHA-256: `ab34fc39a1cf635e0cdd1c69a37b6e0d46eab90f4ec1104bf7e2962eced43706`
- Exact source/output snapshot commit: `ca8b333`

`build0519_relinked.elf` is a map-only relink whose SHA-256 exactly matched the preserved Build 0519 ELF. `build0519_link.map` provides the corresponding section/symbol ownership evidence.

`build_audit.py` writes its generated results into this directory. To regenerate against the exact historical checkout, set `RASTAN_AUDIT_SOURCE_ROOT` to that checkout. Running it against a later working tree is not equivalent historical evidence.

No ROM was built or published by this audit.
