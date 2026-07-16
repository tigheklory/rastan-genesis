# Andy — Build 0183 (80-Record Mirror) Visual Rejection / Player Sprite Boundary

**Date:** 2026-07-16
**Type:** Analysis (diagnostic range builds + runtime evidence). No gameplay-logic change; configurable-mirror mechanism unchanged.
**Baselines:** 0181 (256) `1ef9085e…`, 0182 (128) `5f7264db…`, 0183 (80) `defe5173…`.

## User visual observations recorded
- Build 0182 / 128: consistent with prior working gameplay; Rastan on expected left, orientation normal; title/story/READY render; black bars + slowdown remain; no enemies; uncontrollable.
- Build 0183 / 80: **visually rejected** — Rastan appears on the opposite/right side, orientation/composition wrong (looks like attribute/position/flip data associated with the wrong record). Title/story/READY still mostly render. Not acceptable as a diagnostic cap.

## Primary question — answered: classification **D (records 120..127 required)**
Specifically records **120..121** (the player anchor). Minimum visually-safe record count = **122**.

## Threshold sweep (head sprite = staged_sprite_sat slot 0 @ fixed 0xFFA1B0, gameplay F900+, stable across F800..F1700)
| RECORDS | Build | Head slot-0 X | Result |
|---:|---|---|---|
| 256 | 0181 | 0x0090 | NORMAL (screen X≈16, left) |
| 128 | 0182 | 0x0090 | NORMAL |
| 124 | 0187 | 0x0090 | NORMAL |
| 122 | 0190 | 0x0090 | NORMAL (stable all frames) |
| 120 | 0186 | 0x0000 | EMPTY head slot |
| 118 | 0189 | 0x0000 | EMPTY head slot |
| 116 | 0188 | 0x0000 | EMPTY head slot |
| 112 | 0185 | 0x01A0 | FLIPPED (screen X≈288, right) |
| 96 | 0184 | 0x01A0 | FLIPPED |
| 80 | 0183 | 0x01A0 | FLIPPED |

Three-way behavior: >=122 correct; 116..120 head sprite empty; <=112 flipped to the right. The safe boundary is **122** (records 0..121 present).

## Mechanism (proven)
- The player cluster is **duplicated**: a low copy at mirror records 0,1,4,5,6,8..11 (codes 009E/009F/008E/008F/0090/0076..0079) and the **arcade-canonical copy at records 120..137** (same codes; this is the Build 0164 / arcade 0x041F5E A5+0x11B2->records 120..137 mapping). In the 128 build both are represented; head slot 0 = record 0.
- **Mirror records 0..14 are byte-identical between the 128 and 80 builds** (e.g. r0: Y=0049 code=009E X=0010 in both). The divergence is therefore NOT in the low player record data.
- The SAT head X flips 0x0090 <-> 0x01A0. `0x01A0 = (320 - 0x10 - 16) + 0x80` exactly matches the PC090OJ **flip-screen transform** (x = 320 - x - 16). So the 80/96/112 builds render Rastan (and all sprites) mirrored to the right; the represent head composition also collapses (empty) at 116..120.
- Root: the represent/player composition is load-bearing on the **high canonical player records 120..121**. Dropping them (any cap <122) breaks Rastan's head/position/orientation even though the low duplicate records survive. This is a game/represent-architecture dependency, **not** a bug in the configurable-mirror mechanism: 256 and 128 both render correctly (config drops records exactly as designed; `oob` counts scale as expected).

## Player-cluster answers
1. Player anchor record: **120 (009E) / 121 (009F)** — arcade-canonical (0x041F5E/Build 0164), mirrored at low records 0/1.
2. Player body-part records: 124,125,126,128..137 (008E/008F/0090/0076..0079) canonical; 4,5,6,8..11 low duplicate.
3. Flip/position/attr data: every player record carries word0 (attr, e.g. 4003), Y, X; the flip is the GLOBAL flip-screen applied in decode, which ends up wrong when the canonical anchor is dropped.
4. Duplicated player records from the 0x041F5E / Build 0164 lineage: **120..137** (secondary dup also near 88..95).
5. Does 80 lose an anchor but keep a body record? It drops the entire canonical block (>=80); the surviving low duplicate cannot compose Rastan correctly on its own (head empty/flipped).
6. Does that explain the right-side / wrong orientation? **Yes** — losing records 120..121 leaves the represent producing the flip-screen-transformed (right-side, mirrored) or empty head.

## Config-mechanism bug check — NONE
128 and 256 render correctly; the corruption appears only when records 120..121 are dropped. `PC090OJ_BITSET_BYTES`/`record_to_slot`/sentinel sizing are correct at every tested count (no off-by-one: e.g. 122 and 124 straddle the boundary cleanly by record presence, not by a sizing artifact). No code fix is warranted; the mechanism works.

## Safe lower bound / recommendation
- 80/96/112/116/118/120 are all visually unsafe. **Minimum visually safe = 122.**
- 124/128/256 are safe. Recommend **128** as the practical safe diagnostic cap (margin above 122, byte-clean, Tighe-confirmed).
- None of the prompt's suggested caps (96/112/120) is safe. Keep project default **256**.

## Diagnostic builds (all preserved, GATE_PASS, deterministic; diagnostic-only, NOT accepted)
0181=256 `1ef9085ed272edacd5d73edf806eab867c1687aa61d502227d6f898fd0ae6abc`;
0182=128 `5f7264dbac1b8cb084568f740f4ef21070463ea806d48219bd663b183841e7c0`;
0183=80 `defe5173ae57b4e55f9fe35cbbe783cc0f453f4275e6527dfcbe80bbdad4c68c`;
0184=96 `cd79e758…`; 0185=112 `712d3bc6…`; 0186=120 `748cb98f…`; 0187=124 `67c85475…`;
0188=116 `501ba597…`; 0189=118 `0385662e…`; 0190=122 `21aa7c91…`. All size 1,582,840.
0191 = restored default 256 (== 0181). Repo left configured at default 256; counter 191.

## Not touched
Configurable-mirror mechanism, Build 0180 SAT-dirty gating, Build 0178 tile-DMA cache, Build 0175 palette route, Build 0172 FG / 0171 BG projections — all preserved. No input/collision/enemy/sky-reset/D00298/continue/Exodus work.
