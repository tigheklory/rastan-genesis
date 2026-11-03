#!/usr/bin/env bash
# AUDIO-012 — fetch the LOCAL webVGM engine into tools/audio_composer/engine/ (git-ignored).
# This repo does NOT redistribute wothke's webVGM/VGMPlay (GPL-family + MAME-licensed chip cores).
# This script downloads a personal, local copy for your own use only. Do not commit the engine/ dir.
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"
ENG="engine"; TMP="$(mktemp -d)"
echo "Cloning wothke/vgmplay-0.40.9 (shallow) ..."
git clone --depth 1 https://github.com/wothke/vgmplay-0.40.9 "$TMP/up"
mkdir -p "$ENG"
cp "$TMP/up/emscripten/htdocs/backend_vgm.js" "$ENG/"
cp "$TMP/up/emscripten/htdocs/VGMPlay.ini" "$ENG/"
cp "$TMP/up/emscripten/htdocs/stdlib/scriptprocessor_player.min.js" "$ENG/"
cp "$TMP/up/src/licenses/GPL.txt" "$ENG/" 2>/dev/null || true
cp "$TMP/up/src/licenses/mame_license.txt" "$ENG/" 2>/dev/null || true
: > "$ENG/yrw801.rom"
rm -rf "$TMP"
echo "Engine fetched into $ENG/ (local, git-ignored). webvgm_player.html is already provided."
