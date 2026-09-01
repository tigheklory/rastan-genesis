# Build 0324 — Permanent Pattern-Reuse Build Pipeline

## Intent
Make the Tighe-approved Segment-11 reference-substitution decision a permanent, reusable,
automatically-consumed part of the normal `make` build — not an analysis-only artifact — with
validation and provenance, and generic enough to carry future approved consolidations through the
same mechanism.

## What shipped (permanent, in the ordinary build)
1. **`specs/pattern_reuse_policy.json`** — canonical, versioned registry of APPROVED offline
   reference-substitutions. Schema per entry: `domain, round, phase, segment, original_code,
   original_bank, replacement_code, replacement_bank, cells_affected, status, reason, provenance`.
   Populated with ONLY the 47 approved R1/P1 Segment-11 entries. No additional substitutions; no
   other round/phase/segment populated. Analysis/proposal files remain provenance only.
2. **`tools/translation/apply_pattern_reuse.py`** — validating resolver. Resolves every `approved`
   entry against the real `plane_a_uses.json` `(code,bank)` inventory and emits
   `build/regions/pattern_reuse_resolved.json` with `policy_sha256`. Hard-fails (nonzero exit) if
   any original `(code,bank)` is not a genuine use in its declared segment, any replacement is not
   an existing use, or any approved entry is left unresolved. Proven: a corrupted entry yields
   "47 approved, 46 resolved, 1 unresolved" and exit 1.
3. **Makefile wiring** — `PATTERN_REUSE_POLICY` → `PATTERN_REUSE_RESOLVED` is an ordinary build
   dependency of the Layer-A region and the boundary compile. Editing the policy re-triggers the
   validation gate and downstream rebuild. No special command, no env var, no hardcoded segment
   list, no dependency on `analysis/`.
4. **Provenance** — the boundary compiler records the policy SHA + resolved/unresolved counts into
   `build/pc080sn_boundary/boundary_report.json` (`pattern_reuse_policy` block). Verified the
   recorded `policy_sha256` equals `sha256(specs/pattern_reuse_policy.json)`.
5. **Build 0324** — full production build PASS: seven-epoch gate PASS (records 0,3,4,10,11,12,15),
   plane-A and plane-B full-LUT checks PASS, plane drops 0, A cap 484.

## Honest scope boundary (not yet visible in the ROM)
The shipped Layer-A graphics path is still **code-keyed**: the boundary compiler allocates one slot
per arcade `code` per epoch (`slot_of[code]`, `tile_bytes(code)`), and the runtime name word maps
`code → slot`. A `(code,bank)` reference substitution can only change on-screen pixels through a
**bank-aware name-word path**, which this code-keyed architecture does not have. Consequently Build
0324's Layer-A imagery is equivalent to Build 0320's: the policy is validated and its provenance is
recorded, but the 47 substitutions do not yet alter pixels.

The remaining substantive work (the prompt's "full `(code,bank)` integration, dominant maps = 0")
is therefore:
- restructure the boundary compiler's slot allocation from code-keyed to `(code,bank)`-keyed,
  applying `pattern_reuse_resolved.json` before dedup/residency so Segment 11's faithful
  `(code,bank)` set lands at the 484 cap (authoritative proposal figure 531→484), and
- add a runtime bank-aware name-word generator that selects the `(code,bank)` slot.

This was deliberately NOT half-shipped under a numbered build: an incomplete `(code,bank)` routing
change is exactly what caused the Builds 0317–0319 regression. The permanent policy pipeline is now
in place to carry that change cleanly when implemented.

## Scaffolding inventory / removal plan
None added to the production ROM. All new code is offline build tooling
(`apply_pattern_reuse.py`) and a canonical spec (`pattern_reuse_policy.json`), both intended to be
permanent. No NOP/RTS, no runtime JSON/policy processing, no Line-2/Layer-B change.
