#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/../.." && pwd)
audit_dir="$repo_root/analysis/build0311_phase1_hardware_visual_audit"
source_video="$repo_root/states/screenshots/Build_0311_Playthough_Round_1_Phase_1_crashes_Phase_2.mp4"

mkdir -p "$audit_dir/frames/baseline" "$audit_dir/frames/dense" "$audit_dir/metadata"
find "$audit_dir/frames/baseline" -maxdepth 1 -type f -name 'frame_*.jpg' -delete
find "$audit_dir/frames/dense" -mindepth 1 -delete

# The complete baseline is intentionally 4 fps. Dense windows are added separately only
# after transition intervals have been identified from this chronological pass.
ffmpeg -nostdin -hide_banner -loglevel error -y -i "$source_video" \
  -vf "fps=4,scale=960:-2:flags=lanczos" -q:v 3 \
  "$audit_dir/frames/baseline/frame_%06d.jpg"

# Bounded 12-fps windows selected from the chronological pass. They cover gameplay entry,
# the first record-1 descent, and later horizontal/vertical camera transitions without
# expanding the complete capture to source-frame density.
while IFS=, read -r name start duration; do
  out="$audit_dir/frames/dense/$name"
  mkdir -p "$out"
  ffmpeg -nostdin -hide_banner -loglevel error -y -ss "$start" -t "$duration" \
    -i "$source_video" -vf "fps=12,scale=960:-2:flags=lanczos" -q:v 3 \
    "$out/frame_%06d.jpg"
done <<'EOF'
gameplay_entry,17.500,3.000
section02_record01_descent,27.250,17.250
section02_record01_exit,46.500,4.000
vertical_transition_01,56.500,17.000
mid_phase_transition_01,89.000,12.000
mid_phase_transition_02,117.000,12.000
late_phase_transition_01,145.000,12.000
late_phase_transition_02,175.000,12.000
fortress_approach,202.000,12.000
EOF

python3 "$audit_dir/make_storyboard.py" \
  --video "$source_video" \
  --audit-dir "$audit_dir" \
  --sample-rate 4
