#!/usr/bin/env bash
# READ-ONLY user-driven Plane-A combined-X/Y trace (Build 0398).
# Tighe plays normally; press M once when a misplaced Plane-A tile is SEEN.
# No ROM/WRAM modification; external MAME Lua only. Mirrors run_genesis_trace_wsl.sh.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MACHINE="${MAME_GENESIS_MACHINE:-genesis}"
# Default cart: the current user-tested baseline Build 0398 (pass a different ROM as arg 1 to override).
DEFAULT_CART="${ROOT}/dist/rastan-direct/rastan_direct_video_test_build_0398.bin"
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
  elif [[ -e /dev/snd ]]; then MAME_SOUND="sdl"; else MAME_SOUND="none"; fi
fi

if [[ $# -gt 0 && "${1}" != -* ]]; then CART="$1"; shift; fi

if command -v mame >/dev/null 2>&1; then MAME_BIN="$(command -v mame)"
elif command -v mame64 >/dev/null 2>&1; then MAME_BIN="$(command -v mame64)"
else
  echo "MAME executable not found. Install: sudo apt-get install -y mame mame-data mame-tools p7zip-full" >&2
  exit 1
fi

if [[ ! -f "${CART}" ]]; then
  echo "Genesis cart ROM not found: ${CART}" >&2
  echo "Pass a ROM path as the first argument (default is Build 0398)." >&2
  exit 1
fi

HOMEPATH="${ROOT}/build/mame/home"
TRACE_DIR="${HOMEPATH}/plane_a_xy"
mkdir -p "${TRACE_DIR}"
export GENESISTAN_ROOT="${ROOT}"

echo "=========================================================================="
echo " PLANE-A COMBINED-X/Y TRACE  (ROM: $(basename "${CART}"))"
echo " Play normally.  Fastest repro: Segment 2/3 CLIMBABLE ROPE -> jump off so"
echo " the camera moves vertically AND a little horizontally."
echo " When you SEE a misplaced Plane-A tile, press  M  ONCE, then press  F12  for a"
echo " MAME screenshot of the stray cell.  (The Plane-A name-table content is already"
echo " captured in the trace .txt as staged-vs-VRAM words; no tilemap viewer needed.)"
echo " Trace output: ${TRACE_DIR}/plane_a_xy_marker_<frame>.txt (+_summary.txt)"
echo "=========================================================================="

exec "${MAME_BIN}" "${MACHINE}" \
  -cart "${CART}" \
  -window -nomaximize -resolution "${MAME_RESOLUTION}" \
  -nokeepaspect -nounevenstretch -prescale 1 -nofilter \
  -sound "${MAME_SOUND}" -midiprovider "${MAME_MIDIPROVIDER}" \
  -skip_gameinfo \
  -homepath "${HOMEPATH}" \
  -snapshot_directory "${TRACE_DIR}" \
  -autoboot_script "${ROOT}/tools/mame/scripts/plane_a_xy_trace.lua" \
  "$@"
