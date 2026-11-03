#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MAME_BIN="$(command -v mame || command -v mame64 || true)"
if [[ -z "${MAME_BIN}" ]]; then
  echo "MAME executable not found" >&2
  exit 1
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
TRACE_DIR="${CAVE_ROUTE_TRACE_DIR:-${ROOT}/states/traces/original_arcade_stage1_cave_route_${STAMP}}"
HOMEPATH="${ROOT}/build/mame/home"
SCRIPT="${ROOT}/tools/mame/scripts/arcade_stage1_cave_route.lua"
mkdir -p "${TRACE_DIR}" "${HOMEPATH}"

CMD=(
  "${MAME_BIN}" rastan
  -window
  -skip_gameinfo
  -rompath "${ROOT}/roms"
  -homepath "${HOMEPATH}"
  -autoboot_script "${SCRIPT}"
)

{
  printf 'platform=ORIGINAL ARCADE\n'
  printf 'machine=rastan\n'
  printf 'trace_dir=%s\n' "${TRACE_DIR}"
  printf 'logger=%s\n' "${SCRIPT}"
  printf 'logger_sha256='; sha256sum "${SCRIPT}" | awk '{print $1}'
  printf 'mame_version='; "${MAME_BIN}" -version | head -1
  printf 'started=%s\n' "$(date --iso-8601=seconds)"
  printf 'command='; printf '%q ' "${CMD[@]}"; printf '\n'
} > "${TRACE_DIR}/capture_command.txt"

printf 'CAVE_ROUTE_TRACE_DIR=%s\n' "${TRACE_DIR}"
printf 'Logging is active from machine start; exit MAME normally when the route is complete.\n'

set +e
CAVE_ROUTE_TRACE_DIR="${TRACE_DIR}" "${CMD[@]}"
STATUS=$?
set -e
{
  printf 'finished=%s\n' "$(date --iso-8601=seconds)"
  printf 'mame_exit_status=%d\n' "${STATUS}"
} >> "${TRACE_DIR}/capture_command.txt"
exit "${STATUS}"
