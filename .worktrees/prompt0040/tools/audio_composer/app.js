"use strict";
// Rastan Audio Composer (Phase 1) frontend. Tooling only; no ROM/build interaction.
const $ = s => document.querySelector(s);
const el = (t, c, h) => { const e = document.createElement(t); if (c) e.className = c; if (h != null) e.innerHTML = h; return e; };
const DESTS = ["unassigned", "ym2612_fm1", "ym2612_fm2", "ym2612_fm3", "ym2612_fm4", "ym2612_fm5",
  "psg_tone1", "psg_tone2", "psg_tone3", "psg_noise"];
const DEST_LABEL = {
  unassigned: "Unassigned", ym2612_fm1: "FM1", ym2612_fm2: "FM2", ym2612_fm3: "FM3",
  ym2612_fm4: "FM4", ym2612_fm5: "FM5", psg_tone1: "PSG T1", psg_tone2: "PSG T2",
  psg_tone3: "PSG T3", psg_noise: "PSG Noise"
};
const SLOTS = ["ym2612_fm1", "ym2612_fm2", "ym2612_fm3", "ym2612_fm4", "ym2612_fm5",
  "psg_tone1", "psg_tone2", "psg_tone3", "psg_noise", "ym2612_fm6_dac"];

let INV = null, PSG = null, PROF = null, TRACK = null, DIRTY = false;

function status(m, cls) { const s = $("#status"); s.textContent = m || ""; s.style.color = cls || ""; }
function setDirty(d) { DIRTY = d; $("#dirty").textContent = d ? "● unsaved" : ""; }

async function getJSON(u, opt) { const r = await fetch(u, opt); return r.json(); }

function destClass(d) {
  if (d && d.startsWith("ym2612_fm")) return "fm";
  if (d === "psg_noise") return "noise";
  if (d && d.startsWith("psg_")) return "psg";
  return "un";
}

// ---- boot -----------------------------------------------------------------
async function boot() {
  INV = await getJSON("/api/inventory");
  PSG = await getJSON("/api/psg_model");
  renderPSGModel();
  renderTrackList();
  await loadAudition();
  await refreshProfiles();
  await loadProfile($("#profile").value || "baseline_current");
  $("#help").onclick = () => $("#helpbox").classList.toggle("hide");
  $("#branch").onclick = branchProfile;
  $("#save").onclick = saveProfile;
  $("#reload").onclick = () => loadProfile($("#profile").value);
  $("#profile").onchange = e => loadProfile(e.target.value);
  await initPlayer();
  footer();
}

// ---- AUDIO-012 playback (read-only; never touches routing/profiles) -------
let PLAYSRCS = null, AUDIOCTX = null, CURVGM = null;
async function initPlayer() {
  PLAYSRCS = await getJSON("/api/playback_sources");
  const sel = $("#playsrc"); sel.innerHTML = "";
  const og = el("optgroup"); og.label = PLAYSRCS.sources.original_arcade_ym2151.label;
  PLAYSRCS.sources.original_arcade_ym2151.tracks.forEach(t => {
    const o = el("option"); o.value = "capture:" + t.id; o.textContent = t.name + (t.vgm_available ? "" : " (not generated)");
    o.disabled = !t.vgm_available; og.appendChild(o);
  });
  sel.appendChild(og);

  $("#pb-open").onclick = () => {
    const t = PLAYSRCS.sources.original_arcade_ym2151.tracks.find(t => "capture:" + t.id === sel.value);
    if (t) window.open(t.vgm_url, "_blank");
  };

  // ▶ Play Genesis — render the AUTHORED routing (left-selected track + current approved_routing) to a
  // real YM2612+PSG VGM and play it (same engine). This is your authored arrangement, provisional stage.
  $("#pb-genesis").onclick = async () => {
    const info = $("#pb-genesis-info");
    if (!TRACK) { info.textContent = "select a track (left) first"; return; }
    const routing = (PROF && PROF.approved_routing) || {};
    if (!Object.keys(routing).length) { info.textContent = "approve some routing first (per channel → Approve)"; return; }
    info.textContent = "rendering " + TRACK.musical_name + " …";
    const levels = {};
    Object.entries(PROF.instrument_overrides || {}).forEach(([ch, ov]) => { if (ov && ov.level != null) levels[ch] = ov.level; });
    let r;
    try {
      r = await getJSON("/api/render_genesis", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ track: TRACK.track_id, approved_routing: routing, noise_mode: (PROF.noise_mode || "fixed_1024"), levels }) });
    } catch (e) { info.textContent = "render failed: " + e.message; return; }
    if (r.error) { info.textContent = "render error: " + r.error; return; }
    const s = r.stats;
    info.innerHTML = `<b>authored Genesis:</b> FM${JSON.stringify(s.fm_targets)} · PSG ${JSON.stringify(s.psg_targets)}` +
      (s.dropped_channels.length ? ` · dropped CH${JSON.stringify(s.dropped_channels)}` : "") +
      ` · ${s.duration_s}s · <i>${r.stage}</i>`;
    const eng = PLAYSRCS.engine;
    if (eng.local_engine_present) {
      let fr = document.getElementById("pb-frame");
      if (!fr) { fr = el("iframe"); fr.id = "pb-frame"; fr.style.cssText = "width:100%;height:132px;border:1px solid var(--line);border-radius:6px;margin-top:6px;background:#14171c"; $("#player").appendChild(fr); }
      fr.src = "/engine/webvgm_player.html?vgm=" + encodeURIComponent(r.media_url) + "&boost=0";
    } else {
      window.open(r.media_url, "_blank");
    }
  };

  const eng = PLAYSRCS.engine;
  const st = $("#pb-status");
  if (eng.local_engine_present) {
    // Real local webVGM engine present → play in-Composer via an isolated iframe host page.
    st.innerHTML = `<b>Local webVGM engine detected.</b> In-Composer playback below (real chip emulation).`;
    st.className = "pbstatus okmsg";
    $("#transport").style.display = "none";
    $("#pb-seek").parentElement.style.display = "none";
    let fr = document.getElementById("pb-frame");
    if (!fr) { fr = el("iframe"); fr.id = "pb-frame"; fr.style.cssText = "width:100%;height:132px;border:1px solid var(--line);border-radius:6px;margin-top:6px;background:#14171c"; $("#player").appendChild(fr); }
    const loadFrame = () => {
      const t = PLAYSRCS.sources.original_arcade_ym2151.tracks.find(t => "capture:" + t.id === sel.value);
      if (!t) return;
      fr.src = "/engine/webvgm_player.html?vgm=" + encodeURIComponent(t.engine_media_url) + "&boost=0";
    };
    sel.addEventListener("change", loadFrame);
    loadFrame();
  } else {
    // No engine: honest unavailable + working Open/Download-into-your-own-webVGM path.
    st.innerHTML = `<b>In-browser engine not installed.</b> ${eng.how_to_enable_real_playback}`;
    st.className = "pbstatus unavail";
    // transport stays disabled (as authored in HTML); "Open / Download VGM" works.
  }
}

function fmtTime(s) { s = Math.max(0, Math.floor(s)); return (s / 60 | 0) + ":" + String(s % 60).padStart(2, "0"); }

function wireRealTransport(sel) {
  // Only reached when an authorized local engine is present. Timing is driven by the engine's audio
  // clock via adapter.positionSamples — NOT setInterval (a UI-only poll just reads that clock).
  const A = window.VgmPlayerAdapter;
  ["pb-play", "pb-pause", "pb-stop", "pb-restart", "pb-loop", "pb-vol", "pb-seek"].forEach(id => $("#" + id).disabled = false);
  async function loadCur() {
    const t = PLAYSRCS.sources.original_arcade_ym2151.tracks.find(t => "capture:" + t.id === sel.value);
    if (!t) return;
    CURVGM = await A.fetchVgm(t.vgm_url); return A.engine.load(CURVGM);
  }
  sel.onchange = () => { A.engine.stop(); };
  $("#pb-play").onclick = async () => { if (AUDIOCTX.state === "suspended") await AUDIOCTX.resume(); if (!CURVGM) await loadCur(); A.engine.play(); };
  $("#pb-pause").onclick = () => A.engine.pause();
  $("#pb-stop").onclick = () => A.engine.stop();
  $("#pb-restart").onclick = () => { A.engine.seekSamples(0); A.engine.play(); };
  $("#pb-loop").onchange = e => A.engine.setLoop(e.target.checked);
  $("#pb-vol").oninput = e => A.engine.setVolume(e.target.value / 100);
}

function footer() {
  $("#foot").innerHTML = INV.audio003_status.decoded ? "" :
    "<b>AUDIO-003 not decoded:</b> " + INV.audio003_status.limitation +
    " &nbsp;·&nbsp; " + INV.deep_fm_finding;
}

// ---- track browser --------------------------------------------------------
function renderTrackList() {
  const box = $("#tracklist"); box.innerHTML = "";
  INV.tracks.forEach(t => {
    const d = el("div", "trk");
    d.innerHTML = `<b>${t.musical_name}</b><span class="meta">${t.track_id}<br>` +
      `keyed ${t.channels_ever_keyed_count ?? "?"} · peak-keyed ${t.peak_simultaneously_keyed ?? "?"} · ` +
      `sustained≈${t.sustained_voice_count_heuristic ?? "?"} · ` +
      `${t.capture_available ? "capture ✓" : "no capture"}</span>`;
    d.onclick = () => selectTrack(t.track_id, d);
    box.appendChild(d);
  });
}

// Each song keeps its OWN independent mapping in PROF.track_routings[track_id]. The top-level
// approved_routing/proposals/noise_mode/instrument_overrides are the working copy for the ACTIVE track.
function stashTrackRouting(tid) {
  if (!PROF || !tid) return;
  PROF.track_routings = PROF.track_routings || {};
  PROF.track_routings[tid] = {
    approved_routing: PROF.approved_routing || {},
    proposals: PROF.proposals || {},
    noise_mode: PROF.noise_mode || "fixed_1024",
    instrument_overrides: PROF.instrument_overrides || {},
  };
}
function applyTrackRouting(tid) {
  const r = (PROF.track_routings && PROF.track_routings[tid]) || {};
  PROF.approved_routing = r.approved_routing || {};
  PROF.proposals = r.proposals || {};
  PROF.noise_mode = r.noise_mode || "fixed_1024";
  PROF.instrument_overrides = r.instrument_overrides || {};
}

function selectTrack(id, node) {
  document.querySelectorAll("#tracklist .trk").forEach(n => n.classList.remove("on"));
  if (node) node.classList.add("on");
  const prev = TRACK ? TRACK.track_id : (PROF && PROF.track_id);
  if (PROF && prev && prev !== id) stashTrackRouting(prev);   // save the outgoing song's mapping
  TRACK = INV.tracks.find(t => t.track_id === id);
  if (PROF) {
    PROF.track_id = id; PROF.track = TRACK;
    PROF.track_routings = PROF.track_routings || {};
    applyTrackRouting(id);                                    // load THIS song's independent mapping
  }
  $("#trkhdr").innerHTML = `Original YM2151 channels <span class="dim">— ${TRACK.musical_name}</span>`;
  renderChannels();
  renderRouting();
  validate();
  // keep the playback source on the same song so original vs authored A/B matches
  const ps = $("#playsrc");
  if (ps && [...ps.options].some(o => o.value === "capture:" + id)) {
    ps.value = "capture:" + id; ps.dispatchEvent(new Event("change"));
  }
}

// ---- original arcade channels + per-channel routing -----------------------
function renderChannels() {
  const box = $("#archannels"); box.innerHTML = "";
  if (!TRACK) { box.innerHTML = '<div class="dim">Select a track.</div>'; return; }
  box.appendChild(el("div", "dim",
    "Instrument identity is <b>capture-derived</b> (programmed YM2151 patch state), not from the ROM " +
    "instrument table. Command-ID: <b>UNRESOLVED</b> (not inferred from filename)."));
  TRACK.channels.forEach(c => {
    const row = el("div", "chan");
    const prop = (PROF.proposals || {})[c.ch];
    const appr = (PROF.approved_routing || {})[c.ch];
    const roleBadge = `<span class="badge ${c.role}">${c.role}</span>`;
    row.innerHTML =
      `<div class="cid">CH${c.ch}</div>` +
      `<div class="info"><span class="role">${c.role === "musical" ? "musical voice" : c.role}</span>${roleBadge}` +
      `<div class="ev">keyon ${c.keyon} · pitches ${c.distinct_pitches} · algo ${c.algorithm ?? "–"} fb ${c.feedback ?? "–"}` +
      ` · PSG-fit(heur): ${c.psg_candidacy_inferred}</div></div>`;
    const sel = el("div", "destsel");
    const dd = el("select");
    DESTS.forEach(d => { const o = el("option"); o.value = d; o.textContent = DEST_LABEL[d]; dd.appendChild(o); });
    dd.value = (prop && prop.dest) || appr || "unassigned";
    dd.onchange = () => setProposal(c.ch, dd.value);
    const rowbtn = el("div", "row");
    const ap = el("button", null, "Approve"); ap.onclick = () => approve(c.ch);
    const cl = el("button", null, "Clear"); cl.onclick = () => clearCh(c.ch);
    rowbtn.appendChild(ap); rowbtn.appendChild(cl);
    const stat = el("div");
    if (appr) stat.innerHTML = `<span class="badge appr">approved → ${DEST_LABEL[appr]}</span>`;
    else if (prop && prop.dest !== "unassigned") stat.innerHTML = `<span class="badge prop">proposed → ${DEST_LABEL[prop.dest]}</span>`;
    // per-channel volume (0..100, 100 = original level). Stored in instrument_overrides[ch].level.
    const lvl = ((PROF.instrument_overrides || {})[c.ch] || {}).level;
    const vol = el("div", "chvol");
    vol.innerHTML = `vol <input type="range" min="0" max="200" value="${lvl == null ? 100 : lvl}" title="0=mute · 100=original · >100=boost"> <span>${lvl == null ? 100 : lvl}</span>`;
    const vr = vol.querySelector("input"), vn = vol.querySelector("span");
    vr.oninput = () => {
      vn.textContent = vr.value;
      PROF.instrument_overrides = PROF.instrument_overrides || {};
      PROF.instrument_overrides[c.ch] = Object.assign({}, PROF.instrument_overrides[c.ch], { level: parseInt(vr.value, 10) });
      setDirty(true);
    };
    sel.appendChild(dd); sel.appendChild(rowbtn); sel.appendChild(stat); sel.appendChild(vol);
    row.appendChild(sel);
    box.appendChild(row);
  });
}

function setProposal(ch, dest) {
  PROF.proposals = PROF.proposals || {};
  if (dest === "unassigned") delete PROF.proposals[ch];
  else PROF.proposals[ch] = { dest, rationale: "user proposal (unaudited)", evidence: "capture-derived role" };
  setDirty(true); renderChannels(); renderRouting(); validate();
}
function approve(ch) {
  const prop = (PROF.proposals || {})[ch];
  const dest = prop ? prop.dest : "unassigned";
  if (!dest || dest === "unassigned") { status("No proposal to approve for CH" + ch, "var(--warn)"); return; }
  PROF.approved_routing = PROF.approved_routing || {};
  PROF.approved_routing[ch] = dest;
  setDirty(true); renderChannels(); renderRouting(); validate();
}
function clearCh(ch) {
  if (PROF.proposals) delete PROF.proposals[ch];
  if (PROF.approved_routing) delete PROF.approved_routing[ch];
  setDirty(true); renderChannels(); renderRouting(); validate();
}

// ---- PSG noise mode (only tone3_clocked couples tone 3) -------------------
function renderNoiseMode() {
  const box = $("#routing");
  const cur = (PROF && PROF.noise_mode) || "fixed_1024";
  const wrap = el("div", "slot");
  wrap.style.gridColumn = "1 / -1";
  const modes = ["fixed_512", "fixed_1024", "fixed_2048", "tone3_clocked"];
  let opts = modes.map(m => `<option value="${m}"${m === cur ? " selected" : ""}>${m}</option>`).join("");
  wrap.innerHTML = `<b>PSG noise frequency</b><div class="asg">` +
    `<select id="noisemode">${opts}</select> ` +
    `<span class="dim">only <kbd>tone3_clocked</kbd> couples tone 3 ↔ noise pitch</span></div>`;
  box.appendChild(wrap);
  wrap.querySelector("#noisemode").onchange = e => {
    PROF.noise_mode = e.target.value; setDirty(true); validate();
  };
}

// ---- Genesis destination slots -------------------------------------------
function renderRouting() {
  const box = $("#routing"); box.innerHTML = "";
  renderNoiseMode();
  const appr = PROF.approved_routing || {};
  const byDest = {}; Object.entries(appr).forEach(([ch, d]) => (byDest[d] = byDest[d] || []).push(ch));
  SLOTS.forEach(s => {
    const isDac = s === "ym2612_fm6_dac";
    const cls = isDac ? "dac" : destClass(s);
    const slot = el("div", "slot " + cls);
    const chs = byDest[s] || [];
    if (chs.length > 1) slot.classList.add("over");
    slot.innerHTML = `<b>${isDac ? "FM6 — DAC (reserved)" : DEST_LABEL[s]}</b>` +
      `<div class="asg">${isDac ? "voices / sampled SFX only" :
        (chs.length ? chs.map(c => "CH" + c).join(", ") : "—")}</div>`;
    box.appendChild(slot);
  });
}

// ---- validation -----------------------------------------------------------
async function validate() {
  if (!PROF) return;
  const r = await getJSON("/api/validate", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approved_routing: PROF.approved_routing || {}, track: TRACK,
      noise_mode: PROF.noise_mode || "fixed_1024" })
  });
  const box = $("#conflicts"); if (!box) return;   // right column may be disabled
  box.innerHTML = "";
  const cs = r.conflicts || [];
  if (!cs.length) { box.innerHTML = '<div class="okmsg">No conflicts in the approved routing.</div>'; return; }
  cs.forEach(c => {
    const d = el("div", "conf " + (c.severity || "warning"));
    d.innerHTML = `<span class="t">${c.type}</span> <span class="cert">[${c.severity}/${c.certainty}]</span>` +
      `<div>${c.detail}</div>`;
    box.appendChild(d);
  });
}

// ---- profiles -------------------------------------------------------------
async function refreshProfiles() {
  const man = await getJSON("/api/profiles");
  const sel = $("#profile"); const cur = sel.value; sel.innerHTML = "";
  man.profiles.forEach(p => {
    const o = el("option"); o.value = p.profile_id;
    o.textContent = p.display_name + (p.immutable ? " (ro)" : "") +
      (p.approval_status ? " · " + p.approval_status : "");
    sel.appendChild(o);
  });
  if (cur) sel.value = cur;
}

async function loadProfile(pid) {
  PROF = await getJSON("/api/profile?p=" + encodeURIComponent(pid) + (TRACK ? "&track=" + encodeURIComponent(TRACK.track_id) : ""));
  PROF.track_routings = PROF.track_routings || {};
  // Migrate the active track's top-level routing into its per-song slot whenever that
  // slot is MISSING (not only when track_routings is entirely empty).  The old
  // "only if empty" guard is why Scene Clear / Final Boss were lost: once any songs
  // were in track_routings, a track whose decisions lived only at top level was never
  // migrated, and selectTrack->applyTrackRouting then wiped the working copy.
  if (PROF.track_id && !(PROF.track_routings[PROF.track_id]) &&
      PROF.approved_routing && Object.keys(PROF.approved_routing).length) {
    PROF.track_routings[PROF.track_id] = {
      approved_routing: PROF.approved_routing, proposals: PROF.proposals || {},
      noise_mode: PROF.noise_mode || "fixed_1024", instrument_overrides: PROF.instrument_overrides || {},
    };
  }
  $("#profile").value = pid;
  setDirty(false);
  const imm = PROF.immutable;
  $("#save").disabled = imm;
  status(imm ? "Baseline is read-only — branch an editable profile to make decisions." : "Loaded " + pid);
  if (PROF.track_id && INV) {
    const node = [...document.querySelectorAll("#tracklist .trk")]
      .find(n => n.querySelector(".meta").textContent.includes(PROF.track_id));
    selectTrack(PROF.track_id, node);
  } else { renderChannels(); renderRouting(); }
  renderInstrument();
}

async function branchProfile() {
  const name = ($("#newprofile").value || "").trim();
  if (!name) { status("Enter a new profile name first.", "var(--warn)"); return; }
  const pid = name.replace(/[^A-Za-z0-9._-]/g, "_");
  PROF = JSON.parse(JSON.stringify(PROF || {}));
  PROF.profile_id = pid; PROF.display_name = name; PROF.immutable = false;
  PROF.parent = $("#profile").value; PROF.approval_status = "draft";
  await persist(); await refreshProfiles(); $("#profile").value = pid;
  $("#save").disabled = false; $("#newprofile").value = "";
  status("Created editable profile '" + name + "'.", "var(--ok)");
}

async function saveProfile() {
  if (PROF.immutable) { status("Cannot overwrite baseline.", "var(--warn)"); return; }
  await persist(); await refreshProfiles();
  setDirty(false); status("Saved " + PROF.profile_id + ".", "var(--ok)");
}

async function persist() {
  if (TRACK) stashTrackRouting(TRACK.track_id);   // fold the active song's mapping into track_routings
  const payload = JSON.parse(JSON.stringify(PROF));
  delete payload.track;              // transient view-join, not persisted
  const r = await getJSON("/api/profile", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
  });
  if (r.error) { status("Save error: " + r.error, "var(--err)"); throw new Error(r.error); }
  PROF.conflicts = r.conflicts || [];
  validate();
}

// ---- side panels (right column may be commented out; all guarded) ---------
function renderInstrument() {
  if (!$("#instrument")) return;
  $("#instrument").innerHTML =
    "<div>Per-channel instrument overrides are modeled in the profile (YM2612: algo, fb, MUL, DT, TL, " +
    "AR/DC/SR/RR, AMS/FMS, stereo pan, time-series; PSG: divider, atten, envelope, vibrato, arp, noise " +
    "mode). <b>Editing UI is deferred to a later phase</b>; persistence already carries these fields so " +
    "later work won't require a format change.</div>";
}

function renderPSGModel() {
  if (!$("#psgmodel")) return;
  const p = PSG;
  $("#psgmodel").innerHTML =
    `<div>${p.chip} @ ${p.clock_hz.toLocaleString()} Hz</div>` +
    `<div>${p.tone_channels} tone (${p.duty})</div>` +
    `<div>Tone f = clock/(32·n), n ${p.tone_divider_range[0]}–${p.tone_divider_range[1]} → ` +
    `${p.tone_freq_hz_range[0]}–${p.tone_freq_hz_range[1]} Hz</div>` +
    `<div>Atten ${p.attenuation_bits}-bit, ${p.attenuation_step_db} dB/step (${p.attenuation_levels} levels)</div>` +
    `<div><b>Stereo:</b> ${p.stereo}</div>` +
    `<div>Noise: ${p.noise.shift_register_bits}-bit LFSR. <i>${p.noise.shift_register_status}</i></div>` +
    `<div><b>Tone-3 coupling:</b> ${p.noise.tone3_coupling}</div>` +
    `<div><b>Divider 0:</b> ${p.divider_zero}</div>` +
    `<div class="dim">${p.provenance}</div>`;
}

async function loadAudition() {
  if (!$("#audition")) return;
  const a = await getJSON("/api/audition");
  $("#audition").innerHTML = a.available
    ? '<div class="okmsg">Audition available.</div>'
    : `<div class="unavail"><b>Playback UNAVAILABLE (Phase 1).</b> ${a.reason}</div>`;
}

boot();
