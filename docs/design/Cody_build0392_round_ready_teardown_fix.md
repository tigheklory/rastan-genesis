# Cody — Build 0392 ROUND/READY Teardown Fix

## Result

Build 0392 restores the generic tilemap-clear side effect that the existing
native replacement of arcade teardown `0x056440` had omitted. The fix is not
conditioned on ROUND/READY, a scene, or a gameplay state.

The complete five-ROM family was produced. Automated build and entry gates
pass; final visual/gameplay acceptance belongs to Tighe.

## Missing semantic effect

The original arcade function at `0x056440` performs two distinct semantic
actions:

1. retire/clear its transient PC090OJ item records; and
2. call the general PC080SN tilemap clear at `0x0561A0` before returning.

The existing whole-function replacement at translated Genesis `0x0564D0`
called `genesistan_pc090oj_hook_zero_fill_56440`, but that helper only cleared
`transient_items_active`. Replacing the whole original function also made its
internal `BSR 0x0561A0` unreachable. Thus the transient-item consequence was
preserved while the general tilemap-clear consequence was lost.

The native clear itself was not defective. Original `0x0561B6`, the
chip-specific fill loop inside `0x0561A0`, is already replaced at Genesis
`0x056246` by a call to `genesistan_hook_cwindow_clear`.

## Original arcade authority

The authoritative transition remains:

`0x055FFA -> 0x056440 -> 0x0561A0`

At `0x056440`, the second original `BSR.W` targets `0x0561A0`. It removes both
old PC080SN tilemaps after READY expiry and before gameplay presentation. The
native port must preserve that call's semantic result even though it does not
execute the PC080SN hardware-writing tail.

## Exact Genesis change

`genesistan_pc090oj_hook_zero_fill_56440` in
`apps/rastan-direct/src/pc090oj_hooks.s` now does:

```asm
clr.w   transient_items_active
bsr     genesistan_hook_cwindow_clear
rts
```

The canonical Build-0392 ROM proves the generated chain:

- translated teardown `0x0564D0`: `JSR 0x00073874`;
- `genesistan_pc090oj_hook_zero_fill_56440` at `0x073874`;
- its `BSR.W` targets `genesistan_hook_cwindow_clear` at `0x07232E`.

The remap note for arcade `0x056440` now records this complete contract.

## Native clear behavior

The reused `genesistan_hook_cwindow_clear`:

- derives the final Genesis blank name word from PC080SN semantic blank code
  `0x0020` through the active tile LUT plus attribute entry zero;
- fills all 2,048 words of `staged_bg_buffer` (final Plane B names);
- fills all 2,048 words of `staged_fg_buffer` (final Plane A names);
- sets `bg_row_dirty` and `fg_row_dirty` to `0xFFFFFFFF`; and
- clears `fg_native_gameplay_owner`.

It does not clear SAT, sprite patterns, CRAM, residency LUTs, collision, or
pattern VRAM. It adds no per-frame operation and no extra full-plane DMA.

## Ordering after the fix

Before teardown, the READY writer legitimately leaves the READY name words in
the staged Plane-B cells. At READY expiry, translated `0x0564D0` now completes
the native full-plane staging clear before it returns. Later scene installation
may reuse the low READY pattern slots, but the full Plane-B publication now
reads blank names rather than the old READY layout. Consequently the later
display-enable operation cannot expose READY-shaped terrain.

## Mechanical verification

The bounded verification used the established READY evidence plus generated
Build-0392 code and the normal entry gate; no new video comparison or forensic
probe was created.

| Check | Evidence | Result |
|---|---|---|
| READY names exist before teardown | Established representative staged/name words include `R=0x0027`, `O=0x0025`, `U=0x002A`, `N=0x0024`, `D=0x001A`, `1=0x0009`, `E=0x001B`, `A=0x0017`, `Y=0x002D`, `!=0x0034` | YES |
| Teardown reaches native clear | Canonical ROM `0x0564D0 -> 0x073874 -> 0x07232E` | YES |
| Staged Plane B blank after clear | The reached helper unconditionally overwrites exactly 2,048 `staged_bg_buffer` words with the translated blank | YES |
| Staged Plane A blank after clear | The same invocation unconditionally overwrites exactly 2,048 `staged_fg_buffer` words | YES |
| READY names can remain before first gameplay display-on | Clear completes synchronously before teardown returns; later full-plane publication therefore consumes cleared staging | NO |
| Normal READY-to-gameplay path survives | Gameplay-entry gate: READY, fixed-B install, record-0 Plane A, gameplay, and player control all PASS; 240 post-entry frames; zero address/bus/illegal/crash events | PASS |

## Native-replacement boundary proof

1. **Semantic decision above the boundary:** arcade control flow has selected
   the generic `0x056440` teardown, meaning transient items end and both old
   tilemaps must be cleared.
2. **Arcade-owned state/side effects retained:** READY timing, state
   progression, call/return flow, and later gameplay setup remain owned by the
   copied arcade program. Native transient-item retirement and the clear's
   return contract are preserved.
3. **Chip-specific execution below the boundary:** original `0x056440` begins
   PC090OJ object-RAM parking/zero-fill and then enters `0x0561A0`'s PC080SN
   clearing path.
4. **Complete bypassed tail:** the already-established full-body replacement
   keeps the PC090OJ object-RAM body and the PC080SN C-window fill loop
   unreachable. Build 0392 restores the omitted semantic result without
   reviving either tail.
5. **Input representation:** the replacement consumes the arcade semantic
   teardown event itself and emits final Genesis-format staged name words. It
   does not consume or construct chip-shaped RAM.

Semantic cut: retain the arcade decision to execute the general teardown and
clear; replace the PC090OJ record operation and PC080SN C-window fill below it
with direct native transient-state retirement and final Genesis name staging.

## Native-replacement policy checklist

- Semantic rather than chip-write boundary: **YES**.
- Complete PC080SN/PC090OJ block bypassed: **YES** — the original `0x056440`
  object-RAM body and `0x0561A0` C-window fill tail remain bypassed.
- New code consumes arcade semantic state, not chip-shaped state: **YES**.
- New mirror, shadow, virtual device RAM, range dispatcher, or projector:
  **NO**. `staged_bg_buffer` and `staged_fg_buffer` contain final Genesis VDP
  name words and are the native publication surfaces, not arcade-format
  PC080SN name RAM.
- Transitional compatibility retained by this change: **NONE**.
- Arcade still owns gameplay, frame progression, and VBlank: **YES**.
- Helper directly generates final VDP representation: **YES** — final Plane
  A/B name words are staged for the existing VBlank publisher.
- Newly superseded compatibility requiring a retirement path: **NONE**. No
  legacy path was added or newly retained; the already-retired chip tails stay
  unreachable.

## Build 0392

All artifacts were generated by the Makefile-owned release flow:

| Variant | Bytes | SHA-256 |
|---|---:|---|
| canonical | 1,744,568 | `deb28761f0e57af01d4c81c2008bb5ee49aaf3fa34973c9c28ad0a8453989237` |
| `_c` | 1,748,664 | `f5627c189bdd40b3b59c71c7f07afd9ada992414d02d1d2bb2d3c9bfb22848ba` |
| `_d` | 1,744,568 | `07edcb688807632918c3c37ce170d611cdddbc4e1213b61cf542d51f4791a8cf` |
| `_do` | 1,744,568 | `47d34180d029d642c591560db7ea00d82f4ddfec9cee8b51ddbf7245c6d89c52` |
| `_s` | 1,744,568 | `754b7e7531bdafaf7862ee1e2d55adb6a4fe932c020db3c0d3536654d77dace6` |

- Canonical gate: **PASS**.
- Gameplay-entry gate: **PASS**.
- Complete-variant verification: **PASS**.
- Transition-retention verification: **PASS**.
- Genesis NTSC MAME smoke: completed with no unmapped-memory report.
- Phase-1 seven-epoch gate: **FAIL/WARNING**, the known pre-existing gate result
  also recorded for Build 0391; it did not prevent artifact preservation.
- Patch manifest: 231 opcode replacements; expected Genesis coverage
  `0x1A9EB8`.
- Counter: `391 -> 392`.
- Palette, final Plane-A resolver, and collision logic: unchanged.

## Ledger and curated-finding impact

- Classification: **EXTENDING**. This repairs one omitted side effect inside
  the established native PC080SN/PC090OJ replacement architecture.
- Open issues touched: **OPEN-001, OPEN-018**.
- Context only: **OPEN-017** and **CLOSED-020**; neither was changed or
  reopened.
- New issues opened: **NONE**.
- Issues closed: **NONE**. Visual/gameplay acceptance is still pending.
- Issues intentionally deferred: **NONE beyond the prompt's explicit user
  regression checks**.
- Known findings consulted as controlling priors: KF-010, KF-013, KF-032,
  KF-035, KF-054, KF-071/KF-072, and KF-078.

**Option A — No new finding to index.** Rationale: the result confirms and
applies the existing direct-native staging and arcade-owned sequencing priors;
it does not establish a new reusable system behavior beyond the documented
omitted-call defect.

## User verification

**USER MUST VERIFY.** Tighe must confirm normal READY display, no terrain
garbage in READY positions at expiry, a clean gameplay transition, the Phase-1
waterfall, immediate Phase-2 Plane-A population after MODE jump, and the Flying
Demon whole-body death from a wing kill.
