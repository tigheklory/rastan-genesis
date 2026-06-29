# Andy — 0x0010D000 PC080SN Descriptor Table WRAM Mapping (Design Only)

**Author:** Andy
**Date:** 2026-06-29
**Baseline:** Build 0115 (`dist/rastan-direct/rastan_direct_video_test_build_0115.bin`, SHA256 `5af34e440a79f2d9d447a767592ea903d026edea3f174a97d446b03ed23026e3`). rastan-direct.
**Scope:** DESIGN only. No source/spec/tool/Makefile/ROM/build/bookmark/diagnostic/implementation; no runtime probing (existing evidence only). Output: this doc + one AGENTS_LOG entry. Code-PC via `address_map.json` (no ±0x200 as authority). Labels: **[OBS]** verified this task; **[CODY]** Cody evidence; **[INT]** interpretation. **Class:** KF-036 (raw arcade work-RAM via literal address). **SEPARABLE from KF-038** (scroll/staging-size aliasing) — not fixed here.

---

## Phase 0 — Baseline

**Classification:** EXTENDING (KF-036; OPEN-023). **Contradiction:** NONE. **Root (Cody, re-verified):** Build 0115 crashes at `runtime_genesis_pc 0x00055B1A` (`arcade_pc 0x0005591A`), `move.w %a4@,%a2@+`, fault addr `0x0000000F`, item state `%a5@(0)=2/%a5@(2)=2/%a5@(4)=4`. The PC080SN descriptor rebuild reads its 16 source pointers from **raw literal `0x0010D000`**, which `address_map.json` places in the `genesis_only` ROM segment (`0x070000..0x17CF08`); ROM bytes at file offset `0x10D000` are `00 00 00 0F` → `%a4=0x0000000F` → `move.w %a4@` faults on the odd source address. [OBS — disasm + ROM bytes confirm]

---

## 1. Selected design + justification — **(a) DIRECT IMMEDIATE REBASING**

**Rewrite each raw `0x0010D0xx` immediate/absolute operand to its KF-036-mapped Genesis-WRAM equivalent `0x00FF10xx`.** Byte-neutral (4-byte immediate → 4-byte immediate; 4-byte absolute → 4-byte absolute), exactly the CLOSED-017 NAME-source-base pattern. Chosen over (b) helper/(c) broad mirror because the lifecycle analysis (§3) proves the table already lives in mapped WRAM via the code's **A5-relative** accesses; the *only* defect is the **raw-literal** accessors pointing at ROM. Rebasing those literals to the same WRAM the A5-relative accesses already use makes every accessor consistent — minimal, byte-neutral, no helper, no invented contents, no new WRAM lifecycle.

---

## 2. Exact KF-036 mapping (CORRECTION) and the WRAM binding [OBS]

KF-036 is **offset-preserving from base `0x0010C000 → 0x00FF0000`** (proven: NAME source `0x0010C157 → 0x00FF0157`). Therefore:

> **arcade `0x0010D000` → Genesis-WRAM `0x00FF1000`** (`0x00FF0000 + (0x10D000 − 0x10C000) = 0x00FF0000 + 0x1000`).

**This corrects the task's suggested `0x00FFD000`** — that would require a low-16-preserving map, which contradicts `0x10C000 → 0xFF0000`. The offset-preserving formula (the actual KF-036) gives `0xFF1000`. So the table range `0x0010D000..0x0010D0FC` → Genesis-WRAM `0x00FF1000..0x00FF10FC`.

---

## 3. Lifecycle (THE CRUX) — resolved: A5 = work-RAM base, table already in mapped WRAM [OBS+INT]

**Arcade `A5` = the work-RAM base `0x0010C000`** (Genesis `A5 = 0x00FF0000` per KF-036; consistent with KF-001's `%a5@(0x2C) = 0x00FF002C` watchdog counter). Proof from this ROM: the descriptor output byte is accessed **both** ways at the same location —
- raw literal `0x0010D0A8` (writes at `0x55AF8`, `0x55B40`), and
- A5-relative `%a5@(4264)` (reads at `0x55AE8`, `0x505E4`, `0x50684`).

`%a5@(4264) = A5 + 0x10A8`. With arcade `A5 = 0x10C000`, that is `0x10D0A8` — **identical to the raw literal.** So `0x10D0A8` (raw) and `%a5@(4264)` are the **same work-RAM byte**; on Genesis `A5 = 0xFF0000`, so `%a5@(4264) = 0x00FF10A8`. The raw literal `0x10D0A8` was **never rebased** and still points at ROM `0x10D0A8`. [OBS]

**Consequences (lifecycle fully resolved):**
- **Who populates `0x10D000..0x10D03F`:** the 16 source pointers live at `A5+0x1000.. = %a5@(4096)..`. The only raw-literal `0x10D000` sites are the **mutate** (`0x55AC6`) and **read** (`0x55B04`) — neither is the initial populator. The populator therefore writes via **A5-relative** addressing (`%a5@(4096)..`), which on Genesis already targets mapped WRAM `0x00FF1000..` (correct). [INT — strong; confirmed by the A5=base equivalence and the validation gate in §8]
- **Does the populator need the same mapping:** NO — being A5-relative, it already writes the mapped WRAM `0x00FF1000`. The bug is purely the **raw-literal readers/mutators/writers** pointing at ROM. Rebasing those to `0x00FF10xx` makes them read the populator's already-correct WRAM.
- **Seed-from-ROM vs built-at-runtime:** the table is **built at runtime in work-RAM** (A5-relative); no ROM seed is copied to `0x10D000`, and no contents are invented. (The seed *values* are ROM descriptor addresses like `0x1691C..0x3725C` per Cody, written into the A5/WRAM table by the runtime builder.)
- **Persistence (`0x55AC6` mutation):** the mutate does `addql #4` to each of the 16 entries every pass — requiring the table to **persist** across visits. WRAM `0x00FF1000..` persists; ROM does not (and the current raw mutate writes to ROM = dropped, so on Genesis the mutation is currently a silent no-op). Rebasing `0x55AC8` to `#0x00FF1000` restores the persistent mutation.

> **Net:** the table is already populated and persisted in mapped WRAM via A5-relative code; the raw-literal accessors are the lone KF-036 gap. No invented data, clean lifecycle. [INT]

---

## 4. Exact table range (Genesis-WRAM-bound) [OBS/CODY]

| arcade-RAM | Genesis-WRAM | contents |
|---|---|---|
| `0x10D000..0x10D03F` | `0x00FF1000..0x00FF103F` | 16 source descriptor pointers (longs) |
| `0x10D040..0x10D07F` | `0x00FF1040..0x00FF107F` | 16 rebuilt pointer entries (longs) |
| `0x10D080..0x10D09F` | `0x00FF1080..0x00FF109F` | 16 copied descriptor first words |
| `0x10D0A0 / 0x10D0A4` | `0x00FF10A0 / 0x00FF10A4` | dest-pointer slots (hold `0xC08000`/`0xC00000`) |
| `0x10D0A8` | `0x00FF10A8` | byte/word output (= `%a5@(4264)`) |

**Crash-fix bounded core (task range `0x10D000..0x10D0A8`):** the descriptor table + dest-pointer slots + output. The full proven-used page extends to `0x10D0FC` (count `0x10D0AA`, reads `0x10D0D8/DA`, clear `0x10D0EA`, dest `0x10D0F8`, `0x10D0FC`) — same work-RAM page, same KF-036 class (§5 full list).

---

## 5. Static references to patch/route (complete scan) [OBS]

Full-ROM scan of raw `0x10D0xx` literals/absolutes:

**Descriptor-table crash core (MINIMUM to clear `0x55B1A`):**
| runtime_genesis_pc | instr | literal → rebased |
|---|---|---|
| 0x00055AC8 | `moveal #0x0010D000,a0` (mutate base) | `#0x00FF1000` |
| 0x00055AF8 | `movew d0,0x0010D0A8` (output) | `0x00FF10A8` |
| 0x00055B04 | `moveal #0x0010D000,a0` (read base) | `#0x00FF1000` |
| 0x00055B0A | `moveal #0x0010D040,a1` (rebuilt base) | `#0x00FF1040` |
| 0x00055B10 | `moveal #0x0010D080,a2` (copied base) | `#0x00FF1080` |
| 0x00055B40 | `movew d0,0x0010D0A8` (output) | `0x00FF10A8` |

**Same-page siblings (item-page render work-RAM; recommended in the same pass — same class, byte-neutral):**
| runtime_genesis_pc | instr | literal → rebased |
|---|---|---|
| 0x000505EC | `movel #0xC08000,0x0010D0A0` | `0x00FF10A0` |
| 0x000505F6 | `movel #0xC00000,0x0010D0F8` | `0x00FF10F8` |
| 0x00050600 | `movel #0xC08000,0x0010D0A4` | `0x00FF10A4` |
| 0x0005060C | `movel #0xC00000,0x0010D0F8` | `0x00FF10F8` |
| 0x00050616 | `movel #0xC08000,0x0010D0A0` | `0x00FF10A0` |
| 0x00050626 | `movel d0,0x0010D0A4` | `0x00FF10A4` |
| 0x0005062C | `movew #64,0x0010D0AA` | `0x00FF10AA` |
| 0x00050644 | `subil #16380,0x0010D0A0` | `0x00FF10A0` |
| 0x0005064E | `subil #16380,0x0010D0F8` | `0x00FF10F8` |
| 0x00050668 | `subil #16380,0x0010D0F8` | `0x00FF10F8` |
| 0x00050672 | `subqw #1,0x0010D0AA` | `0x00FF10AA` |
| 0x00050678 | `cmpiw #0,0x0010D0AA` | `0x00FF10AA` |
| 0x000514D2 | `movew 0x0010D0DA,d6` | `0x00FF10DA` |
| 0x000514E8 | `movew 0x0010D0DA,d6` | `0x00FF10DA` |
| 0x000514FE | `movew 0x0010D0D8,d6` | `0x00FF10D8` |
| 0x0005151C | `movew 0x0010D0D8,d6` | `0x00FF10D8` |
| 0x000528E4 | `clrw 0x0010D0EA` | `0x00FF10EA` |
| 0x00055E14 | `moveal #0x0010D0FC,a0` | `#0x00FF10FC` |
| 0x00055E2E | `moveal #0x0010D0FC,a0` | `#0x00FF10FC` |

> Note [INT]: the dest-pointer **slots** `0x10D0A0/A4` hold PC080SN HW addresses (`0xC08000/0xC00000`) that the render loop (`0x55B48`/`0x55E4A`) later uses as raw write dests — that raw PC080SN write is **KF-038/KF-032 (out of scope)**. This design rebases the **work-RAM slots** (KF-036), not the render loop's HW writes.

---

## 6. Patch shape for Cody + byte/opcode_replace impact

- **Shape:** in-place immediate/absolute rebasing — each `0x0010D0xx` operand → `0x00FF10xx` (high word `0x0010 → 0x00FF`, low word `0xD0xx → 0x10xx`). 4 bytes → 4 bytes, **byte-neutral**.
- **opcode_replace delta:** +N patched_sites, where N = number of rebased instructions (**6** for the minimum crash core; **~25** for the full page incl. siblings — exact count = the §5 row count Cody applies).
- **total_genesis_bytes_covered:** **UNCHANGED** (byte-neutral immediate edits; no helper growth; no relocation). Same invariant profile as the CLOSED-017 NAME-source-base rebasing.
- **Collision check:** `0x00FF1000..0x00FF10FC` lies **within the A5 state struct** (`A5=0x00FF0000`; the code already uses `%a5@(4264)=0x00FF10A8`, `%a5@(4298)=0x00FF10CA`, … up to `%a5@(5148)=0x00FF141C`). So the rebased literals point at **WRAM already in legitimate use by the A5-relative accesses** — no new collision; it makes raw and A5-relative accessors agree. Does **not** overlap `staged_fg_buffer` (0xFF501A), `staged_bg_buffer`, scroll-staging (0xFF40xx), `fg_row_dirty` (0xFF4006), high-score (0xFF0157), or audit_guard (0xFF67xx). [OBS]
- **Recommendation:** apply the **full §5 set** in one pass (all same KF-036 class, all byte-neutral) so the descriptor table *and* its sibling render work-RAM agree; at minimum the 6 crash-core sites clear `0x55B1A`. (Rebasing only the 6 clears the crash but leaves the dest-pointer slots `0x10D0A0/A4` written-to-ROM-dropped → the render loop reads stale dests → likely a downstream crash/garbage = "acceptable progress," but the full set avoids that churn.)

---

## 7. Out of scope (enforced)

- NO KF-038 staging-size / item-scroll fix; NO `bg_fill` global row remap.
- NO routing of the render loop's raw PC080SN HW writes (the `0xC08000/0xC00000` dest values) — that is KF-032/KF-038, separate.
- NO sprites/HUD/Window implementation; NO temporary skip/bypass; NO fake/invented table data.
- NO broad arcade-RAM mirror — bounded to the proven-used `0x10D000..0x10D0FC` page (the §5 accessors).

---

## 8. Validation plan for Cody

- Build passes canonical gate; new build/SHA.
- `0x55B04..0x55B46` runs **WITHOUT ADDRESS ERROR** (no fault at `0x55B1A`).
- **`%a4` loads VALID descriptor source pointers** (matching the original-arcade pattern `0x1691C..0x3725C` class) from `0x00FF1000`, **NOT** wrapper/ROM bytes. *(This is also the populator gate: if `%a4` reads zeros/garbage instead of valid pointers, the populator is NOT A5-relative as inferred and must itself be found + rebased — STOP and report. Strong expectation per §3 is valid pointers.)*
- Table outputs at the mapped equivalents `0x00FF1040 / 0x00FF1080 / 0x00FF10A8` match the original-arcade 16-entry rebuild behavior (rebuilt pointers, copied words, `D0A8` output); the `0x55AC6` mutation now persists (`addql #4` per pass actually advances the WRAM table).
- Item page MAY still render incorrectly (KF-038) but MUST NOT crash at `0x55B1A`.
- Execution progresses PAST item cleanup toward the next attract/gameplay state; a NEW later crash is acceptable progress — report it (esp. if only the 6-site core is applied and the render loop hits stale dest pointers).
- No dispatcher/LUT/VDP-commit regression; title/story/high-score still render.
- Byte-neutral confirmed; document the exact opcode_replace count delta (= number of §5 sites patched); total_genesis_bytes_covered unchanged.

---

## 9. Risks / open questions

| Item | Note |
|---|---|
| Populator not A5-relative (mapped-but-empty) | §3 infers A5-relative (strong, from A5=base equivalence). §8 `%a4`-valid-pointer gate catches it if wrong → STOP/find populator. |
| Partial fix (6-site core only) surfaces downstream dest-pointer issue | Expected/acceptable ("new later crash = progress"); full §5 set avoids it. |
| WRAM collision | Ruled out — `0xFF1000..0xFF10FC` already in use by A5-relative accesses; disjoint from staging/scroll/highscore/audit. |
| KF-038 entanglement | Explicitly out of scope; this only rebases work-RAM SLOTS, not the render loop's HW writes. |
| Mapping-formula error | Corrected to `0xFF1000` (offset-preserving, proven by `0x10C157→0xFF0157`); NOT the task's `0xFFD000`. |

## Open / Closed Issues Impact

- Open issues touched: **OPEN-023** (item-page descriptor-table crash — designed via KF-036 immediate-rebasing; not closed pending implementation + the `%a4`-valid-pointer validation gate), KF-036 class (new instance: the `0x10D0xx` work-RAM page), OPEN-001 (context — item-page progression). KF-038 (explicitly out of scope). OPEN-015 not touched.
- New issues opened: NONE (the same-page sibling accessors are folded into this fix's §5 list; the render loop's raw PC080SN writes remain KF-038).
- Issues closed: NONE.
- Intentionally deferred: implementation; KF-038 item scroll/staging-size + the render loop's raw HW writes; any later downstream crash exposed by progress.

## STOP triggered

NO (the design binds the whole table to mapped WRAM via byte-neutral immediate rebasing, with the lifecycle resolved — populator already A5-relative-mapped, no invented contents, clean persistence).
