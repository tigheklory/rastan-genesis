#!/usr/bin/env python3
"""Prove a temporary Composer edit changes only its native song assets."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def song_hashes(manifest: dict) -> dict[str, tuple[str, str]]:
    return {
        row["track"]: (row["intro_sha256"], row["loop_sha256"])
        for row in manifest["songs"]
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--baseline-manifest", required=True, type=Path)
    ap.add_argument("--driver", required=True, type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    profile_path = root / "analysis/audio/decision_profiles/music-test.json"
    profile_before = sha(profile_path)
    driver_before = sha(args.driver)
    baseline = json.loads(args.baseline_manifest.read_text())
    target = "01 - Credit"

    with tempfile.TemporaryDirectory(prefix="audio015_profile_workflow_") as tmp_name:
        tmp = Path(tmp_name)
        edited_profile = tmp / "music-test.json"
        profile = json.loads(profile_path.read_text())
        decision = profile["track_routings"][target]
        levels = decision.setdefault("channel_levels", {})
        levels["6"] = 0.5 if levels.get("6") != 0.5 else 0.625
        edited_profile.write_text(json.dumps(profile, indent=1) + "\n")
        output = tmp / "audio_native"
        include = tmp / "audio_assets_generated.inc"
        manifest_path = output / "library.json"
        subprocess.run([
            sys.executable, str(root / "tools/audio/compile_genesis_native_library.py"),
            "--profile", str(edited_profile),
            "--song-map", str(root / "specs/audio_native_song_map.json"),
            "--capture-dir", str(root / "audio/rastan_music_dump/conversion_attempts"),
            "--vgz-dir", str(root / "audio/rastan_music_dump"),
            "--compiler", str(root / "tools/audio/compile_genesis_native_music.py"),
            "--renderer", str(root / "tools/audio/render_genesis_vgm.py"),
            "--output-dir", str(output),
            "--assembly-include", str(include),
            "--manifest", str(manifest_path),
        ], check=True, stdout=subprocess.DEVNULL)
        edited = json.loads(manifest_path.read_text())

    before = song_hashes(baseline)
    after = song_hashes(edited)
    changed = sorted(track for track in before if before[track] != after[track])
    if changed != [target]:
        raise ValueError(f"temporary profile edit changed unexpected songs: {changed}")
    if sha(profile_path) != profile_before:
        raise ValueError("real Audio Composer profile was modified")
    if sha(args.driver) != driver_before:
        raise ValueError("Z80 driver changed during Composer asset rebuild")
    if baseline["dispatch"] != edited["dispatch"]:
        raise ValueError("temporary routing edit changed command registry")
    print(
        "AUDIO_NATIVE_PROFILE_WORKFLOW_PASS "
        f"changed={target!r} unchanged={len(before) - 1} "
        "real_profile=UNCHANGED driver=UNCHANGED registry=UNCHANGED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
