#!/bin/bash
# Supervisor Tool: Move Screenshot & Auto-Log (v6)
PROJECT_ROOT="/home/tighe/projects/rastan-genesis"
WIN_SHOT_DIR="/mnt/c/Users/Tighe Lory/Pictures/Screenshots"
AGENTS_LOG="${PROJECT_ROOT}/AGENTS_LOG.md"

# 1. Check if Windows C: drive is mounted
if [ ! -d "/mnt/c" ]; then
    echo "ERROR: /mnt/c is not mounted. Run: sudo mount -t drvfs C: /mnt/c"
    exit 1
fi

# 2. Get Build Number and Setup Folder
echo "Enter Build Number (e.g., 87): "
read -r BUILD_NUM
TARGET_DIR="${PROJECT_ROOT}/states/screenshots/build_${BUILD_NUM}"
mkdir -p "$TARGET_DIR"

# 3. Get the latest shot
LATEST_SHOT=$(find "$WIN_SHOT_DIR" -maxdepth 1 -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -f2- -d" ")

if [ -z "$LATEST_SHOT" ]; then
    echo "No new screenshots found."
    exit 1
fi

# 4. Select Platform & Stage
echo "Enter platform (m=MAME, b=BlastEm, e=Exodus, h=Hardware): "
read -r PLAT_KEY
case $PLAT_KEY in m) PLAT="MAME" ;; b) PLAT="BlastEm" ;; e) PLAT="Exodus" ;; h) PLAT="Hardware" ;; *) PLAT="Unknown" ;; esac

echo "Enter stage (l=launcher, i=ingame): "
read -r STAGE_KEY
case $STAGE_KEY in l) STAGE="Launcher" ;; i) STAGE="In-Game" ;; *) STAGE="Unknown" ;; esac

TIMESTAMP=$(date +%Y%m%d_%H%M)
NEW_NAME="B${BUILD_NUM}_${PLAT}_${STAGE}_${TIMESTAMP}.png"

# 5. Move and Log
if cp "$LATEST_SHOT" "$TARGET_DIR/$NEW_NAME"; then
    rm "$LATEST_SHOT"
    echo "Moved to: $NEW_NAME"
    
    # Append to AGENTS_LOG.md
    echo "- **Visual Evidence ($PLAT):** Screenshot saved as \`$NEW_NAME\` (Stage: $STAGE)" >> "$AGENTS_LOG"
    echo "Appended to AGENTS_LOG.md"
else
    echo "ERROR: Move failed."
fi