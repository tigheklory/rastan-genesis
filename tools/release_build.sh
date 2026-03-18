#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <build_number>"
  exit 1
fi

BUILD_NUM="$1"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist/build_${BUILD_NUM}"
ROOT_DIST_ROM="${ROOT_DIR}/dist/Rastan_${BUILD_NUM}.bin"
ROM_BIN="${ROOT_DIR}/apps/rastan/out/rom.bin"
ROM_OUT="${ROOT_DIR}/apps/rastan/out/rom.out"
SYMBOL_TXT="${ROOT_DIR}/apps/rastan/out/symbol.txt"
BUILD_INFO_FILE="${DIST_DIR}/build_info.txt"

if [[ ! "${BUILD_NUM}" =~ ^[0-9]+$ ]]; then
  echo "Build number must be numeric."
  exit 1
fi

cd "${ROOT_DIR}"
source tools/setup_env.sh

make -C apps/rastan clean debug

mkdir -p "${ROOT_DIR}/dist"
mkdir -p "${DIST_DIR}"

# Copy all directly available artifacts first.
find apps/rastan/out -maxdepth 2 -type f -name "*.bin" -exec cp "{}" "${DIST_DIR}/" \;
find apps/rastan/out -maxdepth 2 -type f -name "*.elf" -exec cp "{}" "${DIST_DIR}/" \;
find apps/rastan/out -maxdepth 2 -type f -name "*.map" -exec cp "{}" "${DIST_DIR}/" \;

# Ensure an ELF artifact exists for downstream tooling.
if ! compgen -G "${DIST_DIR}/*.elf" > /dev/null; then
  if [[ -f "${ROM_OUT}" ]]; then
    cp "${ROM_OUT}" "${DIST_DIR}/rastan_build_${BUILD_NUM}.elf"
  fi
fi

# Ensure a MAP artifact exists for downstream tooling.
if ! compgen -G "${DIST_DIR}/*.map" > /dev/null; then
  if [[ -f "${SYMBOL_TXT}" ]]; then
    cp "${SYMBOL_TXT}" "${DIST_DIR}/rastan_build_${BUILD_NUM}.map"
  fi
fi

if [[ ! -f "${ROM_BIN}" ]]; then
  echo "Expected ROM not found: ${ROM_BIN}"
  exit 1
fi

cp "${ROM_BIN}" "${ROOT_DIST_ROM}"

ROM_MD5="$(md5sum "${ROM_BIN}" | awk '{print $1}')"
BUILD_DATE="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

cat > "${BUILD_INFO_FILE}" <<EOF
build_number=${BUILD_NUM}
date_utc=${BUILD_DATE}
rom_file=rom.bin
rom_md5=${ROM_MD5}
EOF

echo "Build ${BUILD_NUM} packaged at: ${DIST_DIR}"
echo "Root ROM artifact: ${ROOT_DIST_ROM}"
