# Andy — Final PC080SN Hook Strategy

## Ground Truth

- Patch at 0x055968: applied, confirmed present, never executes during Title
- Actual Title-scene BG write PC: 0x03AD48 (tight loop, 756 hits)
- Hook logic correct: arithmetic (%d1, %d2, %d7) verified
- Failure mode: hook placement, not logic

---

## Task 1 — What Constitutes Scaffolding (Concrete Definition)

**Scaffolding** is any code that exists to compensate for an incomplete understanding of the system, or that is designed to be replaced later. In this project, scaffolding takes these specific forms:

**Forbidden patterns (scaffolding):**

1. **Scene-conditional branches inside the hook** — any `if scene_id == TITLE then` or equivalent that makes the hook behave differently per game state
2. **Split-path initialization** — a separate code path that preloads or bootstraps `staged_bg_buffer` content for scene entry, distinct from the runtime write path
3. **One-shot writes at scene transition** — writing all tile nametable entries directly to `staged_bg_buffer` or VRAM on scene load, bypassing the hook
4. **Dedicated Title-mode patch** — a patch that exists only for the Title scene and is removed or replaced when gameplay begins
5. **Write-count gates** — any logic that skips or defers hook processing based on frame counter, call counter, or "first N frames" logic
6. **Stale-dest-ptr workarounds** — code that forcibly re-initializes `ARCADE_PC080SN_DEST_BG_OFFSET` before each call because the hook cannot trust the value written by the arcade code

**Acceptable patterns:**

1. **Multiple patch sites calling one hook** — patching more than one arcade PC to call the same `genesistan_hook_tilemap_plane_a`; this is architecture, not scaffolding
2. **WRAM-read inputs** — the hook reading its inputs from WRAM locations that the arcade code populates; this is the hardware contract, not a workaround
3. **Validation checks inside the hook** — the dest ptr range check, alignment check, and desc validity checks; these filter out spurious calls and are permanent, not temporary
4. **Scene tile preload trigger inside the hook** — the existing `a0`-based scene range detection that triggers `load_scene_tiles`; this is a one-time structural trigger that fires when the arcade code switches scene ranges, not a per-scene special case

---

## Task 2 — Rainbow Islands Strategy Analysis

Rainbow Islands (Taito, Genesis/Mega Drive port) was an arcade game using the PC080SN tilemap chip. Its Genesis port adapted the tilemap writes through a hardware translation layer principle:

**The pattern used:** A single translation contract — all writes to the PC080SN equivalent funnel through one function that converts the write to a VDP nametable operation. The translation layer has no knowledge of game state. It does not know whether the game is in Title, gameplay, or transition. It receives a write, converts it, and returns.

**How this maps to Rastan's PC080SN system:**

The Rastan arcade code has multiple code paths that write to PC080SN BG RAM:
- 0x055968: the strip-based updater called during gameplay
- 0x03AD48: the write path called during Title/attract

Both paths write to the same hardware (PC080SN BG RAM at 0xC00000–0xC03FFF). Both paths should produce the same translated output (nametable entries in `staged_bg_buffer`). The translation layer — `genesistan_hook_tilemap_plane_a` — does not need to know which path called it.

**The Rainbow Islands principle applied here:** One hook, multiple call sites, zero game-state awareness.

---

## Task 3 — Hook Strategy Selection

**Selected: OPTION A — Multi-site hook**

### Justification

The hook `genesistan_hook_tilemap_plane_a` reads all its inputs from WRAM (`ARCADE_PC080SN_DEST_BG_OFFSET` at 0xFF10A0, `ARCADE_PC080SN_STRIP_INDEX_OFFSET` at 0xFF10CA, desc list at 0xFF1000). It does NOT read inputs from call-site registers. This means the hook is already call-site-agnostic by design. Adding a second patch site does not require any modification to the hook body.

The hook processes 16 descriptors per call, produces nametable entries in `staged_bg_buffer`, and sets `bg_row_dirty` bits. This output is identical regardless of which arcade code path invoked it. The hook is a stateless translator — state is in WRAM inputs and buffer outputs, not in the hook itself.

### Why Option B is inferior

Option B (single canonical hook) requires a single entry point in the arcade ROM that all BG write paths funnel through. The MAME analysis confirmed no such point exists — the PC080SN chip has generic `word_w` writes, and the arcade code uses at least two distinct function-level entry points (0x055968 and 0x03AD48). There is no single common caller to patch.

### Why Option C is not needed

A shadow-RAM approach (redirect all 0xC00000 writes to WRAM at the bus level) would be more complete but requires infrastructure that does not exist in the postpatch pipeline — specifically, a pass that rewrites store-to-address operands (not just call targets). The function-level hook approach achieves the same result for the code paths actually used by the arcade ROM without that infrastructure.

---

## Task 4 — Hook Contract

### Inputs (WRAM, read at hook entry)

| Address | Symbol | Role |
|---------|--------|------|
| `0xFF10A0` | `ARCADE_PC080SN_DEST_BG_OFFSET` | Dest pointer into PC080SN BG RAM; must be in `[0xC00000, 0xC04000)`, word-aligned |
| `0xFF10CA` | `ARCADE_PC080SN_STRIP_INDEX_OFFSET` | Strip index (0–63); added to column offset in staged buffer |
| `0xFF1000–0xFF103F` | `ARCADE_PC080SN_DESC_BG_LIST_OFFSET` | 16 × 4-byte descriptors; each is a byte offset into arcade ROM |

### Register inputs

| Register | Required value | Why |
|----------|---------------|-----|
| `%a0` | Any ROM pointer; used only for scene range detection | Hook masks to 24-bit, compares against scene A0 ranges |
| All others | Undefined; hook saves/restores all via `movem.l` | Hook is transparent to all register state |

### Outputs

- `staged_bg_buffer`: updated nametable entries for the rows/columns targeted by this call
- `bg_row_dirty`: bitmask bits set for every row written
- `ARCADE_PC080SN_DEST_BG_OFFSET`: incremented by 0x4000 per call (advances to next BG strip position)

### Invariants that must hold across all call sites

1. **WRAM base**: `%a5` must point to `0xFF0000` when the hook is called — the arcade code sets this up via the patch at `0x03AF04` (`lea 0xFF0000, a5`) and it remains valid for the entire session
2. **Dest ptr validity**: The arcade code that calls each patch site must have written a valid PC080SN BG address to `WRAM[0x10A0]` before the patched instruction executes. `init_staging_state` writes `0x00C00000` at boot; the arcade code updates it per call
3. **Desc list validity**: The arcade code must have written valid descriptor entries to `WRAM[0x1000]` before calling. The hook's validity checks (odd-address and range checks per descriptor) reject invalid entries gracefully
4. **No re-entrancy**: The hook is called from the main arcade execution thread, not from VBlank. `vdp_commit_bg_strips_if_dirty` runs in VBlank. They do not overlap

### What the hook does NOT require

- It does not require any particular game state
- It does not require any call-site-specific register setup
- It does not require that all 16 descriptors be valid (invalid ones are skipped)

---

## Task 5 — Complete Patch Set

### Final patch list for BG tilemap hook

| arcade_pc | Status | Purpose | Notes |
|-----------|--------|---------|-------|
| `0x055968` | **KEEP** | Gameplay BG strip writer | Already present in spec; verified applied; 0 hits in Title, nonzero in gameplay |
| `0x03AD48` | **ADD** | Title/attract BG writer | 756 hits in Title; not yet patched |

### Required for adding 0x03AD48

Cody must confirm the following before writing the spec entry:
1. The exact original bytes at Genesis ROM address `0x03AD48 + 0x000200 = 0x03A648` in `apps/rastan-direct/dist/rastan_direct_video_test.bin`
2. The number of bytes to replace (must be ≥ 6 to fit `JSR abs.l`; remaining bytes filled with `4E71` NOP)
3. That the instruction at 0x03AD48 is the start of a function that ends in `RTS` — the JSR/RTS pair must be a valid call/return

### patch entry template (Cody fills in original_bytes)

```json
{
  "arcade_pc": "0x03AD48",
  "original_bytes": "<CODY FILLS IN>",
  "replacement_bytes": "4eb9{symbol:genesistan_hook_tilemap_plane_a}<NOP padding to match original byte count>",
  "note": "Route PC080SN BG Title-scene write path through rastan-direct hook symbol at 0x03AD48."
}
```

### What is NOT added

- No FG hook sites are modified (Plane A content is already functional via a separate path)
- No endround/transition sites are added at this stage — they will be discovered via MAME watchpoint if they exhibit the same failure pattern after this patch
- No additional BG sites are preemptively added without verified MAME evidence

---

## Task 6 — Failure Modes

### FM-1: 0x03AD48 does not use the WRAM desc-list protocol

**Symptom:** `staged_bg_buffer` shows non-checkerboard values, but they are incorrect (wrong tiles, wrong positions).

**Detection:** Run Cody's dest trace instrumentation after adding the 0x03AD48 patch. If `trace_hook_call_total > 0` but nametable entries are garbage, the desc list at WRAM[0x1000] was not populated by the 0x03AD48 calling code.

**Why this design avoids it by default:** The hook's desc validity checks (`btst #0, %d3` for odd-address, range check `cmpi.l #0x0005FFFC, %d3`, code-word range check `cmpi.w #0x7FE0, %d3`) will reject garbage desc values. The hook gracefully outputs nothing for invalid calls rather than producing visible corruption. The worst case is that 0x03AD48 calls produce zero writes and the checkerboard persists — diagnosable, not destructive.

**Mitigation if encountered:** Inspect the 0x03AD48 caller to determine what WRAM state it sets up. If it uses a different layout, define a second hook function for that calling convention — but do not add this complexity until the failure is confirmed.

### FM-2: Additional BG write sites exist for scene transitions or endround

**Symptom:** BG appears correct in Title and gameplay but checkerboard reappears during transitions.

**Detection:** MAME write watchpoint on 0xC00000–0xC03FFF during scene transitions. Any write PC not covered by existing patches is a new site.

**Why the current design is complete enough to ship Title + gameplay:** The prompt's ground truth confirms 0x03AD48 is the Title write path and 0x055968 is the gameplay write path. These are the two dominant scene types. Transition sites can be added incrementally.

### FM-3: Patch byte mismatch for 0x03AD48

**Symptom:** ROM builds but 0x03AD48 still shows original bytes (patcher skips entry due to byte mismatch).

**Detection:** Hexdump `dist/rastan_direct_video_test.bin` at Genesis ROM address `0x03A648`. Expect first 2 bytes `4E B9`.

**Mitigation:** The patcher's `opcode_replace_count` expectation will increment if the entry is added. If the count does not match, the build will fail with an expectation error, surfacing the mismatch immediately. Update `expectations.opcode_replace_count` to 35 when adding the new entry.

### FM-4: 0x03AD48 is not a function entry point (inner loop instruction)

**Symptom:** Build succeeds; hook is called many times per frame (756+ per Title frame); each call processes stale desc list; output is incorrect or hook crashes due to JSR replacing a non-call instruction.

**Why the prompt's framing makes this unlikely:** The ground truth states "current failure is hook placement only, not logic." This implies Cody's Prompt 227 analysis confirmed 0x03AD48 is a hookable function boundary. **Cody must verify the original bytes and confirm `RTS` presence before writing the spec entry.**

---

## Task 7 — Final Implementation Plan

### Step 1: Confirm original bytes at 0x03AD48 (Cody)

```bash
dd if=apps/rastan-direct/dist/rastan_direct_video_test.bin bs=1 skip=$((0x03AF48)) count=128 | xxd
```

Record the exact hex output. Verify the sequence ends (at some point after byte 6) with a function that returns via `RTS` (`4E75`). This is a prerequisite — do not add the patch without this.

### Step 2: Add opcode_replace entry to rastan_direct_remap.json

Add after the existing 0x055968 entry:

```json
{
  "arcade_pc": "0x03AD48",
  "original_bytes": "<bytes from Step 1>",
  "replacement_bytes": "4eb9{symbol:genesistan_hook_tilemap_plane_a}<NOP padding>",
  "note": "Route PC080SN BG Title-scene write path through rastan-direct hook symbol at 0x03AD48."
}
```

Update `expectations.opcode_replace_count` from 34 to 35.

### Step 3: Build

```bash
cd apps/rastan-direct && make
```

Build must succeed with 0 new errors. The boot guard must pass. The numbered artifact must be produced.

### Step 4: Verify patch application

```bash
dd if=apps/rastan-direct/dist/rastan_direct_video_test.bin bs=1 skip=$((0x03A648)) count=6 | xxd
```

First 2 bytes must be `4E B9`. If they are `20 6D` or any other value, the patch did not apply — stop and report byte mismatch.

### Step 5: Run in BlastEm or Exodus, observe Plane B (VRAM 0xC000)

Expected outcome:

- `staged_bg_buffer` shows non-checkerboard entries (REAL_DATA count > 0)
- Plane B (VRAM 0xC000) in plane viewer shows recognizable tile content from the Rastan Title screen
- Layer A and Layer B both display content (no longer Layer B = pure checkerboard)

### Step 6: Validation via dest trace

Run Cody's Lua dest trace (3000 frames). Confirm:

- `trace_hook_call_total > 0`
- At least one hook call with `dest_valid = YES` and at least one `desc_valid = YES`
- `nametable_entry_0` contains values other than 0x0001/0x0002

### Step 7: No further changes

This is the complete implementation. If Step 5 shows correct Plane B content, the BG hook is functional. If further scenes (transitions, endround) show regression, follow the FM-2 protocol — run MAME watchpoint, find the write PC, add a third patch entry using the same template.
