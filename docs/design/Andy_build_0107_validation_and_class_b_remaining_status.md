# Andy — Build 0107 Validation + Remaining Class B Visual Defects (Status)

**Author:** Andy
**Date:** 2026-06-27
**Build:** 0107 (`dist/rastan-direct/rastan_direct_video_test_build_0107.bin`, SHA256 `4b4a588b1da2ccec6b31cac781bd53627993eaa6170ec013da56f349c99ef1e3`). rastan-direct.
**Scope:** DOCUMENTATION / ledger status only. No source/spec/tool/ROM/build/bookmark/diagnostic/implementation changes; no Class B fix design (future scope only). Address spaces labeled. Labels: **[USER]** user-confirmed; **[CODY]** Cody implementation result; **[OBS]** static fact; **[INT]** interpretation.

---

## 1. Build 0107 — new validated working baseline

[USER][CODY] **Build 0107 supersedes Build 0106 as the current validated working baseline for the OPEN-018 immediate-absolute Class A arc.**
- SHA256: `4b4a588b1da2ccec6b31cac781bd53627993eaa6170ec013da56f349c99ef1e3`.
- The story-page crash at the comma point is **fixed on BlastEm and on real Genesis hardware** [USER].
- The comma **renders visibly** [USER].
- This **positively validates the Class A routing model**: raw PC080SN write → trampoline → live LUT → `genesistan_hook_tilemap_fg_fill` → FG staging → dirty row → VBlank commit. [INT, now evidence-backed]

[CODY] Build invariants:
- `opcode_replace`: `98 → 102` (+4).
- `total_genesis_bytes_covered`: `0x17CD68 → 0x17CDD4` (helper growth `0x6C`).
- Four immediate-absolute Class A raw FG writes routed via the approved **byte-neutral 8-byte `jsr abs.l + nop`** patch shape.
- Attr gate passed for all four cells.
- Raw HW watchpoints no longer observed for the four routed addresses.
- Runtime staging observed for `0x3ACEA` and `0x3A908`.
- `%d0` preservation runtime-proven for `0x3A908 → 0x3A910`.

> **Patch-shape note** [OBS]: the original `move.w #imm,(abs).L` is **8 bytes** (opcode 2 + immediate 2 + absolute-long 4), not 6. The earlier sweep design mislabeled it "6-byte"; Cody's approved **8-byte `jsr abs.l (6) + nop (2)`** shape is byte-neutral against the true 8-byte original. Invariants confirm site byte-neutrality: arcade space unchanged, all growth is the `0x6C` helper region.

---

## 2. OPEN-018 immediate-absolute Class A routing — VALIDATED for the observed blocker

[CODY][USER] **Implemented and validated path (the actual story-page blocker):**
- `runtime_genesis_pc 0x0003ACEA` / `arcade_pc 0x0003AAEA` — original raw `move.w #0x2749, 0x00C09172` → routed; strict-target crash gone, comma visible. ✅

[CODY] **Implemented same-shape siblings (structurally covered):**

| runtime_genesis_pc | arcade_pc | runtime/visual proof in Build 0107 |
|---|---|---|
| 0x0003ACEA | 0x0003AAEA | crash fixed + comma rendered [USER]; staging observed [CODY] |
| 0x0003A908 | 0x0003A708 | staging observed; `%d0` preservation runtime-proven (→ 0x3A910) [CODY] |
| 0x0003A550 | 0x0003A350 | implemented, same mechanism; **NOT runtime-reached** in sampled windows [CODY] |
| 0x0003A8FE | 0x0003A6FE | implemented, same mechanism; **NOT runtime-reached** in sampled windows [CODY] |

> **Honest scope** [INT]: `0x3A550` and `0x3A8FE` are implemented with the identical approved patch/helper mechanism and are **structurally covered**, but were **not** exercised in Cody's sampled validation windows. **No visual/runtime proof is claimed for those two branch-specific sites** until separately observed. (They are conditional branches; reaching them depends on the runtime state flags `42(a5)`/`40(a5)`.)

---

## 3. Remaining OPEN-018 raw-write follow-ups — DEFERRED (did not block the story-page path)

[OBS] These raw PC080SN write shapes remain unrouted in Build 0107:

- **Register-absolute:** `runtime_genesis_pc 0x3A92A` (`move.w %d0,0xC08C62`), `0x3D24C` (`move.w %d1,0xC08C66`).
- **Producer loops:** `0x3B3CC`, `0x3B7F6`, `0x3B7F8` (`move.w dN,(aN)` walks).

Wording [INT]:
- They **did not block** the now-validated story-page comma path (Build 0107 is clean on strict targets at that point).
- They remain **real raw PC080SN write shapes** and may matter for full raw-write closure or other screens.
- **OPEN-018 is not globally closed**: the immediate-absolute portion is implemented and validated; the register-absolute and producer-loop portions remain. Each needs its own decode (confirm register holds a tile code; loop-routing design) before implementation — distinct from the immediate-absolute trampoline pattern.

---

## 4. Class B still open — parens and TAITO (NOT a Build 0107 regression, NOT a Class A failure)

[USER] Build 0107 still has these visual defects:
- TAITO logo still missing tiles.
- `INSERT COIN(S)` parentheses still do not render.

[INT] These are **not regressions from Build 0107** and **not failures of the Class A fix**. They remain under **KF-033 / OPEN-019 / OPEN-020**.

**Parens:**
- Low codes `0x0028` and `0x0029` still do not render.
- Prior finding [OBS]: the live LUT entries for the **raw low codes** resolve to `0x0000`, while the **mapped aliases** `0x2747`/`0x2748` already have valid slots (`0x0037`/`0x0038`) and byte-identical patterns.
- This is a **Class B LUT coverage** issue, **not** a raw-write routing issue (the paren writes are already routed through the glyph renderer + FG staging).

**TAITO missing cells:**
- User-observed missing/magenta cells remain missing in Build 0107.
- Known raw low codes: `0x0022`, `0x0027`, `0x002C`, `0x003F` — all **Class B**.
- **Open question (keep open):** does arcade runtime intend the **raw low-code** tiles, or should runtime apply the `0x563CE` low-code-to-`0x274x` mapping before staging? **Do not assume LUT-only** until this runtime-mapping question is resolved (the TAITO low codes are NOT byte-identical to their mapped tiles and have their own nonblank ROM patterns — they may need preload/slot coverage in addition to / instead of a LUT alias).

---

## 5. Defect taxonomy — POSITIVE confirmation

[INT, evidence-backed] Build 0107 **confirms the two-class taxonomy** (KF-032 / KF-033):

- **Class A — raw PC080SN writes bypassing Genesis staging.** The comma crash was Class A; routing it through `fg_fill` **fixed the strict-target crash and rendered the comma**. ✅
- **Class B — low-code FG glyph/symbol coverage gaps.** Parens and TAITO **remain missing after the Class A fix**, which **confirms they are distinct defects**, not the same crash/routing problem.

This is a positive confirmation of the model: fixing Class A removed the crash and rendered the routed tiles, while the Class B symptoms persisted independently — exactly as the two-class split predicted.

---

## 6. Forward pointers (no design here)

- OPEN-018 next: register-absolute (`0x3A92A`/`0x3D24C`) and producer-loop (`0x3B3CC`/`0x3B7F6`/`0x3B7F8`) raw-write decode + routing (separate shapes).
- OPEN-019/OPEN-020 next (Class B, future scope): resolve the `0x563CE` raw-vs-mapped runtime question; then LUT-alias (parens) and preload+LUT (TAITO low codes) coverage. **Not designed in this doc.**

## Open / Closed Issues Impact

- Open issues touched: **OPEN-018** (status updated — immediate-absolute portion implemented & validated in Build 0107; register-absolute + producer-loop remain; **not** closed), **OPEN-019 / OPEN-020** (reaffirmed open — parens/TAITO still missing in 0107, Class B), OPEN-001 (context — title/story visual completeness), OPEN-005/OPEN-017 (context — strict-target crash family, comma instance resolved). OPEN-015 not touched.
- New issues opened: NONE.
- Issues closed: NONE.
- Intentionally deferred: register-absolute + producer-loop raw writes (OPEN-018); Class B parens/TAITO (KF-033/OPEN-019/OPEN-020); all implementation and Class B design.

## KNOWN_FINDINGS impact

KF-032 updated with a Build 0107 validation note (routing model validated on strict targets; approved 8-byte `jsr abs.l + nop` shape; remaining raw-write shapes tracked under OPEN-018). KF-033 unchanged (Class B parens/TAITO still open, confirmed by 0107).

## STOP triggered

NO.
