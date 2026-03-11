#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export ROOT_DIR

export GDK="$ROOT_DIR/tools/sgdk"
export JAVA_HOME="$ROOT_DIR/tools/local/java/jdk-21.0.10+7"
export M68K_ELF_ROOT="$ROOT_DIR/tools/local/toolchain/m68k-elf"
export JAVA_TOOL_OPTIONS="${JAVA_TOOL_OPTIONS:-} -Djava.awt.headless=true"

export PATH="$JAVA_HOME/bin:$M68K_ELF_ROOT/bin:$ROOT_DIR/tools/local/bin:$PATH"

cat <<EOF
Environment configured:
  GDK=$GDK
  JAVA_HOME=$JAVA_HOME
  M68K_ELF_ROOT=$M68K_ELF_ROOT
  JAVA_TOOL_OPTIONS=$JAVA_TOOL_OPTIONS
EOF
