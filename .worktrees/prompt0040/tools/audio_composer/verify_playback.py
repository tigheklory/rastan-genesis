#!/usr/bin/env python3
"""AUDIO-012 — playback integration regression suite. Read-only; no ROM/build; no profile writes.

HTTP-level against an in-process server on an isolated temp PROF_DIR. Independent parsing is used for VGM
checks (not the engine's own output). Features that require the (non-bundled) emulation core are reported
UNAVAILABLE, never as working. Exit 0 = all PASS (UNAVAILABLE items are informational, not failures)."""
import importlib.util, json, os, sys, struct, tempfile, threading, time, hashlib
import urllib.request as ureq, urllib.error
from urllib.parse import quote
from http.server import ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PASS, FAIL, UNAVAIL = [], [], []


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m


S = load(os.path.join(HERE, "server.py"), "audio_composer_server")


def ck(n, c, extra=""):
    (PASS if c else FAIL).append(n)
    print(("PASS " if c else "FAIL ") + n + (("  -> " + str(extra)) if extra and not c else ""))


def unavail(n, why):
    UNAVAIL.append(n); print("UNAVAIL " + n + "  (" + why + ")")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None


TMP = tempfile.mkdtemp(prefix="audio012_prof_")
S.PROF_DIR = TMP; S.ensure_baseline()
httpd = ThreadingHTTPServer(("127.0.0.1", 0), S.Hd); PORT = httpd.server_address[1]
threading.Thread(target=httpd.serve_forever, daemon=True).start(); time.sleep(0.2)
B = "http://127.0.0.1:%d" % PORT


def gj(p):
    try:
        r = ureq.urlopen(B + p); return r.getcode(), json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, {}


def gb(p):
    try:
        r = ureq.urlopen(B + p); return r.getcode(), r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""


def parse_vgm(buf):
    assert buf[:4] == b"Vgm ", "bad magic"
    return {"version": struct.unpack_from("<I", buf, 0x08)[0],
            "ym2151": struct.unpack_from("<I", buf, 0x30)[0],
            "ym2612": struct.unpack_from("<I", buf, 0x2C)[0],
            "total": struct.unpack_from("<I", buf, 0x18)[0]}


# hashes of protected inputs before any playback traffic
prof_before = sha(os.path.join(TMP, "profile_manifest.json"))
base_before = sha(os.path.join(TMP, "baseline_current.json"))
cap_before = sha(os.path.join(ROOT, "audio/rastan_music_dump/conversion_attempts/03 - Aggressive World (Scene 1)_ym2151_writes.csv"))
counter_before = open(os.path.join(ROOT, "build/rastan-direct/build_counter.txt")).read().strip()

try:
    # 1. engine initialization — honest unavailable (no bundled core)
    code, es = gj("/api/engine_status")
    ck("1. engine_status served", code == 200)
    ck("1b. no engine bundled + reason given", es.get("bundled_engine") is False and "MAME" in es.get("reason", ""), es.get("reason"))
    ENGINE = bool(es.get("local_engine_present"))
    if ENGINE:
        c1, _ = gb("/engine/webvgm_player.html"); c2, _ = gb("/engine/backend_vgm.js")
        c3, _ = gb("/engine/scriptprocessor_player.min.js")
        ck("1c. local webVGM engine files served (html+backend+player)", c1 == 200 and c2 == 200 and c3 == 200, (c1, c2, c3))
    else:
        unavail("1c. real engine initialization", "no local engine installed; licensing/toolchain blocker")

    # 2. Lawrence source removed from the tool
    code, _ = gj("/api/vgm?src=lawrence")
    ck("2. Lawrence source removed (rejected)", code == 400, code)
    ps = gj("/api/playback_sources")[1]
    ck("2b. playback sources contain only the arcade captures (no Lawrence)",
       list(ps["sources"].keys()) == ["original_arcade_ym2151"], list(ps["sources"].keys()))

    # 3. valid original YM2151 VGM loading (served)
    code, ab = gb("/api/vgm?src=capture&id=" + quote("03 - Aggressive World (Scene 1)"))
    ck("3. Aggressive World YM2151 VGM served", code == 200 and ab[:4] == b"Vgm ")
    ah = parse_vgm(ab)

    # 4. corrupt/unknown rejection
    code, _ = gj("/api/vgm?src=capture&id=" + quote("../../etc/passwd"))
    ck("4a. traversal/unknown capture id rejected", code == 400, code)
    code, _ = gj("/api/vgm?src=bogus")
    ck("4b. bad src rejected", code == 400, code)

    # 5-6. timing/duration + clock metadata
    import csv
    csvp = os.path.join(ROOT, "audio/rastan_music_dump/conversion_attempts/03 - Aggressive World (Scene 1)_ym2151_writes.csv")
    last = 0
    for row in csv.DictReader(open(csvp, newline="")):
        try: last = int(float(row["sample"]))
        except Exception: pass
    ck("5. Aggressive World duration = last capture sample", ah["total"] == last, (ah["total"], last))
    ck("6. YM2151 VGM clock = 4 MHz", ah["ym2151"] == 4000000, ah["ym2151"])

    # 7. register-write count & order (delegated to the independent capture-VGM validator)
    vcap = load(os.path.join(ROOT, "tools/audio/verify_capture_vgm.py"), "vcap")
    # the validator's own main() prints; here we just assert the generated file round-trips 1:1
    conv = load(os.path.join(ROOT, "tools/audio/ym2151_capture_to_vgm.py"), "conv")
    ev = conv.read_capture(csvp)
    hdr2, ev2, flagged = vcap.parse_vgm_ym2151(ab)
    ck("7. reg-write count & order match capture", len(ev2) == len(ev) and all(
        (ev2[i][1], ev2[i][2]) == (ev[i][1], ev[i][2]) for i in range(len(ev))) and flagged == [], (len(ev2), len(ev)))

    # 11-14,17. engine-dependent transport/mute — explicitly UNAVAILABLE (not faked)
    unavail("11. pause/resume position preservation", "browser-audio behavior; verify by listening")
    unavail("12. stop/restart behavior", "browser-audio behavior; verify by listening")
    unavail("13. loop behavior (engine-driven)", "browser-audio behavior; verify by listening")
    unavail("17. per-chip channel mute/solo", "wothke engine exposes no per-chip mute API; unavailable")

    # 14. repeated loading via endpoint (server side) works + deterministic bytes
    _, ab2 = gb("/api/vgm?src=capture&id=" + quote("03 - Aggressive World (Scene 1)"))
    ck("14. repeated VGM load is byte-identical (no leak/cleanup issue)", ab2 == ab)

    # 15. engine media route serves the capture .vgm (engine present) / honest unavailable (absent)
    if ENGINE:
        cm2, b2 = gb("/engine_media/capture/" + quote("03 - Aggressive World (Scene 1)") + ".vgm")
        ck("15. engine capture .vgm media route serves", cm2 == 200 and b2[:4] == b"Vgm ", cm2)
    else:
        ck("15. default path honestly reports engine unavailable (no fake playback)", es.get("local_engine_present") is False)

    # 16. same-timestamp ordering (converter guarantee)
    v, _ = conv.convert([(5, 0x20, 0x11), (5, 0x28, 0x22), (5, 0x08, 0x78)])
    _, ev3, _ = vcap.parse_vgm_ym2151(v)
    ck("16. same-timestamp event ordering preserved", [(e[1], e[2]) for e in ev3] == [(0x20, 0x11), (0x28, 0x22), (0x08, 0x78)])

    # 18. no profile modification from playback
    ck("18. playback did not modify profile manifest/baseline",
       sha(os.path.join(TMP, "profile_manifest.json")) == prof_before and sha(os.path.join(TMP, "baseline_current.json")) == base_before)

    # 19. no production asset modification
    ck("19a. original capture CSV unchanged", sha(csvp) == cap_before)
    ck("19c. build counter unchanged", open(os.path.join(ROOT, "build/rastan-direct/build_counter.txt")).read().strip() == counter_before)

    # 20. existing Composer functionality intact
    for ep in ["/api/inventory", "/api/psg_model", "/api/profiles", "/api/profile?p=baseline_current"]:
        code, _ = gj(ep); ck("20. existing endpoint still 200: " + ep, code == 200, code)
    code, body = gb("/"); ck("20b. index still served", code == 200 and b"Rastan Audio Composer" in body)
    code, _ = gb("/player_adapter.js"); ck("20c. player adapter served", code == 200)

    # ---- AUDIO-012 STAGE 1: authored-routing Genesis renderer ----
    def post(p, o):
        try:
            r = ureq.urlopen(ureq.Request(B + p, data=json.dumps(o).encode(), headers={"Content-Type": "application/json"}))
            return r.getcode(), json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, (json.load(e) if e.headers.get("Content-Type", "").startswith("application/json") else {})

    TRK = "03 - Aggressive World (Scene 1)"
    fm_routing = {"0": "ym2612_fm1", "1": "ym2612_fm2", "2": "ym2612_fm3", "3": "ym2612_fm4", "4": "ym2612_fm5", "5": "psg_tone1"}
    code, rr = post("/api/render_genesis", {"track": TRK, "approved_routing": fm_routing, "noise_mode": "fixed_1024"})
    ck("R1. authored render ok (YM2612 FM1-5 + PSG)", code == 200 and rr.get("ok") and rr["stats"]["fm_targets"] == [1, 2, 3, 4, 5] and rr["stats"]["psg_targets"] == ["psg_tone1"], (code, rr.get("error")))
    code, av = gb(rr["media_url"])
    import struct as _st

    def cmd_counts(buf):
        from collections import Counter as _C
        o = 0x40; n = len(buf); h = _C()
        while o < n:
            c = buf[o]
            if c == 0x66: break
            h[c] += 1
            o += 3 if c in (0x52, 0x53) else 2 if c == 0x50 else 3 if c == 0x61 else 1
        return h
    ah = cmd_counts(av)
    ck("R2. render emits real YM2612 writes (0x52/0x53)", av[:4] == b"Vgm " and ah[0x52] > 0 and ah[0x53] > 0, dict(ah))
    ck("R3. render emits real PSG writes (0x50) for PSG-routed voice", ah[0x50] > 0, dict(ah))
    ck("R4. authored VGM declares YM2612 + SN76489 clocks", _st.unpack_from("<I", av, 0x2C)[0] == 7670454 and _st.unpack_from("<I", av, 0x0C)[0] == 3579545)
    ck("R5. authored duration preserved (== capture last sample)", _st.unpack_from("<I", av, 0x18)[0] == last, (_st.unpack_from("<I", av, 0x18)[0], last))
    # routing determines output: move CH1 FM2 -> PSG tone2 ; PSG command count must increase, FM port0 change
    alt = dict(fm_routing); alt["1"] = "psg_tone2"
    code, rr2 = post("/api/render_genesis", {"track": TRK, "approved_routing": alt, "noise_mode": "fixed_1024"})
    _, av2 = gb(rr2["media_url"]); ah2 = cmd_counts(av2)
    ck("R6. changing FM->PSG changes the rendered output (audible routing)", rr2["media_url"] != rr["media_url"] and ah2[0x50] > ah[0x50], (ah[0x50], ah2[0x50]))
    ck("R7. PSG-noise routing renders noise channel", post("/api/render_genesis", {"track": TRK, "approved_routing": {"0": "psg_noise"}, "noise_mode": "fixed_1024"})[1]["stats"]["psg_targets"] == ["psg_noise"])
    ck("R8. FM6 render rejected (DAC reserved)", post("/api/render_genesis", {"track": TRK, "approved_routing": {"0": "ym2612_fm6_dac"}})[0] == 403)
    ck("R9. render did NOT modify profiles", sha(os.path.join(TMP, "profile_manifest.json")) == prof_before and sha(os.path.join(TMP, "baseline_current.json")) == base_before)
    ck("R10. render did NOT modify the original capture", sha(csvp) == cap_before)

    def psg_atten_set(buf):
        from collections import Counter as _C
        o = 0x40; n = len(buf); a = _C()
        while o < n:
            c = buf[o]
            if c == 0x66: break
            if c == 0x50:
                b = buf[o + 1]
                if b & 0x80 and ((b >> 5) & 3) == 0 and (b >> 4) & 1 and (b & 0xF) != 15: a[b & 0xF] += 1
                o += 2
            else:
                o += 3 if c in (0x52, 0x53, 0x61) else 1
        return a
    _, rfull = post("/api/render_genesis", {"track": TRK, "approved_routing": {"5": "psg_tone1"}, "levels": {}})
    _, rhalf = post("/api/render_genesis", {"track": TRK, "approved_routing": {"5": "psg_tone1"}, "levels": {"5": 50}})
    _, bfull = gb(rfull["media_url"]); _, bhalf = gb(rhalf["media_url"])
    af, ah = psg_atten_set(bfull), psg_atten_set(bhalf)
    ck("R11. per-channel volume trims PSG (50% => quieter/higher attenuation)",
       af and ah and min(ah.keys()) > min(af.keys()), (dict(af), dict(ah)))
    _, rboost = post("/api/render_genesis", {"track": TRK, "approved_routing": {"5": "psg_tone1"}, "levels": {"5": 200}})
    _, bboost = gb(rboost["media_url"]); ab2 = psg_atten_set(bboost)
    ck("R11b. per-channel volume BOOSTS PSG (200% => louder/lower attenuation)",
       af and ab2 and min(ab2.keys()) < min(af.keys()), (dict(af), dict(ab2)))
    code, rmute = post("/api/render_genesis", {"track": TRK, "approved_routing": {"5": "psg_tone1"}, "levels": {"5": 0}})
    ck("R12. volume 0 mutes the voice (dropped, no PSG target)",
       5 in rmute["stats"]["dropped_channels"] and rmute["stats"]["psg_targets"] == [], rmute["stats"])

    # Per-song independent mappings: track_routings round-trips through save/reload (server preserves it)
    pid = "persong_test"
    tr = {"03 - Aggressive World (Scene 1)": {"approved_routing": {"0": "ym2612_fm1"}, "noise_mode": "fixed_1024"},
          "05 - Re-In-Carnation (Scene 2)": {"approved_routing": {"0": "psg_tone1"}, "noise_mode": "fixed_512"}}
    code, _ = post("/api/profile", {"profile_id": pid, "track_routings": tr})
    _, back = gj("/api/profile?p=" + pid)
    ck("P1. per-song mappings round-trip independently",
       back.get("track_routings", {}).get("03 - Aggressive World (Scene 1)", {}).get("approved_routing") == {"0": "ym2612_fm1"}
       and back.get("track_routings", {}).get("05 - Re-In-Carnation (Scene 2)", {}).get("approved_routing") == {"0": "psg_tone1"},
       back.get("track_routings"))

    # 11(actual-audio) §11: real PCM render from the core — UNAVAILABLE (no bundled engine; not fabricated)
    unavail("AUDIO §11. headless PCM render", "ScriptProcessor/WebAudio render needs a real browser; "
            + ("engine installed -> verify by LISTENING in the Composer" if ENGINE else "no engine installed")
            + "; not faked here")
finally:
    httpd.shutdown()

print("\n%d passed, %d failed, %d unavailable (engine not bundled)" % (len(PASS), len(FAIL), len(UNAVAIL)))
sys.exit(1 if FAIL else 0)
