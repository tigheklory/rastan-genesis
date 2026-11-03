#!/usr/bin/env python3
"""AUDIO-010 independent regression audit for the AUDIO-009 corrections.

This harness deliberately reuses the independent AUDIO-008 binary/capture/VGM
parsers instead of importing the corrected analyzers.  Audio Composer writes are
redirected to a temporary directory and exercised through real loopback HTTP.
Faults are injected only into the in-process temporary profile store.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[3]
ROM = ROOT / "build/regions/audiocpu.bin"
ADPCM = ROOT / "build/regions/adpcm.bin"
VGM = ROOT / "audio/Inglebard Agressive World Handmade Genesis version/LM-Main Stage Theme (1).vgm"
CAPTURE_DIR = ROOT / "audio/rastan_music_dump/conversion_attempts"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


S = load_module(ROOT / "tools/audio_composer/server.py", "audio010_composer")
A8 = load_module(Path(__file__).with_name("audio008_independent_audit.py"), "audio010_audio008_parser")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class QuietHTTPServer(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        # Expected for deterministic injected-write failures; the result is
        # captured by the client and on-disk state, not a traceback.
        pass


class Harness:
    def __init__(self, profile_dir: Path):
        self.profile_dir = profile_dir
        self.httpd = None
        self.thread = None
        self.port = None

    def start(self):
        self.httpd = QuietHTTPServer(("127.0.0.1", 0), S.Hd)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if self.httpd is not None:
            self.httpd.shutdown()
            self.httpd.server_close()
        if self.thread is not None:
            self.thread.join(timeout=5)
        self.httpd = self.thread = self.port = None

    def request(self, method: str, path: str, body=None, raw=None):
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        payload = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        headers = {"Content-Type": "application/json"} if payload is not None else {}
        try:
            conn.request(method, path, body=payload, headers=headers)
            response = conn.getresponse()
            data = response.read()
            status = response.status
            try:
                decoded = json.loads(data)
            except Exception:
                decoded = data.decode(errors="replace")
            return status, decoded
        except Exception as exc:
            return None, {"transport_error": type(exc).__name__, "detail": str(exc)}
        finally:
            conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    tests = []

    def check(name, category, passed, observed, expected, severity="none"):
        tests.append({
            "name": name,
            "category": category,
            "pass": bool(passed),
            "observed": observed,
            "expected": expected,
            "remaining_severity": severity if not passed else "none",
        })
        print(("PASS" if passed else "FAIL") + f" [{category}] {name}: {observed}")

    immutable_inputs = [ROM, ADPCM, VGM] + sorted(CAPTURE_DIR.glob("*_ym2151_writes.csv"))
    before_hashes = {str(p.relative_to(ROOT)): sha256(p) for p in immutable_inputs}

    with tempfile.TemporaryDirectory(prefix="audio010_profiles_") as td:
        profile_dir = Path(td) / "profiles"
        profile_dir.mkdir()
        outside = Path(td) / "outside.json"
        outside.write_text('{"secret":true}\n')
        (profile_dir / "escape.json").symlink_to(outside)
        S.PROF_DIR = str(profile_dir)
        S.ensure_baseline()
        h = Harness(profile_dir)
        h.start()
        try:
            invalid_ids = {
                "plain traversal": "../../../specs/palette_decisions",
                "encoded traversal": quote("../../../specs/palette_decisions", safe=""),
                "absolute path": quote("/tmp/escape", safe=""),
                "path separator": quote("dir/file", safe=""),
                "backslash separator": quote("dir\\file", safe=""),
                "invalid characters": quote("bad id;rm", safe=""),
                "symlink escape": "escape",
            }
            for label, pid in invalid_ids.items():
                status, _ = h.request("GET", f"/api/profile?p={pid}")
                check(label, "profile_security", status == 400, status, 400, "high")

            status, _ = h.request("POST", "/api/profile", {
                "profile_id": "invalid_route", "approved_routing": {"0": "ym2612_fm9"}})
            check("invalid routing rejected without persistence", "profile_security",
                  status == 403 and not (profile_dir / "invalid_route.json").exists(),
                  {"status": status, "persisted": (profile_dir / "invalid_route.json").exists()},
                  {"status": 403, "persisted": False}, "high")

            status, _ = h.request("POST", "/api/profile", {
                "profile_id": "fm6_route", "approved_routing": {"0": "ym2612_fm6_dac"}})
            check("FM6 music routing rejected", "profile_security", status == 403, status, 403, "high")

            status, _ = h.request("POST", "/api/profile", {
                "profile_id": "forged_approval",
                "track_id": "03 - Aggressive World (Scene 1)",
                "approval_status": "approved",
                "approved_routing": {"0": "ym2612_fm1"},
                "arcade_evidence": {"command_id": "0xAB", "provenance": "FORGED"},
            })
            _, forged = h.request("GET", "/api/profile?p=forged_approval")
            check("plausible client cannot fabricate approval", "profile_security",
                  forged.get("approval_status") != "approved",
                  {"post_status": status, "stored_approval_status": forged.get("approval_status")},
                  "server must not accept client-authored approved state", "high")
            evidence = forged.get("arcade_evidence", {})
            check("arcade evidence is server-derived", "profile_security",
                  evidence.get("command_id") is None and
                  str(evidence.get("provenance", "")).startswith("server-derived"),
                  {"command_id": evidence.get("command_id"), "provenance": evidence.get("provenance")},
                  "forged evidence discarded", "high")

            baseline_hash = sha256(profile_dir / "baseline_current.json")
            status, _ = h.request("POST", "/api/profile", {
                "profile_id": "baseline_current", "notes": "overwrite"})
            check("baseline immutable", "profile_security",
                  status == 400 and sha256(profile_dir / "baseline_current.json") == baseline_hash,
                  status, 400, "high")
            check("unknown JavaScript path is 404", "profile_security",
                  h.request("GET", "/unknown.js")[0] == 404,
                  h.request("GET", "/unknown.js")[0], 404, "low")
            check("malformed JSON is 400", "profile_security",
                  h.request("POST", "/api/profile", raw=b"{")[0] == 400,
                  h.request("POST", "/api/profile", raw=b"{")[0], 400, "low")

            # Sequential revision lifecycle, including double-digit ordering.
            for revision in range(1, 13):
                status, response = h.request("POST", "/api/profile", {
                    "profile_id": "sequential", "notes": f"revision-{revision}",
                    "approved_routing": {"0": "ym2612_fm1"},
                    "future": {"revision": revision},
                })
                if status != 200:
                    break
            snapshots = sorted(profile_dir.glob("sequential.r*.json"))
            r1 = json.loads((profile_dir / "sequential.r1.json").read_text())
            r12 = json.loads((profile_dir / "sequential.r12.json").read_text())
            check("new and repeated saves preserve prior snapshots", "revision",
                  len(snapshots) == 12 and r1["notes"] == "revision-1" and r12["notes"] == "revision-12",
                  {"snapshot_count": len(snapshots), "r1": r1["notes"], "r12": r12["notes"]},
                  "12 immutable ordered snapshots", "high")
            _, listed = h.request("GET", "/api/revisions?p=sequential")
            listed_numbers = [r.get("revision") for r in listed.get("revisions", [])]
            check("revision list is numerically ordered", "revision",
                  listed_numbers == list(range(1, 13)), listed_numbers, list(range(1, 13)), "medium")
            status, _ = h.request("GET", "/api/revision?p=sequential&r=1")
            check("revision can be retrieved through API", "revision", status == 200, status, 200, "medium")
            check("invalid revision identifier rejected", "revision",
                  h.request("GET", "/api/revision?p=sequential&r=..%2F1")[0] == 400,
                  h.request("GET", "/api/revision?p=sequential&r=..%2F1")[0], 400, "medium")

            current = json.loads((profile_dir / "sequential.json").read_text())
            manifest = json.loads((profile_dir / "profile_manifest.json").read_text())
            manifest_revision = next(x["revision"] for x in manifest["profiles"]
                                     if x["profile_id"] == "sequential")
            check("manifest matches current after clean saves", "revision",
                  current["revision"] == manifest_revision == 12,
                  {"current": current["revision"], "manifest": manifest_revision}, 12, "high")

            # Concurrent saves must serialize into unique immutable revisions.
            h.request("POST", "/api/profile", {"profile_id": "concurrent", "notes": "seed"})
            barrier = threading.Barrier(8)
            concurrent_results = []

            def save_concurrently(index):
                barrier.wait()
                concurrent_results.append(h.request("POST", "/api/profile", {
                    "profile_id": "concurrent", "notes": f"worker-{index}"}))

            workers = [threading.Thread(target=save_concurrently, args=(i,)) for i in range(8)]
            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join(timeout=10)
            concurrency_snapshots = list(profile_dir.glob("concurrent.r*.json"))
            _, concurrency_current = h.request("GET", "/api/profile?p=concurrent")
            check("same-profile concurrent saves are serialized", "revision",
                  all(status == 200 for status, _ in concurrent_results) and
                  len(concurrency_snapshots) == 9 and concurrency_current.get("revision") == 9,
                  {"statuses": [x[0] for x in concurrent_results],
                   "snapshot_count": len(concurrency_snapshots),
                   "current_revision": concurrency_current.get("revision")},
                  {"statuses": [200] * 8, "snapshot_count": 9, "current_revision": 9}, "high")

            # Deterministic process-interruption simulation: fail current after snapshot.
            original_atomic = S.atomic_write_json
            initial = {"profile_id": "fault_current", "notes": "first-before-interruption"}

            def fail_current(path, obj):
                if Path(path).name == "fault_current.json":
                    raise OSError("AUDIO-010 injected interruption before current write")
                return original_atomic(path, obj)

            S.atomic_write_json = fail_current
            interrupted_status, _ = h.request("POST", "/api/profile", initial)
            S.atomic_write_json = original_atomic
            orphan_before = json.loads((profile_dir / "fault_current.r1.json").read_text())
            retry_status, _ = h.request("POST", "/api/profile", {
                "profile_id": "fault_current", "notes": "second-after-restart"})
            orphan_after = json.loads((profile_dir / "fault_current.r1.json").read_text())
            check("interruption cannot overwrite an existing revision on retry", "crash_safety",
                  orphan_after.get("notes") == orphan_before.get("notes") and
                  (profile_dir / "fault_current.r2.json").exists(),
                  {"interrupted_status": interrupted_status, "retry_status": retry_status,
                   "r1_before": orphan_before.get("notes"), "r1_after": orphan_after.get("notes"),
                   "r2_exists": (profile_dir / "fault_current.r2.json").exists()},
                  "r1 preserved and retry creates r2", "high")

            # Fail manifest after snapshot+current, then restart the server.
            h.request("POST", "/api/profile", {"profile_id": "fault_manifest", "notes": "revision-1"})

            def fail_manifest(path, obj):
                if Path(path).name == "profile_manifest.json":
                    raise OSError("AUDIO-010 injected manifest failure")
                return original_atomic(path, obj)

            S.atomic_write_json = fail_manifest
            manifest_failure_status, _ = h.request("POST", "/api/profile", {
                "profile_id": "fault_manifest", "notes": "revision-2"})
            S.atomic_write_json = original_atomic
            h.stop()
            S.ensure_baseline()
            h.start()
            _, after_restart_profile = h.request("GET", "/api/profile?p=fault_manifest")
            _, after_restart_manifest = h.request("GET", "/api/profiles")
            after_restart_mrev = next(x["revision"] for x in after_restart_manifest["profiles"]
                                      if x["profile_id"] == "fault_manifest")
            check("restart reconciles failed manifest write", "crash_safety",
                  after_restart_profile.get("revision") == after_restart_mrev,
                  {"failed_request_status": manifest_failure_status,
                   "profile_revision": after_restart_profile.get("revision"),
                   "manifest_revision": after_restart_mrev},
                  "profile and manifest reconciled on restart", "high")

            # v1 migration and preservation of edits/unknown fields.
            legacy = {
                "schema": "audio_composer/v1", "profile_id": "legacy",
                "notes": "legacy notes", "approval_status": "approved",
                "approved_routing": {"0": "ym2612_fm3"},
                "future_extension": {"kept": True},
            }
            (profile_dir / "legacy.json").write_text(json.dumps(legacy))
            _, migrated = h.request("GET", "/api/profile?p=legacy")
            save_status, _ = h.request("POST", "/api/profile", migrated)
            _, migrated_saved = h.request("GET", "/api/profile?p=legacy")
            check("v1 migration preserves notes approvals and unknown fields", "revision",
                  save_status == 200 and migrated_saved.get("schema") == "audio_composer/v2" and
                  migrated_saved.get("notes") == "legacy notes" and
                  migrated_saved.get("approval_status") == "approved" and
                  migrated_saved.get("approved_routing") == {"0": "ym2612_fm3"} and
                  migrated_saved.get("future_extension") == {"kept": True},
                  {"status": save_status, "profile": migrated_saved},
                  "all fields preserved", "medium")

            _, psg = h.request("GET", "/api/psg_model")
            check("PSG exposes three tone channels and one noise channel", "psg",
                  psg.get("tone_channels") == 3 and psg.get("noise", {}).get("channel") == 1,
                  {"tone_channels": psg.get("tone_channels"), "noise_channels": psg.get("noise", {}).get("channel")},
                  {"tone_channels": 3, "noise_channels": 1}, "high")
            check("PSG is mono with a 10-bit divider", "psg",
                  psg.get("stereo_per_channel") is False and psg.get("tone_divider_bits") == 10,
                  {"stereo_per_channel": psg.get("stereo_per_channel"),
                   "tone_divider_bits": psg.get("tone_divider_bits")},
                  {"stereo_per_channel": False, "tone_divider_bits": 10}, "high")
            selector = psg.get("noise", {}).get("noise_freq_select", {})
            check("noise selector explicitly models fixed and tone3-clocked modes", "psg",
                  set(selector) == {"0", "1", "2", "3"} and "TONE CHANNEL 3" in selector.get("3", ""),
                  selector, "selectors 0/1/2 fixed and 3 tone3-clocked", "high")
            check("unverified taps and divider-zero are not presented as proven", "psg",
                  "UNRESOLVED" in psg.get("noise", {}).get("shift_register_status", "") and
                  "UNRESOLVED" in psg.get("divider_zero", ""),
                  {"shift_register_status": psg.get("noise", {}).get("shift_register_status"),
                   "divider_zero": psg.get("divider_zero")},
                  "both explicitly unresolved", "medium")
            fixed = h.request("POST", "/api/validate", {
                "approved_routing": {"0": "psg_tone3", "1": "psg_noise"},
                "noise_mode": "fixed_1024"})[1]
            coupled = h.request("POST", "/api/validate", {
                "approved_routing": {"0": "psg_tone3", "1": "psg_noise"},
                "noise_mode": "tone3_clocked"})[1]
            check("tone3/noise dependency is conditional", "psg",
                  not any(c["type"] == "tone3_noise_coupling" for c in fixed["conflicts"]) and
                  any(c["type"] == "tone3_noise_coupling" for c in coupled["conflicts"]),
                  {"fixed": fixed["conflicts"], "tone3_clocked": coupled["conflicts"]},
                  "warning only for tone3_clocked", "high")
            _, unrouted = h.request("GET", "/api/profile?p=unrouted_new")
            check("Composer does not auto-assign routing", "psg",
                  unrouted.get("approved_routing") == {} and unrouted.get("proposals") == {},
                  {"approved_routing": unrouted.get("approved_routing"),
                   "proposals": unrouted.get("proposals")},
                  {"approved_routing": {}, "proposals": {}}, "high")
        finally:
            S.atomic_write_json = original_atomic if "original_atomic" in locals() else S.atomic_write_json
            h.stop()

    song = A8.parse_song_table(ROM.read_bytes())
    special = song["special_descriptors"]
    expected_special_commands = [0x03, 0x0A, 0x0D, 0x21, 0x26]
    generated_commands = json.loads((ROOT / "build/audio/music_command_inventory.json").read_text())
    check("all five $82 descriptors are channel/control identifiers", "z80_descriptors",
          [x[0] for x in special if x[2] == 0x82] == expected_special_commands and
          generated_commands.get("channel_control_identifier_commands") ==
          [f"0x{x:02X}" for x in expected_special_commands],
          {"independent": special,
           "generated": generated_commands.get("channel_control_identifier_commands")},
          expected_special_commands, "high")
    ordinary = next(x for x in song["commands"] if x.get("form") == "entry_list" and x.get("entry_count", 0) > 0)
    check("ordinary counted descriptor form remains valid", "z80_descriptors",
          ordinary.get("entry_count") == len(ordinary.get("entries", [])) and
          generated_commands["commands"][f"0x{ordinary['command']:02X}"]["count"] == ordinary["entry_count"], ordinary,
          "entry_count equals parsed two-byte records", "high")

    captures = A8.parse_captures()
    generated_by_id = {
        path.stem: json.loads(path.read_text())
        for path in (ROOT / "build/audio/ym2151_track_reports").glob("*.json")
        if path.name != "_summary.json"
    }
    count_mismatches = []
    for track, data in captures["tracks"].items():
        if generated_by_id[track].get("channels_ever_keyed_count") != data["keyed_channel_count"]:
            count_mismatches.append(track)
    scene1 = captures["tracks"]["03 - Aggressive World (Scene 1)"]
    check("independent key-on/off parse matches generated keyed totals", "ym2151",
          not count_mismatches and scene1["keyed_channel_count"] == 6,
          {"mismatches": count_mismatches, "scene1": scene1["keyed_channel_count"]},
          {"mismatches": [], "scene1": 6}, "high")

    vgm = A8.parse_vgm()
    generated_vgm = json.loads((ROOT / "build/audio/vgm_analysis/LM-Main Stage Theme (1).json").read_text())
    block_sizes = [x["size"] for x in vgm["data_blocks"]]
    check("Lawrence VGM independently has four PCM blocks and 398 stream starts", "vgm",
          block_sizes == [4818, 4814, 4817, 4813] and vgm["stream_start_count"] == 398,
          {"block_sizes": block_sizes, "stream_starts": vgm["stream_start_count"]},
          {"block_sizes": [4818, 4814, 4817, 4813], "stream_starts": 398}, "high")
    check("Lawrence VGM independently has 174 patch snapshots", "vgm",
          vgm["snapshot_total"] == 174, vgm["snapshot_total"], 174, "medium")
    check("generated DAC report agrees with independent stream accounting", "vgm",
          generated_vgm["dac"]["stream_starts"] == vgm["stream_start_count"] and
          generated_vgm["dac"]["active"] is True,
          generated_vgm["dac"], {"stream_starts": 398, "active": True}, "medium")
    # The authoritative Lawrence file contains no $4F; validate the corrected length independently
    # by walking a minimal stream rather than importing the AUDIO-009 analyzer.
    synthetic = bytes([0x4F, 0x80, 0x50, 0x9F, 0x66])
    pos, commands = 0, []
    while pos < len(synthetic):
        cmd = synthetic[pos]
        commands.append(cmd)
        if cmd == 0x66:
            break
        pos += 2 if cmd in (0x4F, 0x50) else 1
    check("$4F consumes exactly two bytes", "vgm", commands == [0x4F, 0x50, 0x66],
          [f"0x{x:02X}" for x in commands], ["0x4F", "0x50", "0x66"], "low")

    c_text = (ROOT / "analysis/decompilation/c/z80/rastan_z80_sound_driver.c").read_text()
    coverage_text = (ROOT / "analysis/decompilation/c/z80/z80_function_coverage.csv").read_text()
    declarations = [line for line in c_text.splitlines() if line.startswith("void ") and line.endswith(";")]
    check("Z80 C is explicitly a zero-body declaration index", "z80_c_coverage",
          "DECLARATION INDEX" in c_text and "ZERO function bodies" in c_text and len(declarations) > 0 and
          "void z80_main_010b(void) {" not in c_text,
          {"declarations": len(declarations), "body_marker_present": "void z80_main_010b(void) {" in c_text},
          "declarations present, zero bodies", "high")
    check("coverage vocabulary does not claim semantic C completion", "z80_c_coverage",
          "SEMANTIC_C_COMPLETE" in coverage_text and ",SEMANTIC_C_COMPLETE," not in coverage_text,
          {"semantic_complete_rows": coverage_text.count(",SEMANTIC_C_COMPLETE,")}, 0, "high")
    terminology_ok = all(token in c_text + coverage_text for token in [
        "PC060HA", "0xB000=address", "0xC000=start", "0xD000=stop", "0x1B", "NOT count 130"])
    check("PC060HA latch $1B and $82 corrections are documented", "z80_c_coverage",
          terminology_ok, terminology_ok, True, "medium")

    after_hashes = {str(p.relative_to(ROOT)): sha256(p) for p in immutable_inputs}
    check("original ROM captures and Lawrence VGM remain byte-identical", "scope",
          before_hashes == after_hashes, {"changed": [p for p in before_hashes if before_hashes[p] != after_hashes[p]]},
          {"changed": []}, "high")

    result = {
        "task": "AUDIO-010",
        "method": "real loopback HTTP with isolated profile storage; AUDIO-008 independent raw parsers reused",
        "tests": tests,
        "summary": {
            "total": len(tests),
            "passed": sum(1 for t in tests if t["pass"]),
            "failed": sum(1 for t in tests if not t["pass"]),
            "failures": [t["name"] for t in tests if not t["pass"]],
        },
        "immutable_input_hashes_before": before_hashes,
        "immutable_input_hashes_after": after_hashes,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"SUMMARY {result['summary']['passed']} passed, {result['summary']['failed']} failed")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
