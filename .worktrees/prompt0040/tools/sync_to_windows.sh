#!/bin/bash
set -euo pipefail

# 1. Get the directory where THIS script lives, then go up one level to the project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_ROOT/dist"

echo "Project Root: $PROJECT_ROOT"
echo "Searching in: $DIST_DIR"

# 2. Determine which build to sync.
#    With argument:    ./sync_to_windows.sh 97  -> uses dist/Rastan_97.bin
#    Without argument: finds the most recently modified .bin in dist/
if [[ $# -ge 1 ]]; then
    BUILD_NUM="$1"
    if [[ ! "${BUILD_NUM}" =~ ^[0-9]+$ ]]; then
        echo "ERROR: Build number must be numeric."
        exit 1
    fi
    SRC_PATH="${DIST_DIR}/Rastan_${BUILD_NUM}.bin"
    if [[ ! -f "${SRC_PATH}" ]]; then
        echo "ERROR: ${SRC_PATH} does not exist."
        exit 1
    fi
    echo "Using specified build: ${BUILD_NUM}"
else
    # Fall back to most recently modified .bin in dist/
    SRC_PATH=$(ls -t "$DIST_DIR"/Rastan_*.bin 2>/dev/null | head -1)
    if [[ -z "${SRC_PATH}" ]]; then
        echo "ERROR: Could not find any Rastan_*.bin files in $DIST_DIR"
        exit 1
    fi
    # Extract the build number from the chosen filename for the bat file
    BUILD_NUM=$(basename "${SRC_PATH}" | grep -oP 'Rastan_\K[0-9]+')
    echo "No build number given — using most recently modified: $(basename "${SRC_PATH}")"
fi

# 3. Define Windows Paths
DEST_DIR="/mnt/c/Rastan-Genesis"
DEST_BIN="${DEST_DIR}/Rastan_${BUILD_NUM}.bin"
BAT_FILE="${DEST_DIR}/launch_blastem.bat"

# 4. Create Windows Directory and Copy
mkdir -p "${DEST_DIR}"
cp "${SRC_PATH}" "${DEST_BIN}"
echo "Copied to: ${DEST_BIN}"

# 5. Generate the Windows .bat file
cat << EOT > "${BAT_FILE}"
@echo off
"C:\Users\Tighe Lory\Documents\Installation Programs\blastem-win32-0.6.2\blastem.exe" "C:\Rastan-Genesis\Rastan_${BUILD_NUM}.bin" -d
echo %ERRORLEVEL% > "C:\Rastan-Genesis\exit_status_build_${BUILD_NUM}.txt"
exit
EOT

# Convert to Windows line endings
sed -i 's/$/\r/' "${BAT_FILE}"
echo "Generated: ${BAT_FILE}"
