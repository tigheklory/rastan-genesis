# BUILD_INSTRUCTIONS.md — How to make a numbered Rastan Genesis build from the current palette profile

Audience: a human **or** an agent (e.g. Cody) who needs to turn the current Palette Composer profile
(`Test.json`) into a complete numbered ROM family. This is the exact workflow Andy used for Builds
0381–0385. Read `CLAUDE.md` and `PROMPT_TEMPLATE.md` first for the governing rules; this file is the
operational recipe.

> **Human builders starting from a fresh project copy:** begin with
> [HUMAN_BUILD_INSTRUCTIONS.md](HUMAN_BUILD_INSTRUCTIONS.md). It explains prerequisites, where to put
> your legally obtained MAME `rastan.zip` and its extracted ROM images, how to verify them, and the exact
> commands to build and launch a test ROM. Return here only when authoring a new palette profile or
> diagnosing the full numbered-release pipeline.

> **TL;DR** — freeze the profile → point the Makefile at the frozen snapshot → `make clean && make release`
> in `apps/rastan-direct/` → fix the coverage invariant if the sprite region size changed → you get five
> ROMs (`base, _c, _d, _do, _s`) numbered with the next build number. Never delete/withhold/reuse a build
> number.

---

## 0. Where everything lives

| Thing | Path |
|---|---|
| **Live editable palette profile** (authored in the Composer) | `analysis/graphics_optimizer/editor_policy/Test.json` |
| Frozen per-build profile snapshot (build input) | `build/rastan-direct/build<NNNN>/Test.snapshot.json` |
| Makefile (owns the whole build) | `apps/rastan-direct/Makefile` |
| Build counter (last consumed number) | `build/rastan-direct/build_counter.txt` |
| Consumed-number ledger | `build/rastan-direct/consumed_build_numbers.txt` |
| Numbered ROM artifacts | `dist/rastan-direct/rastan_direct_video_test_build_<NNNN>*.bin` |
| **Sprite reindex + (code,bank) variant generator** | `tools/graphics_editor/gen_reindexed_pc090oj.py` |
| Independent sprite-reindex verifier | `tools/graphics_editor/verify_reindexed_pc090oj.py` |
| Palette-line LUT generator (scene,bank→CRAM line) | `tools/translation/gen_pc090oj_palsel_lut.py` |
| Plane-A (PC080SN) reindex generator | `tools/graphics_editor/gen_reindexed_region.py` |
| Coverage invariants (2 copies, keep in sync) | `tools/translation/postpatch_startup_rom.py`, `tools/translation/verify_canonical_rom.py` |
| Palette Composer server (to author the profile) | `tools/graphics_editor/server.py` |

The m68k toolchain is vendored at `tools/local/toolchain/m68k-elf/bin/` (the Makefile uses it).

---

## 1. What the palette JSON actually is

`Test.json` → `usage_palette_mappings` holds one entry per semantic object. Keys look like:

- `object:player.rastan` — Rastan body (both torso + legs)
- `object:weapon.sword` / `object:weapon.axe` / `object:weapon.hammer` / `object:weapon.fire_sword`
- `usage:<enemy>:bank0x<BB>` — enemies (e.g. `usage:lizardman:bank0x36`, `usage:flying_demon:bank0x35`)
- `usage:cave_block:bank0x3C` — destroyable cave block
- `usage:burst:bank0x30` — demon/boss impact burst effect

Each entry has:
- `"line"`: the Genesis CRAM palette line (0–3) the object renders on. **Line 2 is arcade Layer-B and is
  PROTECTED — do not author to it.**
- `"index_map"`: `{ arcade_source_pixel_index : genesis_palette_line_slot }`. This **points** each source
  pixel at a *slot in a shared line*; the rendered color is whatever color that slot already holds. Lines are
  shared across many objects (15 colors each), so an object can only use colors already present on its line.

**(code,bank) variants:** when the same raw PC090OJ tile code is used by two different objects under two
different effective palette **banks** with different maps (e.g. the 0xA73 anim block shared by
chimera/lizardman/four_armed, or 0x28E–0x2A8 shared by flying_demon and burst), the generator produces
**separate transformed cells** and an O(1) runtime selector. Never collapse these — the generator asserts on
them.

---

## 2. Author the palette (optional — only if you're changing it)

Tighe usually authors in the Composer. To run it:

```bash
cd /home/tighe/projects/rastan-genesis
python3 tools/graphics_editor/server.py       # then open the printed localhost URL in a browser
```

Authoring saves back to `analysis/graphics_optimizer/editor_policy/Test.json` (via the server's POST
handler). **A build never edits `Test.json`** — it consumes a frozen snapshot (next step). If you are only
building (not authoring), skip this section entirely.

---

## 3. Pick the next build number

```bash
cat build/rastan-direct/build_counter.txt      # e.g. 385  -> next build is 0386
```

**Build-number discipline (CLAUDE.md, non-negotiable):**
- Every build gets the **next sequential** number, passing or failing.
- **Never delete, withhold, or reuse** a numbered artifact. If a family comes out incomplete (a variant
  failed), preserve what you built and advance to the next number for the retry.
- The Makefile refuses to overwrite an existing numbered artifact and won't move the counter backwards.

For the rest of this doc, `NNNN` = your target number (e.g. `0386`).

---

## 4. Freeze the profile snapshot

The build must consume an immutable snapshot, not the live file:

```bash
NNNN=0386     # <-- set to your target number
mkdir -p build/rastan-direct/build${NNNN}
cp analysis/graphics_optimizer/editor_policy/Test.json build/rastan-direct/build${NNNN}/Test.snapshot.json
sha256sum analysis/graphics_optimizer/editor_policy/Test.json build/rastan-direct/build${NNNN}/Test.snapshot.json
```

Record the SHA (they must match). **Recommended:** diff the new snapshot against the previous build's
snapshot so you know exactly what changed:

```bash
python3 - <<'PY'
import json
new=json.load(open('build/rastan-direct/build0386/Test.snapshot.json'))
old=json.load(open('build/rastan-direct/build0384/Test.snapshot.json'))   # previous build's input
nu,ou=new['usage_palette_mappings'], old['usage_palette_mappings']
for k in sorted(set(nu)|set(ou)):
    a=nu.get(k); b=ou.get(k)
    if a!=b:
        print('CHANGED' if (a and b) else ('ADDED' if a else 'REMOVED'), k)
        if a: print('   new line',a.get('line'),{int(x):int(y) for x,y in (a.get('index_map') or {}).items()})
        if b: print('   old line',b.get('line'),{int(x):int(y) for x,y in (b.get('index_map') or {}).items()})
print('CRAM changed:', new.get('target_palette_lines')!=old.get('target_palette_lines'))
PY
```

---

## 5. Point the Makefile at the frozen snapshot

Edit `apps/rastan-direct/Makefile`, the `EDITOR_LAYERA_SNAPSHOT` line (near line 79):

```make
EDITOR_LAYERA_SNAPSHOT := $(ROOT)/build/rastan-direct/build0386/Test.snapshot.json
```

This one variable feeds **all** the palette generators (sprite reindex, palsel LUT, Plane-A reindex). You do
**not** run the generators by hand for a build — `make` runs them as dependency rules. (You *may* run them
manually to inspect/verify; see §7.)

---

## 6. Build the complete five-variant family

```bash
cd apps/rastan-direct
make clean          # STRONGLY recommended — avoids stale-object / boundary-mismatch gate failures
make release
```

`make release` (a.k.a. `dual-build`) produces **five ROMs for ONE build number** and advances the counter
once:

| Suffix | Meaning |
|---|---|
| *(none)* base | the numbered release ROM |
| `_d` | diagnostic CPU-load raster bar |
| `_s` | diagnostic numeric score metric |
| `_do` | display-off VBlank publication variant |
| `_c` | P1 six-button MODE rack-advance cheat (also uses the current build number) |

On success you'll see `complete build artifact set verified for NNNN (canonical, _d, _s, _do, _c)`.

### What the generators do during the build (for reference)
- `gen_reindexed_pc090oj.py` reads the snapshot + the complete sprite corpus
  (`analysis/actor_decompilation/r1p1_enemy_semantic_corpus.tsv`, the H24 player/weapon TSVs) and writes
  `build/regions/pc090oj_editor.bin` (base cells + appended (code,bank) variant cells) plus
  `apps/rastan-direct/out/pc090oj_sprite_variants.inc` (the O(1) runtime variant index consumed by
  `pc090oj_hooks.s`).
- `gen_pc090oj_palsel_lut.py` reads the snapshot and writes `out/pc090oj_palsel_lut.inc` — the
  (scene, effective_bank) → CRAM-line table. It is **profile-authoritative**: banks the profile authors
  (e.g. burst 0x30→line 0, cave 0x3C→line 0) override the legacy oracle.
- `gen_reindexed_region.py` reindexes the PC080SN Plane-A region from the same snapshot.

---

## 7. (Optional) Verify the sprite reindex independently

```bash
cd /home/tighe/projects/rastan-genesis
python3 tools/graphics_editor/verify_reindexed_pc090oj.py \
    --profile build/rastan-direct/build0386/Test.snapshot.json
```

Expect `VERIFY: PASS` with `mismatched 0, incomplete 0, unexpectedly-raw 0, stray 0`, all divergent codes
`all-distinct`, and `rastan base codes` matching with `0 mismatched`. **Always pass `--profile` explicitly** —
the script's built-in default points at whatever the last build used and drifts.

---

## 8. Expected gate results & how to fix the common failures

The release runs three gates and records them in the consumed ledger as `[canonical=… entry=… epoch=…]`:

- **`canonical=PASS`** and **`entry=PASS`** are the targets.
- **`epoch=FAIL` is EXPECTED and OK** — the Phase-1 seven-epoch gate has been failing on every recent build
  (0378+). The ROM is still numbered and preserved. Do not chase it.

### 8a. Coverage invariant failure (happens whenever the sprite region size changes)
If the postpatch stops with:
```
RuntimeError: Build 0029 invariant failure: expected total_genesis_bytes_covered=0xAAAAAA ... got 0xBBBBBB
```
the sprite region (or the generated `.inc` tables) changed size. This failure happens **before numbering, so
no build number is consumed.** Update **both** copies of the constant to the observed (`got`) value:

- `tools/translation/postpatch_startup_rom.py` — `CANONICAL_TOTAL_GENESIS_BYTES_COVERED = 0x…` (~line 113)
- `tools/translation/verify_canonical_rom.py` — same constant (~line 127)

Then re-run `make release`. (If the base passes but the invariant fires again for a *later* variant, see 8c.)

### 8b. Palsel LUT `--verify` mismatch for a bank you just authored
If you moved a bank to a **new** line (e.g. authored burst 0x30 or cave 0x3C to a different line), the
generator's verify is profile-authoritative and should pass. If it still fails, confirm the mismatch is only
for banks the profile authors — those are intentional overrides of the legacy route oracle.

### 8c. `_c` (cheat) variant coverage invariant `+0x1000`
If only the cheat variant fails with `got` exactly `0x1000` over the base, its MODE rack-advance code landed
on a new aligned page. In the `$(CHEAT_ROM):` rule in the Makefile (~line 524) add/adjust the postpatch flag:
```make
        --genesis-coverage-delta 4096
```
(Set it to 0 again if a future base build re-absorbs that page.)

### 8d. Stale-object / boundary INCBIN mismatch (`GATE_FAIL_2_1_INCBIN_SHA_MISMATCH`)
Almost always a stale object from not cleaning. Run `make clean && make release`. Do **not** hand-edit
generated files to make it pass.

---

## 9. Collect and record the artifacts

```bash
cd /home/tighe/projects/rastan-genesis
cat build/rastan-direct/build_counter.txt            # should now be your NNNN
tail -1 build/rastan-direct/consumed_build_numbers.txt
for v in "" _c _d _do _s; do
  f="dist/rastan-direct/rastan_direct_video_test_build_0386$v.bin"
  printf "%-14s %8d  %s\n" "0386$v" "$(stat -c%s "$f")" "$(sha256sum "$f" | cut -d' ' -f1)"
done
```

A build is **only complete when all five ROMs exist** and `verify-variant-set` passed.

---

## 10. Andy performs static/build verification only — gameplay is Tighe's

Do not claim "the palette looks right" or "gameplay is fixed." Report the SHA/size matrix, gate results, and
what changed; **Tighe performs all gameplay/visual verification.**

---

## 11. One-shot checklist (copy/paste, edit `NNNN` and the previous-build number)

```bash
cd /home/tighe/projects/rastan-genesis
NNNN=0386; PREV=0384                                  # PREV = previous build's snapshot dir
# 1) freeze
mkdir -p build/rastan-direct/build${NNNN}
cp analysis/graphics_optimizer/editor_policy/Test.json build/rastan-direct/build${NNNN}/Test.snapshot.json
sha256sum build/rastan-direct/build${NNNN}/Test.snapshot.json
# 2) point Makefile (edit EDITOR_LAYERA_SNAPSHOT to build${NNNN}/Test.snapshot.json)
sed -i "s#build/rastan-direct/build[0-9]\{4\}/Test.snapshot.json#build/rastan-direct/build${NNNN}/Test.snapshot.json#" apps/rastan-direct/Makefile
# 3) verify sprite reindex (optional)
python3 tools/graphics_editor/verify_reindexed_pc090oj.py --profile build/rastan-direct/build${NNNN}/Test.snapshot.json
# 4) build
cd apps/rastan-direct && make clean && make release
#    -> if "invariant failure ... got 0xXXXX": update CANONICAL_TOTAL_GENESIS_BYTES_COVERED in BOTH
#       tools/translation/postpatch_startup_rom.py and tools/translation/verify_canonical_rom.py, then rebuild
# 5) record SHAs (see §9)
```

---

## 12. Golden rules (do not violate)

- **No manual pixel recoloring, no runtime nibble transforms.** All color remapping is build-time Python
  driven by the frozen JSON.
- **Do not edit `Test.json` during a build.** Freeze it; build from the snapshot.
- **Do not hand-edit generated files** (`build/regions/*.bin`, `out/*.inc`, manifests, address maps) to make
  a gate pass. Fix the generator or the invariant constant instead.
- **Do not change Tighe's authored mappings** to work around a rendering issue without proof that the mapping
  itself is wrong.
- **Every build gets the next number; never delete/withhold/reuse one.** Incomplete family → preserve it,
  advance to the next number.
- `epoch=FAIL` is fine; `canonical=PASS` + `entry=PASS` are the targets.
