#!/usr/bin/env bash
# Read-only, human-driven Build-0532 trace for PROMT-ID-0072.
# This is intentionally separate from the SHA-guarded Build-0530 tracer.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ROM="${R1S2_0532_ROM:-${ROOT}/dist/rastan-direct/rastan_direct_video_test_build_0532_invincible_S1-2.bin}"
SYMBOLS="${ROOT}/apps/rastan-direct/out/symbol.txt"
TRACE_ROOT="${R1S2_0532_TRACE_ROOT:-${ROOT}/states/traces/r1s2_remaining_build_0532}"
TRACE_ROUTE="${R1S2_0532_TRACE_ROUTE:-unspecified_manual_route}"
TRACE_INSTRUCTION="${R1S2_0532_TRACE_INSTRUCTION:-Reproduce the later record-21 corruption. Press M immediately when it first becomes visible, then close MAME.}"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
TRACE_DIR="${TRACE_ROOT}/genesis_${STAMP}"
LUA="${ROOT}/tools/mame/scripts/r1s2_build0532_remaining_plane_a.lua"
EXPECTED_ROM_SHA="adf3eb18b633f547e21b129ad026c59862a7f921734db9155fe2294c57917879"
EXPECTED_SYMBOL_SHA="1dfbfa4b8dcf4ff4e9b53c1c04e782c83b59bdf8aba0f6092b8533cd71022b21"
EXPECTED_NATIVE_SHA="823c200a7fafd73fb29d21672252b9124b268e46f49ae98da6fba56bcc285900"
EXPECTED_PAN_SHA="d88893fcd9bdf927bb39599bbbdd7b9a768bd9511dba7d2ff03dca4c619c6910"
NATIVE_MAPS="${ROOT}/build/pc080sn_boundary/record_native_maps.bin"
PAN_ROWS="${ROOT}/build/pc080sn_boundary/pan_row_maps.bin"

for path in "$ROM" "$SYMBOLS" "$LUA" "$NATIVE_MAPS" "$PAN_ROWS"; do
  [[ -f "$path" ]] || { echo "missing required file: $path" >&2; exit 1; }
done
[[ "$(sha256sum "$ROM" | awk '{print $1}')" == "$EXPECTED_ROM_SHA" ]] || {
  echo "refusing non-Build-0532 ROM" >&2; exit 1; }
[[ "$(sha256sum "$SYMBOLS" | awk '{print $1}')" == "$EXPECTED_SYMBOL_SHA" ]] || {
  echo "refusing symbols not produced with Build 0532" >&2; exit 1; }
[[ "$(sha256sum "$NATIVE_MAPS" | awk '{print $1}')" == "$EXPECTED_NATIVE_SHA" ]] || {
  echo "refusing non-Build-0532 record-native oracle" >&2; exit 1; }
[[ "$(sha256sum "$PAN_ROWS" | awk '{print $1}')" == "$EXPECTED_PAN_SHA" ]] || {
  echo "refusing non-Build-0532 pan-row oracle" >&2; exit 1; }
[[ ! -e "$TRACE_DIR" ]] || { echo "refusing to overwrite: $TRACE_DIR" >&2; exit 1; }
mkdir -p "$TRACE_DIR"

if command -v mame >/dev/null 2>&1; then MAME_BIN="$(command -v mame)"
elif command -v mame64 >/dev/null 2>&1; then MAME_BIN="$(command -v mame64)"
else echo "MAME executable not found" >&2; exit 1
fi

sym() {
  local value
  value="$(awk -v n="$1" '$3 == n {print "0x" $1; exit}' "$SYMBOLS")"
  [[ -n "$value" ]] || { echo "missing Build-0532 symbol: $1" >&2; exit 1; }
  printf '%s' "$value"
}

export TRACE_DIR ROM_SHA="$EXPECTED_ROM_SHA" ROM_SOURCE_COMMIT="566e9c63e5254be6179a0948a34958c20959c68c"
export R1S2_TRACE_ROUTE="$TRACE_ROUTE"
export R1S2_STAGED_FG_ADDR="$(sym staged_fg_buffer)"
export R1S2_FG_ROW_DIRTY_ADDR="$(sym fg_row_dirty)"
export R1S2_PROVENANCE_ADDR="$(sym plane_a_resident_logical_rows)"
export R1S2_PC_FG_COMMIT="$(sym vdp_commit_fg_strips_if_dirty)"
export R1S2_PC_SCROLL_COMMIT="$(sym vdp_commit_scroll)"
export R1S2_PC_SELECTOR0="$(sym genesistan_hook_tilemap_plane_a_selector0_native)"
export R1S2_PC_SELECTOR12="$(sym genesistan_hook_tilemap_plane_a_selector12_native)"
export R1S2_PC_RESEED="$(sym genesistan_plane_a_scene_scroll_reseed_native)"
export R1S2_PC_PAN="$(sym genesistan_plane_a_pan_publish_entering_rows_up)"
export R1S2_PC_RESOLVER="$(sym resolve_plane_a_cell)"
export R1S2_PC_FG_FILL="$(sym genesistan_hook_tilemap_fg_fill)"
export R1S2_PC_PHASE3="$(sym genesistan_phase3_fg_anim_native)"

MAME_SOUND="${MAME_SOUND:-auto}"
if [[ "$MAME_SOUND" == auto ]]; then
  if [[ -S /mnt/wslg/PulseServer || -e /dev/snd ]]; then MAME_SOUND=sdl; else MAME_SOUND=none; fi
fi

echo "Build 0532 remaining R1-S2 Plane-A capture (read-only)"
echo "ROM: $ROM"
echo "SHA-256: $EXPECTED_ROM_SHA"
echo "Output: $TRACE_DIR"
echo "Route: $TRACE_ROUTE"
echo "$TRACE_INSTRUCTION"
echo "No controller input, ROM, game memory, or save state is modified by this script."
exec "$MAME_BIN" genesis -cart "$ROM" -window -resolution 640x448 \
  -sound "$MAME_SOUND" -midiprovider none -skip_gameinfo \
  -debug -debugger none -autoboot_script "$LUA" "$@"
