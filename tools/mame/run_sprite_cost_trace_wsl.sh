#!/usr/bin/env bash
# READ-ONLY Build-0400 sprite-count vs per-frame-CPU-cost trace.
# Play normally, then into a sprite-heavy room; quit MAME (Esc) -> summary written.
# No ROM/WRAM modification; external MAME Lua only. Mirrors run_plane_a_xy_trace_wsl.sh.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MACHINE="${MAME_GENESIS_MACHINE:-genesis}"
DEFAULT_CART="${ROOT}/dist/rastan-direct/rastan_direct_video_test_build_0400.bin"
CART="${GENESISTAN_CART:-${DEFAULT_CART}}"
MAME_SOUND="${MAME_SOUND:-auto}"; MAME_MIDIPROVIDER="${MAME_MIDIPROVIDER:-none}"
BASE_WIDTH=320; BASE_HEIGHT=224; WINDOW_SCALE=2
MAME_RESOLUTION="$((BASE_WIDTH*WINDOW_SCALE))x$((BASE_HEIGHT*WINDOW_SCALE))"
if [[ "${MAME_SOUND}" == "auto" ]]; then
  if [[ -S /mnt/wslg/PulseServer ]]; then
    export SDL_AUDIODRIVER="${SDL_AUDIODRIVER:-pulse}"; export PULSE_SERVER="${PULSE_SERVER:-unix:/mnt/wslg/PulseServer}"; MAME_SOUND="sdl"
  elif [[ -e /dev/snd ]]; then MAME_SOUND="sdl"; else MAME_SOUND="none"; fi
fi
if [[ $# -gt 0 && "${1}" != -* ]]; then CART="$1"; shift; fi
if command -v mame >/dev/null 2>&1; then MAME_BIN="$(command -v mame)"
elif command -v mame64 >/dev/null 2>&1; then MAME_BIN="$(command -v mame64)"
else echo "MAME not found. sudo apt-get install -y mame mame-tools" >&2; exit 1; fi
if [[ ! -f "${CART}" ]]; then echo "cart not found: ${CART}" >&2; exit 1; fi
HOMEPATH="${ROOT}/build/mame/home"; TRACE_DIR="${HOMEPATH}/sprite_cost"; mkdir -p "${TRACE_DIR}"
echo "=========================================================================="
echo " SPRITE-COST TRACE  (ROM: $(basename "${CART}"))"
echo " Play normally, then move into a SPRITE-HEAVY room (many lizard men /"
echo " projectiles / effects) so the sprite count climbs. Quit MAME (Esc) when"
echo " done. Summary: ${TRACE_DIR}/sprite_cost_summary.txt"
echo "=========================================================================="
exec "${MAME_BIN}" "${MACHINE}" -cart "${CART}" \
  -window -nomaximize -resolution "${MAME_RESOLUTION}" -nokeepaspect -nounevenstretch -prescale 1 -nofilter \
  -sound "${MAME_SOUND}" -midiprovider "${MAME_MIDIPROVIDER}" -skip_gameinfo \
  -homepath "${HOMEPATH}" \
  -autoboot_script "${ROOT}/tools/mame/scripts/sprite_cost_trace.lua" "$@"
