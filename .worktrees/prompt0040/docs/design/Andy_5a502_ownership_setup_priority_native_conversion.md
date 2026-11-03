# Andy — 0x05A502 Ownership Fix + Setup/Priority PC090OJ Retirement (Build 0287)

**Agent:** Andy · **Baseline:** current forward tree containing Build 0286. **No rollback**; Build 0286 preserved as
a rejected/diagnostic candidate. Labels: **PROVEN / HYPOTHESIS / DISPROVEN**.

## BASELINE / BUILD0286 LESSON
Build 0286 converted the transient-item family and retired the 0x5A502 producer, but invoked the native GAME OVER
emitter from the broad `.Lnq_frontend_object_scan` (all non-gameplay scenes) gated only on `a5+0x34==0` and
`a5+0x200` bit5. **PROVEN (Cody model + user):** those two fields do not identify one screen — the HIGH SCORE
TABLE also has `a5+0x34==0` (terminal exit cleared it at `0x03A460`; only a paid start re-sets it) and can observe
the retained gameplay tick `a5+0x200` bit5 clear. So the eight-glyph row wrongly appeared over the high-score
table. **Lesson:** frontend ownership needs the original game-flow state tuple, not a Genesis scene ID plus two
ambiguous fields.

## CORRECT 0x05A502 SEMANTIC OWNERSHIP
**PROVEN (`Cody_frontend_gameover_highscore_semantic_model.md`):** there are two distinct GAME OVER paths.
- **0x05A502** = the **no-human attract/demo** eight-glyph GAME OVER row. Its caller `arcade_pc 0x051046` invokes it
  only under active attract gameplay: `a5+0x00==2` (gameplay/session umbrella), `a5+0x02==3` (active/attract-demo
  gameplay), nested `a5+0x04 ∈ {0,1}`, `a5+0x34==0` (no-human), visible when `a5+0x200` bit5 clear.
- **Human terminal GAME OVER** = a **separate** producer at `arcade_pc 0x03A420`, set up at tuple `(2,4,5)` and
  displayed/dwelled at `(2,4,6)`. **DISPROVEN:** 0x05A502 is not that screen; it must not be repurposed for it.
  (The terminal text path is out of scope here and untouched.)

## 0x05A502 FORWARD FIX
**IMPLEMENTED.** `.Lnq_gameover_emit`:
1. **Removed** from `.Lnq_frontend_object_scan` (the broad non-gameplay ownership).
2. **Invoked from the GAMEPLAY native finalizer** `.Lnq_gameplay`, appended after the native lanes (shares that
   pass's `a3/a2/a1/d5` SAT context).
3. Gate rewritten to the exact retained original ownership:
   `word(a5+0x00)==2 AND word(a5+0x02)==3 AND (word(a5+0x04)==0 OR 1) AND word(a5+0x34)==0 AND (word(a5+0x200)&0x20)==0`.
   Absolute WRAM reads (`0x00FF0000/2/4/34/200`); `a5` is saved/restored (reused as the label walker). This excludes
   CONTINUE `(2,4,3/8)`, terminal human GAME OVER `(2,4,5/6)`, HIGH SCORE `(0,1,2)`, title/history state 0, and
   paid-start state 1 — so the high-score overlay cannot recur. The Build0286 broken-`0x10C200`→WRAM correction
   remains valid (now expressed as the tuple + `a5+0x200` bit5). **0x05A502 object-RAM publication is NOT restored.**

## BUILD0286 ITEM CONVERSION PRESERVATION
**PRESERVED (unchanged).** `transient_items_active`/`_source_ptr`/`_scroll` and the converted producers 0x056114 /
0x05607C / 0x056440, plus `.Lnq_transient_items_emit` (still in the frontend scan — the item page is a frontend
branch). **PROVEN (Cody):** these neither read nor write `a5+0x00/0x02/0x04/0x34/0x200`, so they are independent of
the 0x05A502 ownership defect. No redesign, no rollback.

## 0x054052 SEMANTICS
**PROVEN.** `genesistan_pc090oj_hook_slot_init_54052` (caller `arcade_pc 0x051260`) only initialized object-RAM
records 72..75 with **code=0** (blank / not-drawable), off-screen. PLAYER_BODY is already main-loop native staging;
the former tuple-init loops have no consumer. **No enduring visible semantic output.** Verified no producer writes
records 72..75 with nonzero code, so they remain boot-blank. → retire the hardware tail (no native state invented).

## 0x03AD84 SEMANTICS
**PROVEN.** `genesistan_pc090oj_hook_init_priority_3ad84` only initialized records 76..79 with **code=0** (blank) at
off-screen X=0x160. The former priority/flip "ladder" intent is **already owned by native lane ORDER** (the gameplay
finalizer emits lanes in priority order), so no ordering is lost by retiring the blank record emit. → retire the
hardware tail.

## 0x03B926 / 0x059F5E LIFECYCLE
**PROVEN.** Both are pure PC090OJ **park/clear maintenance**: `0x03B926` cleared records 5..13; `0x059F5E` cleared
records 9..16 (its retired PLAYER_FRONT `a5+0x170` rebuild was already absent; PLAYER_FRONT is native). The producers
that formerly populated that band (arcade HUD builders `0x3B8B0`/`0x3B902`, generic copier `0x3B930`) are retired /
have no executable route. **Verified:** after this build there is **no live producer** writing records 5..16 with
content (the only `emit_slot`/`clear_slot` callers in the source were these setup/priority hooks). So the clears
service nothing — records stay boot-blank. The genuine semantic lifecycle (state progression) lives in the arcade
state machine, which is untouched; only the hardware record clearing (category B) is retired.

## 0x03AD44 PC090OJ D-RANGE RETIREMENT
**RETAINED + WHY.** `genesistan_hook_3ad44_dispatch` splits `[0xC00000,0xC10000)` → PC080SN tilemap/scroll fills
(**preserved**) and `[0xD00000,0xD00800)` → `pc090oj_object_ram` long-fill. The D-range branch is the shared
object-RAM **reset/transition clear** still invoked by the gameplay/frontend reset sequence, and it still services
the remaining object-RAM consumers (frontend scanner content, Mode-2 P1 HUD record). Per policy ("delete B once the
producers it services no longer require PC090OJ output"), it is **not yet dead** and is retained. **PC080SN C-range
branches preserved: YES** (untouched). This D-range branch is a final-infrastructure-retirement candidate, not a
this-family retirement.

## IMPLEMENTATION
Source-only changes in `apps/rastan-direct/src/pc090oj_hooks.s` (no spec/opcode_replace change):
- `.Lnq_gameover_emit`: 5-condition tuple gate; call moved from `.Lnq_frontend_object_scan` to `.Lnq_gameplay`.
- Retired to a register-preserving no-op (`rts`): `slot_init_54052`, `init_priority_3ad84`, `target_3b926`,
  `target_59f5e`. (Task-authorized producer retirement; disclosed here and in the ledgers.)
- Canonical constants: `opcode_replace_count` unchanged at 228; `total_genesis_bytes_covered` 0x184A98 → **0x184A34**
  (the retirements shrank the genesis-only helper region; no maincpu replacement byte changed, refs unchanged at 7).

## DEAD COMPATIBILITY CODE
After this build, made dead **for these families** (retained, linked, but no live executable caller):
- `.Lpc090oj_emit_slot` and `.Lpc090oj_clear_slot` — their only source callers were the four retired hooks.
- `genesistan_pc090oj_hook_target_3b930` (generic copier) and `.Lpc090oj_mirror_write_word_a1_d0` — 3b930 has no
  executable route (its callers `0x3B8B0`/`0x3B902` are retired); the mirror helper's only caller is 3b930.
Not deleted this task: their symbols are still referenced by spec `opcode_replace` (the retired arcade functions
`jsr` them), so removal is a spec+source infrastructure step, not a source-only edit. Recorded as
final-infrastructure-retirement candidates. `staged_sprite_descriptor_table` remains only for legacy references.

## CURRENT REMAINING PC090OJ CONSUMERS
- **Live `pc090oj_object_ram` producer families:** (1) the shared **0x03AD44 D-range reset/transition long-fill**
  (infrastructure clear); (2) the **Mode-2 P1 HUD** score-record write (`.Lpc090oj_mode2_project_p1_hud`, preserved
  gameplay HUD); (3) the retained-but-**dead/unreachable** 0x5A502 tail destinations (`+0x298/+0x2B0`, redirected so
  no raw 0xD002xx is live). The dedicated slot-producer path (`emit_slot`/`clear_slot`) is now **caller-free**.
- **Frontend scanner `.Lnq_frontend_object_scan` still required:** **YES** — invoked for non-gameplay, non-title
  frontend scenes (`scene != 1`, and scene 0 with stage != 0).
- **Generic decoder `.Lpc090oj_decode_record` still required:** **YES** — invoked by that scanner.
- **Executable PC090OJ D-range output paths:** the 0x03AD44 D-range branch (retained); mapped destination patches
  for remaining families. **No dedicated emit_slot/clear_slot producer remains live.**
- **Families preventing final infrastructure deletion:** the 0x03AD44 D-range fill + the frontend
  scanner/decoder consumers of object-RAM content (whatever remaining mapped-destination producers route through
  them) + the Mode-2 P1 HUD object-RAM record. The setup/priority slot-producer families are now retired.

## POST-HIGHSCORE EXCEPTION STATUS
**NOT investigated/fixed — intentionally OPEN.** Cody proved its root cause is unresolved and the crash screen is
untrustworthy (displays a stacked runtime Genesis PC and handler-clobbered D0–D5; stale `BUILD 0038` footer). No
`arcade_pc` attribution is possible from it. Required future evidence is one narrow crash record:
`CRASH_EXCEPTION_TYPE` (`0x00FF6802`), `CRASH_STACKED_PC` (`0x00FF6806`), `CRASH_FAULT_ADDRESS` (`0x00FF6854`, vec
2/3), and the state tuple `0x00FF0000/+2/+4`. This PC090OJ retirement task is **not blocked** on it.

## BUILD / SMOKE
- **GATE_PASS**; numbered **Build 0287**.
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0287.bin`
- SHA-256: `a03094b046f3aeb66f3c31797081612d5ac73e1b4cfb67653938f9dd9015f12d`
- Size: 1,591,860 bytes · Counter transition **286 → 287**.
- Canonical verification: **PASS** (`opcode_replace_count=228`, `total_genesis_bytes_covered=0x184A34`,
  `genesis_only_maincpu_ref_count=7`). Boot guard PASS (pre+post).
- Makefile 30s Genesis-NTSC smoke: **PASS** (`Average speed: 953.85%`, no crash;
  `states/traces/rastan_direct_video_test_build_0287_mame_30s_20260816_215208`).
- Built with `RASTAN_GAMEPLAY_HUD_SPRITES=2` (0285/0286 config preserved).
- Interactive validation: **DEFERRED TO TIGHE**.

## DOCUMENTATION UPDATES
KNOWN_FINDINGS.md, GRAPHICS_STATUS.md, OPEN_ISSUES.md updated; Build0286 semantic record corrected (0x05A502 is the
no-human attract/demo GAME OVER row, not the human terminal screen; the overlay was an ownership-gate defect). No
CLOSED_ISSUES entry for the runtime-visible behavior pending Tighe acceptance; the mechanical setup/priority
retirement is recorded.
