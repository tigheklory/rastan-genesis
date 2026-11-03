#!/usr/bin/env bash
# GENESIS NTSC crash-evidence capture. Runs the display-off "_do" ROM (or any
# ROM passed as the first argument) under the USA/NTSC `genesis` machine with
# tools/mame/scripts/genesis_crash_capture.lua armed. Play to the crashing
# scene; the crash handler's WRAM record + stack call-trail are dumped to
# build/mame/home/genesis_crash_capture/genesis_crash_capture.log the instant
# the crash fires.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MACHINE="${MAME_GENESIS_MACHINE:-genesis}"

# Default cart: newest built display-off (_do) ROM.
DEFAULT_CART="$(ls -t "${ROOT}"/dist/rastan-direct/rastan_direct_video_test_build_*_do.bin 2>/dev/null | head -1 || true)"
CART="${GENESISTAN_CART:-${DEFAULT_CART}}"
MAME_SOUND="${MAME_SOUND:-auto}"
MAME_MIDIPROVIDER="${MAME_MIDIPROVIDER:-none}"

BASE_WIDTH=320; BASE_HEIGHT=224; WINDOW_SCALE=2
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
  CART="$1"; shift
fi

if command -v mame >/dev/null 2>&1; then MAME_BIN="$(command -v mame)"
elif command -v mame64 >/dev/null 2>&1; then MAME_BIN="$(command -v mame64)"
else
  echo "MAME executable not found." >&2; exit 1
fi

if [[ -z "${CART}" || ! -f "${CART}" ]]; then
  echo "Genesis _do ROM not found. Build one (make all) or pass a path:" >&2
  echo "  tools/mame/run_genesis_crash_capture_wsl.sh dist/rastan-direct/rastan_direct_video_test_build_0346_do.bin" >&2
  exit 1
fi

HOMEPATH="${ROOT}/build/mame/home"
mkdir -p "${HOMEPATH}/genesis_crash_capture"
export GENESISTAN_ROOT="${ROOT}"

echo "Cart: ${CART}"
echo "Log:  ${HOMEPATH}/genesis_crash_capture/genesis_crash_capture.log"

exec "${MAME_BIN}" "${MACHINE}" \
  -cart "${CART}" \
  -window -nomaximize -resolution "${MAME_RESOLUTION}" \
  -nokeepaspect -nounevenstretch -prescale 1 -nofilter \
  -sound "${MAME_SOUND}" -midiprovider "${MAME_MIDIPROVIDER}" \
  -skip_gameinfo -homepath "${HOMEPATH}" \
  -autoboot_script "${ROOT}/tools/mame/scripts/genesis_crash_capture.lua" \
  "$@"
