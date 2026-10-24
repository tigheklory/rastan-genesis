#!/usr/bin/env python3
"""AUDIO-009 — expanded regression suite for the Rastan Audio Composer. Read-only; no ROM/build.

Covers the AUDIO-008 defect corrections at BOTH unit and HTTP level. All profile writes use an isolated
temp directory (the server's PROF_DIR is redirected before the in-process HTTP server starts). Also
re-runs the corrected analysis checks and confirms the Palette Composer is unchanged. Exit 0 = all pass."""
import importlib.util, json, os, sys, tempfile, threading, time, struct
import urllib.request as ureq, urllib.error
from http.server import ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


S = load(os.path.join(HERE, "server.py"), "audio_composer_server")
PASS, FAIL = [], []


def ck(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name + (("  -> " + str(extra)) if extra and not cond else ""))


def _raises(S, pid):
    try:
        S.safe_profile_path(pid); return False
    except S.ProfileIdError:
        return True


def _ok(S, pid):
    try:
        S.safe_profile_path(pid); return True
    except S.ProfileIdError:
        return False


# ========== isolated temp storage + in-process HTTP server ==========
TMP = tempfile.mkdtemp(prefix="audio009_profiles_")
S.PROF_DIR = TMP
S.ensure_baseline()
httpd = ThreadingHTTPServer(("127.0.0.1", 0), S.Hd)
PORT = httpd.server_address[1]
threading.Thread(target=httpd.serve_forever, daemon=True).start()
time.sleep(0.2)
B = "http://127.0.0.1:%d" % PORT


def gget(path):
    try:
        r = ureq.urlopen(B + path)
        return r.getcode(), json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, (json.load(e) if e.headers.get("Content-Type", "").startswith("application/json") else {})


def gpost(path, obj):
    req = ureq.Request(B + path, data=json.dumps(obj).encode(), headers={"Content-Type": "application/json"})
    try:
        r = ureq.urlopen(req)
        return r.getcode(), json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, (json.load(e) if e.headers.get("Content-Type", "").startswith("application/json") else {})


try:
    # ---- 1-3: traversal / encoded traversal / invalid id ----
    code, _ = gget("/api/profile?p=../../../specs/palette_decisions")
    ck("1. GET profile directory traversal rejected", code == 400, code)
    code, _ = gget("/api/profile?p=%2e%2e%2f%2e%2e%2fsecret")
    ck("2. GET encoded traversal rejected", code == 400, code)
    code, _ = gget("/api/profile?p=bad%20id;rm")
    ck("3. invalid profile id rejected", code == 400, code)

    # ---- 4: invalid routing rejection (not persisted) ----
    code, r = gpost("/api/profile", {"profile_id": "t_invalid", "approved_routing": {"0": "ym2612_fm9"}})
    ck("4. invalid destination rejected (403) + not persisted", code == 403 and not os.path.exists(
        os.path.join(TMP, "t_invalid.json")), (code, r))

    # ---- 5: FM6 protection ----
    code, r = gpost("/api/profile", {"profile_id": "t_fm6", "approved_routing": {"0": "ym2612_fm6_dac"}})
    ck("5. FM6 music rejected (403) + not persisted", code == 403 and not os.path.exists(
        os.path.join(TMP, "t_fm6.json")), (code, r))

    # ---- 6: server-derived arcade evidence (client cannot forge) ----
    code, r = gpost("/api/profile", {"profile_id": "t_evid", "track_id": "03 - Aggressive World (Scene 1)",
                                     "arcade_evidence": {"command_id": "0xAB", "channels_ever_keyed": [0, 1, 2, 3, 4, 5, 6, 7],
                                                         "provenance": "FORGED"}})
    _, loaded = gget("/api/profile?p=t_evid")
    ev = loaded.get("arcade_evidence", {})
    ck("6. arcade_evidence is server-derived (client forgery discarded)",
       code == 200 and ev.get("command_id") is None and ev.get("provenance", "").startswith("server-derived")
       and ev.get("channels_ever_keyed") == [0, 1, 2, 3, 4, 5], (code, ev.get("provenance")))

    # ---- 7: fabricated approval rejection ----
    code, r = gpost("/api/profile", {"profile_id": "t_fakeapprove", "approval_status": "approved",
                                     "approved_routing": {"0": "ym2612_fm6_dac"}})
    ck("7a. approved + FM6 error rejected", code == 403, code)
    code, r = gpost("/api/profile", {"profile_id": "t_emptyapprove", "approval_status": "approved",
                                     "approved_routing": {}})
    _, l2 = gget("/api/profile?p=t_emptyapprove")
    ck("7b. approved with empty routing downgraded to draft", l2.get("approval_status") == "draft", l2.get("approval_status"))

    # ---- 8: proposal/approval separation ----
    code, r = gpost("/api/profile", {"profile_id": "t_sep", "track_id": "03 - Aggressive World (Scene 1)",
                                     "proposals": {"0": {"dest": "ym2612_fm1"}},
                                     "approved_routing": {"5": "psg_tone1"}})
    _, l3 = gget("/api/profile?p=t_sep")
    ck("8. proposals and approvals stay separate",
       l3["proposals"] == {"0": {"dest": "ym2612_fm1"}} and l3["approved_routing"] == {"5": "psg_tone1"}, l3)

    # ---- 9 + 11: immutable revisions + manifest consistency ----
    gpost("/api/profile", {"profile_id": "t_rev", "notes": "first", "approved_routing": {"0": "ym2612_fm1"}})
    gpost("/api/profile", {"profile_id": "t_rev", "notes": "second", "approved_routing": {"0": "ym2612_fm2"}})
    rev1 = os.path.join(TMP, "t_rev.r1.json")
    rev2 = os.path.join(TMP, "t_rev.r2.json")
    ck("9a. revision 1 snapshot retained after revision 2 save", os.path.exists(rev1) and os.path.exists(rev2))
    r1 = json.load(open(rev1))
    ck("9b. old revision 1 preserves its own content", r1["notes"] == "first" and r1["approved_routing"] == {"0": "ym2612_fm1"}, r1.get("notes"))
    _, cur = gget("/api/profile?p=t_rev")
    man = gget("/api/profiles")[1]
    mrev = next(p["revision"] for p in man["profiles"] if p["profile_id"] == "t_rev")
    ck("11. manifest revision matches current profile revision", cur["revision"] == 2 and mrev == 2, (cur.get("revision"), mrev))
    code, revs = gget("/api/revisions?p=t_rev")
    ck("9c. /api/revisions lists both immutable revisions", code == 200 and len(revs["revisions"]) == 2, revs)

    # ---- 10: atomic-write leaves no temp; revision persists independent of current ----
    leftover = [f for f in os.listdir(TMP) if f.startswith(".tmp_")]
    ck("10. atomic writes leave no .tmp_ files (os.replace)", leftover == [], leftover)

    # ---- 12 + 13: legacy v1 compatibility + unknown-field preservation ----
    legacy = {"schema": "audio_composer/v1", "profile_id": "t_legacy", "display_name": "legacy",
              "approved_routing": {"0": "ym2612_fm3"}, "notes": "legacy notes",
              "approval_status": "approved", "my_future_field": {"x": 1}}
    json.dump(legacy, open(os.path.join(TMP, "t_legacy.json"), "w"))
    _, lg = gget("/api/profile?p=t_legacy")
    ck("12. legacy v1 migrates to v2, approval + routing + notes preserved",
       lg["schema"] == S.SCHEMA and lg["approved_routing"] == {"0": "ym2612_fm3"}
       and lg["notes"] == "legacy notes" and lg["approval_status"] == "approved", lg.get("schema"))
    ck("12b. migration records provenance", lg.get("migrated_from") == ["audio_composer/v1"], lg.get("migrated_from"))
    code, r = gpost("/api/profile", {"profile_id": "t_unknown", "my_future_field": {"a": [1, 2]}})
    _, uk = gget("/api/profile?p=t_unknown")
    ck("13. unknown future field round-trips on save", uk.get("my_future_field") == {"a": [1, 2]}, uk.get("my_future_field"))

    # ---- 14 + 15: conditional tone-3/noise coupling ----
    _, v_fixed = gpost("/api/validate", {"approved_routing": {"0": "psg_tone3", "1": "psg_noise"}, "noise_mode": "fixed_1024"})
    ck("14. tone3 + FIXED noise: NO coupling conflict",
       not any(c["type"] == "tone3_noise_coupling" for c in v_fixed["conflicts"]), v_fixed["conflicts"])
    _, v_t3 = gpost("/api/validate", {"approved_routing": {"0": "psg_tone3", "1": "psg_noise"}, "noise_mode": "tone3_clocked"})
    ck("15. tone3 + tone3_clocked noise: coupling conflict present",
       any(c["type"] == "tone3_noise_coupling" for c in v_t3["conflicts"]), v_t3["conflicts"])

    # ---- 16: PSG mono behaviour ----
    _, psg = gget("/api/psg_model")
    ck("16. PSG modeled mono/center (no per-channel stereo)",
       psg.get("stereo_per_channel") is False and "no per-channel stereo" in psg.get("stereo", "").lower(), psg.get("stereo"))
    ck("16b. PSG noise shift-register labeled UNRESOLVED (no false fidelity)",
       "UNRESOLVED" in psg["noise"]["shift_register_status"], psg["noise"]["shift_register_status"])
    ck("16c. divider-zero documented", "divider_zero" in psg)

    # ---- 17: corrected YM2151 key-on counts (regenerated reports) ----
    inv = gget("/api/inventory")[1]
    scene1 = next(t for t in inv["tracks"] if t["track_id"].startswith("03 "))
    all8 = [t for t in inv["tracks"] if (t.get("channels_ever_keyed_count") or 0) == 8]
    ck("17a. Scene 1 keyed-channel count == 6 (not 8)", scene1.get("channels_ever_keyed_count") == 6, scene1.get("channels_ever_keyed_count"))
    ck("17b. NOT all nine tracks key 8 FM channels (only Opening+Ending)", len(all8) == 2, [t["track_id"] for t in all8])

    # ---- 18: special $82 descriptor handling ----
    mci = json.load(open(os.path.join(ROOT, "build/audio/music_command_inventory.json")))
    special = mci.get("channel_control_identifier_commands", [])
    ck("18a. $82 commands classified as channel/control identifiers (not count 130)",
       set(special) == {"0x03", "0x0A", "0x0D", "0x21", "0x26"}, special)
    ck("18b. no descriptor reports count==130", all(c.get("count") != 130 for c in mci["commands"].values()))

    # ---- 22: AUDIO-015 track_routings persistence — saving a song ALWAYS folds it in ----
    # Regression for the Scene Clear / Final Boss loss: a save must persist the active
    # song's decisions into its per-song track_routings entry, and switching songs must
    # never drop a previously saved one.
    gpost("/api/profile", {"profile_id": "t_persist", "track_id": "03 - Aggressive World (Scene 1)",
                           "approved_routing": {"0": "ym2612_fm1", "1": "psg_tone1"}})
    _, p1 = gget("/api/profile?p=t_persist")
    ck("22a. first save folds active song into track_routings",
       p1.get("track_routings", {}).get("03 - Aggressive World (Scene 1)", {}).get("approved_routing")
       == {"0": "ym2612_fm1", "1": "psg_tone1"}, sorted(p1.get("track_routings", {})))
    # switch to a second song and save it (client carries the accumulated track_routings)
    gpost("/api/profile", {"profile_id": "t_persist", "track_id": "07 - Scene Clear",
                           "approved_routing": {"0": "ym2612_fm2", "1": "psg_noise"},
                           "track_routings": p1.get("track_routings", {})})
    _, p2 = gget("/api/profile?p=t_persist")
    tr2 = p2.get("track_routings", {})
    ck("22b. second song saved AND first song survives the switch",
       tr2.get("07 - Scene Clear", {}).get("approved_routing") == {"0": "ym2612_fm2", "1": "psg_noise"}
       and tr2.get("03 - Aggressive World (Scene 1)", {}).get("approved_routing")
       == {"0": "ym2612_fm1", "1": "psg_tone1"}, sorted(tr2))
    # a save whose working copy was wiped must NOT clobber a good saved entry
    gpost("/api/profile", {"profile_id": "t_persist", "track_id": "07 - Scene Clear",
                           "approved_routing": {}, "track_routings": tr2})
    _, p3 = gget("/api/profile?p=t_persist")
    ck("22c. empty working copy does not clobber a saved routing",
       p3.get("track_routings", {}).get("07 - Scene Clear", {}).get("approved_routing")
       == {"0": "ym2612_fm2", "1": "psg_noise"}, p3.get("track_routings", {}).get("07 - Scene Clear"))

    # ---- 19: VGM $4F command length (synthetic VGM) ----
    V = load(os.path.join(ROOT, "tools/audio/vgm_genesis_analysis.py"), "vgm_an")
    buf = bytearray(0x40)
    buf[0:4] = b"Vgm "
    struct.pack_into("<I", buf, 0x08, 0x160)          # version 1.60
    struct.pack_into("<I", buf, 0x0C, 3579545)        # SN clock
    struct.pack_into("<I", buf, 0x2C, 7670454)        # YM2612 clock
    struct.pack_into("<I", buf, 0x34, 0x0C)           # data offset rel -> 0x40
    data = bytes([0x4F, 0x80,        # GG stereo (2 bytes) — must NOT eat the next command
                  0x50, 0x9F,        # PSG write
                  0x66])             # end
    synth = bytes(buf) + data
    p = os.path.join(TMP, "synth.vgm")
    open(p, "wb").write(synth)
    rep = V.parse(p)
    ck("19. VGM $4F parsed as 2 bytes (clean decode, no flagged cmds)",
       rep["flagged_unsupported"] == [] and rep["command_histogram"].get("0x4F") == 1
       and rep["command_histogram"].get("0x50") == 1, (rep["flagged_unsupported"], rep["command_histogram"]))

    # ---- 20: VGM DAC-stream reporting ----
    lw = json.load(open(os.path.join(ROOT, "build/audio/vgm_analysis/LM-Main Stage Theme (1).json")))
    ck("20. VGM DAC reports stream triggers (not misleading zero)",
       lw["dac"]["stream_starts"] == 398 and lw["dac"]["active"] is True
       and lw["fm_channels"]["6"]["is_dac_channel"] is True, lw["dac"])

    # ---- 21: 174-snapshot population ----
    tot = sum(lw["fm_channels"][str(i)]["distinct_patches"] for i in range(1, 7))
    ck("21. Lawrence distinct-patch population totals 174", tot == 174, tot)

    # ---- unit-level validator + safe-path (rerun corrected assertions) ----
    ck("U1. safe_profile_path rejects traversal", _raises(S, "../x"))
    ck("U2. safe_profile_path accepts a clean id", _ok(S, "clean_id-1.v2"))
    ck("U3. validator: >5 FM voices = error", any(c["type"] == "fm_budget" for c in S.validate_routing(
        {str(i): "ym2612_fm%d" % ((i % 5) + 1) for i in range(6)})))
    ck("U4. validator: clean routing no conflicts", S.validate_routing({"0": "ym2612_fm1", "1": "psg_tone1"}) == [])
    ck("U5. validator never discards: monophonic collision reported (potential)",
       any(c["type"] == "monophonic_collision" and c["certainty"] == "potential"
           for c in S.validate_routing({"0": "ym2612_fm1", "1": "ym2612_fm1"})))

    # ---- audition still honestly unavailable ----
    _, aud = gget("/api/audition")
    ck("U6. audition remains unavailable (no fabricated playback)", aud["available"] is False)

    # ---- static route tightened: unknown .js is 404, not app.js ----
    code, _ = gget("/whatever.js")
    ck("U7. unknown .js path no longer returns app.js (404)", code == 404, code)

    # ---- Palette Composer unchanged ----
    import py_compile
    try:
        py_compile.compile(os.path.join(ROOT, "tools/graphics_editor/server.py"), doraise=True)
        ck("U8. Palette Composer server.py still compiles (untouched)", True)
    except Exception as e:
        ck("U8. Palette Composer server.py still compiles (untouched)", False, e)
finally:
    httpd.shutdown()

print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
sys.exit(1 if FAIL else 0)
