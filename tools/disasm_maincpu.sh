#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT_DIR/tools/setup_env.sh" >/dev/null

python3 "$ROOT_DIR/tools/build_rastan_regions.py" >/dev/null

OUT_FILE="$ROOT_DIR/build/maincpu.disasm.txt"

m68k-elf-objdump \
  -D \
  -b binary \
  -m m68k:68000 \
  --adjust-vma=0 \
  "$ROOT_DIR/build/regions/maincpu.bin" \
  >"$OUT_FILE"

printf 'wrote %s\n' "$OUT_FILE"
