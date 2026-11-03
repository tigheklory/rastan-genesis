#!/usr/bin/env bash
# GENESIS NTSC human-played Round 1 Phase 1 semantic trace.
# Tighe plays normally; the harness records camera/scroll -> entering rows/columns -> map segments
# -> residency packages -> Plane A publication, plus a keypress marker for visible Layer-A corruption.
#
#   tools/mame/run_rastan_phase1_trace_wsl.sh            # traces Build 0348 (default)
#   tools/mame/run_rastan_phase1_trace_wsl.sh <rom.bin>  # trace a specific ROM
#
# Output: states/traces/rastan_phase1_human_trace_<timestamp>/  (unique; never overwritten)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MACHINE="${MAME_GENESIS_MACHINE:-genesis}"
DEFAULT_ROM="${ROOT}/dist/rastan-direct/rastan_direct_video_test_build_0348.bin"
ROM="${1:-$DEFAULT_ROM}"
SYMFILE="${ROOT}/tools/mame/rastan_phase1_trace_symbols.txt"
HARNESS="${ROOT}/tools/mame/scripts/rastan_phase1_semantic_trace.lua"
MARKER_KEY="${MARKER_KEY:-KEYCODE_M}"

for f in "$ROM" "$SYMFILE" "$HARNESS"; do
  [[ -s "$f" ]] || { echo "ERROR: required input missing: $f" >&2; exit 1; }
done

if command -v mame >/dev/null 2>&1; then MAME_BIN="$(command -v mame)"
elif command -v mame64 >/dev/null 2>&1; then MAME_BIN="$(command -v mame64)"
else echo "MAME not found (apt-get install mame)." >&2; exit 1; fi

STAMP="$(date +%Y%m%d_%H%M%S)"
TRACE_DIR="${ROOT}/states/traces/rastan_phase1_human_trace_${STAMP}"
mkdir -p "$TRACE_DIR"

ROM_SHA="$(sha256sum "$ROM" | cut -d' ' -f1)"
SYMFILE_SHA="$(sha256sum "$SYMFILE" | cut -d' ' -f1)"
HARNESS_SHA="$(sha256sum "$HARNESS" | cut -d' ' -f1)"

# Audio/video for real-time human play (WSLg).
MAME_SOUND="${MAME_SOUND:-auto}"
if [[ "${MAME_SOUND}" == "auto" ]]; then
  if [[ -S /mnt/wslg/PulseServer ]]; then
    export SDL_AUDIODRIVER="${SDL_AUDIODRIVER:-pulse}"
    export PULSE_SERVER="${PULSE_SERVER:-unix:/mnt/wslg/PulseServer}"
    MAME_SOUND="sdl"
  elif [[ -e /dev/snd ]]; then MAME_SOUND="sdl"; else MAME_SOUND="none"; fi
fi
BASE_WIDTH=320; BASE_HEIGHT=224; SCALE="${WINDOW_SCALE:-2}"
RES="$((BASE_WIDTH*SCALE))x$((BASE_HEIGHT*SCALE))"

echo "ROM:      $ROM"
echo "ROM SHA:  $ROM_SHA"
echo "Symbols:  $SYMFILE"
echo "Trace to: $TRACE_DIR"
echo "Marker:   press '${MARKER_KEY#KEYCODE_}' when Layer A visibly breaks"
echo

HOMEPATH="${ROOT}/build/mame/home"; mkdir -p "$HOMEPATH"

TRACE_DIR="$TRACE_DIR" SYMFILE="$SYMFILE" ROM_NAME="$(basename "$ROM")" \
ROM_SHA="$ROM_SHA" SYMFILE_SHA="$SYMFILE_SHA" HARNESS_SHA="$HARNESS_SHA" MARKER_KEY="$MARKER_KEY" \
"$MAME_BIN" "$MACHINE" \
  -cart "$ROM" \
  -window -nomaximize -resolution "$RES" -nokeepaspect -nounevenstretch -prescale 1 -nofilter \
  -sound "$MAME_SOUND" -midiprovider none -skip_gameinfo \
  -homepath "$HOMEPATH" \
  -autoboot_script "$HARNESS"

# After MAME exits: hash the raw evidence and lock it read-only (immutable).
echo
echo "=== raw trace evidence (do not modify) ==="
( cd "$TRACE_DIR" && sha256sum trace_metadata.txt phase1_frames.tsv phase1_events.tsv 2>/dev/null | tee SHA256SUMS.txt )
chmod -R a-w "$TRACE_DIR" 2>/dev/null || true
echo "Locked read-only: $TRACE_DIR"
