# Andy — PC090OJ 0x3B930 / 0x3B802 Object-RAM-Faithful Replacement Design (Audit / Design Only)

**Author:** Andy
**Date:** 2026-07-02
**Baseline:** rastan-direct Build 0126 (`dist/rastan-direct/rastan_direct_video_test_build_0126.bin`, SHA256 `f5935113ef4ab8ea231d4e31764b96a36c8bd2fe246846a2ca929facdfccd921`). rastan-direct.
**Scope:** DESIGN / AUDIT only. No implementation; no source/spec/tool/Makefile/ROM/build changes. Arcade↔Genesis correlation via `address_map.json` (no arithmetic-offset proof). Labels: **[OBS]** verified this task; **[CODY]** Cody evidence; **[INT]** interpretation. **Object-RAM-faithful (not screen-result-faithful).**

> **BOTTOM LINE:** The current Genesis `0x3B930` helper is broken **four** independent ways vs the arcade: it (1) **ignores caller A1** (hardcodes helper slot 14), (2) **clamps D1 to 4** (arcade writes 5 and 9), (3) **swaps the word2/word3 field sizes**, and (4) **omits the `jsr 0x5b512` transform**. The field-swap is the exact mechanism of the wrong title sprites (the X-word `0x0088` lands in the code field → `code 0x0080`). The fix is object-RAM-faithful: preserve caller **A1/D1**, reproduce the arcade 4-word-per-object layout **into `pc090oj_object_ram` at `(A1−0xD00000)`**, call the preserved transform (runtime `0x5b712`), mark the mirror dirty, and write **no** descriptors/SAT — let the VBlank scan derive them. **Verdict: GO** with a narrow plan.

---

## == PHASE 0 ==

**Relevant priors:** KF-021 (staged/true/linked SAT divergence — context), KF-032 (route to mirror not raw), KF-036 (arcade work-RAM `0x10xxxx`→`0xFF0000` mapping — the `0x3B802` helper already remaps its work-RAM score pointer via this), Andy PC090OJ architecture audit (object-RAM-mirror direction; this is the producer-side correction).
**High-rediscovery hazards:** KF-021 HIGH (do not conflate mirror correctness with final composite).
**Task classification:** DESIGN AUDIT / EXTENDING OPEN-024.
**Contradiction detected:** NO (consistent with the architecture audit and Cody's producer-to-mirror trace; this refines the producer-side helpers).
**Open/Closed Issues pre-check:** OPEN-024 primary; OPEN-001 context (title completeness); OPEN-021 context (score sprites); OPEN-006 context (colbank). Not closing OPEN-001/OPEN-024.
**title 27-sprite arcade baseline acknowledged:** YES (codes incl. 0x2A–0x2D, 0x31, 0x39–0x3E, 0x46–0x49).
**wrong 3/4 Genesis helper-owned sprites acknowledged:** YES (0x0001@e4, 0x0110@e14, 0x0080@e16/17).
**SAT link-chain refuted as title cause:** YES (chain `0→1→2→3→0` structurally valid).
**Build 0125 suppression context acknowledged:** YES (temporary; not canonical; baseline is 0126).
**object-RAM-faithful architecture rule acknowledged:** YES.
**address_map.json loaded:** YES.
**arithmetic offset used as proof:** NO.

**Mapped sites (JSON):** arcade `0x3B930`→runtime `0x3BB30` (patched_site); `0x3B802`→`0x3BA02` (patched_site); `0x3B902`→`0x3BB02` (patched_site); `0x3B926`→`0x3BB26` (patched_site); code-transform `0x5B512`→`0x5B712` (**arcade_copy** — original arcade routine preserved, callable).

---

## == ARCADE 0x03B930 SEMANTICS (Part A) == [OBS]

**Caller sites (title score):**
- `0x3B902` (`arcade_pc`): `lea 0xD00088,a1; … lea (pc,0x3B984),a0; moveq #5,d1; bsr 0x3B930` → copies **5** objects from table `0x3B984` to PC090OJ object RAM **`0xD00088`**. (When `d1≠0` it instead byte-pokes attr at `+2` over 5 entries — the digit-highlight path.)
- `0x3B926`: `lea 0xD00128,a1; moveq #9,d0; …` → **9** objects to **`0xD00128`**.
- Top driver `0x3B8F0`: `bsr 0x3B902` (5 @ 0xD00088), then `bsr 0x3B802 (d0=3)`, `bsr 0x3B802 (d0=4)` (score digits).

**Object-RAM destination spans:** `0xD00088..0xD000B0` (5×8B) and `0xD00128..0xD00170` (9×8B), plus the `0x3B802` digit destinations — all within the PC090OJ active `0x800` range (`0x88`, `0x128` ≪ `0x800`).

**Per-object write layout (`0x3B930` loop, 4 words to `(a1)+`):** [OBS]
```
[+0] word0 = 0                         (clr.w d2; move.w d2,(a1)+)   → flip/color = 0
[+2] word1 = (a0)+ byte                                              → Y
[+4] word2 = (a0)+ byte                                              → code   (e.g. 0x3B,0x3A,0x3C,0x3D…)
[+6] word3 = 0x5B512( (a0)+ word )     (move.w (a0)+,d7; jsr 0x5B512; move.w d7,(a1)+)  → X (transformed)
```
Source consumes 4 bytes/object: `[Y.b][code.b][X.w]`. Table `0x3B984`/`0x3B950` = `00 3B 00 88 | 00 3A 00 78 | 00 3C 00 98 | 00 3D 00 A8 …` → **code = 0x3B/0x3A/0x3C/0x3D** (matches the expected title codes), X-word = 0x88/0x78/0x98/0xA8. (Per MAME `pc090oj.cpp`: word2=code&0x1FFF, word3=X&0x1FF — the transform at `0x5B512` operates on the X/position word, not the code; the "code-conv" label is a mis-name — flag for Cody, but reproduce faithfully regardless.)

**General-purpose vs title-only:** `0x3B930` is a **general PC090OJ object-table copy primitive** (caller supplies `a0`/`a1`/`d1`); the title score is one caller. **Preserving A1/D1 (and the word layout + transform) is sufficient** for the title top-score objects — no title special-casing needed.

---

## == GENESIS 0x03B930 HELPER AUDIT (Part B) == [OBS]

`genesistan_pc090oj_hook_target_3b930` (runtime `0x3BB30`, arcade `0x3B930`, patched_site):
1. runtime address: `0x0003BB30`.
2. patched arcade site: `0x0003B930`.
3. **A0 preserved:** YES (reads source `(a0)+`).
4. **A1 preserved:** **NO** — ignores caller A1; hardcodes `moveq #14,d0` (start **slot 14**).
5. **D1 preserved:** **NO** — `cmpi #4,d6; bls ok; moveq #4,d6` → **clamps count to 4** (arcade uses 5 / 9).
6. hardcoded start slot: **14**.
7. count clamp: **max 4**.
8. object mirror write destination: helper slots 14,15,16,17 (via `.Lpc090oj_emit_slot`, which writes `pc090oj_object_ram + slot*8`) — **NOT** `(A1−0xD00000)`.
9. descriptor/SAT side effects: **YES** — `.Lpc090oj_emit_slot` also writes `staged_sprite_descriptor_table`/`staged_sprite_sat` (semantic record) — producer-side descriptor writes, which violates the "descriptors/SAT only from the VBlank scan" rule.
10. writes mirror directly or via helper-owned slot: **helper-owned slot** path (`.Lpc090oj_emit_slot`, slot-indexed), not A1-addressed.
11. **field order (the decisive bug):** reads `d2=(a0)+.b`, `d4=(a0)+.b`, `d3=(a0)+.w`; `.Lpc090oj_emit_slot` writes `word1=d2, word2=d3, word3=d4`. So Genesis puts the **X-word into word2 (code)** and **code-byte into word3 (X)** — **word2/word3 swapped vs arcade**, and the `0x5B512` transform is **omitted**.
12. why it cannot produce the 27 arcade title objects: wrong destination (slot 14 not `0xD00088`→entry 17), dropped objects (clamp 4<5, and no 9-object path), scrambled code/X, missing transform → the mirror never contains the arcade title entries in arcade-equivalent form.

**Classification: helper-owned slot emission / NOT equivalent.**

---

## == ARCADE 0x03B802 SEMANTICS (Part C) == [OBS]

`0x3B802` is the **score-digit updater**. Record = 10 bytes at `0x3B87E + mode*10` (mode = `d0`). Fields: `[+0]` digit count, `[+1]` attr/Y byte, `[+2]` **PC090OJ destination pointer (a1←record+2)**, `[+6]` **score-data source pointer (a2←record+6, in arcade work-RAM `0x10xxxx`)**. It loops the digit count, extracts BCD nibbles from the score data, converts each via `0x3B866`, and writes the digit **code = `nibble + 0x2A`** into the destination PC090OJ entry (`move.w d1,4(a1)` = word2/code region; `move.b d6,3(a1)` attr), advancing the destination. `code = nibble + 0x2A` matches the expected title codes **0x2A–0x33** (digits). It **uses a destination pointer** (record+2, a PC090OJ object-RAM address) and updates **title score digits** (and shares the mechanism with in-game score/HUD via the mode table). It **relates to `0x3B930`** as the *dynamic* counterpart: `0x3B902/0x3B926` lay down the static score-strip objects; `0x3B802` overwrites the digit entries with live score values at their PC090OJ destinations.

**Needs a faithful replacement, and can share the same PC090OJ write-mirror primitive** as `0x3B930` (both write object-RAM entries at an arcade-provided PC090OJ destination pointer).

---

## == GENESIS 0x03B802 HELPER AUDIT (Part D) == [OBS]

`genesistan_pc090oj_hook_score_digit_3b802` (runtime `0x3BA02`, arcade `0x3B802`, patched_site):
1. runtime address: `0x0003BA02`.
2. patched arcade span: `0x0003B802`.
3. destination mapping: reads record `a4 = record+2` (arcade PC090OJ dest) and `a2 = record+6` (score data, correctly KF-036-remapped `0x10xxxx→A5+off`), then maps digits into **helper-owned slot** territory via `.Lpc090oj_emit_slot`-style paths (partial), rather than writing the mirror at `(a4−0xD00000)`.
4. supported range: only the limited helper-owned slot range it maps.
5. missing range: the arcade `a4` PC090OJ destinations that fall outside its mapped slots → those digit entries never reach the mirror faithfully.
6. writes mirror in object-RAM-faithful form: **NO** (helper-owned mapping; `a4` destination not used as the mirror offset).
7. can it explain wrong small title sprites: **PARTIALLY** — helper-owned digit emission contributes to the wrong/missing score sprites alongside `0x3B930`.
8. can it explain missing score digits: **YES** — the live digits never land at their arcade PC090OJ destinations in the mirror, so the scan doesn't emit them.

**Classification: partial helper-owned mapping / NOT equivalent.**

---

## == OBJECT-RAM-FAITHFUL DESIGN (Part E) == [INT]

**Recommended strategy — reproduce the arcade producer into the mirror, addressed by the caller's PC090OJ pointer:**
- **0x3B930 replacement writes directly into `pc090oj_object_ram` using caller A1 and D1.** (Q1: yes.)
- **A1→mirror mapping:** `mirror_off = (A1 & 0x00FFFFFF) − 0x00D00000`; dest = `pc090oj_object_ram + mirror_off`. (Q2.)
- **Mirror range:** preserve the **active `0x800`** range only (the drawable range the scan reads). (Q3/Q5: active-only.)
- **A1 outside active `0x800` but inside `0x4000`:** for the title path this never happens (`0x88`, `0x128`); design a **bounds guard**: if `mirror_off ≥ 0x800` (or `< 0` / `A1` outside `[0xD00000,0xD00800)`) → **skip + count** (`pc090oj_producer_oob_count`), do not write out of the mirror buffer. (Q4/Q7.) A larger `0x4000` mirror is **not** required (drawable range is `0x800`). (Q5.)
- **D1 trusted as arcade count** (Q6), but bounded by the guard: clamp writes so `mirror_off + D1*8 ≤ 0x800` (never a fixed max-4).
- **Code transform:** reproduce `jsr 0x5B512` by calling the preserved routine at **runtime `0x5B712`** (arcade_copy) for word3, exactly as the arcade does. (Q8/Q9: yes; it currently isn't represented in the helper — it must be added.)
- **Word order (Q10):** faithfully `[word0=0][word1=Y.b][word2=code.b][word3=0x5B712(X.w)]` — **fix the current word2/word3 swap.**
- **Dirty marking (Q11):** set `pc090oj_mirror_dirty = 1` after writing (as `.Lpc090oj_emit_slot` already does for the bridge path).
- **No direct descriptor/SAT writes (Q12/Q13):** the producer writes **only** the mirror. Descriptors/SAT are **solely** the VBlank mirror-scan product. (Remove the producer-side `staged_sprite_descriptor_table`/`staged_sprite_sat` writes from this path.)
- **Blank/unmapped interaction (Q14):** none at the producer — the mirror holds arcade truth (including code 0x2A–0x49). The blank-bitset and `≥0x1000` unmapped guard apply **only** at the VBlank scan's emit step (Build 0125/0126 work), unchanged. (The title codes 0x2A–0x49 are nonblank and <0x1000, so they pass.)
- **Scaffolding risk (Q15): NONE** — this is a faithful reproduction of arcade writes into the mirror; no synthetic sprite list, no screen-result reconstruction, no fake data. Arcade code still owns the object data (source table `a0`, count `d1`, destination `a1`).

**mirror range:** active `0x800`. **A1-to-mirror mapping:** `(A1&0xFFFFFF)−0xD00000`. **D1 handling:** trust + bound. **bounds checks:** `mirror_off∈[0,0x800)` and `mirror_off+D1*8≤0x800` else skip+count. **word order:** arcade-exact (fix swap). **code conversion:** call runtime `0x5B712`. **dirty:** set. **descriptor/SAT responsibility:** VBlank scan only. **blank/unmapped:** scan-side only, unchanged. **scaffolding risk:** none.

---

## == SCORE-DIGIT DESIGN (Part F) ==

**Recommended: Option 3 — a shared PC090OJ write-mirror primitive used by both `0x3B930` and `0x3B802`.** [INT]
A small `.Lpc090oj_mirror_write_word_at_hwaddr(hw_addr in a1, word in d?)` (and/or an entry-level variant) that maps `hw_addr→(hw_addr−0xD00000)` with the bounds guard and writes the mirror + marks dirty. `0x3B930` uses it for its 4-word entries (calling `0x5B712` for word3); `0x3B802` uses it to write each digit's `code=nibble+0x2A` (and attr) at its arcade destination `a4`.

| Option | architectural correctness | risk | title-score coverage | gameplay/HUD risk | story-page risk | preserves arcade ownership |
|---|---|---|---|---|---|---|
| **1** (0x3B802 writes faithful mirror at its own dest) | correct | low | digits only | low | low | yes |
| **2** (reduce/remove 0x3B802; rely on 0x3B930 + raw) | risky | **high** (live digits never updated → static/blank score) | incomplete | high | medium | partial |
| **3** (shared write-mirror primitive) | **correct + minimal duplication** | low | full (statics + digits) | low | low | **yes** |

**Recommend Option 3.** Why: both helpers do the same operation (write arcade object words to a PC090OJ destination); one shared, bounds-guarded, faithful primitive eliminates the helper-owned divergence in both and keeps arcade ownership (source/dest/count all arcade-provided). **Evidence required:** post-fix mirror at `0xD00088`/`0xD00128`/the digit destinations matches arcade object words; scan emits digit codes `0x2A–0x33` + strip codes `0x39–0x49`.

---

## == WRONG GENESIS SPRITES IMPACT (Part G) == [OBS+INT]

- **current wrong sprites source:** helper-owned artifacts. Entry **14** = the `0x3B930` helper's hardcoded start slot; the wrong **codes** are the field-swap: the X-word `0x0088` mis-placed into word2 → `code&0x1FFF = 0x0080`; `0x0110` similarly an X/position word; `0x0001` a low byte. So `0x0080`, `0x0110`, `0x0001` are **directly the scrambled `0x3B930` outputs**, not arcade objects.
- **expected effect of the design:** the object-RAM-faithful `0x3B930`/`0x3B802` would **replace** these wrong entries with the correct arcade title objects at their arcade mirror offsets (entries `0x88/8=17…`, `0x128/8=37…`, digits), with correct codes `0x2A–0x49`. The wrong `0x0080/0x0110/0x0001` disappear because slot 14 is no longer force-written.
- **could any be a legitimate arcade object from another path?** Unlikely for these three (they trace to the `0x3B930` helper's slot 14 + field swap), but Cody must confirm no *other* producer legitimately writes entry 14/16/17 (e.g. a status-sprite path) before assuming all three vanish.
- **verification Cody must capture:** post-fix `pc090oj_object_ram` dump showing entries 17–21 / 37–45 / digit entries hold the arcade codes (0x2A–0x49) with word0=0 and transformed X; scan `emitted` list containing those codes; the three wrong codes absent (or explained by another path).

---

## == STORY-PAGE IMPACT (Part H) == [INT] (does NOT claim to fix story black cover)

1. **Could helper-owned slot emission also explain wrong story-page sprites?** Possibly — if the story page uses `0x3B930`/`0x3B802` (or the same helper-owned slot path), its objects would be equally mis-placed/scrambled. Not proven; flag.
2. **Could faithful producer replacement change story-page SAT output?** YES — any story-page caller of these shared helpers would now write faithful mirror entries → different (more correct) SAT. This is desirable but must be regression-checked.
3. **Risks if story shares the helpers:** a faithful change could alter story-page sprites (better or exposing a new issue); the bounds guard prevents overflow; but story destinations outside `[0xD00000,0xD00800)` would be skipped+counted (verify story uses the active range).
4. **Post-implementation evidence Cody must capture:** title score appears (codes 0x2A–0x49); wrong title sprites gone; **story black cover state reported (changed/unchanged — not claimed fixed)**; `pc090oj_object_ram` matches arcade for target entries; SAT chain still valid; staged-vs-true SAT compared if the VDP-SAT read path is available (KF-021).

---

## == IMPLEMENTATION READINESS (Part I) ==

**GO/NO-GO: GO.** The defect is precisely diagnosed (4-way `0x3B930` divergence + partial `0x3B802`), the arcade semantics are JSON-mapped and byte-read, and the faithful design is narrow, bounded, and non-scaffolding.

**Cody implementation outline (narrow):**
- **Files to edit:** `apps/rastan-direct/src/pc090oj_hooks.s` only.
- **Functions to edit:** `genesistan_pc090oj_hook_target_3b930`, `genesistan_pc090oj_hook_score_digit_3b802`; add a shared `.Lpc090oj_mirror_write_*` primitive (bounds-guarded, `hw_addr→mirror_off`, mark dirty).
- **What to preserve:** caller `a0`(source)/`a1`(dest)/`d1`(count); the arcade 4-word layout `[0][Y.b][code.b][X.w→0x5B712]`; the `0x3B802` record semantics (dest `a4`=record+2, score src `a2`=record+6 KF-036-remapped); the digit code `nibble+0x2A`.
- **What to remove:** hardcoded slot 14; count clamp to 4; the word2/word3 swap; producer-side descriptor/SAT writes; helper-owned slot emission for these two paths.
- **What to add:** call runtime `0x5B712` for word3; bounds guard + `pc090oj_producer_oob_count`; `pc090oj_mirror_dirty=1`.
- **Counters/evidence:** OOB count; decoded/emitted title codes; entries-written offsets.
- **Required runtime proof:** `pc090oj_object_ram` at `0xD00088`/`0xD00128`/digit dests = arcade object words; VBlank scan emits the 27 title codes; wrong `0x0080/0x0110/0x0001` gone; SAT chain valid; (if available) staged-vs-true VDP SAT match.
- **Regression checks:** story-page sprites (report change, don't claim fix); high-score/gameplay score digits (Option-3 shared primitive must not break in-game score); no PC080SN/Window/D00298 change; no `descriptor/SAT` written by producers.
- **Constraints:** no fake/synth score data; no direct score-sprite synthesis; no direct SAT emission from producers; no C/SGDK; no MAME copy; no D00298; no Window.

**do not implement yet / implement next:** **implement next** (GO), with the above narrow plan and the object-RAM dump + title-code emit as the acceptance evidence.

---

## Open / Closed Issues Impact

- **Open issues touched:** OPEN-024 (producer-to-mirror faithfulness — root defect diagnosed + design; not closed), OPEN-001 (context — title score is the missing element), OPEN-021 (context — score-sprite provenance), OPEN-006 (context — colbank). OPEN-015 not touched.
- **Closed issues touched:** NONE.
- **New issues opened:** NONE (recommend a tracked note: producer-side helper-owned emission must be replaced by mirror writes; descriptors/SAT are VBlank-scan-only).
- **Issues closed:** NONE (do not close OPEN-001/OPEN-024).
- **Issues intentionally deferred:** story-page black cover (separate; KF-021 true-VDP-SAT capture); in-game (non-title) score/HUD callers of the shared primitive (regression-check scope); implementation itself.

## AGENTS_LOG updated
YES (analysis-doc log entry per standing process).

## evidence artifacts
NONE created (design/audit only; cites existing Cody traces + disasm/JSON verified this task).

## STOP status
NO — audit complete; object-RAM-faithful design specified; GO with narrow Cody plan.
