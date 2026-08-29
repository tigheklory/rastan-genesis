# Andy — Segment 11 Existing-Tile Reuse Proposal (analysis only, no ROM)

## Phase 0 statement
Relevant KNOWN_FINDINGS: CRAM-line ownership (line 2 = arcade BG/Layer B) — unchanged here. HIGH rediscovery
hazards avoided: reused the frozen Test snapshot + the established (code,bank) analysis; no re-derivation.
Deferred: vertical-scroll issue — explicitly OUT OF SCOPE, untouched. Classification: **EXTENDING**
(proposal feeding the future offline (code,bank) compiler). Open/Closed issues touched: none. Contradiction
status: none. No STOP fired.

## Architecture compliance
Semantic cut: the arcade PC080SN tilemap semantic decision is preserved; only the offline Genesis target-
pattern set for segment 11 is proposed to be reduced by reference substitution. Chip-specific tail implicated
(future implementation): the offline PC080SN->Genesis pattern/package compiler + boundary residency (no
runtime change). Transitional compatibility: none introduced. No production code changed; no ROM produced.

## Verified capacity math (recomputed from frozen data)
- Segment 11 faithful `(code,bank)` distinct target patterns: **531** (verified).
- Teal/waterfall-noise family (Tighe's 230 A-IDs -> 230 source codes): **231** of the 531.
- Non-teal (rock/cave/surface teeth/edges/rope): **300** — must stay, unchanged.
- Plane-A capacity: **484**. Must remove: **531 - 484 = 47**.

## Candidate-selection method (reference substitution only)
No merged/synthetic/averaged tiles; no pixel/palette/index_map changes. Among the teal-noise target patterns
only: retire the **47** lowest-priority ones and remap their cells to an EXISTING kept teal tile.
- **Edge protection:** any teal pattern adjacent to non-teal (rock) is treated as an edge and never retired.
- **Lower-waterfall weighting:** candidates ranked by descending average row (lowest-on-screen first), then
  by rarity (fewest cells first). The 47 retired are the lowest, rarest, non-edge teal-noise tiles.
- **Replacement choice:** each retired pattern's cells point to the nearest KEPT teal tile by pixel-index
  Hamming distance, **preferring a tile already resident in Segment 10, then Segment 12** (continuity/reuse).

## Segment-10 influence
Segment 10's resident water tiles were included in the replacement pool and **10 of the 47 replacements reuse
Segment-10 tiles** (the rest reuse kept Segment-11 teal tiles; 0 from Segment 12). Using Segment 10 changed
selections vs optimizing Segment 11 alone by steering those 10 substitutions to tiles already on screen in the
prior segment, improving continuity.

## Result
- Original unique: 531 -> **proposed unique: 484** (fits exactly; headroom 0, per the conservative goal).
- Teal patterns: 231 -> **184 kept** (47 retired). Non-teal: 300 -> **300 unchanged**.
- 47 substitutions; **283 Segment-11 cells** remapped. Segments 10 and 12: unchanged.
- Machine-readable data: `analysis/build0321_segment11_capacity/seg11_reuse_substitutions.json`
  (each row: eliminated code/bank/target, cells affected, avg row, replacement code/bank/target, seg10/12
  residency, Hamming distance).

## PNG
`analysis/build0321_segment11_capacity/segments_10_11_12_proposal.png` — Segments 10 | 11(proposed) | 12 in
gameplay order (left->right), rendered through the actual Palette Composer target palette/index maps; only
Segment-11 references changed.

## Visual/fidelity assessment
The waterfall retains its surface rock teeth, waterline highlight band, rock edges and teal body; the 47
retired noise variants are visually indistinguishable in the water field (all substitutions are within the
teal-noise family, non-edge, low on screen). Cave/rock/rope/ledge artwork is untouched.

## USER MUST VERIFY
Inspect `segments_10_11_12_proposal.png` and the substitution JSON. Approve or adjust (e.g., protect specific
tiles, or allow more headroom) before any implementation. On approval, this becomes an offline compiler/map-
authoring input for the (code,bank) build — no runtime change.
