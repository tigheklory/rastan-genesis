# RG-023 — Correct native Layer A/B stage assembly

RG-023 is implemented in candidate Build 0500. The permanent build-numbered report is:

`docs/design/Cody_build0500_native_plane_stage_assembly.md`

Original arcade and Genesis NTSC evidence proves that the castle does not use a transposed map. It uses the same direct 64-column semantic layout, with R1-S2 selecting a vertical producer and a `0x100` scroll origin. The Build 0499 defect was loss of the raw destination's 64-row identity: nonresident logical rows 42–44 were folded with `row & 31` and could overwrite resident boss-stage rows 10–12. Build 0500 preserves the logical row through the native semantic boundary and publishes only rows owned by the live 32-row Genesis window.

All six currently native-covered R1/R2 subround variants now pass exact arcade-to-Genesis pattern identity, orientation, LUT, VDP publication, and collision-buffer checks. The established rope route remains deterministic at `795/795/795` and 13,267.083 ms. Build 0500 remains a test candidate pending Tighe's hardware review; the exact R1-S2 obstruction, live boss-defeat transition, palette authoring, and Rounds 3–6 are explicitly not claimed complete.
