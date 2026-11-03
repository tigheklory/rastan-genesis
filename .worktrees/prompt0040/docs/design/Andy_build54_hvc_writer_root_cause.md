# Andy — Build 54 HV Counter Writer Classification

**Agent:** Andy (Claude Code)
**Type:** Root cause classification (analytical synthesis only — no implementation, no new evidence collection)
**Build:** rastan-direct Build 0054 (post-D6-fix, post-v3.2 dispatch)
**Date:** 2026-04-29
**Architecture compliance:** CONFIRMED for the analysis below. No fix is proposed that would touch v3.1/v3.2 closures, bootstrap routing, audit guards, or any of the 10 Andy v3.2 §1.8 invariants.

---

## 0. Executive verdict

**Read 4 (False candidate) for Site 1 (arcade_pc 0x000590) — DEFINITIVELY CONFIRMED.**
**Actual HV Counter writer source — UNIDENTIFIED in available static evidence; STOP and identify Cody follow-up.**

The Cody writer search (`Cody_build54_hvc_writer_search.md`) flagged three indirect-postincrement candidates as potential sources of the BlastEm "Illegal write to HV Counter port 8" crash. Andy's analysis verifies each:

- **Site 1 (arcade_pc 0x000590, RAM-test routine in low arcade ROM)**: The arcade routine at `0x00054A..0x000596` is a ROM/RAM diagnostic loop (read-modify-write probe with bounds check via A1). It DOES test `[A0, A1)` with A0 starting at `0xC00000` and A1 at `0xC04000`, and the loop body would overshoot into `0xC00008` on iteration 5. **However: this code is NOT in the Genesis ROM at runtime.** The arcade source bytes at `0x000000..0x000F07` are EXCLUDED by `address_map.json`'s first segment (`preserved_vectors`, 4360 bytes covering Genesis vector table + header + bootstrap), and the Genesis ROM at runtime PC `0x590` contains GENESIS BOOTSTRAP CODE (specifically the crash-handler's VDP register-init subroutine), not the arcade RAM-test routine. Arcade execution starts at the relocated arcade reset vector (`0x0003A000` per `build/maincpu.disasm.txt:9` reset-vector longword), which Genesis bootstrap reaches via `jmp (0x00003A200).l` at the end of `_bootstrap` ([boot.s:166](apps/rastan-direct/src/boot/boot.s#L166)). **The arcade RAM-test at arcade_pc 0x590 is dead code on Genesis — never reached, never executed.** Read 4 confirmed.

- **Site 2 (arcade_pc 0x03AD44)**: opcode_replace covers this site with the v3.2 dispatch helper `genesistan_hook_3ad44_dispatch`. The dispatch's tilemap branch routes to `genesistan_hook_tilemap_bg_fill` which writes to `staged_bg_buffer` (Genesis WRAM at `0xFF4000+`), NOT to VDP I/O. The dispatch's PC090OJ branch writes via `.Lpc090oj_clear_slot`/`.Lpc090oj_emit_slot` to staged SAT/descriptor buffers, NOT to VDP I/O. The dispatch's audit fall-through reads `0xC00008` (READ, legal) and halts. **No path through `genesistan_hook_3ad44_dispatch` writes to VDP I/O at all, let alone `0xC00008`.** Read 1/3 ruled out at this site.

- **Site 3 (arcade_pc 0x0561CE)**: the address_map declares `arcade_start 0x0561B6..0x0561D4` as `kind: patched_site` with `replacement_bytes: 4eb90007106c...` (= `JSR genesistan_hook_cwindow_clear`). The arcade write loop at `0x0561C6..0x0561D4` does NOT execute; the patched-site replacement intercepts at `0x0561B6` and routes to `genesistan_hook_cwindow_clear` (runtime PC `0x7106c`), which writes to staged buffers. **No path from Site 3 reaches `0xC00008`.** Read 1/3 ruled out at this site.

The BlastEm "Illegal write to HV Counter port 8" message therefore originates from a write site **NOT enumerated in Cody's three candidates**. Static-evidence analysis has eliminated all three. The actual source must be:

- A postincrement / computed-address write whose A-register source isn't a literal `lea 0xC00000, %aN` or `moveal #0xC00000, %aN` (i.e., the address is loaded from memory or computed via arithmetic at runtime — invisible to Cody's grep patterns)
- Or a longword write at `0xC00006` whose 4-byte span crosses into `0xC00008` (BlastEm may detect this as an HV-Counter-byte write)
- Or a code path that Cody's static search did not enumerate

**This requires binary runtime trace evidence Cody did not provide.** Per Rule 20 (no new evidence collection) Andy STOPS and specifies the downstream Cody follow-up in §1.7.

---

## §1.1 Arcade routine reading (verbatim from `build/maincpu.disasm.txt`)

The full arcade routine spanning `arcade_pc 0x00054A..0x000596` is read from [build/maincpu.disasm.txt:390-410](build/maincpu.disasm.txt#L390-L410):

```text
   54a: 41f9 00c0 0000     lea     0xc00000, %a0
   550: 43f9 00c0 4000     lea     0xc04000, %a1
   556: 6100 0024          bsrw    0x57c
   55a: 41f9 00c0 8000     lea     0xc08000, %a0
   560: 43f9 00c0 c000     lea     0xc0c000, %a1
   566: 6100 0014          bsrw    0x57c
   56a: 41f9 00d0 0000     lea     0xd00000, %a0
   570: 43f9 00d0 1000     lea     0xd01000, %a1
   576: 6100 0004          bsrw    0x57c
   57a: 4e75               rts
   57c: 3010               movew   %a0@, %d0          ; D0 := *(A0)
   57e: 30bc 0000          movew   #0, %a0@           ; *(A0) := 0
   582: 4a50               tstw    %a0@               ; test *(A0)
   584: 6612               bnes    0x598              ; bail if not 0
   586: 30bc ffff          movew   #-1, %a0@          ; *(A0) := 0xFFFF
   58a: 0c50 ffff          cmpiw   #-1, %a0@          ; cmp *(A0), 0xFFFF
   58e: 6608               bnes    0x598              ; bail if not 0xFFFF
   590: 30c0               movew   %d0, %a0@+         ; *(A0)++ := D0
   592: b1c9               cmpal   %a1, %a0           ; cmp A0, A1
   594: 65e6               bcss    0x57c              ; loop if A0 < A1
   596: 4e75               rts
   598: 3080               movew   %d0, %a0@          ; restore *(A0) := D0
   59a: ...                                            ; (early-bail path)
```

**Routine intent:** classic 68k word-stride RAM probe. The subroutine at `0x57C` is called three times from the outer wrapper at `0x54A`:

| Outer call | A0 base | A1 limit | Intent |
|------------|---------|----------|--------|
| `0x556`     | `0xC00000` | `0xC04000` | Probe VDP region (16 KB) — diagnostic only on real arcade hardware where `0xC00000+` may be RAM-mapped or unconnected |
| `0x566`     | `0xC08000` | `0xC0C000` | Probe alternate VDP region |
| `0x576`     | `0xD00000` | `0xD01000` | Probe PC090OJ sprite RAM (4 KB) |

The subroutine body (`0x57C..0x596`):
1. Read `*(A0)` into D0 (preserve original).
2. Write `0` to `*(A0)`; bail if read-back is non-zero (RAM not writable).
3. Write `0xFFFF` to `*(A0)`; bail if read-back is not `0xFFFF`.
4. Restore `*(A0) := D0` via postincrement (advances A0 by 2).
5. Loop while A0 < A1.
6. Bail path (`0x598`) restores `*(A0) := D0` and returns to caller.

**Loop iteration count for the first outer call (A0=0xC00000, A1=0xC04000):** 8192 iterations (16 KB / 2 bytes per iteration).

**Word-postincrement at 0x590:** `movew %d0, %a0@+` — writes 2 bytes at A0, then A0 += 2. With A0 = 0xC00000 initially, iteration 5's write lands at A0 = 0xC00008 (= HV Counter, illegal). Iteration 4 lands at 0xC00006 (CTRL mirror, legal).

**Per Cody §1.4 evidence:** also note that `0x57E movew #0, %a0@` and `0x586 movew #-1, %a0@` would similarly write to `*(A0)` on each iteration. With A0 = 0xC00008 on iteration 5, those writes would also be illegal HV-Counter writes — and would be the FIRST illegal write per iteration (at `0x57E`, before the postincrement at `0x590` even fires).

So if this routine were live, it would crash at `0x57E movew #0, %a0@` on iteration 5 with A0 = 0xC00008, BEFORE reaching `0x590`. Site 1 in Cody's writer search lists `0x590` as the postincrement, but the FIRST illegal write would actually be at `0x57E`.

This routine, if executed, would crash. **But it is NOT executed.** §1.3 / §1.4 below explain why.

---

## §1.2 Loop overshoot computation

Given:
- Starting `A0 = 0xC00000`
- Loop body writes via `movew #imm, %a0@` (at `0x57E`, `0x586`) and `movew %d0, %a0@+` (at `0x590` with postincrement)
- A0 advances by 2 per iteration

Iteration trace:
| Iteration | A0 at start | Address written by `0x57E movew #0, %a0@` | Legal? |
|-----------|-------------|-------------------------------------------|--------|
| 1 | 0xC00000 | 0xC00000 (VDP DATA) | yes |
| 2 | 0xC00002 | 0xC00002 (DATA mirror) | yes |
| 3 | 0xC00004 | 0xC00004 (VDP CTRL) | yes |
| 4 | 0xC00006 | 0xC00006 (CTRL mirror) | yes |
| 5 | 0xC00008 | **0xC00008 (HV Counter)** | **NO — ILLEGAL WRITE** |

The first illegal write would fire on iteration 5 at the `0x57E movew #0, %a0@` instruction (the FIRST write of the iteration body), not at `0x590`. Cody's writer search flagged `0x590` because of the visible postincrement pattern; the actual crash trigger inside this routine would be `0x57E` on iteration 5.

**However: this routine does not execute on Genesis.** See §1.3 and §1.4. The overshoot computation is informational only — it confirms the Cody-flagged routine WOULD crash if executed, ruling in favor of a "false candidate" classification only on the basis of execution path, not address arithmetic.

---

## §1.3 Address-map boundary analysis

Read [build/rastan-direct/address_map.json:1-90](build/rastan-direct/address_map.json#L1-L90):

- `arcade_source_start: 0x000000` — the arcade ROM starts at offset 0 (in source).
- `arcade_source_end_exclusive: 0x060000` — arcade ROM is 384 KB.
- `relocation_delta: 0x000200` — arcade code is shifted by +0x200 in the Genesis ROM.

The first segment in the Genesis ROM:

```json
{
  "genesis_start": "0x000000",
  "genesis_end_exclusive": "0x001108",
  "size_bytes": 4360,
  "kind": "preserved_vectors",
  "tag": "genesis_vectors_header"
}
```

This 4360-byte segment is `kind: preserved_vectors` — it is GENESIS-SPECIFIC content (vector table + header + bootstrap code from `apps/rastan-direct/src/boot/boot.s`), **not arcade-source-derived**. The arcade source bytes at `arcade_pc 0x000000..0x000F07` (= 0x1108 - 0x200) are NOT mapped into the Genesis ROM.

The second segment is the first arcade content:

```json
{
  "genesis_start": "0x001108",
  "genesis_end_exclusive": "0x03A20C",
  "size_bytes": 233732,
  "kind": "arcade_copy",
  "arcade_start": "0x000F08",
  "arcade_end_exclusive": "0x03A00C",
  "source": "whole_maincpu_copy",
  "identity_offset": 512
}
```

So **arcade content begins at arcade_pc `0x000F08`** in the Genesis ROM. Arcade addresses below `0x000F08` are intentionally not present.

**Boundary classification: INTENTIONAL (architectural).** The 4360 bytes of preserved_vectors at runtime `0x000000..0x001107` accommodate:
- Genesis 68k vector table (`0x000000..0x0003FF`, 256 vectors × 4 bytes = 1024 bytes)
- Genesis ROM header (`0x000100..0x0001FF`, 256 bytes)
- Genesis bootstrap code (`_start` at `0x000202`, `_bootstrap` at `0x000226`, supporting helpers, crash stubs) up to `0x001107`

The `arcade_source_start: 0x000F08` value in the SECOND segment is a derived consequence of `relocation_delta: 0x000200` and the bootstrap region size (4360 bytes total). It is not an "exclusion" of arcade code per se — the arcade code below `0x000F08` is REPLACED by Genesis-specific code, which is the architecturally-intended behavior for the Strategy A boot pipeline.

**No opcode_replace entry covers arcade_pc 0x00054A, 0x000556, 0x00057C, 0x000590, or any nearby low-ROM address** (per `grep -nE "0x000590|0x000556|0x00057C|0x00054A|0x590|0x556|0x57C|0x54A" specs/rastan_direct_remap.json` returning 0 matches outside of `arcade_source_start: 0x000000`). This is consistent with the boundary intent: the bytes at those arcade_pcs do not exist in the Genesis ROM, so they cannot be patched — they are simply absent.

---

## §1.4 Bootstrap routing analysis

Read [apps/rastan-direct/src/boot/boot.s:142-167](apps/rastan-direct/src/boot/boot.s#L142-L167):

```asm
.org 0x000200
_boot_guard_legacy_rte:
    rte

_start:
    move.w  #0x2700, %sr
    lea     0x00FF0000, %sp
    move.b  HW_VERSION, %d0
    andi.b  #0x0F, %d0
    beq.s   .Ltmss_done
    move.l  #0x53454741, TMSS_REG
.Ltmss_done:
    jsr     _bootstrap

_bootstrap:
    jsr     vdp_boot_setup
    bsr     _bootstrap_clear_staging
    moveq   #0, %d0
    jsr     load_scene_tiles
    lea     0x00FF0000, %a5
    jsr     genesistan_pc090oj_dma_self_test
    jmp     (0x00003A200).l                ; ◄── jumps to relocated arcade_pc 0x3A000
```

**Genesis reset vector setup:** [boot.s:57-58](apps/rastan-direct/src/boot/boot.s#L57-L58):

```asm
.long 0x00FF0000             ; initial SP at vector index 0
.long _start                  ; initial PC at vector index 1
```

(`_start` resolves to `0x000202` per `apps/rastan-direct/out/symbol.txt`.)

**Genesis CPU executes:** `_start` → TMSS → `jsr _bootstrap` → vdp_boot_setup → clear_staging → load_scene_tiles → DMA self-test → `jmp (0x00003A200).l` → arcade execution at `runtime_genesis_pc 0x00003A200` (= relocated arcade_pc 0x3A000).

**Arcade reset vector contents (per arcade ROM):** at arcade_pc `0x000004` the arcade ROM stores the longword `0x0003A000` ([build/maincpu.disasm.txt:9](build/maincpu.disasm.txt#L9) — the 4-byte initial PC value embedded in the Genesis-vector format that the original arcade ROM also uses). So on real arcade hardware, the original 68k reset would also start at `0x3A000` — matching the Genesis-side `jmp (0x3A200).l` (relocated address).

**Path from Genesis reset to arcade_pc 0x000590:** none. Genesis bootstrap deliberately bypasses arcade_pc `0x000000..0x000F07` because:
1. The arcade reset vector points to arcade_pc `0x3A000` (NOT `0x590` or any other low-ROM address) — even on real arcade hardware, the routine at `0x590` is reached only via internal arcade BSRs, which themselves execute only if some path through `0x3A000`'s arcade boot chain calls them.
2. On Genesis, the arcade source at `0x000000..0x000F07` is REPLACED by Genesis bootstrap content (per §1.3); the BSRs at arcade_pc `0x000556` / `0x000566` / `0x000576` (which call `0x57C`) do not exist as arcade-original instructions in the Genesis ROM.
3. `_bootstrap` at runtime `0x000226` does NOT call any address in `0x000556..0x000596` range.

**Verification of postpatch content at runtime 0x590:** [build/genesis_postpatch.disasm.txt:402-403](build/genesis_postpatch.disasm.txt#L402-L403) shows:

```text
   590: 00c0 0004                          ; tail bytes of preceding `movel #0xC0000000, 0xC00004`
   594: 33fc 0000 00c0 0000  movew #0,0xc00000
   59c: 33fc 0eee 00c0 0000  movew #3822,0xc00000
   5a4: 4e75               rts
```

These are CRAM-init instructions inside the Genesis crash-handler's VDP setup (called from runtime `_crash_stub_*` paths via `bsrw 0x520; bsrw 0x58a; bsrw 0x5a6; bsrw 0x5e2; stop #0x2700` chain at runtime `0x504..0x518`). NOT the arcade RAM-test routine.

**Conclusion:** arcade_pc `0x000590` is NEVER executed on Genesis. Read 4 (False candidate) confirmed for Site 1.

---

## §1.5 Build 54 trajectory cross-check

Per `Cody_exodus_frame_extraction_build_54_11_16.md`, Build 54 reaches `runtime_genesis_pc 0x0003A196` (in arcade ROM execution, frame 58+, t=11s+ wall clock). This is well past:
- The Genesis bootstrap (`_start` at `0x202`, `_bootstrap` at `0x226`, `jmp (0x3A200).l` at the end of `_bootstrap` body)
- The arcade reset entry at `0x3A200` (relocated arcade_pc `0x3A000`)

**If arcade_pc `0x000590` were the bug source**, the crash would occur DURING bootstrap (specifically when the bootstrap calls into the routine), well before `0x3A196` is reached. But Build 54 reaches `0x3A196` — which means bootstrap completed successfully without firing the HV Counter trap.

**Reconciliation: arcade_pc `0x000590` is NOT the source of the Build 54 HV Counter trap.** The crash must occur at some point AFTER `0x3A196` (during arcade gameplay execution) or during a hooked-helper invocation that touches VDP I/O in an unexpected way. Consistent with §1.4: the arcade RAM-test at `0x000590` simply does not exist in the Genesis ROM.

The Cody Port Monitor cross-check (`Cody_build54_hvc_writer_search.md` §1.6) shows visible rows up through frame 100 (~t=11s + 100/30s ≈ t=14.3s) include CTRL writes (`0x8174`, `0x4000`, etc.) but NO writes to `0xC00008`. The crash either fires AFTER the visible window or is generated by a write the Port Monitor's "HV Counter Write" category (not enabled) would have caught.

---

## §1.6 Read classification

**For Site 1 (arcade_pc 0x000590): Read 4 — False candidate.** DEFINITIVELY CONFIRMED via §1.3, §1.4, §1.5.

Cited evidence:
- `address_map.json` first segment (`0x000000..0x001108` = `preserved_vectors`) replaces arcade_pc `0x000000..0x000F07` with Genesis bootstrap content.
- `boot.s` reset-vector-and-bootstrap chain routes execution `_start` → `_bootstrap` → `jmp (0x3A200).l`, never visiting `0x000556` / `0x000590`.
- Postpatch disassembly at `runtime_genesis_pc 0x590` shows Genesis crash-handler CRAM-init instructions, NOT the arcade RAM-test loop.
- Build 54 reaches `runtime_genesis_pc 0x3A196` (post-bootstrap arcade execution), proving bootstrap completed without hitting the alleged Site-1 crash.

**For Site 2 (arcade_pc 0x03AD44): Read 4 — covered by v3.2 dispatch, no VDP write.** Confirmed via Andy v3.2 §2.2.A Path B / dispatch contract — neither tilemap branch nor PC090OJ branch nor audit fall-through writes to VDP I/O.

**For Site 3 (arcade_pc 0x0561CE): Read 4 — covered by patched_site, no VDP write.** Confirmed via `address_map.json` `kind: patched_site, replacement_bytes: 4eb90007106c...` (= JSR to `genesistan_hook_cwindow_clear` which writes to staged buffers, not VDP).

**For the actual HV Counter writer source: STOP — UNIDENTIFIED.** Cody's three candidates are all confirmed false. The actual writer is somewhere static analysis has not yet enumerated. Andy cannot identify it without binary runtime evidence Cody did not provide. Per Rule 20 (no new evidence collection), Andy STOPS and specifies the downstream Cody follow-up in §1.7.

The unidentified writer's hypothesized characteristics (per the elimination of all three Cody candidates):
- Likely uses an A-register loaded with the destination address from MEMORY (not from a literal `lea` / `moveal #...`), so `grep "lea 0xc00000"` does not reveal it.
- OR uses arithmetic to compute the destination at runtime (e.g., add a base register and an offset that lands at `0xC00008`).
- OR is a longword write at `0xC00006` (BlastEm may detect the byte-span overflow into `0xC00008`).
- OR is in an opcode_replace helper that has a previously-unnoticed VDP-write path.
- Triggers at some game-state moment after Build 54 reaches `0x3A196` (per §1.5).

---

## §1.7 Fix plan and downstream Cody follow-up specification

### 1.7.1 Site 1 — confirmation only

**No fix required for Site 1 (arcade_pc 0x000590).** It is a false candidate (Read 4). The arcade routine at this address is dead code on Genesis. No spec change, no source change, no opcode_replace addition, no bootstrap routing change. Cody should NOT add an opcode_replace entry covering `0x000590` / `0x000556` / `0x000557C` / `0x00054A` — those addresses don't exist in the Genesis ROM, and any postpatcher attempt to patch them would either fail (segment lookup) or wrongly modify the Genesis bootstrap code at the corresponding runtime address.

### 1.7.2 Cody follow-up to identify actual writer (REQUIRED next task)

The following Cody binary-evidence task is required before any fix can be proposed:

> **Inputs:**
> - Build 54 ROM (`dist/rastan-direct/rastan_direct_video_test_build_0054.bin` or current equivalent)
> - BlastEm with full instruction trace enabled at the moment of the HV Counter halt
>
> **Method:**
> - Run BlastEm to the point of the "Illegal write to HV Counter port 8" halt
> - Capture the EXACT PC of the offending instruction at the moment of halt
> - Capture full register state (D0..D7, A0..A6, A7/SP, SR) at that moment
> - Capture the value being written (D-register source) and the effective address (computed per the instruction's addressing mode)
> - Disassemble the instruction at the captured PC verbatim
> - Trace backward from the captured PC to identify how the destination address ended up at `0xC00008` (which register / which memory load / which arithmetic chain)
>
> **Outputs:**
> - `docs/design/Cody_build54_hvc_actual_writer_trace.md` documenting:
>   - Halting PC (in `runtime_genesis_pc` format and, if applicable, `arcade_pc`)
>   - Halting instruction verbatim
>   - Halting register state
>   - Effective address computation at the halt instruction
>   - Backward trace of how the effective address became `0xC00008`
>   - Containing function (per source mapping, addressing the symbol-coverage illusion concern from prior cycles)
>
> **Deliverable success criterion:** the document must definitively identify the SOURCE-LEVEL or RELOCATED-ARCADE-LEVEL instruction responsible for the write. "PC 0x????" alone is insufficient; the document must explain the address computation chain.

### 1.7.3 Anticipated Andy follow-up after Cody's evidence

Once the actual writer is identified, an Andy follow-up classification task will:
- Determine if the writer is in arcade code (relocated, with potential opcode_replace coverage gap) → Read 1
- Or in a hooked Genesis-side helper (with a bug in the helper's address computation) → Read 5 (helper bug)
- Or in a non-PC090OJ subsystem (palette, tilemap, sound, scene_load) that touches VDP I/O incorrectly → Read 5 (other subsystem bug)
- Or genuinely in Genesis bootstrap (low-probability per §1.3 / §1.4 verification) → Read 5

The fix at that point will be one of:
- Add opcode_replace covering the arcade-pc range responsible
- Patch the Genesis-side helper's address computation (similar in form to the v3.2 Resolution B / D6-fix patches)
- Add a bounds check at the writer (similar to the existing dispatch helper's `cmpi.l #0x00C10000, %d2; blo` range check)

### 1.7.4 What this fix plan does NOT touch

- v3.1 closures (Resolution B for 0x54052, LUT MUST NOT consultation, jsr-not-bsr): UNTOUCHED
- v3.2 dispatch contract (`genesistan_hook_3ad44_dispatch` polymorphic-utility A0 dispatch): UNTOUCHED
- D6-fix patches in `_3b930` / `_54810`: UNTOUCHED
- `opcode_replace` at arcade_pc 0x3AF04: UNTOUCHED
- `_bootstrap` ending with `jmp (0x3A200).l`: UNTOUCHED
- `_vblank_service` ending with `jmp (0x3A208).l`: UNTOUCHED
- 18-entry opcode_replace count (Andy v3.2 final = 90): UNTOUCHED
- Slot-LUT, staging buffers, commit logic, audit guards: UNTOUCHED
- The arcade source mapping boundary at `arcade_source_start: 0x000F08`: UNTOUCHED (correctly architectural per §1.3)

No spec revision. No new source edits. No build-pipeline changes. The fix surface — once the actual writer is identified — will be bounded to either (a) a single opcode_replace entry, or (b) a single-helper bounds-check / address-computation patch.

---

## §1.8 Architecture compliance verification

Both the analytical conclusion (Site 1 = false candidate) AND the proposed downstream methodology (Cody trace task → Andy classification follow-up → bounded source/spec patch) preserve all 10 architectural invariants:

| Invariant | Compliance | Reasoning |
|-----------|------------|-----------|
| No Genesis-side lifecycle introduced | YES | The fix surface is bounded to either an opcode_replace entry or a helper bounds check; neither introduces a lifecycle/scheduler/main-loop. |
| Helpers RTS-return | YES | Existing helpers all RTS; any added bounds-check patch preserves RTS exit. No new lifecycle helper. |
| No memory shadowing | YES | No PC090OJ-address-space mirror is proposed. |
| No scaffolding | YES | The eventual fix is production-intent (real defect class — VDP I/O range overshoot or missing intercept). The Cody trace task is investigatory, not scaffolding (no test code or temporary system in production). |
| v3.1 Resolution B preserved | YES | `genesistan_pc090oj_hook_slot_init_54052` and its text-RAM clear loops are not touched. |
| v3.2 dispatch contract preserved | YES | `genesistan_hook_3ad44_dispatch` body unchanged; A0 ranges unchanged; tilemap branch unchanged. |
| `opcode_replace` at 0x3AF04 preserved | YES | Spec entry untouched. |
| `_bootstrap` closure preserved | YES | [boot.s:166](apps/rastan-direct/src/boot/boot.s#L166) `jmp (0x00003A200).l` untouched. |
| `_vblank_service` closure preserved | YES | [vdp_comm.s:179](apps/rastan-direct/src/vdp_comm.s#L179) `jmp (0x00003A208).l` untouched. |
| Arcade owns execution | YES | Arcade still drives all calls into helpers; helpers RTS-return; bootstrap routes to arcade entry once. The HV Counter writer (whatever it turns out to be) is NOT a Genesis-side lifecycle issue — it's either an arcade-write that needs interception or a helper-side address-computation bug. Both fix categories preserve the arcade-owns-execution invariant. |

All 10 invariants pass.

---

## Phase 2 integrity

| Check | Status |
|-------|--------|
| §1.1 arcade routine 0x54A-0x596 read and quoted verbatim | YES |
| §1.2 loop overshoot computed | YES; the arcade routine WOULD write to 0xC00008 on iteration 5 at instruction 0x57E (informational; routine does not execute) |
| §1.3 address-map boundary analyzed | YES; intentional/architectural — preserved_vectors first segment (4360 bytes) replaces arcade_pc 0x0..0x000F07 with Genesis bootstrap |
| §1.4 bootstrap routing analyzed | YES; arcade reset vector = 0x0003A000; Genesis `_bootstrap` ends with `jmp (0x00003A200).l`; arcade_pc 0x000590 NEVER reached |
| §1.5 Build 54 trajectory cross-checked | YES; Build 54 reaches runtime 0x3A196 (post-bootstrap), proving bootstrap completed without firing the alleged Site-1 crash |
| §1.6 Read classified | Site 1 = Read 4 (DEFINITIVELY CONFIRMED); actual writer = Read 5 (UNIDENTIFIED, downstream Cody follow-up specified) |
| §1.7 Fix plan produced | PARTIAL — Site 1 confirmation requires no fix; actual fix awaits Cody binary trace per §1.7.2 |
| §1.8 Architecture compliance verified | YES (10/10 invariants preserved by the analysis and the proposed downstream methodology) |
| All conclusions cited (Rule 17) | YES (every claim references address_map.json, boot.s, maincpu.disasm.txt, genesis_postpatch.disasm.txt, Andy v3.2 spec, RULES.md, or ARCHITECTURE.md) |
| No new evidence collection (Rule 20) | YES |
| No source/spec/tool modifications | YES |
| STOP conditions | TRIGGERED — actual writer source unidentified; Cody binary-trace follow-up specified in §1.7.2. Site 1 classification is complete and definitive (Read 4); the STOP applies only to the broader question of "what is the actual writer?" |

---

## Cross-reference

- `RULES.md` (Rules 1, 4, 5, 8) — architectural compliance check
- `ARCHITECTURE.md` — helper-function contract
- [build/maincpu.disasm.txt:390-410](build/maincpu.disasm.txt#L390-L410) — arcade routine 0x54A-0x596
- [build/maincpu.disasm.txt:9](build/maincpu.disasm.txt#L9) — arcade reset vector longword `0x0003A000`
- [build/genesis_postpatch.disasm.txt:402-403](build/genesis_postpatch.disasm.txt#L402-L403) — Genesis postpatch at runtime 0x590 (CRAM-init, not arcade routine)
- [build/genesis_postpatch.disasm.txt:298-340](build/genesis_postpatch.disasm.txt#L298-L340) — Genesis crash handler at runtime 0x4A8+
- [build/rastan-direct/address_map.json](build/rastan-direct/address_map.json) lines 1-90 — boundary analysis (preserved_vectors first segment + arcade_copy second segment)
- [apps/rastan-direct/src/boot/boot.s:142-167](apps/rastan-direct/src/boot/boot.s#L142-L167) — `_start` and `_bootstrap` source
- [apps/rastan-direct/out/symbol.txt:26-27](apps/rastan-direct/out/symbol.txt#L26-L27) — `_start` at 0x202, `_bootstrap` at 0x226
- `docs/design/Cody_build54_hvc_writer_search.md` — primary input (12 callsites, 3 indirect candidates)
- `docs/design/Cody_exodus_frame_extraction_build_54_11_16.md` — Build 54 trajectory (PC reaches 0x3A196 post-bootstrap)
- `docs/design/Andy_pc090oj_implementation_spec.md` v3.2 — design authority
- `docs/design/Andy_build53_d0_origin_root_cause.md` — prior cycle (D6 fix)
