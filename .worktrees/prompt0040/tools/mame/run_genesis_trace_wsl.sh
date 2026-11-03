#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MACHINE="${MAME_GENESIS_MACHINE:-genesis}"
DEFAULT_CART="${ROOT}/apps/rastan/out/rom.bin"
CART="${GENESISTAN_CART:-${DEFAULT_CART}}"
MAME_SOUND="${MAME_SOUND:-auto}"
MAME_MIDIPROVIDER="${MAME_MIDIPROVIDER:-none}"

# Force a sharp 2x window every time.
# Genesis active image is typically treated here as 320x224, so 2x = 640x448.
BASE_WIDTH=320
BASE_HEIGHT=224
WINDOW_SCALE=2
MAME_RESOLUTION="$((BASE_WIDTH * WINDOW_SCALE))x$((BASE_HEIGHT * WINDOW_SCALE))"

if [[ "${MAME_SOUND}" == "auto" ]]; then
  if [[ -S /mnt/wslg/PulseServer ]]; then
    export SDL_AUDIODRIVER="${SDL_AUDIODRIVER:-pulse}"
    export PULSE_SERVER="${PULSE_SERVER:-unix:/mnt/wslg/PulseServer}"
    MAME_SOUND="sdl"
  elif [[ -e /dev/snd ]]; then
    MAME_SOUND="sdl"
  else
    MAME_SOUND="none"
  fi
fi

if [[ $# -gt 0 && "${1}" != -* ]]; then
  CART="$1"
  shift
fi

if command -v mame >/dev/null 2>&1; then
  MAME_BIN="$(command -v mame)"
elif command -v mame64 >/dev/null 2>&1; then
  MAME_BIN="$(command -v mame64)"
else
  echo "MAME executable not found. Install it first with:" >&2
  echo "  sudo apt-get update && sudo apt-get install -y mame mame-data mame-tools p7zip-full" >&2
  exit 1
fi

if [[ ! -f "${CART}" ]]; then
  echo "Genesis cart ROM not found: ${CART}" >&2
  echo "Pass a ROM path as the first argument, for example:" >&2
  echo "  tools/mame/run_genesis_trace_wsl.sh dist/Rastan_59_20260316_170643.bin" >&2
  exit 1
fi

HOMEPATH="${ROOT}/build/mame/home"
TRACE_DIR="${HOMEPATH}/genesistrace"

mkdir -p "${TRACE_DIR}"

export GENESISTAN_ROOT="${ROOT}"

exec "${MAME_BIN}" "${MACHINE}" \
  -cart "${CART}" \
  -window \
  -nomaximize \
  -resolution "${MAME_RESOLUTION}" \
  -nokeepaspect \
  -nounevenstretch \
  -prescale 1 \
  -nofilter \
  -sound "${MAME_SOUND}" \
  -midiprovider "${MAME_MIDIPROVIDER}" \
  -skip_gameinfo \
  -homepath "${HOMEPATH}" \
  -autoboot_script "${ROOT}/tools/mame/scripts/genesistrace.lua" \
  "$@"