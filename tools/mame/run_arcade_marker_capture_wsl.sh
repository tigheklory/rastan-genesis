#!/usr/bin/env bash
# ORIGINAL ARCADE Rastan reusable marker capture (read-only).
# ONE harness, multiple user markers in a single manual play session. Reuses the established repo MAME
# layout, ROM path, homepath, cheat plugin, and the proven arcade coin/start workflow (coin key 5, start
# key 1). Drives tools/mame/scripts/arcade_marker_capture.lua.
#
# Usage:
#   tools/mame/run_arcade_marker_capture_wsl.sh [--output-dir DIR] [-- <extra MAME args>]
#
# Env (optional):
#   CAPTURE_ROLL_FRAMES       rolling pre-marker history window (default 180).
#   CAPTURE_COLLISION_ADDR    hex collision/state word to sample at each marker (e.g. 0x0010D2EA).
#   CAPTURE_AUTO_MARK_FRAMES  comma frames to auto-mark (SMOKE TEST ONLY; no human input).
#   CAPTURE_MAX_FRAMES        stop after N frames (0 = until you quit).
#   MARKER_SECONDS_TO_RUN     pass -seconds_to_run to MAME (smoke tests).
#   MARKER_QT_PLATFORM        exported as QT_QPA_PLATFORM (e.g. offscreen for headless smoke).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LUA="${ROOT}/tools/mame/scripts/arcade_marker_capture.lua"
ROM_PATH="${ROOT}/roms"

OUT_DIR=""
EXTRA=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-dir) shift; OUT_DIR="${1:?--output-dir needs a value}"; shift;;
    --) shift; EXTRA=("$@"); break;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
    *) echo "ERROR: unknown argument: $1" >&2; exit 1;;
  esac
done

if command -v mame >/dev/null 2>&1; then MAME_BIN="$(command -v mame)"
elif command -v mame64 >/dev/null 2>&1; then MAME_BIN="$(command -v mame64)"
else
  echo "STOP: MAME not found. Install: sudo apt-get install -y mame mame-data mame-tools p7zip-full" >&2
  exit 1
fi
[[ -f "${ROM_PATH}/rastan.zip" ]] || { echo "STOP: arcade ROM not found at ${ROM_PATH}/rastan.zip" >&2; exit 1; }
[[ -f "${LUA}" ]] || { echo "STOP: capture script missing at ${LUA}" >&2; exit 1; }

if [[ -z "${OUT_DIR}" ]]; then
  OUT_DIR="${ROOT}/states/traces/arcade_marker_capture_$(date +%Y%m%d_%H%M%S)"
fi
mkdir -p "${OUT_DIR}"

HOMEPATH="${ROOT}/build/mame/home"
PLUGINPATHS="${ROOT}/tools/mame/plugins;/usr/share/games/mame/plugins;/usr/local/share/games/mame/plugins"
CHEATPATHS="${ROOT}/tools/mame/cheat;${HOMEPATH}/cheat;cheat"
mkdir -p "${HOMEPATH}"

echo "ORIGINAL ARCADE marker capture"
echo "  Insert coin: key 5   |   Start: key 1   |   Mark (default): key M"
echo "  Mark: duck/weapon warrior pose, and ONE FULL CYCLE of each hazard (spikes/gate/trap/water/flame)."
echo "  Output: ${OUT_DIR}"

MAME_ARGS=( rastan -window -skip_gameinfo -plugins -plugin cheat -cheat
  -rompath "${ROM_PATH}" -homepath "${HOMEPATH}"
  -pluginspath "${PLUGINPATHS}" -cheatpath "${CHEATPATHS}"
  -autoboot_script "${LUA}" )
[[ -n "${MARKER_SECONDS_TO_RUN:-}" ]] && MAME_ARGS+=( -seconds_to_run "${MARKER_SECONDS_TO_RUN}" )
[[ ${#EXTRA[@]} -gt 0 ]] && MAME_ARGS+=( "${EXTRA[@]}" )

(
  cd "${OUT_DIR}"
  export TRACE_DIR="${OUT_DIR}"
  [[ -n "${MARKER_QT_PLATFORM:-}" ]] && export QT_QPA_PLATFORM="${MARKER_QT_PLATFORM}"
  "${MAME_BIN}" "${MAME_ARGS[@]}"
) >"${OUT_DIR}/mame_stdout.log" 2>"${OUT_DIR}/mame_stderr.log" || true

echo "Capture finished. Files in ${OUT_DIR}:"
ls -1 "${OUT_DIR}" | sed 's/^/  /'
