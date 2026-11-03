#!/usr/bin/env python3
"""AUDIO-008 independent, read-only verification harness.

This deliberately does not import the three Andy audio analyzers.  It parses the
authoritative ROM/capture/VGM inputs independently, then imports only the Audio
Composer server for isolated HTTP behavior tests.  Composer writes are redirected
to a temporary profile tree; production profiles and evidence remain untouched.
"""

from __future__ import annotations

import csv
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import tempfile
import threading
from collections import Counter
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[3]
ROM = ROOT / "build/regions/audiocpu.bin"
ADPCM = ROOT / "build/regions/adpcm.bin"
CAPTURE_DIR = ROOT / "audio/rastan_music_dump/conversion_attempts"
VGM = ROOT / "audio/Inglebard Agressive World Handmade Genesis version/LM-Main Stage Theme (1).vgm"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def le16(data: bytes, off: int) -> int:
    return data[off] | data[off + 1] << 8


def le32(data: bytes, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


def parse_song_table(data: bytes) -> dict:
    commands = []
    invalid_table_ptrs = []
    invalid_subseq_ptrs = []
    direct_commands = []
    special_descriptors = []
    all_subseq = []
    for command in range(0x2C):
        descriptor = le16(data, 0x2300 + command * 2)
        if not 0 <= descriptor < 0x4000:
            invalid_table_ptrs.append([command, descriptor])
            continue
        lead = data[descriptor]
        row = {"command": command, "descriptor": descriptor, "lead": lead}
        if lead >= 0x12:
            # 0x02c3..0x02ca passes this byte directly to 0x02fe; it is not a count.
            row["form"] = "single_descriptor"
            row["channel_or_control_id"] = lead
            special_descriptors.append([command, descriptor, lead])
        else:
            row["form"] = "entry_list"
            row["entry_count"] = lead
            entries = []
            for i in range(lead):
                lo = data[descriptor + 1 + i * 2]
                hi = data[descriptor + 2 + i * 2]
                if hi == 0:
                    entries.append({"direct_command": lo})
                    direct_commands.append([command, i, lo])
                else:
                    ptr = lo | hi << 8
                    first = data[ptr] if 0 <= ptr < len(data) else None
                    entries.append({"subsequence": ptr, "first": first})
                    all_subseq.append(ptr)
                    if not 0 <= ptr < 0x4000 or first is None or first < 0x12:
                        invalid_subseq_ptrs.append([command, i, ptr, first])
            row["entries"] = entries
        commands.append(row)
    return {
        "command_count": len(commands),
        "descriptor_min": min(r["descriptor"] for r in commands),
        "descriptor_max": max(r["descriptor"] for r in commands),
        "special_descriptors": special_descriptors,
        "direct_commands": direct_commands,
        "subsequence_min": min(all_subseq),
        "subsequence_max": max(all_subseq),
        "invalid_table_pointers": invalid_table_ptrs,
        "invalid_subsequence_references": invalid_subseq_ptrs,
        "commands": commands,
    }


def parse_captures() -> dict:
    tracks = {}
    final_algorithms = Counter()
    all_algorithm_writes = Counter()
    for path in sorted(CAPTURE_DIR.glob("*_ym2151_writes.csv")):
        state = [{"algo": None, "feedback": None, "keyons": 0, "keyoffs": 0,
                  "pitches": set(), "first": None, "last": None} for _ in range(8)]
        active = set()
        peak = 0
        noise_enable_writes = 0
        rows = 0
        for row in csv.DictReader(path.open(newline="")):
            rows += 1
            try:
                reg = int(row["register"], 16)
                value = int(row["value"], 16)
                seconds = float(row["seconds"])
            except (KeyError, ValueError):
                continue
            if 0x20 <= reg <= 0x27:
                ch = reg - 0x20
                state[ch]["algo"] = value & 7
                state[ch]["feedback"] = value >> 3 & 7
                all_algorithm_writes[value & 7] += 1
            elif 0x28 <= reg <= 0x2F:
                state[reg - 0x28]["pitches"].add(value)
            elif reg == 0x08:
                ch = value & 7
                mask = value >> 3 & 0xF
                if mask:
                    state[ch]["keyons"] += 1
                    state[ch]["first"] = seconds if state[ch]["first"] is None else state[ch]["first"]
                    state[ch]["last"] = seconds
                    active.add(ch)
                else:
                    state[ch]["keyoffs"] += 1
                    active.discard(ch)
                peak = max(peak, len(active))
            elif reg == 0x0F and value & 0x80:
                noise_enable_writes += 1
        keyed = [i for i, s in enumerate(state) if s["keyons"]]
        for i in keyed:
            final_algorithms[state[i]["algo"]] += 1
        tracks[path.stem.removesuffix("_ym2151_writes")] = {
            "rows": rows,
            "keyed_channels": keyed,
            "keyed_channel_count": len(keyed),
            "peak_simultaneously_keyed_channels": peak,
            "noise_enable_writes": noise_enable_writes,
            "per_channel": {
                str(i): {
                    "keyons": s["keyons"],
                    "keyoffs": s["keyoffs"],
                    "distinct_kc_values": len(s["pitches"]),
                    "active_span_s": round((s["last"] - s["first"]), 6)
                    if s["first"] is not None else 0,
                    "final_algorithm": s["algo"],
                    "final_feedback": s["feedback"],
                }
                for i, s in enumerate(state)
            },
        }
    return {
        "track_count": len(tracks),
        "tracks": tracks,
        "final_algorithm_distribution_over_keyed_channel_tracks": dict(sorted(final_algorithms.items())),
        "all_algorithm_register_writes": dict(sorted(all_algorithm_writes.items())),
    }


class FMState:
    def __init__(self) -> None:
        self.algorithm = None
        self.feedback = None
        self.pan = None
        self.operators = {i: {} for i in range(4)}
        self.last_snapshot = None
        self.snapshots = []
        self.keyons = 0

    def snapshot(self, sample: int) -> None:
        snap = json.dumps({
            "algorithm": self.algorithm,
            "feedback": self.feedback,
            "pan": self.pan,
            "operators": self.operators,
        }, sort_keys=True)
        if snap != self.last_snapshot:
            self.snapshots.append({"sample": sample, "state": json.loads(snap)})
            self.last_snapshot = snap


def parse_vgm() -> dict:
    data = VGM.read_bytes()
    version = le32(data, 0x08)
    rel_data = le32(data, 0x34) if version >= 0x150 else 0
    pos = 0x34 + rel_data if rel_data else 0x40
    fm = {i: FMState() for i in range(1, 7)}
    psg_latch = [0, 0]
    psg_atten = [15, 15, 15, 15]
    psg_first = [None, None, None, None]
    psg_keyons = [0, 0, 0, 0]
    histogram = Counter()
    data_blocks = []
    stream_freqs = []
    stream_starts = 0
    sample = 0
    unsupported = []
    dac_enable_seen = False
    direct_dac_writes = 0
    while pos < len(data):
        cmd = data[pos]
        histogram[cmd] += 1
        if cmd == 0x66:
            pos += 1
            break
        if cmd == 0x50:
            value = data[pos + 1]
            pos += 2
            if value & 0x80:
                ch = value >> 5 & 3
                typ = value >> 4 & 1
                psg_latch[:] = [ch, typ]
                if typ:
                    old = psg_atten[ch]
                    psg_atten[ch] = value & 0xF
                    if old == 15 and psg_atten[ch] != 15:
                        psg_keyons[ch] += 1
                        if psg_first[ch] is None:
                            psg_first[ch] = sample
            continue
        if cmd in (0x52, 0x53):
            reg, value = data[pos + 1], data[pos + 2]
            port = cmd - 0x52
            pos += 3
            base = 1 + port * 3
            if reg == 0x28:
                ch = {0: 1, 1: 2, 2: 3, 4: 4, 5: 5, 6: 6}.get(value & 0xF)
                if ch is not None and value >> 4 & 0xF:
                    fm[ch].keyons += 1
                    fm[ch].snapshot(sample)
            elif reg == 0x2A:
                direct_dac_writes += 1
            elif reg == 0x2B and value & 0x80:
                dac_enable_seen = True
            elif 0x30 <= reg <= 0x9F and reg & 3 != 3:
                ch = base + (reg & 3)
                if ch <= 6:
                    op = reg >> 2 & 3
                    fm[ch].operators[op][f"r{reg & 0xF0:02x}"] = value
            elif 0xB0 <= reg <= 0xB2:
                ch = base + (reg & 3)
                fm[ch].algorithm = value & 7
                fm[ch].feedback = value >> 3 & 7
            elif 0xB4 <= reg <= 0xB6:
                fm[base + (reg & 3)].pan = value
            continue
        if cmd == 0x61:
            sample += le16(data, pos + 1)
            pos += 3
        elif cmd == 0x62:
            sample += 735
            pos += 1
        elif cmd == 0x63:
            sample += 882
            pos += 1
        elif 0x70 <= cmd <= 0x7F:
            sample += (cmd & 0xF) + 1
            pos += 1
        elif 0x80 <= cmd <= 0x8F:
            direct_dac_writes += 1
            sample += cmd & 0xF
            pos += 1
        elif cmd == 0x67:
            if data[pos + 1] != 0x66:
                unsupported.append([pos, cmd, "bad data-block marker"])
                break
            block_type = data[pos + 2]
            size = le32(data, pos + 3)
            data_blocks.append({"type": block_type, "size": size})
            pos += 7 + size
        elif cmd == 0x68:
            pos += 12
        elif cmd == 0xE0:
            pos += 5
        elif cmd == 0x90:
            pos += 5
        elif cmd == 0x91:
            pos += 5
        elif cmd == 0x92:
            stream_freqs.append(le32(data, pos + 2))
            pos += 6
        elif cmd == 0x93:
            stream_starts += 1
            pos += 11
        elif cmd == 0x94:
            pos += 2
        elif cmd == 0x95:
            stream_starts += 1
            pos += 5
        elif cmd == 0x4F:
            pos += 2
        elif cmd in (0x51, 0x54, 0x55):
            pos += 3
        elif 0x30 <= cmd <= 0x3F:
            pos += 2
        elif 0x40 <= cmd <= 0x4E:
            pos += 3 if version >= 0x160 else 2
        else:
            unsupported.append([pos, cmd, "unknown"])
            break
    algo = Counter()
    feedback = Counter()
    snapshot_counts = {}
    for ch, state in fm.items():
        snapshot_counts[str(ch)] = len(state.snapshots)
        for snap in state.snapshots:
            algo[snap["state"]["algorithm"]] += 1
            feedback[snap["state"]["feedback"]] += 1
    return {
        "version": f"{version >> 8}.{version & 0xFF:02d}",
        "ym2612_clock": le32(data, 0x2C),
        "sn76489_clock": le32(data, 0x0C),
        "total_samples_header": le32(data, 0x18),
        "loop_samples_header": le32(data, 0x20),
        "samples_parsed": sample,
        "end_marker_reached": pos <= len(data) and data[pos - 1] == 0x66,
        "unsupported": unsupported,
        "command_histogram": {f"0x{k:02X}": v for k, v in sorted(histogram.items())},
        "fm_keyons": {str(ch): state.keyons for ch, state in fm.items()},
        "fm_snapshot_counts": snapshot_counts,
        "snapshot_total": sum(snapshot_counts.values()),
        "algorithm_distribution": {str(k): v for k, v in sorted(algo.items())},
        "feedback_distribution": {str(k): v for k, v in sorted(feedback.items())},
        "initial_fm123_patch_equal": all(
            fm[i].snapshots and fm[i].snapshots[0]["state"]["operators"] == fm[1].snapshots[0]["state"]["operators"]
            and fm[i].snapshots[0]["state"]["algorithm"] == fm[1].snapshots[0]["state"]["algorithm"]
            and fm[i].snapshots[0]["state"]["feedback"] == fm[1].snapshots[0]["state"]["feedback"]
            for i in (1, 2, 3)
        ),
        "initial_fm123_pan": {str(i): fm[i].snapshots[0]["state"]["pan"] for i in (1, 2, 3)},
        "psg_keyons": {str(i): psg_keyons[i] for i in range(4)},
        "psg_first_seconds": {str(i): round(psg_first[i] / 44100, 6) if psg_first[i] is not None else None for i in range(4)},
        "data_blocks": data_blocks,
        "stream_frequencies": sorted(set(stream_freqs)),
        "stream_start_count": stream_starts,
        "dac_enable_seen": dac_enable_seen,
        "direct_or_0x8n_dac_writes": direct_dac_writes,
    }


def load_composer():
    path = ROOT / "tools/audio_composer/server.py"
    spec = importlib.util.spec_from_file_location("audio008_composer", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def request(port: int, method: str, path: str, body=None, raw=None) -> tuple[int, object]:
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    if raw is not None:
        payload = raw
    elif body is not None:
        payload = json.dumps(body).encode()
    else:
        payload = None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    conn.request(method, path, body=payload, headers=headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    try:
        decoded = json.loads(data)
    except Exception:
        decoded = data.decode(errors="replace")
    return response.status, decoded


def composer_http_audit() -> dict:
    server_module = load_composer()
    with tempfile.TemporaryDirectory(prefix="audio008_composer_") as td:
        root = Path(td)
        profile_dir = root / "analysis/audio/decision_profiles"
        profile_dir.mkdir(parents=True)
        secret = root / "specs/secret.json"
        secret.parent.mkdir(parents=True)
        secret.write_text('{"secret_marker":"PROFILE_TRAVERSAL_REPRODUCED"}\n')
        server_module.PROF_DIR = str(profile_dir)
        server_module.ensure_baseline()
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), server_module.Hd)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        port = httpd.server_address[1]
        try:
            results = {}
            for endpoint in ("/api/inventory", "/api/psg_model", "/api/lawrence",
                             "/api/audition", "/api/profiles", "/api/profile?p=baseline_current"):
                status, _ = request(port, "GET", endpoint)
                results[f"GET {endpoint}"] = status

            valid = server_module.default_profile("valid_test", "03 - Aggressive World (Scene 1)")
            valid["proposals"] = {"0": {"dest": "ym2612_fm1", "rationale": "test"}}
            valid["approved_routing"] = {"0": "ym2612_fm1"}
            valid["approval_status"] = "approved"
            valid["unknown_future_field"] = {"preserve": True}
            status, _ = request(port, "POST", "/api/profile", valid)
            results["valid_save_status"] = status
            status, loaded = request(port, "GET", "/api/profile?p=valid_test")
            results["valid_reload_status"] = status
            results["proposal_approval_separate"] = loaded.get("proposals") != loaded.get("approved_routing")
            results["unknown_field_preserved"] = loaded.get("unknown_future_field") == {"preserve": True}

            fm6 = server_module.default_profile("fm6_test")
            fm6["approved_routing"] = {"0": "ym2612_fm6_dac"}
            results["fm6_rejection_status"] = request(port, "POST", "/api/profile", fm6)[0]
            results["fm6_file_written"] = (profile_dir / "fm6_test.json").exists()

            invalid = server_module.default_profile("invalid_dest_test")
            invalid["approved_routing"] = {"0": "../../production"}
            invalid["approval_status"] = "approved"
            status, response = request(port, "POST", "/api/profile", invalid)
            results["invalid_destination_save_status"] = status
            results["invalid_destination_file_written"] = (profile_dir / "invalid_dest_test.json").exists()
            results["invalid_destination_conflict_returned"] = any(
                c.get("type") == "invalid_dest" for c in response.get("conflicts", []))

            tone3 = server_module.validate_routing({"0": "psg_tone3", "1": "psg_noise"})
            results["tone3_noise_warns_without_noise_mode"] = any(
                c.get("type") == "tone3_noise_coupling" for c in tone3)

            results["malformed_json_status"] = request(port, "POST", "/api/profile", raw=b"{")[0]
            results["post_profile_id_traversal_rejected"] = request(
                port, "POST", "/api/profile", {"profile_id": "../escape"})[0]

            traversal_id = quote("../../../specs/secret", safe="")
            status, traversal = request(port, "GET", f"/api/profile?p={traversal_id}")
            results["get_profile_traversal_status"] = status
            results["get_profile_traversal_disclosed_json"] = traversal.get("secret_marker") == "PROFILE_TRAVERSAL_REPRODUCED"

            results["static_suffix_route_unknown_js_status"] = request(port, "GET", "/not-a-real-file.js")[0]

            overwrite = server_module.default_profile("overwrite_test")
            overwrite["notes"] = "first"
            request(port, "POST", "/api/profile", overwrite)
            overwrite["notes"] = "second"
            request(port, "POST", "/api/profile", overwrite)
            saved = json.loads((profile_dir / "overwrite_test.json").read_text())
            manifest = json.loads((profile_dir / "profile_manifest.json").read_text())
            item = next(p for p in manifest["profiles"] if p["profile_id"] == "overwrite_test")
            results["same_id_overwrites_prior_file"] = saved["notes"] == "second"
            results["manifest_revision_after_two_saves"] = item["revision"]
            results["prior_revision_file_exists"] = any(profile_dir.glob("overwrite_test.*.json"))
            return results
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=5)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", help="optional JSON result path")
    args = parser.parse_args()
    output = {
        "task": "AUDIO-008",
        "inputs": {
            "audiocpu": {"path": str(ROM.relative_to(ROOT)), "bytes": ROM.stat().st_size, "sha256": sha256(ROM)},
            "adpcm": {"path": str(ADPCM.relative_to(ROOT)), "bytes": ADPCM.stat().st_size, "sha256": sha256(ADPCM)},
            "lawrence_vgm": {"path": str(VGM.relative_to(ROOT)), "bytes": VGM.stat().st_size, "sha256": sha256(VGM)},
        },
        "song_table": parse_song_table(ROM.read_bytes()),
        "ym2151_captures": parse_captures(),
        "lawrence_vgm": parse_vgm(),
        "audio_composer_http": composer_http_audit(),
    }
    rendered = json.dumps(output, indent=2, sort_keys=True) + "\n"
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered)
        print(f"wrote {out}")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
