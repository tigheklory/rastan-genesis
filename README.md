# Rastan Genesis

Private engineering project for an arcade-accurate `Rastan` port targeting the Sega Genesis.

## Project goals

- Preserve arcade gameplay feel as closely as possible.
- Keep sprite scale and stage logic aligned with the original.
- Allow Genesis-specific compromises in palette depth, audio implementation, and backend structure.
- Build from user-supplied arcade ROM files instead of redistributing original game data.

## Current project shape

- `roms/`: source arcade ROM files supplied locally by the user.
- `apps/`: runnable ROM projects.
- `apps/rastan/`: current known-good text baseline ROM.
- `attic/`: preserved experiments we are not trusting as the baseline.
- `runtime/`: shared Genesis-side runtime and shim code.
- `specs/`: machine-readable build rules, fixups, variants, and runtime config.
- `docs/`: project docs, validation notes, and reverse-engineering research.
- `tools/`: analysis, extraction, conversion, and translation scripts.
- `build/`: disposable generated intermediates and extracted artifacts.
- `dist/`: named ROM releases we intentionally keep.

## Workflow

1. Place source ROMs in `roms/`.
2. Run the ROM inventory tool to fingerprint the set and capture a manifest.
3. Add region definitions and extractors for code, graphics, maps, and sound assets.
4. Build Genesis-side runtime code that consumes the extracted data.
5. Produce a Genesis ROM image from local source material and newly written runtime code.

## First command

```bash
python3 tools/rom_inventory.py
```

This writes `build/rom_inventory.json` and prints a concise summary of the detected files.

## Local toolchain

This project keeps its Genesis toolchain inside the repo so it does not depend on a system-wide install.

Load it with:

```bash
source tools/setup_env.sh
```

That sets:

- `GDK` to the pinned `SGDK` checkout in `tools/sgdk`
- `JAVA_HOME` to the local JDK in `tools/local/java`
- `PATH` entries for the local `m68k-elf` toolchain and SGDK helper tools

## Smoke test

After loading the environment, you can verify the setup with:

```bash
tools/build_sgdk_smoke.sh
```

This builds the SGDK template project into `build/sgdk-smoke/out/rom.bin`.

## Porting Path

The current porting path is strict about preserving original arcade behavior:

- build-time patching of original arcade `68000` code
- build-time extraction/manifests for execution slices
- Genesis runtime kept as a host/shim, not a rewritten game engine

Current first target:

- the startup and basic hardware-test block at `0x3AE86..0x3B05C`
- current default variant: `world_rev1`
- near-term alternate target: `us_rev1`

Run the current scaffold with:

```bash
make patch-maincpu
```

Current known-good ROM baseline:

```bash
make -C apps/rastan release
```

## Reference videos

If you add gameplay or emulator recordings under `video/`, you can turn them
into a small frame set plus contact sheet with:

```bash
tools/extract_video_reference.sh video/your_clip.mp4 build/video_reference
```

This writes:

- `metadata.txt` with `ffprobe` output
- `frames/` with evenly sampled PNGs
- `contact_sheet.png` for quick visual review
