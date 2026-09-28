# HUMAN_BUILD_INSTRUCTIONS.md — Build and test Rastan Genesis from a fresh project copy

This is the shortest human-oriented path from a fresh project copy to a playable Genesis ROM using the
palette profile already selected by the repository.

The project does **not** include or redistribute Taito's arcade ROM images. You must supply your own
legally obtained MAME Rastan set. The current build target is the World Rev 1 program set.

The current pipeline still assigns a sequential project build number and creates five same-number ROM
variants. A simpler unnumbered public/test build may be added later; it does not exist yet.

## 1. Platform and required programs

The commands below assume Linux or WSL with Bash. From the repository root, you need:

- Bash, GNU Make, Python 3, `unzip`, and `timeout`;
- MAME with the `rastan` and `genesis` machines;
- a Motorola 68000 ELF binutils toolchain providing:
  `m68k-elf-as`, `m68k-elf-ld`, `m68k-elf-objcopy`, `m68k-elf-nm`, and `m68k-elf-objdump`.

The project development bundle normally carries the cross-toolchain under
`tools/local/toolchain/m68k-elf/`. That directory is local/ignored project material, so confirm that it
was included in the copy you received. If it is absent, install an equivalent `m68k-elf` binutils
toolchain and put those five command names on `PATH` before building.

On Debian/Ubuntu, the ordinary host-side prerequisites can be installed with:

```bash
sudo apt update
sudo apt install -y make python3 unzip mame coreutils
```

This package command does not install the project's `m68k-elf` cross-toolchain.

## 2. Enter the project and load its environment

Replace the first path with the location of your project copy:

```bash
cd /path/to/rastan-genesis
export PATH="/usr/games:$PATH"
source tools/setup_env.sh
```

Run this preflight before continuing:

```bash
for tool in python3 make unzip timeout mame \
  m68k-elf-as m68k-elf-ld m68k-elf-objcopy m68k-elf-nm m68k-elf-objdump
do
  command -v "$tool" || { echo "MISSING REQUIRED TOOL: $tool"; exit 1; }
done
```

If a `m68k-elf-*` command is missing, do not start the build; install or restore the cross-toolchain
first.

## 3. Put the arcade MAME ROMs in the correct place

The region builder reads **loose ROM images directly from `roms/`**. It does not extract files from the
ZIP itself. Retaining the ZIP in the same directory is useful because MAME uses it for `-verifyroms`.

Copy your legally obtained `rastan.zip` into the project and extract it without subdirectories:

```bash
mkdir -p roms
cp /path/to/your/rastan.zip roms/rastan.zip
unzip -j -o roms/rastan.zip -d roms
```

For the default `world_rev1` target, these 16 loose files must now exist directly under `roms/`:

```text
b04-38.19
b04-37.7
b04-40.20
b04-39.8
b04-42.21
b04-43-1.9
b04-01.40
b04-02.67
b04-03.39
b04-04.66
b04-05.15
b04-06.28
b04-07.14
b04-08.27
b04-19.49
b04-20.76
```

Do not commit anything under `roms/`; the directory is intentionally ignored by Git.

## 4. Verify the exact source ROM images

First ask MAME to validate the set:

```bash
mame -rompath "$PWD/roms" -verifyroms rastan
```

Then compare every file needed by the default build against the repository's machine-readable SHA-1
manifest:

```bash
python3 - <<'PY'
import hashlib
import json
from pathlib import Path

root = Path.cwd()
manifest = json.loads((root / "specs/extraction_manifest.json").read_text())
required = []
for region in ("pc080sn", "pc090oj", "audiocpu", "adpcm"):
    required.extend(manifest["shared_regions"][region])
required.extend(manifest["maincpu_variants"]["world_rev1"])

failed = False
for entry in required:
    path = root / "roms" / entry["name"]
    if not path.is_file():
        print(f"MISSING  {entry['name']}")
        failed = True
        continue
    actual = hashlib.sha1(path.read_bytes()).hexdigest()
    if actual != entry["sha1"]:
        print(f"BAD SHA1 {entry['name']}  expected={entry['sha1']}  actual={actual}")
        failed = True
    else:
        print(f"OK       {entry['name']}")

raise SystemExit(1 if failed else 0)
PY
```

Do not build past a missing file or SHA-1 mismatch. A differently named or revised Rastan set may be a
real MAME set, but it is not the source set selected by the current default translation.

## 5. Confirm which palette snapshot will be used

The build must use the frozen profile named by `EDITOR_LAYERA_SNAPSHOT` in
`apps/rastan-direct/Makefile`:

```bash
grep '^EDITOR_LAYERA_SNAPSHOT' apps/rastan-direct/Makefile
```

For a normal test of the repository as received, leave that line unchanged. Do not point the build at
the live Composer file.

If you intentionally edited the live palette profile
`analysis/graphics_optimizer/editor_policy/Test.json`, stop here and follow
[BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) to review the canonical palette decisions, freeze a new
snapshot, and select it explicitly.

## 6. Build the test ROM family

The following command currently consumes the next sequential build number. It produces the canonical
ROM plus `_d`, `_s`, `_do`, and `_c` variants:

```bash
source tools/setup_env.sh
make -C apps/rastan-direct clean
make -C apps/rastan-direct release
```

The build reconstructs the arcade regions from `roms/`, runs the palette and graphics generators,
assembles and postpatches the Genesis ROM, runs the canonical/gameplay/epoch gates, records the build
number, and verifies the five-artifact family. It may take several minutes because MAME gates run as
part of the release.

The Phase-1 epoch gate is presently known to report `epoch=FAIL` on recent builds. The Makefile records
that result but still preserves and numbers the ROM. Read the complete terminal output; do not assume
that every failure is the known epoch result.

## 7. Find and verify the produced files

After `make release` returns, read the number actually assigned by the Makefile:

```bash
BUILD_NUMBER=$(cat build/rastan-direct/build_counter.txt)
BUILD_TAG=$(printf '%04d' "$BUILD_NUMBER")
echo "Produced build $BUILD_TAG"

for suffix in "" _d _s _do _c; do
  rom="dist/rastan-direct/rastan_direct_video_test_build_${BUILD_TAG}${suffix}.bin"
  test -s "$rom" || { echo "MISSING: $rom"; exit 1; }
  sha256sum "$rom"
done

tail -1 build/rastan-direct/consumed_build_numbers.txt
```

The ordinary test ROM is the file with no suffix:

```text
dist/rastan-direct/rastan_direct_video_test_build_NNNN.bin
```

The `_c` variant adds the six-button MODE rack-advance cheat and is useful for quickly reaching later
sections. The `_d`, `_s`, and `_do` files are diagnostic variants, not the normal gameplay ROM.

## 8. Launch the Genesis ROM in MAME

Run the canonical ROM produced above:

```bash
BUILD_NUMBER=$(cat build/rastan-direct/build_counter.txt)
BUILD_TAG=$(printf '%04d' "$BUILD_NUMBER")
mame genesis \
  -cart "$PWD/dist/rastan-direct/rastan_direct_video_test_build_${BUILD_TAG}.bin" \
  -window -skip_gameinfo
```

To test the MODE-cheat variant instead:

```bash
BUILD_NUMBER=$(cat build/rastan-direct/build_counter.txt)
BUILD_TAG=$(printf '%04d' "$BUILD_NUMBER")
mame genesis \
  -cart "$PWD/dist/rastan-direct/rastan_direct_video_test_build_${BUILD_TAG}_c.bin" \
  -window -skip_gameinfo
```

You may load the same `.bin` file in BlastEm, MiSTer, or compatible Genesis hardware tooling if you
prefer. Gameplay and palette appearance still require human validation; passing build gates does not
prove visual accuracy.

## 9. Common first-run failures

- `FileNotFoundError: .../roms/b04-...`: the ZIP was not extracted, was extracted into a nested
  directory, or is not the expected merged Rastan set. Repeat sections 3–4.
- `m68k-elf-as: command not found`: the local cross-toolchain was not included and no compatible system
  toolchain is on `PATH`.
- `mame: command not found`: install MAME and ensure `/usr/games` is on `PATH`.
- A coverage invariant, canonical gate, or incomplete variant-family failure is an engineering/build
  pipeline issue. Preserve any already-numbered artifacts and consult
  [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md); never overwrite or reuse a consumed build number.

## 10. Minimal copy/paste summary

After installing prerequisites and obtaining `rastan.zip` legally:

```bash
cd /path/to/rastan-genesis
export PATH="/usr/games:$PATH"
source tools/setup_env.sh

mkdir -p roms
cp /path/to/your/rastan.zip roms/rastan.zip
unzip -j -o roms/rastan.zip -d roms

mame -rompath "$PWD/roms" -verifyroms rastan
python3 tools/build_rastan_regions.py --variant world_rev1

make -C apps/rastan-direct clean
make -C apps/rastan-direct release

BUILD_NUMBER=$(cat build/rastan-direct/build_counter.txt)
BUILD_TAG=$(printf '%04d' "$BUILD_NUMBER")
mame genesis \
  -cart "$PWD/dist/rastan-direct/rastan_direct_video_test_build_${BUILD_TAG}.bin" \
  -window -skip_gameinfo
```

For the strongest source validation, run the manifest-driven SHA-1 check in section 4 before the build;
the compact summary's region-builder command primarily gives a quick missing-file check and generates
the region inputs.
