"use strict";
/* AUDIO-012 — reusable VGM player adapter for the Rastan Audio Composer.
 *
 * This adapter is ENGINE-AGNOSTIC and UI-independent. It defines the contract that any real VGM chip
 * emulator must implement, and ships a NullEngine that is honest about the fact that NO emulation core is
 * bundled in this repository (the named engine, wothke webVGM / VGMPlay 0.40.9, uses MAME-licensed
 * YM2151/YM2612/SN76489 cores that are non-commercial / GPL-incompatible and were NOT imported — see
 * docs/design/Andy_AUDIO012_webvgm_audio_composer_integration.md).
 *
 * If the user drops an AUTHORIZED local engine into tools/audio_composer/engine/ exposing a global
 * `createVgmEngine(audioContext)` that returns an object implementing EngineContract below, this adapter
 * will use it automatically and real playback becomes available. Musical timing then comes from that
 * engine + the Web Audio render clock — never from setInterval or requestAnimationFrame.
 *
 * EngineContract (what a real engine must provide):
 *   async load(arrayBuffer)      -> {durationSamples, sampleRate, loopSamples?}
 *   play(), pause(), stop()
 *   seekSamples(n)               // may replay the event stream internally; see docs
 *   get positionSamples()        // driven by the audio clock, authoritative
 *   setVolume(0..1)
 *   setLoop(bool)
 *   muteChannel(chip, index, bool) / soloChannel(chip, index, bool)  // chip in {ym2151,ym2612,psg}
 *   onended(cb)
 *   dispose()
 */
(function (global) {
  const NOT_BUNDLED =
    "In-browser chip emulation is NOT bundled (licensing: webVGM/VGMPlay cores are MAME/GPL-family, " +
    "non-redistributable; and no build toolchain here). Use “Open / Download VGM” to play this exact " +
    "VGM in your existing webVGM, or drop an authorized engine in tools/audio_composer/engine/.";

  // The null engine never fabricates audio and never pretends a transport works.
  class NullEngine {
    constructor() { this.available = false; this.reason = NOT_BUNDLED; }
    async load() { throw new Error(this.reason); }
    play() { throw new Error(this.reason); }
    pause() {} stop() {} seekSamples() {}
    get positionSamples() { return 0; }
    setVolume() {} setLoop() {}
    muteChannel() { return false; } soloChannel() { return false; }
    onended() {} dispose() {}
  }

  const Adapter = {
    engine: null,
    available: false,
    reason: NOT_BUNDLED,

    // Probe the server for a user-supplied local engine; fall back to the honest NullEngine.
    async init(audioContext) {
      try {
        const st = await (await fetch("/api/engine_status")).json();
        if (st.local_engine_present && typeof global.createVgmEngine === "function") {
          this.engine = global.createVgmEngine(audioContext);
          this.available = true;
          this.reason = "";
          return this;
        }
        this.reason = (st && st.reason) || NOT_BUNDLED;
      } catch (e) {
        this.reason = NOT_BUNDLED;
      }
      this.engine = new NullEngine();
      this.available = false;
      return this;
    },

    // Fetch VGM bytes from an authorized project source (served read-only by the Composer server).
    async fetchVgm(url) {
      const r = await fetch(url);
      if (!r.ok) throw new Error("VGM fetch failed: " + r.status);
      return await r.arrayBuffer();
    },

    isAvailable() { return this.available; },
    statusReason() { return this.reason; },
  };

  global.VgmPlayerAdapter = Adapter;
  global.VgmNullEngine = NullEngine;
})(window);
