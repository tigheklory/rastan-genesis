#!/usr/bin/env bash
# Human-played Build 0529 R1-S2 rope trace. No input is automated.
set -euo pipefail

if [[ $# -lt 1 || ( "$1" != "jump" && "$1" != "normal" ) ]]; then
  echo "usage: $0 {jump|normal} [MAME options...]" >&2
  exit 2
fi
MODE="$1"
shift

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ROM="${R1S2_TRACE_ROM:-${ROOT}/dist/rastan-direct/rastan_direct_video_test_build_0529_invincible_S1-2.bin}"
TRACE_ROOT="${R1S2_TRACE_ROOT:-${ROOT}/states/traces/r1s2_rope_build_0529}"
TRACE_DIR="${TRACE_ROOT}/${MODE}"
LUA="${ROOT}/tools/mame/scripts/r1s2_rope_trace.lua"
SYMBOLS="${ROOT}/apps/rastan-direct/out/symbol.txt"

if [[ ! -f "$ROM" ]]; then echo "missing diagnostic ROM: $ROM" >&2; exit 1; fi
if [[ ! -f "$SYMBOLS" ]]; then echo "missing current symbol file: $SYMBOLS" >&2; exit 1; fi
if [[ -e "$TRACE_DIR" ]]; then
  echo "refusing to overwrite trace directory: $TRACE_DIR" >&2
  echo "move it aside or set R1S2_TRACE_ROOT to a new directory" >&2
  exit 1
fi
mkdir -p "$TRACE_DIR"

if command -v mame >/dev/null 2>&1; then MAME_BIN="$(command -v mame)"
elif command -v mame64 >/dev/null 2>&1; then MAME_BIN="$(command -v mame64)"
else echo "MAME executable not found" >&2; exit 1
fi

sym() {
  local name="$1" value
  value="$(awk -v n="$name" '$3 == n {print "0x" $1; exit}' "$SYMBOLS")"
  if [[ -z "$value" ]]; then echo "missing symbol: $name" >&2; exit 1; fi
  printf '%s' "$value"
}

export TRACE_DIR TRACE_MODE="$MODE"
export ROM_NAME="$(basename "$ROM")"
export ROM_SHA="$(sha256sum "$ROM" | awk '{print $1}')"
export SOURCE_COMMIT="$(git -C "$ROOT" rev-parse HEAD)"
export R1S2_STAGED_FG_ADDR="$(sym staged_fg_buffer)"
export R1S2_FG_ROW_DIRTY_ADDR="$(sym fg_row_dirty)"
export R1S2_FG_COL_DIRTY_ADDR="$(sym fg_col_dirty)"
export R1S2_NARROW_COUNT_ADDR="$(sym fg_narrow_desc_count)"
export R1S2_SCROLL_X_ADDR="$(sym staged_scroll_x_fg)"
export R1S2_SCROLL_Y_ADDR="$(sym staged_scroll_y_fg)"
export R1S2_VBLANK_VC_ADDR="$(sym vblank_vc)"
export R1S2_SRC_REF_ADDR="$(sym plane_a_src_ref_block)"
export R1S2_PC_SELECTOR0="$(sym genesistan_hook_tilemap_plane_a_selector0_native)"
export R1S2_PC_SELECTOR12="$(sym genesistan_hook_tilemap_plane_a_selector12_native)"
export R1S2_PC_PAN_UP="$(sym genesistan_plane_a_pan_publish_entering_rows_up)"
export R1S2_PC_PAN_DOWN="$(sym genesistan_plane_a_pan_publish_entering_rows_down)"
export R1S2_PC_FG_COMMIT="$(sym vdp_commit_fg_strips_if_dirty)"
export R1S2_PC_SCROLL_COMMIT="$(sym vdp_commit_scroll)"

MAME_SOUND="${MAME_SOUND:-auto}"
if [[ "$MAME_SOUND" == auto ]]; then
  if [[ -S /mnt/wslg/PulseServer || -e /dev/snd ]]; then MAME_SOUND=sdl; else MAME_SOUND=none; fi
fi

echo "R1-S2 ${MODE^^} trace"
echo "ROM: $ROM"
echo "Output: $TRACE_DIR"
echo "Play manually. Press M whenever corruption becomes visible; F12 takes a screenshot."
echo "Complete the subround, then close MAME normally. No controller input is automated."

exec "$MAME_BIN" genesis -cart "$ROM" -window -resolution 640x448 \
  -sound "$MAME_SOUND" -midiprovider none -skip_gameinfo \
  -debug -debugger none -autoboot_script "$LUA" "$@"
