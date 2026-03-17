#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MACHINE="rastan"

if [[ $# -gt 0 && "${1}" != -* ]]; then
  MACHINE="$1"
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

HOMEPATH="${ROOT}/build/mame/home"
PLUGINPATHS="${ROOT}/tools/mame/plugins;/usr/share/games/mame/plugins;/usr/local/share/games/mame/plugins"
CHEATPATHS="${ROOT}/tools/mame/cheat;${HOMEPATH}/cheat;cheat"

mkdir -p "${HOMEPATH}/rastantrace"
mkdir -p "${ROOT}/tools/mame/cheat"

if [[ ! -f "${ROOT}/tools/mame/cheat/cheat.7z" ]]; then
  echo "warning: tools/mame/cheat/cheat.7z is missing" >&2
  echo "         cheats will not appear until you place cheat.7z there" >&2
fi

exec "${MAME_BIN}" "${MACHINE}" \
  -window \
  -skip_gameinfo \
  -plugins \
  -plugin "cheat" \
  -cheat \
  -rompath "${ROOT}/roms" \
  -homepath "${HOMEPATH}" \
  -pluginspath "${PLUGINPATHS}" \
  -cheatpath "${CHEATPATHS}" \
  -autoboot_script "${ROOT}/tools/mame/scripts/rastantrace.lua" \
  "$@"
