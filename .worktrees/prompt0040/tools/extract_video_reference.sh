#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "Usage: $0 <video-path> [output-dir]" >&2
    exit 1
fi

VIDEO_PATH="$1"
OUTPUT_DIR="${2:-build/video_reference}"

if ! command -v ffprobe >/dev/null 2>&1; then
    echo "ffprobe not found in PATH" >&2
    exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "ffmpeg not found in PATH" >&2
    exit 1
fi

mkdir -p "$OUTPUT_DIR/frames"

BASE_NAME="$(basename "$VIDEO_PATH")"
METADATA_PATH="$OUTPUT_DIR/metadata.txt"
CONTACT_SHEET_PATH="$OUTPUT_DIR/contact_sheet.png"

ffprobe -hide_banner "$VIDEO_PATH" > "$METADATA_PATH" 2>&1
ffmpeg -hide_banner -loglevel error -i "$VIDEO_PATH" \
    -vf "fps=6,scale=640:-1" \
    "$OUTPUT_DIR/frames/frame_%02d.png"
ffmpeg -hide_banner -loglevel error \
    -pattern_type glob -i "$OUTPUT_DIR/frames/frame_*.png" \
    -vf "tile=4x3" \
    -frames:v 1 \
    "$CONTACT_SHEET_PATH"

cat <<EOF
Extracted reference frames for $BASE_NAME
  metadata:      $METADATA_PATH
  frames:        $OUTPUT_DIR/frames
  contact sheet: $CONTACT_SHEET_PATH
EOF
