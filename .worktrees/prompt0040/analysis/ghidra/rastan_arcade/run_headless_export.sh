#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
cd "$ROOT"
source tools/setup_env.sh >/dev/null
export HOME="$ROOT/analysis/ghidra/rastan_arcade/.home"
export XDG_CONFIG_HOME="$HOME/.config"
mkdir -p "$HOME" "$XDG_CONFIG_HOME" analysis/ghidra/rastan_arcade/ghidra_project analysis/ghidra/rastan_arcade/exports analysis/ghidra/rastan_arcade/logs
GHIDRA=/home/tighe/tools/ghidra_12.0.4_PUBLIC/support/analyzeHeadless
PROJECT_DIR="$ROOT/analysis/ghidra/rastan_arcade/ghidra_project"
PROJECT_NAME="rastan_arcade_world_rev1"
INPUT="$ROOT/analysis/ghidra/rastan_arcade/input/rastan_world_rev1_maincpu_68000.bin"
SCRIPTS="$ROOT/analysis/ghidra/rastan_arcade/scripts"
EXPORTS="$ROOT/analysis/ghidra/rastan_arcade/exports"
LOG="$ROOT/analysis/ghidra/rastan_arcade/logs/headless_export.log"
"$GHIDRA" "$PROJECT_DIR" "$PROJECT_NAME" -overwrite -import "$INPUT" \
  -processor 68000:BE:32:default -cspec default \
  -scriptPath "$SCRIPTS" \
  -preScript RastanArcadeSeed.java \
  -postScript RastanArcadeExport.java "$EXPORTS" \
  2>&1 | tee "$LOG"
