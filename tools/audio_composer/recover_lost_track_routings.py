#!/usr/bin/env python3
"""AUDIO-015 one-time recovery of Composer arrangements lost by the track_routings
persistence bug (see Andy_AUDIO015_multisong_dispatch_and_diagnostic.md).

Two authored songs never reached the per-song track_routings store because the client
only migrated a top-level routing into track_routings when that map was ENTIRELY empty:
  * Scene Clear (07)  - its approved routing survives in revision snapshot music-test.r8.json
                        (top-level approved_routing, the track_id active at r8).
  * Final Boss (08)   - its approved routing is in the CURRENT music-test.json top level
                        (the track_id active at the latest revision).

This script folds each song's SAVED top-level decisions into track_routings using exactly
the stored values (approved_routing = the user-approved channels; proposals, noise_mode,
instrument_overrides as stored).  It manufactures no approvals and changes no other song.
It writes a new immutable revision snapshot and updates the current profile + manifest the
same way the server does, so the Composer and the ROM compiler agree afterwards.

Run from the repo root:  python3 -I tools/audio_composer/recover_lost_track_routings.py
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

PROF_DIR = Path("analysis/audio/decision_profiles")
CURRENT = PROF_DIR / "music-test.json"

# (track name, source revision file, which fields to read from that file's TOP LEVEL)
RECOVER = [
    ("07 - Scene Clear", PROF_DIR / "music-test.r8.json"),
    ("08 - Final Destroy (Scene 3 Round 6 Boss)", CURRENT),
]

FIELDS = ("approved_routing", "proposals", "noise_mode", "instrument_overrides")


def entry_from(src: dict) -> dict:
    return {
        "approved_routing": src.get("approved_routing", {}),
        "proposals": src.get("proposals", {}),
        "noise_mode": src.get("noise_mode", "fixed_1024"),
        "instrument_overrides": src.get("instrument_overrides", {}),
    }


def main() -> int:
    prof = json.loads(CURRENT.read_text())
    tr = prof.get("track_routings")
    if not isinstance(tr, dict):
        raise SystemExit("current profile has no track_routings object")

    recovered = []
    for track, src_path in RECOVER:
        if track in tr and tr[track].get("approved_routing"):
            print(f"already present, skipping: {track!r}")
            continue
        src = json.loads(src_path.read_text())
        # The source file's active track must be the one we are recovering.
        if src.get("track_id") != track:
            raise SystemExit(f"{src_path.name}: track_id {src.get('track_id')!r} != {track!r}")
        entry = entry_from(src)
        if not entry["approved_routing"]:
            raise SystemExit(f"{src_path.name}: no approved_routing to recover for {track!r}")
        tr[track] = entry
        recovered.append((track, src_path.name, sorted(entry["approved_routing"])))

    if not recovered:
        print("nothing to recover; track_routings already complete")
        return 0

    prof["track_routings"] = tr
    prof["revision"] = int(prof.get("revision", 0)) + 1
    prof["revision_id"] = "%s.r%d.%s" % (
        prof.get("profile_id", "music-test"), prof["revision"], time.strftime("%Y%m%dT%H%M%SZ"))
    prof["modified"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    prof["notes"] = (prof.get("notes") or "") + (
        "\nAUDIO-015: recovered Scene Clear (from r8) and Final Boss (from r13 top level) into "
        "track_routings after the persistence bug; approvals preserved as stored.")

    rev_path = PROF_DIR / f"{prof.get('profile_id','music-test')}.r{prof['revision']}.json"
    rev_path.write_text(json.dumps(prof, indent=1) + "\n")
    CURRENT.write_text(json.dumps(prof, indent=1) + "\n")

    man_path = PROF_DIR / "profile_manifest.json"
    if man_path.exists():
        man = json.loads(man_path.read_text())
        for p in man.get("profiles", []):
            if p.get("profile_id") == prof.get("profile_id"):
                p["revision"] = prof["revision"]
                p["modified"] = prof["modified"]
        man_path.write_text(json.dumps(man, indent=1) + "\n")

    for track, src, chans in recovered:
        print(f"recovered {track!r} from {src}: channels {chans}")
    print(f"wrote revision {prof['revision']} -> {rev_path.name} and {CURRENT.name}")
    print(f"track_routings now has {len(tr)} songs: {sorted(tr)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
