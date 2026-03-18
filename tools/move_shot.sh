#!/bin/bash
# Supervisor Tool: Move Windows Screenshot to Project (v5 - Auto-Cleanup)
PROJECT_ROOT="/home/tighe/projects/rastan-genesis"
WIN_SHOT_DIR="/mnt/c/Users/Tighe Lory/Pictures/Screenshots"

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

# 3. Get the latest shot EXCLUDING the BK subfolder
LATEST_SHOT=$(find "$WIN_SHOT_DIR" -maxdepth 1 -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -f2- -d" ")

if [ -z "$LATEST_SHOT" ]; then
    echo "No new screenshots found in $WIN_SHOT_DIR (ignoring BK folder)."
    exit 1
fi

echo "Found latest: $(basename "$LATEST_SHOT")"

# 4. Select Platform
echo "Enter platform (m=MAME, b=BlastEm, e=Exodus, h=Hardware/Nomad): "
read -r PLAT_KEY
case $PLAT_KEY in
    m) PLAT="mame" ;;
    b) PLAT="blastem" ;;
    e) PLAT="exodus" ;;
    h) PLAT="hardware" ;;
    *) PLAT="unknown" ;;
esac

# 5. Select Stage
echo "Enter stage (l=launcher, i=ingame): "
read -r STAGE_KEY
case $STAGE_KEY in
    l) STAGE="launcher" ;;
    i) STAGE="ingame" ;;
    *) STAGE="unknown" ;;
esac

TIMESTAMP=$(date +%Y%m%d_%H%M)
NEW_NAME="B${BUILD_NUM}_${PLAT}_${STAGE}_${TIMESTAMP}.png"

# 6. Copy to Repository
cp "$LATEST_SHOT" "$TARGET_DIR/$NEW_NAME"

# 7. Delete from Windows (Cleanup)
if [ $? -eq 0 ]; then
    rm "$LATEST_SHOT"
    echo "Successfully moved and DELETED source: $NEW_NAME"
else
    echo "ERROR: Copy failed. Original file was not deleted."
fi