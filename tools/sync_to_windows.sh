#!/bin/bash

# 1. Get the directory where THIS script lives, then go up one level to the project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_ROOT/dist"

echo "Project Root: $PROJECT_ROOT"
echo "Searching in: $DIST_DIR"

# 2. Look for the highest build number in the filenames within dist/
LATEST_BUILD=$(ls "$DIST_DIR"/Rastan_*.bin 2>/dev/null | grep -oP 'Rastan_\K[0-9]+' | sort -n | tail -1)

if [ -z "$LATEST_BUILD" ]; then
    echo "ERROR: Could not find any Rastan_XX.bin files in $DIST_DIR"
    exit 1
fi

echo "Found Latest Build Number: ${LATEST_BUILD}"

# 3. Find the ACTUAL source file path
SRC_PATH=$(ls "$DIST_DIR"/Rastan_${LATEST_BUILD}.bin 2>/dev/null | head -1)

if [ -z "$SRC_PATH" ]; then
    SRC_PATH=$(ls "$DIST_DIR"/Rastan_${LATEST_BUILD}_*.bin 2>/dev/null | head -1)
fi

# 4. Define Windows Paths
DEST_DIR="/mnt/c/Rastan-Genesis"
DEST_BIN="${DEST_DIR}/Rastan_${LATEST_BUILD}.bin"
BAT_FILE="${DEST_DIR}/launch_blastem.bat"

# 5. Create Windows Directory and Copy
mkdir -p "${DEST_DIR}"
cp "${SRC_PATH}" "${DEST_BIN}"
echo "Copied to: ${DEST_BIN}"

# 6. Generate the Windows .bat file
cat << EOT > "${BAT_FILE}"
@echo off
"C:\Users\Tighe Lory\Documents\Installation Programs\blastem-win32-0.6.2\blastem.exe" "C:\Rastan-Genesis\Rastan_${LATEST_BUILD}.bin" -d
echo %ERRORLEVEL% > "C:\Rastan-Genesis\exit_status_build_${LATEST_BUILD}.txt"
exit
EOT

# Convert to Windows line endings
sed -i 's/$/\r/' "${BAT_FILE}"
echo "Generated: ${BAT_FILE}"