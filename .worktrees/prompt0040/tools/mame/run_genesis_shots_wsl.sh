#!/usr/bin/env bash
# Interactive GENESIS NTSC session for visual A/B screenshot capture of the current build ROM.
# Reuses run_genesis_trace_wsl.sh (USA/NTSC `genesis` machine, sharp 2x window) but DISABLES the
# heavy per-frame genesistrace autoboot so manual play to the cave stays responsive, and adds a
# fixed snapshot directory so F12 shots land where the comparison workflow can read them.
#
#   Default ROM: newest dist/rastan-direct/rastan_direct_video_test_build_*.bin (pass a path to override).
#   Move: arrow keys.  Buttons default to MAME's Genesis map (Tab -> Input to confirm jump/attack).
#   Screenshot: F12   ->   states/screenshots/r1p1_cave_compare/genesis/cave_NNNN.png
#
# Platform label: GENESIS NTSC MAME (candidate validation only).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SHOTS_DIR="${SHOTS_DIR:-${ROOT}/states/screenshots/r1p1_cave_compare/genesis}"
mkdir -p "${SHOTS_DIR}"

if [[ $# -gt 0 && "${1}" != -* ]]; then
  ROM="$1"; shift
else
  ROM="$(ls -1 "${ROOT}"/dist/rastan-direct/rastan_direct_video_test_build_*.bin 2>/dev/null | sort -V | tail -1)"
fi
if [[ -z "${ROM:-}" || ! -f "${ROM}" ]]; then
  echo "No Genesis build ROM found under dist/rastan-direct/; pass one explicitly." >&2
  exit 1
fi

echo "GENESIS NTSC session. ROM: ${ROM}"
echo "F12 snapshots -> ${SHOTS_DIR}   (Move=arrows; Tab->Input to confirm jump/attack)."
# The trailing -autoboot_script overrides run_genesis_trace_wsl.sh's genesistrace default (last wins),
# giving a clean interactive session. /dev/null is an empty (no-op) Lua script.
exec "${ROOT}/tools/mame/run_genesis_trace_wsl.sh" "${ROM}" \
  -snapshot_directory "${SHOTS_DIR}" \
  -snapname "cave_%i" \
  -autoboot_script /dev/null \
  "$@"
