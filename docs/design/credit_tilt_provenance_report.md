# CREDIT / TILT Provenance Report

**Agent:** Andy (Forensic Verification)
**Build investigated:** Rastan_276.bin
**Date:** 2026-03-28
**Mandate:** READ-ONLY forensic analysis. No code, spec, or build files were modified.

---

## 1. Purpose

Determine the provenance of two text strings observed on screen in the current Rastan Genesis port (build ~276) running on BlastEm/Exodus:

- "CREDIT" appears on screen after coin-up
- "TILT" appears in upper-left after Genesis reset input (A+B+C+Start), then system returns to launcher

For each string: identify origin (arcade ROM original, patcher-translated, or C-code scaffold/fake), trace the call chain from trigger to screen, and audit all fake/hardcoded text paths.

---

## 2. Files Read

Mandatory reference files:

- `/home/tighe/projects/rastan-genesis/AGENTS.md`
- `/home/tighe/projects/rastan-genesis/AGENTS_LOG.md` (last 500+ lines, lines ~21200–21733)
- `/home/tighe/projects/rastan-genesis/docs/design/phase1_runtime_ordering_proof.md`
- `/home/tighe/projects/rastan-genesis/docs/design/rom_absolute_call_relocation_vs_shift_proof.md`
- `/home/tighe/projects/rastan-genesis/docs/design/absolute_call_target_fix_plan.md`
- `/home/tighe/projects/rastan-genesis/docs/design/multi_pass_operand_relocation_design.md`
- `/home/tighe/projects/rastan-genesis/docs/research/title_screen_graphics_call_inventory.md`
- `/home/tighe/projects/rastan-genesis/docs/research/build246_real_game_text_translation.md`
- `/home/tighe/projects/rastan-genesis/docs/research/build271_title_logo_sprite_translation.md`
- `/home/tighe/projects/rastan-genesis/docs/research/true_text_producer_entry.md`
- `/home/tighe/projects/rastan-genesis/docs/research/text_producer_execution_failure.md`
- `/home/tighe/projects/rastan-genesis/docs/research/text_record_rejection_point.md`
- `/home/tighe/projects/rastan-genesis/apps/rastan/src/main.c`
- `/home/tighe/projects/rastan-genesis/apps/rastan/src/startup_bridge.c`
- `/home/tighe/projects/rastan-genesis/tools/translation/postpatch_startup_rom.py`
- `/home/tighe/projects/rastan-genesis/specs/startup_title_remap.json`
- `/home/tighe/projects/rastan-genesis/dist/Rastan_276.bin` (binary, searched via Python)
- `/home/tighe/projects/rastan-genesis/roms/rastan.zip` (arcade ROM archive, extracted and searched)

---

## 3. Current Build

**Rastan_276.bin** — Pass B (deferred operand relocation) implemented and validated. Static baseline confirmed: ROM @0x03AAEC = `4EB90005A174`.

---

## 4. CREDIT Provenance

### 4.1 Source Bytes

**Arcade ROM (interleaved maincpu, 256KB binary):**

| Field | Arcade address | Value |
|-------|---------------|-------|
| Descriptor base | 0x3BCBE | — |
| D6 destination | 0x3BCBE–0x3BCC1 | `0x00C09E84` (arcade C-window) |
| Attr word | 0x3BCC2–0x3BCC3 | `0x0000` |
| Text payload | 0x3BCC4–0x3BCCD | `43 52 45 44 49 54 20 20 20 00` = "CREDIT   \0" |

**Genesis ROM (Rastan_276.bin):**

| Field | Genesis address | Value |
|-------|----------------|-------|
| Descriptor base | 0x3BED4 | — |
| D6 destination | 0x3BED4–0x3BED7 | `0xE1000126` (WRAM, translated) |
| Attr word | 0x3BED8–0x3BED9 | `0x0000` |
| Text payload | 0x3BEDA–0x3BEE3 | `43 52 45 44 49 54 20 20 20 00` = "CREDIT   \0" |

Text bytes are **byte-for-byte identical** between arcade and genesis ROM.

### 4.2 Address Arithmetic

Arcade text region 0x3BCC4 + 0x200 (base relocation) + 22 (accumulated shift delta before this address) = **0x3BEDA** — matches the confirmed genesis ROM offset exactly.

### 4.3 Selector Table

Genesis selector table at 0x3BD92 (22 entries, 4 bytes each):

- Entry[2] at genesis 0x3BD9A → pointer `0x0003BED4` → CREDIT descriptor

### 4.4 Call Chain

```
Coin-up input detected (arcade title loop / attract sequence)
  -> arcade 0x03B09C: MOVEQ #2, D0 (selector = 2)
  -> BSR to text dispatch wrapper at genesis 0x2027C0
     (wraps true text producer at 0x20034C)
  -> text producer reads selector table entry[2] at 0x3BED4
  -> loads D6 = 0xE1000126 (translated WRAM destination)
  -> loads attr word
  -> iterates text payload bytes, writing to VDP or WRAM character cells
  -> "CREDIT   " appears on screen
```

### 4.5 Writer Path

The text is written by the translated arcade text producer (originally at arcade ~0x03406C, relocated to genesis 0x20034C). The patcher translated the descriptor's D6 destination field from arcade C-window address 0x00C09E84 to Genesis WRAM address 0xE1000126 via `window_rewrite_rules` in `startup_title_remap.json`. No C code writes or injects this string.

### 4.6 Verdict

**CREDIT is REAL — 100% arcade-original text, byte-for-byte identical to arcade ROM, produced by the translated arcade text producer with a patcher-translated destination address. Zero C-code scaffolding.**

---

## 5. TILT Provenance

### 5.1 Source Bytes

**Arcade ROM:**

| Field | Arcade address | Value |
|-------|---------------|-------|
| Descriptor base | 0x3BDCC | — |
| D6 destination | 0x3BDCC–0x3BDCF | `0x00C08B50` (arcade C-window) |
| Attr word | 0x3BDD0–0x3BDD1 | `0x0000` |
| Text payload | 0x3BDD2–0x3BDD7 | `54 49 4C 54 00` = "TILT\0" |

**Genesis ROM (Rastan_276.bin):**

| Field | Genesis address | Value |
|-------|----------------|-------|
| Descriptor base | 0x3BFE2 | — |
| D6 destination | 0x3BFE2–0x3BFE5 | `0xE0FFEDF2` (WRAM, translated) |
| Attr word | 0x3BFE6–0x3BFE7 | `0x0000` |
| Text payload | 0x3BFE8–0x3BFED | `54 49 4C 54 00` = "TILT\0" |

Text bytes are **byte-for-byte identical** between arcade and genesis ROM.

### 5.2 Address Arithmetic

Arcade text region 0x3BDD2 + 0x200 (base relocation) + 22 (accumulated shift delta) = **0x3BFE8** — matches the confirmed genesis ROM offset exactly.

### 5.3 Selector Table

Genesis selector table at 0x3BD92 (22 entries):

- Entry[14] at genesis 0x3BDC6 → pointer `0x0003BFE2` → TILT descriptor

### 5.4 Call Chain

```
Pre-coin title page ongoing loop (arcade 0x03ABCA region):
  -> BTST #2, (0x390007)   ; test service/tilt input bit
  -> BNE skip               ; if bit 2 SET (not pressed), skip TILT text
  -> bit 2 CLEAR = tilt/service active
  -> MOVEQ #14, D0          ; selector = 14
  -> BSR to text dispatch wrapper at genesis 0x2027C0
  -> text producer reads selector table entry[14] at 0x3BFE2
  -> loads D6 = 0xE0FFEDF2 (translated WRAM destination, upper-left region)
  -> writes "TILT" to screen
```

### 5.5 Genesis Trigger Mapping

In `startup_bridge.c`, `build_system_input_byte()` (lines 132–149) maps the Genesis controller to the arcade system input register (`genesistan_shadow_input_390007`). Holding **A+B+C simultaneously** clears bit 2 (mask `~0x04`) of that register, satisfying the `BTST #2 / BNE skip` condition in the arcade code.

**A+B+C+Start** is simultaneously the Genesis hardware soft-reset combination (handled by SGDK/hardware). This means the sequence the user observed — TILT appears then system returns to launcher — is explained by: A+B+C triggers the TILT display via arcade code, and +Start triggers the Genesis hardware reset, returning execution to `main()` (the launcher). These are two independent effects of the same button combination, not a TILT-induced reset.

### 5.6 Verdict

**TILT is REAL — 100% arcade-original text, byte-for-byte identical to arcade ROM, produced by the translated arcade text producer. The trigger (A+B+C clearing bit 2 of 0x390007) is the correct translation of the arcade tilt/service input check. Zero C-code scaffolding.**

---

## 6. Fake Text Path Audit

### 6.1 C Source Search

All C source files searched for the strings "CREDIT" and "TILT":

**`apps/rastan/src/main.c`:**
- "CREDIT" appears only in lines 162 and 165: `"PRICING FOR CREDITS AND COINS."` and `"STARTING LIVES FOR EACH CREDIT."` — these are settings menu help strings in the Genesis launcher UI, not game-logic text injection.
- "TILT" does not appear.

**`apps/rastan/src/startup_bridge.c`:**
- Neither "CREDIT" nor "TILT" appears.

**`tools/translation/postpatch_startup_rom.py`:**
- Neither "CREDIT" nor "TILT" appears as a string literal or byte constant.

**`specs/startup_title_remap.json`:**
- Neither "CREDIT" nor "TILT" appears.

### 6.2 Conclusion

There are no fake or scaffold text injection paths for either CREDIT or TILT in any C source, patcher script, or spec file. Both strings are exclusively produced by the translated arcade ROM's own text producer subsystem operating on translated data descriptors.

---

## 7. Final Conclusion

Both "CREDIT" and "TILT" are fully authentic arcade-original strings. The patcher translates the descriptor destination fields (D6) from arcade C-window addresses to Genesis WRAM addresses via `window_rewrite_rules`, but the text payloads themselves are never touched. The translated arcade text producer (selector table at genesis 0x3BD92, producer at genesis 0x20034C, wrapper at 0x2027C0) reads these descriptors and writes characters to the translated WRAM destinations. The Genesis input bridge correctly maps controller buttons to the arcade input register byte, including the tilt/service bit 2 condition.

No hardcoded or scaffolded text paths exist for either string.

---

CREDIT verdict: REAL — arcade-original text, patcher-translated destination, no C-code injection
TILT verdict: REAL — arcade-original text, patcher-translated destination, no C-code injection
Fake text path status: NONE FOUND — exhaustive search of all C source, patcher, and spec files returned zero hardcoded instances of either string in game logic
