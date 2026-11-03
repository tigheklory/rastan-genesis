# PALETTE_TOOL_INSTRUCTIONS.md — Using the Rastan Palette Composer, step by step

This walks a human through the **Palette Composer** (a.k.a. the Palette Tool): starting it, what it does,
how to author a sprite's Genesis palette, saving your work, and handing the result to a build. It is written
for someone who has never opened the tool before.

- To turn what you author here into an actual ROM, see **[BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md)**
  (agent/pipeline detail) and **[HUMAN_BUILD_INSTRUCTIONS.md](HUMAN_BUILD_INSTRUCTIONS.md)** (fresh-machine
  setup + running a ROM). This file covers only the authoring tool.
- The tool **never changes the ROM by itself**. It only edits a JSON palette profile. A separate build step
  reads that profile.

---

## 1. What the tool is (read this first)

The Palette Composer is a small local web app. On the left it lists every sprite object it knows about
(Rastan, his weapons, the enemies, the cave block, the burst effect). You pick an object, and the tool shows:

- the **true arcade artwork** for that object (decoded straight from the original arcade ROM), and
- a **Genesis "target" preview** of how that object will look after your palette choices.

The Sega Genesis can only show **4 palette "lines," each with 16 colors** on screen at once, and several
objects have to **share** the same line. So authoring a sprite is really: *"for each color the arcade sprite
uses, pick which slot of a shared Genesis line it should draw from."* The sprite then displays whatever color
already lives in that slot. You are **routing** the sprite's colors onto shared lines — you are not inventing
brand-new colors per sprite.

Everything you do is saved into one file:

```
analysis/graphics_optimizer/editor_policy/Test.json
```

That file (the "Test" profile) is the single input a build consumes.

> **Important boundary:** the arcade artwork on the left is a **READ-ONLY reference** (the tool calls it "the
> oracle"). You can never damage the original ROM data from here. You are only editing the Genesis-side
> mapping.

---

## 2. Requirements

- **Python 3** (3.10+). No extra Python packages are required — the tool uses only the standard library and
  the browser does the drawing.
- A **web browser** (Chrome/Firefox/Edge).
- The project's **generated data files must already exist**, because the tool decodes real arcade graphics
  from them:
  - `build/regions/maincpu.bin`
  - `build/pc090oj_genesis.bin`
  - `build/regions/pc080sn.bin`
  If you have ever run a build (see HUMAN_BUILD_INSTRUCTIONS.md), these exist. If this is a brand-new checkout
  and the tool errors that a file is missing, run one build first (or at least the region-generation step),
  then come back.

---

## 3. Start the tool

Open a terminal in the project root and run:

```bash
cd /home/tighe/projects/rastan-genesis
python3 tools/graphics_editor/server.py
```

You'll see a line like:

```
Palette Composer v0.2 -> http://localhost:8770  (oracle READ-ONLY, Build 313)
```

Open **http://localhost:8770** in your browser.

- To use a different port (if 8770 is busy): `python3 tools/graphics_editor/server.py 8771`.
- The server only listens on your own machine (127.0.0.1) — it is not exposed to the network.
- **Leave the terminal running** while you work. To stop the tool later, press **Ctrl+C** in that terminal.

---

## 4. The screen, at a glance

- **Top bar:** the profile dropdown (should say **Test**), a box to name a new profile, and
  **Create editable profile / Save / Reload / Undo / Redo**. It also shows the arcade oracle is READ-ONLY.
- **"EDITING SCOPE: ROUND 1 / PHASE 1"** and a **local overrides** counter — the context you're editing.
- **Tabs:** **Sprites** (what you'll use), Layer A (backgrounds), Contexts, Palettes.
- **Left column:** the object list, each with a checkbox and a frame count (e.g. *Flying Demon · 2 frames*,
  *Sword frame 0 · 42 frames*, *Burst / Impact Effect · 3 frames*, *Cave Entrance Block*).
- **Middle:** the selected object's arcade source colors (small swatches labelled **i1, i2, i3, …**), the
  **SOURCE → GENESIS MAPPING** table, and two side-by-side previews: **TRUE ARCADE COMPOSITE** vs
  **GENESIS TARGET**. Below the previews is a **frame browser** (◄ Prev · *1/3* · Next ► · a dropdown) to
  step through the object's animation frames/forms.
- **Right column:** **GENESIS TARGET PALETTE** — the four lines (**LINE 0, LINE 1, LINE 2, LINE 3**), each a
  row of 16 clickable color slots. **PROPERTIES / EDITOR** (details about a picked color, closest matches).
  **VALIDATION** (mapping health).

---

## 5. Key concepts you must understand before mapping

1. **A mapping points a source color at a slot — it does not set the slot's color.** If you map the sprite's
   red (say `i2`) onto LINE 0 slot 11, and slot 11 currently holds a dark red, the sprite draws dark red. If
   that slot holds green, the sprite draws green. You are choosing *which existing slot* each sprite color
   reads from.
2. **Lines are shared.** LINE 0 might be used by Rastan, several enemies, the cave block and the burst all at
   once. It only has 16 colors total. So you can only give a sprite colors that **already exist on its line**.
   If the color you want isn't on that line, you either pick the closest available slot, edit that slot's
   color (which affects everything else using it), or put the object on a different line.
3. **LINE 2 is PROTECTED.** It belongs to the arcade Layer-B (time-of-day) path. The tool will not let you
   author onto it. Use LINE 0, 1, or 3.
4. **Each object has one "line" and an index map.** Every frame of the same object shares that one mapping —
   you author the object once, not per frame.
5. **Shared-graphics objects are handled for you.** Some sprites reuse the exact same arcade tiles under a
   different palette (for example the demon/boss burst reuses cells the flying demon also uses). The build
   automatically produces separate Genesis versions for each — you just author each object's mapping; you do
   not need to worry about the overlap.

---

## 6. Step-by-step: author one object's palette

Do this per object you want to change.

**Step 1 — Make sure the Test profile is selected.** In the top-bar dropdown, choose **Test**. (If you want a
fresh scratch profile instead, type a name and click **Create editable profile** — but a build reads
`Test.json`, so for a build you want Test.)

**Step 2 — Pick the object.** On the **Sprites** tab, click the object in the left list (e.g.
**Flying Demon**, or **Burst / Impact Effect**, or **Cave Entrance Block**). The middle panel now shows that
object's arcade source colors (`i1, i2, …`) and both previews.

**Step 3 — Look at the source colors.** The header reads e.g. *ARCADE SOURCE — … (BANK 0x35, 14 used
colors)*. Each swatch `iN` is one color the arcade sprite uses. Under each you'll see its current mapping
(e.g. `→L1:11` meaning "mapped to LINE 1, slot 11").

**Step 4 — Choose the target line.** Decide which Genesis line this object should live on (0, 1, or 3). You
can click **Recommend Line** to let the tool suggest one, or just start mapping onto the line you want on the
right.

**Step 5 — Map each source color to a slot.** For each `iN`:
- **Drag** the `iN` swatch onto a slot in the target line on the right, **or**
- **Click** the `iN` swatch, then **click** a target slot, **or**
- use the shortcuts:
  - **Auto-fill Object** — map every source color at once to the closest available slots (a fast first pass).
  - **Recommend Line** — pick a good line automatically.
  - In **PROPERTIES / EDITOR**, **Map to Closest Legal** — map the currently selected color to the nearest
    legal slot.
- The **SOURCE → GENESIS MAPPING** table updates, and each row shows the **Target color** actually stored in
  that slot. **This is the color the sprite will show** — check it matches what you intend.

**Step 6 — Watch the GENESIS TARGET preview.** It re-renders as you map. Compare it to the TRUE ARCADE
COMPOSITE on the left. Use the zoom buttons if needed.

**Step 7 — Step through frames.** Use **◄ Prev / Next ►** or the dropdown under the previews to check other
frames/forms of the same object (e.g. the three Burst forms, or weapon swing frames). Because all frames
share one mapping, they should all look right once the mapping is right.

**Step 8 — Check VALIDATION (bottom right).** You want **errors: 0**. It also shows **target lines used**
(e.g. 3/4) and how many usages are mapped. If a color can't be represented on the line you chose, that's your
cue to pick a different slot, edit a slot's color, or move the object to another line.

**Step 9 — Repeat** for any other objects you want to change.

---

## 7. Save your work

Nothing is written to disk until you click **Save** in the top bar. Click **Save**.

- **Save** writes your mappings into `analysis/graphics_optimizer/editor_policy/Test.json`.
- **Reload** discards unsaved changes and reloads the last saved state.
- **Undo / Redo** step through your edits in the current session.

You can confirm it saved from a terminal:

```bash
sha256sum analysis/graphics_optimizer/editor_policy/Test.json
```

Re-run that after saving; the hash changes when the file changes.

---

## 8. Turn your palette into a ROM

The tool's only output is the updated `Test.json`. To build a ROM from it, follow
**[BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md)**. In short:

1. **Freeze** the current profile into a per-build snapshot (so the build has an immutable input):
   ```bash
   NNNN=0386   # the next build number: (cat build/rastan-direct/build_counter.txt) + 1
   mkdir -p build/rastan-direct/build${NNNN}
   cp analysis/graphics_optimizer/editor_policy/Test.json build/rastan-direct/build${NNNN}/Test.snapshot.json
   ```
2. **Point the Makefile** at that snapshot — edit the `EDITOR_LAYERA_SNAPSHOT` line in
   `apps/rastan-direct/Makefile` to your `build${NNNN}/Test.snapshot.json`.
3. **Build** the five-ROM family:
   ```bash
   cd apps/rastan-direct && make clean && make release
   ```
4. If the build stops with a *coverage invariant failure* (this happens whenever the sprite region changed
   size), update the constant as described in BUILD_INSTRUCTIONS.md §8 and rebuild.

The resulting ROMs are in `dist/rastan-direct/rastan_direct_video_test_build_${NNNN}*.bin`. Load one in your
Genesis emulator (BlastEm) to see your palette in the actual game. **Only in-game viewing tells you if it's
right** — the tool's preview is a close approximation, not the final hardware.

---

## 9. Tips, gotchas, and rules

- **The preview shows the mapping, not new colors.** If a sprite looks "wrong" but the preview matches the
  game, your *mapping* is doing exactly what you told it — the issue is which slots/colors you chose, or that
  the line simply doesn't contain the color you wanted (e.g. no blue on a warm-toned shared line).
- **You can't give a line a color it doesn't have** without editing a slot — and editing a shared slot recolors
  every other object using that slot. Check what else lives on the line before changing a slot's color.
- **Different objects can share the same graphics but need different palettes** (e.g. the flying demon's wings
  vs. the boss reuse, or the burst). Author each object on its own; don't try to force one universal mapping.
- **One object = one line + one index map**, applied to all its frames.
- **Save is explicit.** Closing the browser without Save loses changes.
- **A build never edits `Test.json`;** it copies a frozen snapshot. So you can keep authoring in the tool
  without disturbing an in-progress build.
- **Don't hand-edit `Test.json` in a text editor** unless you know the schema — use the tool so validation and
  the protected-line rules are enforced.
- When you're done for the day, stop the server with **Ctrl+C** in its terminal.

---

## 10. Quick reference

| Action | How |
|---|---|
| Start tool | `python3 tools/graphics_editor/server.py` → open `http://localhost:8770` |
| Different port | `python3 tools/graphics_editor/server.py 8771` |
| Stop tool | Ctrl+C in the server terminal |
| Pick object | Sprites tab → click it in the left list |
| Map a color | Drag `iN` onto a right-side line slot, or click `iN` then click a slot |
| Fast first pass | **Auto-fill Object**, then fine-tune |
| Suggest a line | **Recommend Line** |
| Step frames | ◄ Prev / Next ► / dropdown under the previews |
| Health check | VALIDATION panel → **errors: 0** |
| Save | **Save** (writes `Test.json`) |
| Build from it | See BUILD_INSTRUCTIONS.md (freeze → point Makefile → `make clean && make release`) |
| Protected line | **LINE 2** — cannot author onto it |
| Output file | `analysis/graphics_optimizer/editor_policy/Test.json` |
