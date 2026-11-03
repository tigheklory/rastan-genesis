# Andy — Build 0442→0446 Round-1 Subround-1 Early-End Regression Archaeology

**Date:** 2026-10-19 · **Type:** READ-ONLY regression / root-cause audit. **No** production source,
Makefile, generator, ROM, MAME, trace, build-number/counter change. Phase D/E not started. Output:
this doc + one `AGENTS_LOG.md` entry + one new OPEN_ISSUES entry. Evidence: git history, build
reports, the preserved numbered ROM binaries, the address map, and the native-title reports — no new
runtime evidence.

## 1. Repository states (corrects the prompt's premise)

| Build | Source commit (verified) | Canonical ROM | Size | Status |
|---|---|---|---|---|
| 0442 | `c7ca1439` "Build 442 — Fix arcade invincibility variant" (accepted, `56b0076b` locks it) | present, SHA `76cdf3f0…` | **2,698,936** | LAST KNOWN GOOD |
| **0443** | native-title candidate (not in main log; ROM preserved) | **present** | **2,711,224 (+0x3000)** | **ROM EXISTS — contrary to the prompt's "no 0443 ROM." This is where the native-title package first grew the ROM by +0x3000.** |
| 0444 | native one-shot title (`Cody_build0444_native_one_shot_title_screen.md`) | present | 2,711,224 | CRASH (BlastEm addr error `0x000721AA`) |
| 0445 | native title address-error repair (`Cody_build0445_…`) | present, SHA `23b574ce…` | 2,711,224 | gameplay-entry gate **FAIL** (new addr error, frame 31) — title off-by-two LEA |
| 0446 | native title mapping repair (`f9686893`) | present | 2,711,224 | title crash fixed (`+8`→`+10` LEA) |
| 0447 | native title (further) | present | **2,723,512 (+0x3000)** | ROM grew again |

> **Correction:** the prompt's "there is NO Build 0443 ROM" is **wrong** — `dist/…/build_0443.bin`
> exists and is the first +0x3000 growth. The native-title work spans 0443–0449, not 0444+.

## 2. Arcade intent (subround-1 extent, "segment," end-of-subround)

R1 Subround-1 ("R1 Phase-1") scrolls through a sequence of map **segments/records**. From the
existing retained-code decompilation (`rastan_scene_map.c`, `rastan_world_stream.c`,
`rastan_world_scroll.c`, and the OPEN-029/030 provenance), the owners are:

- **Segment/record progression:** `A5+0x013E` (record index); the Plane-B descriptor table at
  **arcade `0x3951C`** (6-byte `{attr,src}` entries; the `PLANE_B_DESC_TABLE_ARCADE_BASE`). The
  streaming walker is `A5+0x10FC`, scroll column `A5+0x10F6`.
- **Horizontal/world extent + camera max:** advanced by the retained scroll/stream code
  (`0x55C4A` column stream, `0x557BA`/`0x55AB4` scroll commit) as the record index advances to the
  subround's final record.
- **End-of-subround + automatic walk-right + Subround-2 transition:** a retained scripted
  progression state reached when the record/extent hits the subround's end marker (see OPEN-029 for
  the state-4 scripted-exit machinery). "Segment 15" is Tighe's visual label for the final map
  record of Subround-1; its exact internal meaning is the last descriptor-table record before the
  Subround-2 descriptor set.

**Intent:** the auto-walk/transition fires only when the retained progression reaches the **final
record** of the subround, which requires the correct extent/end data to have been read and the final
map streamed. If the progression reads a **truncated/wrong extent**, it fires the end behavior early.

## 3. Proven regression class — ROM-reflow / stale reference (OPEN-016 class)

The native-title work inserts `shift_replacements` at arcade `0x03AA54` (title entry) and `0x03BB48`
(glyph producer; 52→20 bytes), which **shift all copied ROM content after those points**. The
Build-0445 report proves one concrete instance:

> The Build-0443 `0x03AA54` insertion shifted the copied glyph pointer table from runtime `0x03BD7C`
> to `0x03BD7E`, but the Genesis-only helper `genesistan_hook_glyph_renderer_3bd48` **retained the
> historical literal `0x03BD7C`** → read 2 bytes early → long `0xBEA80003` (garbage) → ADDRESS ERROR
> (Build 0444). Build 0445's PC-relative fix was off-by-two (`+8` → `0x03BD5C` = the preceding RTS);
> Build 0446's `+10` resolved the mapped table.

This is a **ROM-reflow / stale-literal** defect: a reference into the shifted copied region that uses
the **pre-reflow (0442) address** and was not relocated with the shift. The glyph instance is
frontend; **the R1 Subround-1 early-end is the same class** in a gameplay reference into the shifted
gameplay region.

### Byte proof of the gameplay reflow

Comparing the preserved ROMs at the gameplay code region (`0x50000`, which maps to arcade
`~0x4FE00`, after the `0x03AA54` insertion):

| Build | gameplay-region net shift vs 0442 (at 0x50000) |
|---|---|
| 0446 | **+30 bytes** (0446[X] = 0442[X−30]) |
| 0447 | **+28 bytes** |

So the entire gameplay copied region is a **byte-shift** of the 0442 content (not a relayout — the
~105k "different" bytes in `0x40000–0x60000` are the artifact of comparing a +30-shifted stream
byte-aligned). **A reference that still uses the 0442 gameplay address reads δ bytes early** (δ = +30
in 0446, +28 in 0447).

## 4. First proven regression point

- **Last good:** 0442 (no title insertion; no shift).
- **First source state containing the regression:** **Build 0443** (the first `0x03AA54`/`0x03BB48`
  native-title `shift_replacement` insertion; first +0x3000 ROM growth; first gameplay-region shift).
  0444 is where it first **crashed** (the frontend glyph instance), but the reflow that creates the
  stale gameplay reference is introduced at **0443**, not 0444.
- **First observable non-crash gameplay:** 0446 (0444/0445 crash before/at gameplay entry per their
  reports). Tighe's "0445 ≈ Segment 11" is therefore imprecise — 0445 fails the gameplay-entry gate
  with a title-glyph address error; the first build that reaches observable gameplay is 0446.
- **First wrong semantic value:** the gameplay extent/record data read through a reference that is
  **δ bytes stale** into the shifted gameplay region (δ = net reflow shift). Expected: the 0442
  descriptor/extent bytes; actual: the bytes δ earlier → a truncated/wrong end-of-subround record →
  premature auto-walk. **The exact instruction/pointer is not pinned in this read-only pass** (the
  current 0455 source has no hardcoded arcade literals — the frontend one was fixed and later gameplay
  work is cleaned), so it is recorded as the narrowest proven boundary (§7) rather than a named site.

## 5. Why the false endpoint MOVES (0445 vs 0446 vs later)

**Proven, and it is NOT a 0445→0446 difference:** 0445 and 0446 differ in exactly **3 bytes** — the
header checksum (`0x00018F`), the single glyph-LEA displacement byte (`0x03BD55`), and the build
string (`0x2958DB`). **The gameplay region is byte-identical between 0445 and 0446**, so their
gameplay behavior is identical; the Seg11↔Seg13 difference cannot come from a 0445→0446 change.

The failure point moves **across reflow-size builds**, because the gameplay-region net shift δ
changes build-to-build as the native-title `shift_replacements` change byte counts: **δ = +30 at
0446, +28 at 0447** (and other values at 0443/0444/0445). A stale reference off by δ lands on a
**different but still plausible** descriptor/extent value for each δ → a different truncated end record
→ a different premature stop position. This is exactly the prompt's "stale pointer now lands on
different data" mechanism, and it is proven by the differing per-build deltas, not forced numerically.

- **Same underlying root cause:** YES (the reflow stale-reference class).
- The "0445 Seg11 / 0446 Seg13" labels most plausibly correspond to **different reflow builds** Tighe
  compared (e.g., a +0x3000 growth at 0447 vs the 0446 state), not the binary-identical 0445/0446.

## 6. Map vs progression

- **Map source truncated/wrong:** effectively YES **as read** — the gameplay reference reads the
  extent/record data δ bytes stale, so the progression's **input data is wrong**.
- **Progression logic wrong:** NO — the retained arcade progression faithfully reaches end-of-subround
  when it reads an end/extent value; it is reacting correctly to corrupt input.
- **Shared corrupt source:** YES/likely — the same stale-reference δ affects whatever extent/record
  data the progression (and possibly streaming) reads.
- **True end-door data present but unreachable:** UNKNOWN from static evidence (the real end record
  exists in ROM at the correct shifted location; whether the stale reference misses it entirely or
  reads an early end-marker is the fork to resolve by pinning the site).
- **Conclusion:** this is a **corrupt-input** defect (category B/C), **not** a progression-logic bug.
  Do NOT patch the auto-walk, force a camera max, or extend scroll — restore the correct (relocated)
  reference so the progression reads the right extent.

## 7. Current Build 0455 applicability

- **Historical defect still present:** LIKELY YES / CHANGED FORM — the native-title package persists
  and later builds (0447+, 0453+ item screen) grew the ROM further, so the gameplay reflow δ persists
  and keeps changing. The frontend glyph instance was fixed (0446); **the gameplay reference has not
  been shown to be fixed** and is not identified here.
- **Current owner/path:** the reference into the shifted retained gameplay region (R1 Subround-1
  extent/record read). The current source has **no hardcoded arcade literal** (grep clean), so the
  stale reference is most likely an **embedded data pointer not relocated** (OPEN-016 class) or a
  **declared relocation whose target/base the title reflow changed** — not an instruction literal.
- **Architecture differences:** the native-title and native-item work keep changing ROM size, so any
  non-symbolic gameplay reference will keep drifting. The fix must be durable (symbolic/relocated),
  not a one-off address correction.

## 8. Durable fix design (no implementation)

**Smallest correct fix:** identify the specific R1-Subround-1 extent/record reference that is stale
after the reflow and make it **relocation-durable**, exactly as the glyph table was corrected:

- if it is a **Genesis-only helper literal** → replace the hardcoded arcade address with a
  **PC-relative / linker-symbol** reference (the 0446 glyph fix pattern);
- if it is an **embedded data pointer** into the gameplay region → declare it in the shift pipeline's
  `absolute_long_pointer_tables` (the OPEN-016 embedded-pointer relocation class) so it moves with the
  reflow;
- if it is a **declared relocation** whose base/target the title work changed → regenerate it from the
  current `address_map.json` (never a numeric pre-reflow address).

**Prohibited (per task):** hard-coded segment-15, forced camera max, forced player X, disabled
auto-walk, manually extended scroll, fake door injection, or any "if Round 1 then N segments"
special-case.

- **Arcade intent changed:** NO · **hard-coded segment count:** NO · **forced camera endpoint:** NO ·
  **player-state workaround:** NO.
- **Expected affected systems:** the one stale reference (extent/record read); after the fix the
  progression reads the correct final record and the subround completes.
- **Expected unaffected systems:** collision, movement, player state, AI, title, item screen, and all
  other stages (the fix is a single reference relocation).

### What the next (Cody) pass must do to pin the site

1. Disassemble the R1-Subround-1 progression/extent read in the **0442** ROM and the **0446** ROM at
   the gameplay region; find the reference whose operand/pointer is the **0442** gameplay address
   (off by δ in 0446), analogous to the glyph `0x3BD7C`.
2. Classify it (Genesis-only literal / embedded data pointer / declared relocation) and apply the
   matching durable repair above. Use `build/rastan-direct/address_map.json` for the correct
   `arcade_pc ↔ runtime_genesis_pc`, never `+0x200`/`+δ` arithmetic.

## 9. Verification plan (future Cody)

- **Static proof:** the repaired reference resolves to the correct `address_map.json` target in the
  final ROM; `0442`-vs-fixed descriptor/extent read equivalence; no other reference remains stale into
  the shifted region (grep + embedded-pointer audit).
- **Existing automated validation:** canonical gate, boot guards, gameplay-entry gate, family check,
  native-title verifier (must still PASS), fixed 30-second trace.
- **Tighe hardware acceptance:** scrolling continues through the full intended R1 Subround-1; the true
  final map/door appears; auto-walk begins only at the real end; Subround-2 transition occurs; no
  regression to earlier segments or other stages.

## 10. Issue ledger

Searched OPEN_ISSUES.md / CLOSED_ISSUES.md. OPEN-029 (R1 Phase-2 third-chain) and OPEN-030 (Phase-2
Plane-A residency) are **Subround-2**, not this Subround-1 early-end. No existing owner for the
Subround-1 early-end reflow regression → new **OPEN-037** opened (see OPEN_ISSUES.md), cross-referenced
to the native-title reflow (Builds 0443–0446) and the OPEN-016 embedded-pointer relocation class.

## FINAL STATUS

Production modified: NO. ROM built: NO. MAME run: NO. New trace: NO. Build number consumed: NO.
Build counter changed: NO. Phase D: NO. Phase E: NO.
