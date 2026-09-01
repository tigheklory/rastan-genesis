#!/usr/bin/env bash
# Interactive ORIGINAL ARCADE (rastan) session for visual A/B screenshot capture.
# Reuses run_rastan_wsl.sh (rastanmon monitor, cheat, rompath) and adds a fixed snapshot
# directory so F12 shots always land where the comparison workflow can read them.
#
#   Coin:  5     Start: 1     Move: arrow keys     Attack/Jump: Ctrl / Alt  (Tab -> Input to confirm)
#   Screenshot: F12   ->   states/screenshots/r1p1_cave_compare/arcade/cave_NNNN.png
#
# Platform label: ORIGINAL ARCADE MAME (authoritative ground truth).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SHOTS_DIR="${SHOTS_DIR:-${ROOT}/states/screenshots/r1p1_cave_compare/arcade}"
mkdir -p "${SHOTS_DIR}"
echo "ORIGINAL ARCADE session. F12 snapshots -> ${SHOTS_DIR}"
echo "Coin=5  Start=1  Move=arrows  (Tab->Input to confirm attack/jump)."
exec "${ROOT}/tools/mame/run_rastan_wsl.sh" rastan \
  -snapshot_directory "${SHOTS_DIR}" \
  -snapname "cave_%i" \
  "$@"
