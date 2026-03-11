#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT_DIR/tools/setup_env.sh" >/dev/null

SMOKE_DIR="$ROOT_DIR/build/sgdk-smoke"

rm -rf "$SMOKE_DIR"
mkdir -p "$SMOKE_DIR"
cp -R "$GDK/project/template/." "$SMOKE_DIR"

make -C "$SMOKE_DIR" -f "$GDK/makefile.gen" release

echo "Smoke build completed: $SMOKE_DIR/out/rom.bin"
