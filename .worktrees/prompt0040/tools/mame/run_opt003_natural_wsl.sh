#!/usr/bin/env bash
# OPT-003 valid-transition test: reach the record 2(pkg0)->3(pkg5) Layer-A epoch
# transition through NATURAL arcade progression (scroll), not synthetic injection,
# and observe active_lut[0x034C]. GENESIS NTSC target.
#   tools/mame/run_opt003_natural_wsl.sh [rom]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MACHINE="${MAME_GENESIS_MACHINE:-genesis}"
CART="${1:-$(ls -t "${ROOT}"/dist/rastan-direct/rastan_direct_video_test_build_[0-9]*.bin 2>/dev/null | grep -vE '_d\.bin|_s\.bin|_do\.bin' | head -1)}"
SYMBOLS="${ROOT}/apps/rastan-direct/out/symbol.txt"

if command -v mame >/dev/null 2>&1; then MAME_BIN="$(command -v mame)"
elif command -v mame64 >/dev/null 2>&1; then MAME_BIN="$(command -v mame64)"
else echo "MAME not found" >&2; exit 1; fi
[[ -f "$CART" ]] || { echo "ROM not found: $CART" >&2; exit 1; }

# Build the symbol env string the lua needs.
names="fg_boundary_active_record fg_boundary_active_package fg_boundary_active_lut fg_boundary_epoch_transitions genesistan_current_scene_id fg_boundary_advance_segment fg_boundary_install_post_reseed fg_boundary_reseed_pending"
sym=""
for n in $names; do
  a=$(awk -v s="$n" '$3==s{print $1}' "$SYMBOLS" | head -1)
  [[ -n "$a" ]] && sym="${sym}${n}=${a} "
done
export OPT003_SYMBOLS="$sym"

HOMEPATH="${ROOT}/build/mame/home"
mkdir -p "${HOMEPATH}/opt003_natural"
echo "Cart: $CART"
echo "Log:  ${HOMEPATH}/opt003_natural/opt003_natural.log"

exec "${MAME_BIN}" "${MACHINE}" -cart "${CART}" \
  -video none -sound none -skip_gameinfo \
  -seconds_to_run "${MAME_SECONDS:-120}" \
  -homepath "${HOMEPATH}" \
  -autoboot_script "${ROOT}/tools/mame/scripts/opt003_natural_transition.lua"
