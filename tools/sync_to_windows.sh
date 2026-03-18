#!/bin/bash

# 1. Look for the highest build number in the filenames within dist/
# This extracts the digits immediately following "Rastan_"
LATEST_BUILD=$(ls dist/Rastan_*.bin 2>/dev/null | grep -oP 'Rastan_\K[0-9]+' | sort -n | tail -1)

if [ -z "$LATEST_BUILD" ]; then
    echo "ERROR: Could not find any Rastan_XX.bin files in dist/"
    exit 1
fi

echo "Found Latest Build Number: ${LATEST_BUILD}"

# 2. Find the ACTUAL source file path
# Priority 1: A clean file like Rastan_89.bin
# Priority 2: A timestamped file like Rastan_89_20260318_105337.bin
SRC_PATH=$(ls dist/Rastan_${LATEST_BUILD}.bin 2>/dev/null | head -1)

if [ -z "$SRC_PATH" ]; then
    SRC_PATH=$(ls dist/Rastan_${LATEST_BUILD}_*.bin 2>/dev/null | head -1)
fi

if [ -z "$SRC_PATH" ]; then
    echo "ERROR: Found build number ${LATEST_BUILD} but couldn't locate the file."
    exit 1
fi

echo "Source File: ${SRC_PATH}"

# 3. Define Windows Paths
DEST_DIR="/mnt/c/Rastan-Genesis"
DEST_BIN="${DEST_DIR}/Rastan_${LATEST_BUILD}.bin"
BAT_FILE="${DEST_DIR}/launch_blastem.bat"

# 4. Create Windows Directory and Copy
mkdir -p "${DEST_DIR}"
cp "${SRC_PATH}" "${DEST_BIN}"
echo "Copied to: ${DEST_BIN}"

# 5. Generate the Windows .bat file
# We use sed to ensure Windows-friendly line endings (\r\n)
cat << EOT > "${BAT_FILE}"
@echo off
"C:\Users\Tighe Lory\Documents\Installation Programs\blastem-win32-0.6.2\blastem.exe" "C:\Rastan-Genesis\Rastan_${LATEST_BUILD}.bin" -d
echo %ERRORLEVEL% > "C:\Rastan-Genesis\exit_status_build_${LATEST_BUILD}.txt"
exit
EOT

sed -i 's/$/\r/' "${BAT_FILE}"
echo "Generated: ${BAT_FILE}"