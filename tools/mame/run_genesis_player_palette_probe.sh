#!/usr/bin/env bash
# PROMT-ID-0112: run the Genesis player-palette probe against a ROM, resolving the staging symbols
# dynamically from the CURRENT apps/rastan-direct/out/symbol.txt (never a hard-coded WRAM address).
#
# Usage: run_genesis_player_palette_probe.sh <rom> <out_dir> [cap_frame]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ROM="${1:?rom path required}"
OUT="${2:?out dir required}"
CAP_FRAME="${3:-840}"
SYM="${ROOT}/apps/rastan-direct/out/symbol.txt"
MACHINE="${MAME_GENESIS_MACHINE:-genesis}"
MAME_BIN="$(command -v mame || command -v mame64 || echo /usr/games/mame)"

sym() { grep -iE " ${1}\$" "${SYM}" | awk '{print "0x"$1}' | head -1; }
STAGED="$(sym staged_palette_words)"
SAT="$(sym staged_sprite_sat)"
SCENE="$(sym genesistan_current_scene_id)"
[ -n "${STAGED}" ] && [ -n "${SAT}" ] && [ -n "${SCENE}" ] || { echo "symbol resolution failed" >&2; exit 2; }
mkdir -p "${OUT}"
echo "probe: rom=${ROM##*/} staged=${STAGED} sat=${SAT} scene=${SCENE} cap=${CAP_FRAME}"
SECS=$(( CAP_FRAME / 60 + 4 ))
TRACE_DIR="${OUT}" STAGED_PALETTE_ADDR="${STAGED}" SAT_ADDR="${SAT}" SCENE_ID_ADDR="${SCENE}" CAP_FRAME="${CAP_FRAME}" \
  timeout 240 "${MAME_BIN}" "${MACHINE}" -cart "${ROM}" -video none -sound none \
  -seconds_to_run "${SECS}" -skip_gameinfo -nothrottle -homepath "${ROOT}/build/mame/home" \
  -autoboot_script "${ROOT}/tools/mame/scripts/genesis_player_palette_probe.lua" 2>&1 | grep -iE "captured|error|not found" || true
