#!/usr/bin/env bash
# Read-only human captures for PROMT-ID-0062. No gameplay is automated.
set -euo pipefail

if [[ $# -lt 1 || ( "$1" != "genesis" && "$1" != "arcade" ) ]]; then
  echo "usage: $0 {genesis|arcade} [MAME options...]" >&2
  exit 2
fi
MODE="$1"
shift

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TRACE_ROOT="${R1S2_FIRST_BAD_ROOT:-${ROOT}/states/traces/r1s2_first_bad_write_build_0530}"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
TRACE_DIR="${TRACE_ROOT}/${MODE}_${STAMP}"
SYMBOLS="${ROOT}/apps/rastan-direct/out/symbol.txt"
EXPECTED_ROM_SHA="6f2afedca192b275bf3068c9e83b534320ca81cc9c6938940093ef78616c65b3"
ROM_SOURCE_COMMIT="974dc0b0c9f3c351536d982e1f0e9dfa2cc45d38"
ROM="${R1S2_FIRST_BAD_ROM:-${ROOT}/dist/rastan-direct/rastan_direct_video_test_build_0530_invincible_S1-2.bin}"

if [[ -e "$TRACE_DIR" ]]; then echo "refusing to overwrite: $TRACE_DIR" >&2; exit 1; fi
mkdir -p "$TRACE_DIR"
if command -v mame >/dev/null 2>&1; then MAME_BIN="$(command -v mame)"
elif command -v mame64 >/dev/null 2>&1; then MAME_BIN="$(command -v mame64)"
else echo "MAME executable not found" >&2; exit 1
fi

export TRACE_DIR ROM_SOURCE_COMMIT
MAME_SOUND="${MAME_SOUND:-auto}"
if [[ "$MAME_SOUND" == auto ]]; then
  if [[ -S /mnt/wslg/PulseServer || -e /dev/snd ]]; then MAME_SOUND=sdl; else MAME_SOUND=none; fi
fi

if [[ "$MODE" == "arcade" ]]; then
  LUA="${ROOT}/tools/mame/scripts/r1s2_resident_oracle_arcade.lua"
  echo "Original-arcade R1-S2 resident-row oracle"
  echo "Output: $TRACE_DIR"
  echo "Play manually from R1-S1 into R1-S2. Press M at each traversal point corresponding to the Genesis route."
  echo "No input, ROM, or game memory is modified by the trace. Close MAME normally when finished."
  exec "$MAME_BIN" rastan -rompath "${ROOT}/roms" -window -resolution 640x448 \
    -sound "$MAME_SOUND" -midiprovider none -skip_gameinfo \
    -debug -debugger none -autoboot_script "$LUA" "$@"
fi

if [[ ! -f "$ROM" ]]; then echo "missing Build 0530 diagnostic ROM: $ROM" >&2; exit 1; fi
if [[ ! -f "$SYMBOLS" ]]; then echo "missing Build 0530 symbols: $SYMBOLS" >&2; exit 1; fi
ROM_SHA="$(sha256sum "$ROM" | awk '{print $1}')"
if [[ "$ROM_SHA" != "$EXPECTED_ROM_SHA" ]]; then
  echo "refusing non-Build-0530 ROM: expected $EXPECTED_ROM_SHA, got $ROM_SHA" >&2
  exit 1
fi
sym() {
  local value
  value="$(awk -v n="$1" '$3 == n {print "0x" $1; exit}' "$SYMBOLS")"
  if [[ -z "$value" ]]; then echo "missing symbol: $1" >&2; exit 1; fi
  printf '%s' "$value"
}
export ROM_NAME="$(basename "$ROM")" ROM_SHA
export R1S2_STAGED_FG_ADDR="$(sym staged_fg_buffer)"
export R1S2_FG_ROW_DIRTY_ADDR="$(sym fg_row_dirty)"
export R1S2_PROVENANCE_ADDR="$(sym plane_a_resident_logical_rows)"
export R1S2_SRC_REF_ADDR="$(sym plane_a_src_ref_block)"
export R1S2_PC_FG_COMMIT="$(sym vdp_commit_fg_strips_if_dirty)"
export R1S2_PC_SCROLL_COMMIT="$(sym vdp_commit_scroll)"
export R1S2_PC_SELECTOR0="$(sym genesistan_hook_tilemap_plane_a_selector0_native)"
export R1S2_PC_SELECTOR12="$(sym genesistan_hook_tilemap_plane_a_selector12_native)"
export R1S2_PC_FG_FILL="$(sym genesistan_hook_tilemap_fg_fill)"
export R1S2_PC_PHASE3="$(sym genesistan_phase3_fg_anim_native)"
LUA="${ROOT}/tools/mame/scripts/r1s2_first_bad_write_genesis.lua"

echo "Build 0530 Genesis R1-S2 first-bad-write capture"
echo "ROM: $ROM"
echo "SHA-256: $ROM_SHA"
echo "Output: $TRACE_DIR"
echo "Aggressively jump-climb the chains and reverse direction as in the failure route."
echo "Press M immediately when corruption first becomes visible; F12 may be used for a screenshot."
echo "No controller input or game memory is automated or modified. Close MAME normally when finished."
exec "$MAME_BIN" genesis -cart "$ROM" -window -resolution 640x448 \
  -sound "$MAME_SOUND" -midiprovider none -skip_gameinfo \
  -debug -debugger none -autoboot_script "$LUA" "$@"
