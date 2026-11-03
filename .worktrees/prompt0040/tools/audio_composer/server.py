#!/usr/bin/env python3
"""RG-006 / AUDIO-006 — Rastan Audio Composer (Phase 1) server. DEVELOPMENT TOOL ONLY.

Standalone browser-based editor for exploring the ORIGINAL ARCADE Rastan music and making configurable,
auditable Genesis FM/PSG routing decisions. Modeled on tools/graphics_editor/ (read-only evidence oracle
+ editable per-track JSON decision profiles; baseline immutable; generated data kept separate from source).

HARD RULES honored here:
  * NO production Z80/68000 ASM, ROM, build-number, or driver change. Nothing is rebuilt.
  * Original arcade captures and ROMs are READ-ONLY; saving a profile touches only
    analysis/audio/decision_profiles/.
  * NO instrument is auto-assigned to FM or PSG. The server never stores a proposal as an approved
    decision; only an explicit user approval does.
  * FM6 is a reserved DAC resource; the server rejects any attempt to route music to FM6.
  * AUDIO-003 sequence data is NOT decoded -> per-note/time-dependent evidence is absent; the inventory
    marks this and never fabricates an instrument or a capture->command-ID mapping.
  * Audition is UNAVAILABLE in Phase 1 (no validated emulator render); the contract exists, playback is
    explicitly reported unavailable. No oscillator audio is presented as a faithful reference.
"""
import json, os, re, csv, glob, time, tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, quote, unquote

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HERE = os.path.dirname(__file__)
CAP = os.path.join(ROOT, "audio/rastan_music_dump/conversion_attempts")
FMPSG = os.path.join(ROOT, "build/audio/fm_psg_analysis")
YMREP = os.path.join(ROOT, "build/audio/ym2151_track_reports")
MCI = os.path.join(ROOT, "build/audio/music_command_inventory.json")
VGM = os.path.join(ROOT, "build/audio/vgm_analysis")
PROF_DIR = os.path.join(ROOT, "analysis/audio/decision_profiles")
os.makedirs(PROF_DIR, exist_ok=True)

# ---- AUDIO-012 PLAYBACK (read-only; isolated from all profile/approval/manifest/revision code) ----
CAPVGM = os.path.join(ROOT, "build/audio/capture_vgm")          # first-party capture->VGM artifacts
LAWRENCE_VGM = os.path.join(ROOT, "audio/Inglebard Agressive World Handmade Genesis version",
                            "LM-Main Stage Theme (1).vgm")
# Optional, USER-SUPPLIED, git-ignored local emulation engine (e.g. a webVGM build the user is authorized
# to use). NOT redistributed in this repo: the webVGM/VGMPlay cores are MAME-licensed / GPL-family and
# were NOT imported (see docs/design/Andy_AUDIO012_webvgm_audio_composer_integration.md).
ENGINE_DIR = os.path.join(HERE, "engine")
ENGINE_FILE_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def playback_sources():
    """Read-only list of playable sources (original-arcade capture VGMs). NO routing/profile interaction."""
    caps = []
    for stem, nice in CAPTURE_TRACKS:
        vp = os.path.join(CAPVGM, stem + ".vgm")
        caps.append({"id": stem, "name": nice, "kind": "original_arcade_ym2151",
                     "vgm_available": os.path.exists(vp),
                     "vgm_url": "/api/vgm?src=capture&id=" + quote(stem),
                     "engine_media_url": "/engine_media/capture/" + quote(stem) + ".vgm",
                     "provenance": "first-party deterministic conversion of the ORIGINAL ARCADE YM2151 "
                                   "capture (tools/audio/ym2151_capture_to_vgm.py); NOT an auto-converted "
                                   "Genesis version."})
    return {
        "engine": engine_status(),
        "sources": {
            "original_arcade_ym2151": {"label": "Original Arcade — YM2151", "tracks": caps},
        },
    }


_RENDER_MOD = None
GENESIS_CACHE = {}          # token -> vgm bytes (in-memory, session-scoped; never touches profiles/ROM)


def _render_mod():
    global _RENDER_MOD
    if _RENDER_MOD is None:
        import importlib.util
        p = os.path.join(ROOT, "tools/audio/render_genesis_vgm.py")
        spec = importlib.util.spec_from_file_location("render_genesis_vgm", p)
        _RENDER_MOD = importlib.util.module_from_spec(spec); spec.loader.exec_module(_RENDER_MOD)
    return _RENDER_MOD


def render_genesis(track_id, approved_routing, noise_mode="fixed_1024", levels=None):
    """Render an authored Genesis (YM2612+PSG) VGM from a capture + routing + per-channel volume. Returns
    (token, stats) or (None, error). All inputs come from the request, NOT from any stored profile."""
    if track_id not in [s for s, _ in CAPTURE_TRACKS]:
        return None, "unknown track"
    cap = os.path.join(CAP, track_id + "_ym2151_writes.csv")
    if not os.path.exists(cap):
        return None, "capture not found"
    rm = _render_mod()
    vgm, stats = rm.render(rm.read_capture(cap), approved_routing or {}, noise_mode or "fixed_1024", levels or {})
    import hashlib
    token = hashlib.sha256((track_id + json.dumps(approved_routing, sort_keys=True) + str(noise_mode)
                            + json.dumps(levels or {}, sort_keys=True)).encode()).hexdigest()[:16]
    GENESIS_CACHE[token] = vgm
    return token, stats


def engine_status():
    """Report whether a USER-SUPPLIED local engine is present. The repo bundles NO emulation core."""
    present = os.path.isdir(ENGINE_DIR) and any(
        os.path.isfile(os.path.join(ENGINE_DIR, f)) for f in (os.listdir(ENGINE_DIR) if os.path.isdir(ENGINE_DIR) else []))
    return {
        "bundled_engine": False,
        "local_engine_present": present,
        "reason": "No chip-emulation core is bundled. The named engine (wothke webVGM / VGMPlay 0.40.9) "
                  "uses MAME-licensed YM2151/YM2612/SN76489 cores (non-commercial, GPL-incompatible) and "
                  "could not be redistributed into this repo; there is also no emscripten toolchain here "
                  "to rebuild a clean alternative. See the AUDIO-012 report.",
        "how_to_enable_real_playback": "Place an authorized local VGM engine build in tools/audio_composer/"
                  "engine/ (git-ignored, not redistributed). The player adapter will use it automatically. "
                  "Otherwise, open/download the VGM and play it in your existing webVGM.",
        "entry_candidates": sorted(f for f in (os.listdir(ENGINE_DIR) if os.path.isdir(ENGINE_DIR) else [])
                                   if ENGINE_FILE_RE.match(f)),
    }

SCHEMA = "audio_composer/v2"          # AUDIO-009: v1 -> v2 migration (noise selector, revisions, server evidence)
LEGACY_SCHEMAS = ("audio_composer/v1",)

# AUDIO-009 §3A: a profile ID is a single path segment of a strict allowlist, never a filesystem path.
PROFILE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class ProfileIdError(ValueError):
    pass


def safe_profile_path(pid, suffix=".json"):
    """Return an absolute path strictly contained in PROF_DIR for a validated profile ID, or raise.
    Rejects empty, non-str, traversal (.., encoded), separators, absolute paths, unexpected names, and
    any realpath that escapes PROF_DIR (symlink-safe)."""
    if not isinstance(pid, str) or not PROFILE_ID_RE.match(pid):
        raise ProfileIdError("invalid profile id")
    if pid == ".." or pid.startswith(".") and pid not in (".",) and ".." in pid:
        raise ProfileIdError("invalid profile id")
    if "/" in pid or "\\" in pid or "\x00" in pid or os.path.isabs(pid):
        raise ProfileIdError("invalid profile id")
    base = os.path.realpath(PROF_DIR)
    full = os.path.realpath(os.path.join(base, pid + suffix))
    if full != os.path.join(base, pid + suffix) or os.path.dirname(full) != base:
        raise ProfileIdError("profile id escapes profile directory")
    return full

# Genesis destinations the user may route a source channel to. FM6 is DAC-reserved (not musically routable).
MUSIC_DESTS = ["ym2612_fm1", "ym2612_fm2", "ym2612_fm3", "ym2612_fm4", "ym2612_fm5",
               "psg_tone1", "psg_tone2", "psg_tone3", "psg_noise", "unassigned"]
FM_MUSIC = {"ym2612_fm1", "ym2612_fm2", "ym2612_fm3", "ym2612_fm4", "ym2612_fm5"}
PSG_TONES = {"psg_tone1", "psg_tone2", "psg_tone3"}
RESERVED_DAC = "ym2612_fm6_dac"   # shown read-only; music may never be assigned here


def loadj(p, d=None):
    try:
        return json.load(open(p))
    except Exception:
        return d


# ---- Genesis SN76489 PSG hardware model (for the validator + the future audition engine) ----------------
# Values follow the Sega Retro SN76489 page + the TI SN76489 application manual, adapted to the Genesis
# (Sega VDP) PSG. Marked provenance so the UI never over-claims. Genesis clock = 3,579,545 Hz (NTSC).
def psg_model():
    clk = 3579545
    return {
        "chip": "SN76489-class (Sega VDP integrated PSG)",
        "clock_hz": clk,
        "provenance": "Sega Retro SN76489 + TI SN76489 app manual; Genesis NTSC clock. "
                      "Values MODELED for validation; not yet hardware-reverified in this repo.",
        "tone_channels": 3,
        "duty": "50% square only (NO selectable duty — distinct from the NES APU pulse 12.5/25/50/75%)",
        "tone_divider_bits": 10,
        "tone_divider_range": [1, 1023],
        "tone_freq_formula": "f = clock / (32 * n), n = 1..1023",
        "tone_freq_hz_range": [round(clk / (32 * 1023), 2), round(clk / (32 * 1), 2)],
        "tone_freq_hz_musical_floor": round(clk / (32 * 1023), 2),
        "divider_zero": "AUDIO-009: a written divider of 0 is a documented edge case. On the Sega VDP PSG "
                        "n=0 is widely documented to behave as n=1 (not n=0x400 as on some TI parts). "
                        "Marked UNRESOLVED-for-this-target until confirmed against an authoritative "
                        "Genesis hardware/test-vector source; the Composer does not emit n=0.",
        "attenuation_bits": 4,
        "attenuation_step_db": 2,
        "attenuation_levels": 16,
        "attenuation_note": "0 = full volume, 15 = silent (channel off)",
        "noise": {
            "channel": 1,
            "shift_register_bits": 16,
            "shift_register_status": "UNRESOLVED taps/period for this target: the Genesis/Sega VDP PSG is "
                                     "commonly cited as 16-bit vs the TI 15-bit, but exact XOR taps and the "
                                     "periodic-noise period are NOT yet pinned to an authoritative hardware "
                                     "or known-good emulator test vector in this repo. Do not assert fidelity.",
            "white": {"mode": "LFSR white noise", "taps_modeled": "UNRESOLVED (candidate bits 0,3 — unverified)"},
            "periodic": {"mode": "periodic (tonal) noise", "period_modeled": "UNRESOLVED (candidate 16 — unverified)"},
            "noise_freq_select": {
                "0": "clock/512 (fixed)",
                "1": "clock/1024 (fixed)",
                "2": "clock/2048 (fixed)",
                "3": "driven by TONE CHANNEL 3 frequency (COUPLES noise pitch to tone 3)"},
            "tone3_coupling": "ONLY when noise freq-select = 3 is the noise clock tone channel 3's "
                              "frequency; in that mode tone 3 and noise pitch are not independent. "
                              "Fixed selects 0/1/2 coexist with tone 3 WITHOUT coupling."},
        # AUDIO-009 §4 / Cody claim 42: the Genesis VDP PSG has NO per-channel stereo latch. Stereo control
        # on the Genesis is part of the YM2612 FM/DAC path, not the VDP PSG. Treat PSG as mono/center.
        "stereo": "mono / center — the Genesis VDP PSG has no per-channel stereo latch (stereo belongs to "
                  "the YM2612 FM/DAC path). No per-PSG-channel pan is modeled.",
        "stereo_per_channel": False,
        "envelope": "NONE in hardware — attack/decay/vibrato/arp must be driver-written per tick.",
    }


# ---- ORIGINAL ARCADE track inventory (captures + fm_psg_analysis + ym2151 reports) ----------------------
CAPTURE_TRACKS = [
    ("01 - Credit", "Credit"),
    ("02 - Broken The Promises (Opening)", "Opening"),
    ("03 - Aggressive World (Scene 1)", "Scene 1 (Aggressive World)"),
    ("04 - Bad Bible (Name Regist)", "Name Registration"),
    ("05 - Re-In-Carnation (Scene 2)", "Scene 2 (Re-In-Carnation)"),
    ("06 - The Devil Boss Carnival (Scene 3 Boss)", "Scene 3 Boss"),
    ("07 - Scene Clear", "Scene Clear"),
    ("08 - Final Destroy (Scene 3 Round 6 Boss)", "Final Boss"),
    ("09 - The Man Of Saga (Ending)", "Ending"),
]


def track_inventory():
    tracks = []
    for stem, nice in CAPTURE_TRACKS:
        fm = loadj(os.path.join(FMPSG, stem + ".json"), {})
        ym = loadj(os.path.join(YMREP, stem + ".json"), {})
        chans = []
        fc = fm.get("channels", {})
        for c in range(8):
            cc = fc.get(str(c), {})
            chans.append({
                "ch": c,
                "role": cc.get("role", "unknown"),
                "keyon": cc.get("keyon", 0),
                "distinct_pitches": cc.get("distinct_pitches", 0),
                "algorithm": cc.get("algorithm"),
                "feedback": cc.get("feedback"),
                "carrier_operators": cc.get("carrier_operators"),
                "psg_candidacy_inferred": cc.get("psg_candidacy_inferred", "unknown"),
            })
        tracks.append({
            "track_id": stem,
            "musical_name": nice,
            "capture_file": "audio/rastan_music_dump/conversion_attempts/%s_ym2151_writes.csv" % stem,
            "capture_available": os.path.exists(os.path.join(CAP, stem + "_ym2151_writes.csv")),
            "command_id": None,   # UNRESOLVED — never inferred from the filename
            "command_id_provenance": "UNRESOLVED: capture is named by musical identity, NOT proven to a "
                                     "Z80 command byte (AUDIO-002). Do not treat as a verified command ID.",
            # AUDIO-009 (Cody claim 24/25): report KEYED-channel OCCUPANCY, not "voices". These are the
            # corrected ym2151 metrics (key-offs/KC writes no longer inflate "used"); occupancy does NOT
            # prove audible polyphony. "sustained" is the documented heuristic.
            "channels_ever_keyed": ym.get("channels_ever_keyed"),
            "channels_ever_keyed_count": ym.get("channels_ever_keyed_count"),
            "peak_simultaneously_keyed": ym.get("peak_simultaneously_keyed"),
            "sustained_channels_heuristic": ym.get("sustained_channels_heuristic"),
            "sustained_voice_count_heuristic": fm.get("musical_voice_count"),
            "occupancy_note": "Keyed-channel occupancy is NOT proof of audible polyphony or musical-voice "
                              "identity; musical identity needs AUDIO-003.",
            "channels": chans,
            "analysis_source": "build/audio/fm_psg_analysis + ym2151_track_reports (capture-derived)",
        })
    return tracks


def inventory():
    mci = loadj(MCI, {})
    return {
        "schema": SCHEMA,
        "baseline_note": "ORIGINAL ARCADE music is authoritative. Instrument identity is capture-derived "
                         "(the actual programmed YM2151 patch state), NOT from the un-decoded ROM "
                         "instrument table.",
        "audio003_status": {
            "decoded": False,
            "limitation": "AUDIO-003 sequence decoding is NOT complete: no per-note event stream, no "
                          "ROM instrument-table identity, no sample map. Per-channel data below is "
                          "capture-derived summary only; time-dependent/instrument-level evidence is absent.",
        },
        "tracks": track_inventory(),
        "command_descriptors": mci.get("commands", {}),
        "command_to_track_name": mci.get("command_to_track_name"),
        "deep_fm_finding": "AUDIO-004: arcade music is uniformly DEEP FM (YM2151 algo 1-2, high feedback); "
                           "no natural PSG-candidate voices. PSG use is a budget/arrangement decision.",
    }


# ---- decision profile schema + conflict validator -------------------------------------------------------
def default_profile(pid, track_id=None):
    arcade_channels = 8
    return {
        "schema": SCHEMA,
        "profile_id": pid,
        "display_name": "Baseline (immutable)" if pid == "baseline_current" else pid,
        "immutable": pid == "baseline_current",
        "parent": None if pid == "baseline_current" else "baseline_current",
        "track_id": track_id,
        "source": {
            "rom": "build/regions/audiocpu.bin (b04-19.49)",
            "capture_dir": "audio/rastan_music_dump/conversion_attempts",
            "analysis_version": "AUDIO-002/004 capture-derived; AUDIO-003 NOT decoded",
        },
        # THREE SEPARATED LAYERS (never conflated):
        # arcade_evidence is SERVER-DERIVED (read-only) from the analysis artifacts — NOT client-authored.
        "arcade_evidence": server_arcade_evidence(track_id),
        "proposals": {},                 # arcade_ch(str) -> {dest, rationale, evidence}  (PROPOSED, not approved)
        "approved_routing": {},          # arcade_ch(str) -> dest   (user-approved ONLY)
        "noise_mode": "fixed_1024",      # PSG noise-frequency selector (fixed_512/1024/2048 | tone3_clocked)
        "instrument_overrides": {},      # arcade_ch(str) -> {ym2612:{...}, psg:{...}}  (Phase-1 data model; editing deferred)
        "time_dependent_routing": [],    # [{from_s,to_s, routing:{arcade_ch:dest}}]  (model present; UI deferred)
        "conflicts": [],                 # last validator result (informational)
        "notes": "",
        "approval_status": "draft",      # draft | proposed | approved
        "revision": 0,
        "reserved_dac": RESERVED_DAC,
        "music_destinations": MUSIC_DESTS,
        "arcade_channel_count": arcade_channels,
    }


def server_arcade_evidence(track_id):
    """AUDIO-009 §3C: build the factual arcade-evidence snapshot ON THE SERVER from trusted analysis
    artifacts. Client-supplied arcade_evidence is never trusted; this replaces it on load and save."""
    if not track_id:
        return {}
    t = next((x for x in track_inventory() if x["track_id"] == track_id), None)
    if not t:
        return {"track_id": track_id, "status": "no matching capture/analysis"}
    return {
        "track_id": t["track_id"],
        "musical_name": t["musical_name"],
        "command_id": None,                       # UNRESOLVED; never inferred
        "channels_ever_keyed": t.get("channels_ever_keyed"),
        "peak_simultaneously_keyed": t.get("peak_simultaneously_keyed"),
        "sustained_channels_heuristic": t.get("sustained_channels_heuristic"),
        "channels": t.get("channels"),
        "provenance": "server-derived from build/audio/fm_psg_analysis + ym2151_track_reports; "
                      "capture-derived, AUDIO-003 not decoded; occupancy != audible polyphony.",
    }


def atomic_write_json(path, obj):
    """Write JSON atomically: temp file in the same dir + os.replace (atomic on POSIX)."""
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_", suffix=".json")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(obj, f, indent=1)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


NOISE_MODES = {"fixed_512": 0, "fixed_1024": 1, "fixed_2048": 2, "tone3_clocked": 3}


def validate_routing(routing, track=None, noise_mode="fixed_1024"):
    """Structural + (where timing exists) overlap conflict detection. Never discards voices to fit.
    `routing` = {arcade_ch(str): dest}. `noise_mode` is the PSG noise-frequency selector; only the
    tone3-clocked mode couples tone 3 and noise pitch. Returns conflict dicts with severity + certainty."""
    conflicts = []
    # 1. FM6 / reserved DAC may never carry music
    for ch, dest in routing.items():
        if dest in (RESERVED_DAC, "ym2612_fm6", "ym2612_fm6_dac"):
            conflicts.append({"type": "reserved_fm6", "severity": "error", "certainty": "structural",
                              "detail": "Arcade ch %s routed to FM6, which is reserved for DAC." % ch,
                              "channels": [ch]})
        elif dest not in MUSIC_DESTS:
            conflicts.append({"type": "invalid_dest", "severity": "error", "certainty": "structural",
                              "detail": "Arcade ch %s -> unknown destination '%s'." % (ch, dest),
                              "channels": [ch]})
    # 2. monophonic destination collisions (each FM channel / PSG tone is one voice)
    by_dest = {}
    for ch, dest in routing.items():
        if dest == "unassigned":
            continue
        by_dest.setdefault(dest, []).append(ch)
    # structural over-subscription of a single monophonic channel
    for dest, chs in by_dest.items():
        if dest in FM_MUSIC or dest in PSG_TONES or dest == "psg_noise":
            if len(chs) > 1:
                # Is it a proven time overlap, or only a structural (possible) conflict?
                certainty, sev = "potential", "warning"
                detail = ("%d arcade channels (%s) share monophonic %s. Timing data is incomplete "
                          "(AUDIO-003 not decoded) -> POTENTIAL conflict, not proven." %
                          (len(chs), ",".join(chs), dest))
                if track:
                    overlap = _time_overlap(chs, track)
                    if overlap:
                        certainty, sev = "proven", "error"
                        detail = ("Arcade channels %s are simultaneously active (overlap evidence) yet "
                                  "share monophonic %s." % (",".join(chs), dest))
                conflicts.append({"type": "monophonic_collision", "severity": sev, "certainty": certainty,
                                  "detail": detail, "channels": chs, "dest": dest})
    # 3. FM budget: at most 5 FM music VOICES (arcade channels routed to FM). More than 5 forces a
    #    collision because only FM1-5 exist (FM6 is DAC).
    fm_assignments = [ch for ch, dest in routing.items() if dest in FM_MUSIC]
    if len(fm_assignments) > 5:
        conflicts.append({"type": "fm_budget", "severity": "error", "certainty": "structural",
                          "detail": "%d arcade channels routed to FM; only 5 FM music channels exist "
                                    "(FM6 is DAC)." % len(fm_assignments),
                          "channels": fm_assignments})
    # 4. PSG tone-3 / noise coupling — ONLY when the noise selector is tone3-clocked (Cody claim 41).
    #    Fixed noise rates (0/1/2) coexist with tone 3 WITHOUT a coupling warning.
    noise_chs = by_dest.get("psg_noise", [])
    tone3_chs = by_dest.get("psg_tone3", [])
    if noise_chs and tone3_chs and noise_mode == "tone3_clocked":
        conflicts.append({"type": "tone3_noise_coupling", "severity": "warning", "certainty": "structural",
                          "detail": "psg_tone3 and psg_noise are both assigned AND the noise selector is "
                                    "tone3_clocked (freq-select 3): tone 3 and noise pitch are COUPLED — not "
                                    "independent. Use a fixed noise rate (512/1024/2048) to decouple them.",
                          "channels": tone3_chs + noise_chs, "noise_mode": noise_mode})
    return conflicts


def _time_overlap(chs, track):
    """Best-effort time-overlap test from capture-derived spans. Returns True only if we have positive
    evidence of simultaneity; absence of data is reported as 'potential' by the caller, never as proof."""
    spans = []
    for ch in chs:
        cc = next((c for c in track.get("channels", []) if str(c["ch"]) == str(ch)), None)
        if not cc or not cc.get("keyon"):
            return False            # insufficient evidence -> not proven
        spans.append(cc)
    # We only have aggregate activity (role/keyon), not per-note windows, so we cannot PROVE overlap here.
    return False


class Hd(BaseHTTPRequestHandler):
    def _s(self, code, body, ct="application/json"):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path in ("/", "/index.html"):
            return self._s(200, open(os.path.join(HERE, "index.html"), "rb").read(), "text/html")
        # AUDIO-009 (Cody finding #6/LOW): serve ONLY the exact known static files, not any *.js/*.css path.
        if u.path == "/app.js":
            return self._s(200, open(os.path.join(HERE, "app.js"), "rb").read(), "application/javascript")
        if u.path == "/player_adapter.js":                 # AUDIO-012 playback adapter (first-party)
            return self._s(200, open(os.path.join(HERE, "player_adapter.js"), "rb").read(), "application/javascript")
        if u.path == "/style.css":
            return self._s(200, open(os.path.join(HERE, "style.css"), "rb").read(), "text/css")
        if u.path == "/api/inventory":
            return self._s(200, json.dumps(inventory()).encode())
        if u.path == "/api/psg_model":
            return self._s(200, json.dumps(psg_model()).encode())
        if u.path == "/api/audition":
            return self._s(200, json.dumps({
                "available": False,
                "reason": "Phase 1: no validated YM2151/YM2612/PSG render engine is wired. Playback is "
                          "UNAVAILABLE. The interface + backend contract exist; no oscillator audio is "
                          "presented as a faithful reference, and no acoustic comparison is fabricated.",
                "future_contract": {
                    "endpoints": ["/api/render/original", "/api/render/ym2612", "/api/render/psg",
                                  "/api/render/full", "/api/render/lawrence_vgm"],
                    "requires": ["AUDIO-003 sequence decode", "validated emulator render stage"]}}).encode())
        # ---- AUDIO-012 PLAYBACK endpoints (read-only; NO profile/approval/manifest/revision interaction) ----
        if u.path == "/api/playback_sources":
            return self._s(200, json.dumps(playback_sources()).encode())
        if u.path == "/api/engine_status":
            return self._s(200, json.dumps(engine_status()).encode())
        if u.path == "/api/vgm":
            src = q.get("src", [""])[0]
            if src == "capture":
                cid = q.get("id", [""])[0]
                if cid not in [s for s, _ in CAPTURE_TRACKS]:   # strict allowlist; no path from client
                    return self._s(400, b'{"error":"unknown capture id"}')
                vp = os.path.join(CAPVGM, cid + ".vgm")
                if not os.path.exists(vp):
                    return self._s(404, json.dumps({"error": "capture VGM not generated; run "
                                    "tools/audio/ym2151_capture_to_vgm.py"}).encode())
                return self._s(200, open(vp, "rb").read(), "application/octet-stream")
            return self._s(400, b'{"error":"src must be capture"}')
        if u.path.startswith("/engine/"):                 # optional USER-SUPPLIED local engine (git-ignored)
            fn = u.path[len("/engine/"):]
            if not ENGINE_FILE_RE.match(fn):
                return self._s(400, b'{"error":"bad engine filename"}')
            fp = os.path.realpath(os.path.join(ENGINE_DIR, fn))
            if os.path.dirname(fp) != os.path.realpath(ENGINE_DIR) or not os.path.isfile(fp):
                return self._s(404, b'{"error":"engine file not present (none bundled)"}')
            ct = {"wasm": "application/wasm", "js": "application/javascript", "html": "text/html",
                  "css": "text/css", "ini": "text/plain", "woff": "font/woff", "json": "application/json"
                  }.get(fn.rsplit(".", 1)[-1], "application/octet-stream")
            return self._s(200, open(fp, "rb").read(), ct)
        # clean .vgm media URLs so wothke's engine picks the VGM loader by extension
        if u.path.startswith("/engine_media/capture/") and u.path.endswith(".vgm"):
            cid = unquote(u.path[len("/engine_media/capture/"):-4])
            if cid not in [s for s, _ in CAPTURE_TRACKS]:
                return self._s(400, b'{"error":"unknown capture id"}')
            vp = os.path.join(CAPVGM, cid + ".vgm")
            if not os.path.exists(vp):
                return self._s(404, b'{"error":"capture VGM not generated"}')
            return self._s(200, open(vp, "rb").read(), "application/octet-stream")
        if u.path.startswith("/engine_media/authored/") and u.path.endswith(".vgm"):
            tok = u.path[len("/engine_media/authored/"):-4]
            if not re.match(r"^[0-9a-f]{1,32}$", tok) or tok not in GENESIS_CACHE:
                return self._s(404, b'{"error":"authored render not found (POST /api/render_genesis first)"}')
            return self._s(200, GENESIS_CACHE[tok], "application/octet-stream")
        if u.path == "/api/profiles":
            return self._s(200, json.dumps(profile_manifest()).encode())
        if u.path == "/api/profile":
            pid = q.get("p", ["baseline_current"])[0]
            try:                                   # AUDIO-009 §3A: containment-checked path, no traversal
                path = safe_profile_path(pid)
            except ProfileIdError as e:
                return self._s(400, json.dumps({"error": "invalid profile id: %s" % e}).encode())
            pol = loadj(path, default_profile(pid, q.get("track", [None])[0]))
            return self._s(200, json.dumps(backfill(pol, q.get("track", [None])[0])).encode())
        if u.path == "/api/revisions":
            pid = q.get("p", [""])[0]
            try:
                safe_profile_path(pid)
            except ProfileIdError as e:
                return self._s(400, json.dumps({"error": "invalid profile id: %s" % e}).encode())
            return self._s(200, json.dumps({"profile_id": pid, "revisions": list_revisions(pid)}).encode())
        return self._s(404, b'{"error":"nf"}')

    def do_POST(self):
        u = urlparse(self.path)
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        except Exception as e:
            return self._s(400, json.dumps({"error": "bad json: %s" % e}).encode())
        if u.path == "/api/validate":
            routing = body.get("approved_routing") or body.get("routing") or {}
            track = body.get("track")
            noise_mode = body.get("noise_mode", "fixed_1024")
            return self._s(200, json.dumps({"conflicts": validate_routing(routing, track, noise_mode)}).encode())
        if u.path == "/api/render_genesis":
            # AUDIO-012 STAGE 1: render the authored routing to a Genesis YM2612+PSG VGM. Read-only; the
            # routing comes from the request body, NOT from any stored profile; nothing is persisted.
            tid = body.get("track") or body.get("track_id")
            routing = {str(k): v for k, v in (body.get("approved_routing") or {}).items()}
            # never let music target FM6/DAC (defense-in-depth; validator also rejects it)
            for ch, dest in list(routing.items()):
                if dest in (RESERVED_DAC, "ym2612_fm6", "ym2612_fm6_dac"):
                    return self._s(403, json.dumps({"error": "FM6 is DAC-reserved; cannot render music there"}).encode())
            if not any(d in FM_MUSIC or d.startswith("psg_") for d in routing.values()):
                return self._s(400, json.dumps({"error": "no FM/PSG assignments to render"}).encode())
            levels = {str(k): v for k, v in (body.get("levels") or {}).items()}
            tok, stats = render_genesis(tid, routing, body.get("noise_mode", "fixed_1024"), levels)
            if tok is None:
                return self._s(400, json.dumps({"error": stats}).encode())
            return self._s(200, json.dumps({"ok": True, "media_url": "/engine_media/authored/%s.vgm" % tok,
                                            "download_url": "/engine_media/authored/%s.vgm" % tok,
                                            "stats": stats, "stage": "PROVISIONAL (YM2151->YM2612/PSG "
                                            "register translation; not ROM-sequence fidelity)"}).encode())
        if u.path == "/api/profile":
            pid = (body.get("profile_id") or "").strip()
            if pid == "baseline_current":
                return self._s(400, b'{"error":"the immutable baseline cannot be overwritten; branch a new profile"}')
            try:                                   # AUDIO-009 §3A: validate+contain the id before any FS use
                path = safe_profile_path(pid)
            except ProfileIdError as e:
                return self._s(400, json.dumps({"error": "invalid profile id: %s" % e}).encode())

            noise_mode = body.get("noise_mode", "fixed_1024")
            if noise_mode not in NOISE_MODES:
                return self._s(400, json.dumps({"error": "invalid noise_mode '%s'" % noise_mode}).encode())
            routing = body.get("approved_routing") or {}

            # AUDIO-009 §3B: the SERVER recomputes conflicts on the effective approved routing and REJECTS
            # if ANY error-level conflict exists. Client-supplied conflicts are ignored. FM6 is one such error.
            conflicts = validate_routing(routing, None, noise_mode)
            errors = [c for c in conflicts if c["severity"] == "error"]
            if errors:
                return self._s(403, json.dumps({"error": "approved routing has error-level conflicts; not "
                                "persisted", "conflicts": errors}).encode())

            # AUDIO-009 §3C: arcade_evidence is SERVER-DERIVED; client-supplied evidence is discarded.
            # Load the previous revision to preserve unknown fields / notes and bump the revision.
            prev = loadj(path, None)
            base = default_profile(pid, body.get("track_id"))
            merged = dict(prev) if isinstance(prev, dict) else {}
            # start from base defaults for any missing keys, then apply previous, then this request's edits
            for k, v in base.items():
                merged.setdefault(k, v)
            # preserve client-provided editable fields (NOT evidence, NOT schema, NOT revision)
            for k in ("display_name", "track_id", "parent", "proposals", "approved_routing",
                      "noise_mode", "instrument_overrides", "time_dependent_routing", "notes",
                      "approval_status"):
                if k in body:
                    merged[k] = body[k]
            # carry forward any unknown future fields the client sent (schema-extensibility), minus protected ones
            for k, v in body.items():
                if k not in merged and k not in ("schema", "revision", "arcade_evidence", "conflicts",
                                                 "modified", "immutable", "reserved_dac"):
                    merged[k] = v

            merged["schema"] = SCHEMA
            merged["immutable"] = False
            merged["arcade_evidence"] = server_arcade_evidence(merged.get("track_id"))  # server truth only
            merged.setdefault("proposals", {})
            merged.setdefault("approved_routing", {})
            if merged.get("approval_status") == "approved" and not merged["approved_routing"]:
                merged["approval_status"] = "draft"

            # AUDIO-015 persistence fix: track_routings is the authoritative per-song
            # store the ROM compiler reads.  The top-level approved_routing/proposals/
            # noise_mode/instrument_overrides are only the ACTIVE track's working copy.
            # Previously the server trusted the client to fold the active track into
            # track_routings; a client load bug could leave a saved song's decisions at
            # top level only, so it never reached track_routings (Scene Clear/Final Boss).
            # The server now folds the active track every save so a save ALWAYS persists
            # that song's decisions into its per-song entry.  It does not clobber an
            # existing non-empty entry with an empty working copy (guards against a wiped
            # working copy overwriting good saved data).
            tr = merged.get("track_routings")
            if not isinstance(tr, dict):
                tr = {}
            active = merged.get("track_id")
            if active:
                active_entry = {
                    "approved_routing": merged.get("approved_routing", {}),
                    "proposals": merged.get("proposals", {}),
                    "noise_mode": merged.get("noise_mode", "fixed_1024"),
                    "instrument_overrides": merged.get("instrument_overrides", {}),
                }
                prior = tr.get(active)
                prior_has = isinstance(prior, dict) and prior.get("approved_routing")
                if active_entry["approved_routing"] or not prior_has:
                    tr[active] = active_entry
            merged["track_routings"] = tr

            merged["conflicts"] = conflicts
            merged["reserved_dac"] = RESERVED_DAC
            merged["revision"] = (prev.get("revision", 0) + 1) if isinstance(prev, dict) else 1
            merged["revision_id"] = "%s.r%d.%s" % (pid, merged["revision"], time.strftime("%Y%m%dT%H%M%SZ"))
            merged["modified"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")

            # AUDIO-009 §3D: write an IMMUTABLE revision snapshot FIRST, then atomically update current +
            # manifest. Old revisions are retained and recoverable.
            try:
                rev_path = safe_profile_path(pid, ".r%d.json" % merged["revision"])
            except ProfileIdError as e:
                return self._s(400, json.dumps({"error": "invalid revision path: %s" % e}).encode())
            atomic_write_json(rev_path, merged)
            atomic_write_json(path, merged)
            man = profile_manifest()
            m = {p["profile_id"]: p for p in man["profiles"]}
            m[pid] = {"profile_id": pid, "display_name": merged.get("display_name", pid),
                      "track_id": merged.get("track_id"), "approval_status": merged.get("approval_status", "draft"),
                      "parent": merged.get("parent", "baseline_current"),
                      "modified": merged["modified"], "revision": merged["revision"]}
            man["profiles"] = list(m.values())
            atomic_write_json(os.path.join(PROF_DIR, "profile_manifest.json"), man)
            return self._s(200, json.dumps({"ok": True, "profile_id": pid, "revision": merged["revision"],
                                             "conflicts": conflicts}).encode())
        return self._s(404, b'{"error":"nf"}')

    def log_message(self, *a):
        pass


def profile_manifest():
    return loadj(os.path.join(PROF_DIR, "profile_manifest.json"),
                 {"active": "baseline_current",
                  "profiles": [{"profile_id": "baseline_current", "display_name": "Baseline (immutable)",
                                "parent": None, "immutable": True, "revision": 0}]})


def backfill(pol, track_hint=None):
    """AUDIO-009 §3D: deterministic v1 -> v2 upgrade in memory. Preserve ALL existing fields (approvals,
    notes, unknown future fields); only ADD missing v2 fields. arcade_evidence is re-derived server-side."""
    tid = pol.get("track_id") or track_hint
    base = default_profile(pol.get("profile_id", "baseline_current"), tid)
    was_legacy = pol.get("schema") in LEGACY_SCHEMAS
    for k, v in base.items():
        pol.setdefault(k, v)                       # add missing keys only; never overwrite user data
    if was_legacy:
        pol["migrated_from"] = pol.get("migrated_from") or [s for s in LEGACY_SCHEMAS]
    pol["schema"] = SCHEMA
    pol["reserved_dac"] = RESERVED_DAC
    pol["music_destinations"] = MUSIC_DESTS
    pol["arcade_evidence"] = server_arcade_evidence(tid)   # server truth, overrides any stored/client value
    pol.setdefault("noise_mode", "fixed_1024")
    return pol


def list_revisions(pid):
    try:
        base = os.path.realpath(PROF_DIR)
    except Exception:
        return []
    out = []
    for name in sorted(os.listdir(PROF_DIR)):
        if name.startswith(pid + ".r") and name.endswith(".json"):
            d = loadj(os.path.join(PROF_DIR, name), {})
            out.append({"file": name, "revision": d.get("revision"), "revision_id": d.get("revision_id"),
                        "modified": d.get("modified"), "approval_status": d.get("approval_status")})
    return out


def ensure_baseline():
    p = os.path.join(PROF_DIR, "profile_manifest.json")
    if not os.path.exists(p):
        json.dump(profile_manifest(), open(p, "w"), indent=1)
    bp = os.path.join(PROF_DIR, "baseline_current.json")
    if not os.path.exists(bp):
        json.dump(default_profile("baseline_current"), open(bp, "w"), indent=1)


if __name__ == "__main__":
    import sys
    ensure_baseline()
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8781
    print("Rastan Audio Composer (Phase 1) -> http://localhost:%d  "
          "(arcade captures READ-ONLY; no ROM/build change)" % port)
    ThreadingHTTPServer(("127.0.0.1", port), Hd).serve_forever()
