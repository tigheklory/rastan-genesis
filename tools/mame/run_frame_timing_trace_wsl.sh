#!/usr/bin/env bash
# READ-ONLY Build-0400 EXACT frame-timing trace (memory taps + VDP beam).
# Measures gameplay-ticks/display-frame (crawl proof), per-tick producer-done beam position,
# publication span, and publication sub-phase split by VDP target. No ROM/WRAM modification.
#
# Enter normal gameplay, press M once to start the controlled interval, then capture LIGHT,
# MEDIUM, and the HEAVY slowdown area in ONE run.
# Quit MAME (Esc) when done -> summary written (also rewritten every 300 frames).
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
HOMEPATH="${ROOT}/build/mame/home"; TRACE_DIR="${HOMEPATH}/frame_timing"; mkdir -p "${TRACE_DIR}"
export FRAME_TIMING_SYMBOLS="${ROOT}/apps/rastan-direct/out/symbol.txt"
echo "=========================================================================="
echo " FRAME-TIMING TRACE  (ROM: $(basename "${CART}"))"
echo " Play LIGHT (few sprites), then MEDIUM, then the HEAVY slowdown room."
echo " Once normal gameplay is underway, press M ONCE to arm/reset the measured interval."
echo " The headline metric is GAMEPLAY TICKS / DISPLAY FRAME (<1.0 = the crawl)."
echo " Quit MAME (Esc) when done.  Summary: ${TRACE_DIR}/frame_timing_summary.txt"
echo "=========================================================================="
# -debug -debugger none: enables the MAME debugger (for exact worker/publication cycle breakpoints)
# with NO debugger GUI/console, so the game runs normally and the breakpoint actions auto-continue (g).
# This adds ZERO emulated 68000 instructions (host-side only).
exec "${MAME_BIN}" "${MACHINE}" -cart "${CART}" \
  -window -nomaximize -resolution "${MAME_RESOLUTION}" -nokeepaspect -nounevenstretch -prescale 1 -nofilter \
  -sound "${MAME_SOUND}" -midiprovider "${MAME_MIDIPROVIDER}" -skip_gameinfo \
  -debug -debugger none \
  -homepath "${HOMEPATH}" \
  -autoboot_script "${ROOT}/tools/mame/scripts/frame_timing_trace.lua" "$@"
