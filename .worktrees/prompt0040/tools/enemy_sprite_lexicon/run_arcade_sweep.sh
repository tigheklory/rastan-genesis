#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/../.." && pwd)
OUT=${1:-"$ROOT/analysis/enemy_sprite_lexicon/evidence/arcade_sweep"}
FRAMES=${LEXICON_FRAMES:-5200}
mkdir -p "$OUT"

entries=(
  "round1_phase1:0xFF" "round1_castle:0xDF" "round1_boss:0xF7"
  "round2_phase1:0xFE" "round2_castle:0xDE" "round2_boss:0xF6"
  "round3_phase1:0xFD" "round3_castle:0xDD" "round3_boss:0xF5"
  "round4_phase1:0xFC" "round4_castle:0xDC" "round4_boss:0xF4"
  "round5_phase1:0xFB" "round5_castle:0xDB" "round5_boss:0xF3"
  "round6_phase1:0xFA" "round6_castle:0xDA" "round6_boss:0xF2"
)

run_one() {
  local pair=$1
  local label=${pair%%:*}
  local selector=${pair##*:}
  local dir="$OUT/$label"
  mkdir -p "$dir"
  LEXICON_OUT="$dir" LEXICON_LABEL="$label" LEXICON_SELECTOR="$selector" \
    LEXICON_FRAMES="$FRAMES" timeout 180s mame rastan -rompath "$ROOT/roms" \
    -video none -sound none -nothrottle -skip_gameinfo \
    -autoboot_script "$ROOT/tools/enemy_sprite_lexicon/arcade_enemy_sweep.lua" \
    >"$dir/mame_stdout.log" 2>"$dir/mame_stderr.log"
}

export -f run_one
export ROOT OUT FRAMES
printf '%s\n' "${entries[@]}" | xargs -P 6 -n 1 bash -c 'run_one "$1"' _

python3 - "$OUT" <<'PY'
import csv, pathlib, sys
root = pathlib.Path(sys.argv[1])
files = sorted(root.glob("*/observations.csv"))
if len(files) != 18:
    raise SystemExit(f"expected 18 observation files, found {len(files)}")
header = None
rows = []
for path in files:
    with path.open(newline="") as f:
        reader = csv.reader(f)
        current = next(reader)
        if header is None: header = current
        if current != header: raise SystemExit(f"header mismatch: {path}")
        rows.extend(reader)
with (root / "all_observations.csv").open("w", newline="") as f:
    writer = csv.writer(f); writer.writerow(header); writer.writerows(rows)
(root / "sweep_complete.txt").write_text(
    f"entry_points=18\nobservations={len(rows)}\n", encoding="ascii")
print(f"arcade enemy sweep: 18/18 entries, {len(rows)} unique observations")
PY
