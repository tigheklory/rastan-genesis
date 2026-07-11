# Andy — Build 0157: PC090OJ Mirror-Dirty → Candidate Resweep (gameplay sprites reach the SAT)

**Agent:** Andy (temporary implementation/runtime-evidence role). **Type:** implementation + verification.
**Baseline:** `rastan-direct-proposal` @ `5668c6e` (Build 0156 accepted). Build 0156 ROM `03c6e8aa…`, counter 156.
**Evidence dir:** `states/traces/build_0157_gameplay_sprites/`. **Cody handoff:**
`docs/design/Cody_build0157_pc090oj_candidate_dirty_handoff.md`.

## 1. Phase 0 result
Relevant KNOWN_FINDINGS: KF-039 (arcade work-RAM A5-base mapping; PC090OJ record index `(HW−0xD00000)/8`),
KF-040/KF-041 (dynamically-dead arcade paths / producer-vs-generator source models — same class of "records
present but pipeline step not run"). Rediscovery-Hazard HIGH touched: none contradicted. Task classification:
**EXTENDING** (existing PC090OJ candidate/decode/SAT engine). Open issues touched: OPEN-017 (gameplay rendering).
Contradiction of a CONFIRMED/STRONG finding: **NONE**.

## 2. Baseline
branch `rastan-direct-proposal`, HEAD `5668c6e`, clean; Build 0156 ROM SHA `03c6e8aa…`, counter 156.

## 3. Files/evidence inspected
`apps/rastan-direct/src/pc090oj_hooks.s` (vdp_prepare_sprites, process_candidates, set_all_candidates,
emit_slot, family_apply_record), `apps/rastan-direct/src/vdp_comm.s`, `out/symbol.txt`, `address_map.json`,
`states/traces/build_0157_gameplay_sprites/`, Cody's handoff doc.

## 4. vdp_prepare_sprites runtime proof
`vdp_prepare_sprites` (VBlank): one-time `renderer_init` (sets `scan_active=1`, `bootstrap_pending=1`), then on
`bootstrap_pending` calls `set_all_candidates`, then always `process_candidates`, then
`represented_count → staged_sprite_active_count`. After the single bootstrap it **only** processes
`candidate_bitset` and **never** re-evaluates on `mirror_dirty`.

## 5. mirror_dirty proof (Build 0156, gameplay 2/3/0)
`pc090oj_mirror_dirty = 0x0001` (set by producers `.Lpc090oj_emit_slot @0x071A8A` and
`.Lpc090oj_family_apply_record @0x071BB8`). No inspected source consumes/clears it before `process_candidates`.

## 6. candidate_bitset proof (Build 0156)
`pc090oj_candidate_bitset` = **0/32 nonzero bytes (empty)** at gameplay, despite `pc090oj_object_ram` holding
**212 coded records** — because `family_apply_record` clears its record candidate after direct-sync.

## 7. represented/staged/SAT proof (Build 0156, BEFORE)
`represented_count = 6`, `staged_sprite_active_count = 6` (the stale bootstrap set), `sat_dirty = 0` — the 212
mirror records never re-derive into the represented/SAT set.

## 8. First exact divergence
`pc090oj_object_ram` populated (212) + `pc090oj_mirror_dirty` set, but `candidate_bitset` empty ⇒
`process_candidates` re-derives nothing ⇒ `represented`/`staged`/SAT stay at the stale bootstrap set. This is a
bounded **dirty-to-candidate handoff** gap (classification: record staged but not decoded to SAT), not object
existence or control flow.

## 9. Implementation boundary
In `vdp_prepare_sprites`, fold `pc090oj_mirror_dirty` into the existing bootstrap resweep: when either
`bootstrap_pending` **or** `mirror_dirty` is set, clear both and call the existing
`.Lpc090oj_set_all_candidates`, then continue through the existing `.Lpc090oj_process_candidates` → represent →
SAT path (Cody's recommended conservative fallback). +0xC bytes; no new opcode_replace; **no second renderer,
no second SAT path, no manual sprites**. The mirror is a frame-like global snapshot (212 records = the arcade
sprite frame), so a dirty-frame full sweep is faithful.

## 10. Before/after validation (real structures, gameplay 2/3/0)
| structure | Build 0156 (before) | Build 0157 (after, active window F=533-534) |
|---|---|---|
| `candidate_bitset` nonzero | 0/32 | **31/32** |
| `object_ram` coded | 212 | 205-212 |
| `represented_count` | 6 (stale) | **10-11** |
| `staged_sprite_active_count` | 6 | **11** |
| `sat_dirty` | 0 | **1** |
| `staged_sprite_sat` (0xFF6188) | — | **11 real entries** (Y=0x78/0x80/0x88, attr=0xC400-0xC42C, X=0xA8-0x138) |

The dirty gameplay mirror now re-derives candidates → represented → **populated Genesis SAT** through the
existing path. **Sprites do not yet visibly appear** because Rastan dies almost instantly (the active sprite
window F≈533-534 precedes the plane-paint window F≈601, by which point the producer has stopped) — a deferred
control-flow/collision boundary, explicitly out of scope, not a sprite-output defect.

## 11. Regression results
- **Frontend sprites intact:** title `represented=15` (1UP/HIGH SCORE/2UP/RASTAN), no regression from the
  resweep.
- **Build 0155 FG / Build 0154 BG intact:** gameplay `staged_bg=2048`, `staged_fg=2020`.
- **Build 0156 C08C66 route intact:** `0x3D24C = jsr 0x708C8`. **Build 0152 C08C62 route intact:**
  `0x3A92A = jsr 0x70894`.
- **Deterministic:** two clean boots → identical `represented=11` and identical `staged_sprite_sat`.

## 12. Build 0157
- **ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0157.bin`
- **SHA256:** `725c36a27a4ea55a4a99bcbca4bd5dde3bbaf00cffe6b5005b8997b90cdd2c4a`
- **Size:** 1,581,168 B. Counter 157. Builds 0142–0156 not overwritten. GATE_PASS; boot guard PASS; trace clean;
  address-map `gaps=[]`, `overlaps=[]`, covered `0x182070`, `opcode_replace=135`. Canonical coverage
  paired-updated `0x182064 → 0x182070`.

## 13. First downstream boundary
The gameplay sprite SAT path is now correct, but sprites remain visually absent because **Rastan dies almost
instantly** (fall/collision control-flow — deferred). The next focused boundary is the player death/fall, then
scroll/camera — pursued only after this handoff is accepted.

## 14. Architecture compliance
CONFIRMED. Reused the existing `.Lpc090oj_set_all_candidates` / `.Lpc090oj_process_candidates` /
`represented_records` / `staged_sprite_sat` / SAT-DMA path. No second renderer, no second SAT commit, no manual
sprite placement, no hardcoded sprites, no Genesis-owned gameplay lifecycle, no `state==2/3/0` test (gated on
producer-set `mirror_dirty`). Builds 0152/0154/0155/0156 untouched.

## Open issue impact
- **OPEN-017:** advanced — the PC090OJ dirty→candidate→SAT handoff is fixed; populated gameplay sprite records
  now reach the Genesis SAT (represented 6→11, SAT 11 real entries) via the existing path. Sprites remain
  visually absent pending the deferred player-death/fall control-flow boundary. Not closed; no duplicate.
