[Cody — Build 38 Video Frame Extraction + VDP Ground Truth]

Phase 1 — Extraction:
  total frames extracted: 563
  video duration: 18.837313 seconds

Phase 2 — Execution start:
  first_execution_frame: frame_0165
  VDP Image at that frame: transition from full dark field (frame_0164) to split black/light field at frame_0165

Phase 3 — Selected frames:
  start: frame_0165
  every 15th frame from start: frame_0165, frame_0180, frame_0195, frame_0210, frame_0225, frame_0240, frame_0255, frame_0270, frame_0285, frame_0300, frame_0315, frame_0330, frame_0345, frame_0360, frame_0375, frame_0390, frame_0405, frame_0420, frame_0435, frame_0450, frame_0465, frame_0480, frame_0495, frame_0510, frame_0525, frame_0540, frame_0555
  total selected: 27

Per-frame extraction:

  frame_0165:
    CPU:
      PC:  0x00070112
      SR:  0x2710
      D0: 0x00006640  D1: 0x66800001  D2: 0x00000001  D3: 0xFFFFF337
      D4: 0x0004A8A0  D5: 0xFFFFFFFF  D6: 0x00000000  D7: 0x00000007
      A0: 0x000FA1F4  A1: 0xFFFFFFFF  A2: 0x000C3D56  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0xFFFFFFFF  A6: 0xFFFFFFFF  A7: 0x00FEFFC8
      USP: 0xFFFFFFFF  SSP: 0x00FEFFC8
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0EEE
      entries 0-15: 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
                    0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
    Plane Viewer:
      Layer A: uniform light-gray blocks with hard rectangular boundaries
      Layer B: uniform light-gray blocks with lower-half fill and hard boundaries

  frame_0180:
    CPU:
      PC:  0x00070022
      SR:  0x2004
      D0: 0x00000023  D1: 0x6000003F  D2: 0x000000FF  D3: 0xFFFFFFFF
      D4: 0xFFFFFFFF  D5: 0xFFFFFFFF  D6: 0x0000FF33  D7: 0x00000F3F
      A0: 0x0003ABFE  A1: 0x0003B2FB  A2: 0x00FF0167  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FF0000  A6: 0xFFFFFFFF  A7: 0x00FEFFFC
      USP: 0xFFFFFFFF  SSP: 0x00FEFFFC
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0EEE
      entries 0-15: 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
                    0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
    Plane Viewer:
      Layer A: uniform light-gray blocks with hard rectangular boundaries
      Layer B: uniform light-gray blocks with lower-half fill and hard boundaries

  frame_0195:
    CPU:
      PC:  0x0007001C
      SR:  0x2004
      D0: 0x00000041  D1: 0x6000003F  D2: 0x000000FF  D3: 0xFFFFFFFF
      D4: 0xFFFFFFFF  D5: 0xFFFFFFFF  D6: 0x0000FF33  D7: 0x00000F3F
      A0: 0x0003ABFE  A1: 0x0003B2FB  A2: 0x00FF0167  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FF0000  A6: 0xFFFFFFFF  A7: 0x00FEFFFC
      USP: 0xFFFFFFFF  SSP: 0x00FEFFFC
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0EEE
      entries 0-15: 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
                    0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
    Plane Viewer:
      Layer A: uniform light-gray blocks with hard rectangular boundaries
      Layer B: uniform light-gray blocks with lower-half fill and hard boundaries

  frame_0210:
    CPU:
      PC:  0x0007001C
      SR:  0x2004
      D0: 0x00000061  D1: 0x6000003F  D2: 0x000000FF  D3: 0xFFFFFFFF
      D4: 0xFFFFFFFF  D5: 0xFFFFFFFF  D6: 0x0000FF33  D7: 0x00000F3F
      A0: 0x0003ABFE  A1: 0x0003B2FB  A2: 0x00FF0167  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FF0000  A6: 0xFFFFFFFF  A7: 0x00FEFFFC
      USP: 0xFFFFFFFF  SSP: 0x00FEFFFC
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0EEE
      entries 0-15: 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
                    0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
    Plane Viewer:
      Layer A: uniform light-gray blocks with hard rectangular boundaries
      Layer B: uniform light-gray blocks with lower-half fill and hard boundaries

  frame_0225:
    CPU:
      PC:  0x00070022
      SR:  0x2004
      D0: 0x0000007F  D1: 0x6000003F  D2: 0x000000FF  D3: 0xFFFFFFFF
      D4: 0xFFFFFFFF  D5: 0xFFFFFFFF  D6: 0x0000FF33  D7: 0x00000F3F
      A0: 0x0003ABFE  A1: 0x0003B2FB  A2: 0x00FF0167  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FF0000  A6: 0xFFFFFFFF  A7: 0x00FEFFFC
      USP: 0xFFFFFFFF  SSP: 0x00FEFFFC
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0EEE
      entries 0-15: 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
                    0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
    Plane Viewer:
      Layer A: uniform light-gray blocks with hard rectangular boundaries
      Layer B: uniform light-gray blocks with lower-half fill and hard boundaries

  frame_0240:
    CPU:
      PC:  0x00070022
      SR:  0x2004
      D0: 0x0000009F  D1: 0x6000003F  D2: 0x000000FF  D3: 0xFFFFFFFF
      D4: 0xFFFFFFFF  D5: 0xFFFFFFFF  D6: 0x0000FF33  D7: 0x00000F3F
      A0: 0x0003ABFE  A1: 0x0003B2FB  A2: 0x00FF0167  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FF0000  A6: 0xFFFFFFFF  A7: 0x00FEFFFC
      USP: 0xFFFFFFFF  SSP: 0x00FEFFFC
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0EEE
      entries 0-15: 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
                    0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
    Plane Viewer:
      Layer A: uniform light-gray blocks with hard rectangular boundaries
      Layer B: uniform light-gray blocks with lower-half fill and hard boundaries

  frame_0255:
    CPU:
      PC:  0x00070022
      SR:  0x2004
      D0: 0x000000BC  D1: 0x6000003F  D2: 0x000000FF  D3: 0xFFFFFFFF
      D4: 0xFFFFFFFF  D5: 0xFFFFFFFF  D6: 0x000F0033  D7: 0x00000F3F
      A0: 0x0003ABFE  A1: 0x0003C0BC  A2: 0x00C01728  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FF0000  A6: 0xFFFFFFFF  A7: 0x00FEFFFC
      USP: 0xFFFFFFFF  SSP: 0x00FEFFFC
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0EEE
      entries 0-15: 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
                    0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
    Plane Viewer:
      Layer A: uniform light-gray blocks with hard rectangular boundaries
      Layer B: uniform light-gray blocks with lower-half fill and hard boundaries

  frame_0270:
    CPU:
      PC:  0x00070022
      SR:  0x2004
      D0: 0x000000D1  D1: 0x6000003F  D2: 0x000000FF  D3: 0xFFFFFFFF
      D4: 0xFFFFFFFF  D5: 0xFFFFFFFF  D6: 0x000F0033  D7: 0x00000F3F
      A0: 0x0003ABFE  A1: 0x0003C0BC  A2: 0x00C01728  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FF0000  A6: 0xFFFFFFFF  A7: 0x00FEFFFC
      USP: 0xFFFFFFFF  SSP: 0x00FEFFFC
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0EEE
      entries 0-15: 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
                    0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
    Plane Viewer:
      Layer A: uniform light-gray blocks with hard rectangular boundaries
      Layer B: uniform light-gray blocks with lower-half fill and hard boundaries

  frame_0285:
    CPU:
      PC:  0x0007001C
      SR:  0x2004
      D0: 0x000000F0  D1: 0x6000003F  D2: 0x000000FF  D3: 0xFFFFFFFF
      D4: 0xFFFFFFFF  D5: 0xFFFFFFFF  D6: 0x000F0033  D7: 0x00000F3F
      A0: 0x0003ABFE  A1: 0x0003C0BC  A2: 0x00C01728  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FF0000  A6: 0xFFFFFFFF  A7: 0x00FEFFEE
      USP: 0xFFFFFFFF  SSP: 0x00FEFFFC
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0EEE
      entries 0-15: 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
                    0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
    Plane Viewer:
      Layer A: uniform light-gray blocks with hard rectangular boundaries
      Layer B: uniform light-gray blocks with lower-half fill and hard boundaries

  frame_0300:
    CPU:
      PC:  0x00070022
      SR:  0x2004
      D0: 0x0000010D  D1: 0x6000003F  D2: 0x000000FF  D3: 0xFFFFFFFF
      D4: 0xFFFFFFFF  D5: 0xFFFFFFFF  D6: 0x000F0033  D7: 0x00000F3F
      A0: 0x0003ABFE  A1: 0x0003C0BC  A2: 0x00C01728  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FF0000  A6: 0xFFFFFFFF  A7: 0x00FEFFFC
      USP: 0xFFFFFFFF  SSP: 0x00FEFFFC
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0EEE
      entries 0-15: 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
                    0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
    Plane Viewer:
      Layer A: uniform light-gray blocks with hard rectangular boundaries
      Layer B: uniform light-gray blocks with lower-half fill and hard boundaries

  frame_0315:
    CPU:
      PC:  0x00070022
      SR:  0x2004
      D0: 0x0000012C  D1: 0x6000003F  D2: 0x000000FF  D3: 0xFFFFFFFF
      D4: 0xFFFFFFFF  D5: 0xFFFFFFFF  D6: 0x000F0033  D7: 0x00000F3F
      A0: 0x0003ABFE  A1: 0x0003C0BC  A2: 0x00C01728  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FF0000  A6: 0xFFFFFFFF  A7: 0x00FEFFFC
      USP: 0xFFFFFFFF  SSP: 0x00FEFFFC
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0EEE
      entries 0-15: 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
                    0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
    Plane Viewer:
      Layer A: uniform light-gray blocks with hard rectangular boundaries
      Layer B: uniform light-gray blocks with lower-half fill and hard boundaries

  frame_0330:
    CPU:
      PC:  0x00070022
      SR:  0x2004
      D0: 0x0000014B  D1: 0x6000003F  D2: 0x000000FF  D3: 0xFFFFFFFF
      D4: 0xFFFFFFFF  D5: 0xFFFFFFFF  D6: 0x000F0033  D7: 0x00000F3F
      A0: 0x0003ABFE  A1: 0x0003C0BC  A2: 0x00C01728  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FF0000  A6: 0xFFFFFFFF  A7: 0x00FEFFFC
      USP: 0xFFFFFFFF  SSP: 0x00FEFFFC
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0EEE
      entries 0-15: 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
                    0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
    Plane Viewer:
      Layer A: uniform light-gray blocks with hard rectangular boundaries
      Layer B: uniform light-gray blocks with lower-half fill and hard boundaries

  frame_0345:
    CPU:
      PC:  0x00070022
      SR:  0x2004
      D0: 0x0000016B  D1: 0x6000003F  D2: 0x000000FF  D3: 0xFFFFFFFF
      D4: 0xFFFFFFFF  D5: 0xFFFFFFFF  D6: 0x000F0033  D7: 0x00000F3F
      A0: 0x0003ABFE  A1: 0x0003C0BC  A2: 0x00C01728  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FF0000  A6: 0xFFFFFFFF  A7: 0x00FEFFFC
      USP: 0xFFFFFFFF  SSP: 0x00FEFFFC
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0EEE
      entries 0-15: 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
                    0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
    Plane Viewer:
      Layer A: uniform light-gray blocks with hard rectangular boundaries
      Layer B: uniform light-gray blocks with lower-half fill and hard boundaries

  frame_0360:
    CPU:
      PC:  0x00000200
      SR:  0x2011
      D0: 0x00000000  D1: 0x00000041  D2: 0x00005250  D3: 0xFFFF0214
      D4: 0xFFFF000C  D5: 0xFFFFFFFF  D6: 0x0000000F  D7: 0x00000F3F
      A0: 0x0003C24D  A1: 0x50205743  A2: 0x00C01C18  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FF0000  A6: 0xFFFFFFFF  A7: 0x00FBD824
      USP: 0xFFFFFFFF  SSP: 0x00FBD824
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0EEE
      entries 0-15: 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
                    0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE 0x0EEE
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
    Plane Viewer:
      Layer A: uniform light-gray blocks with hard rectangular boundaries
      Layer B: uniform light-gray blocks with lower-half fill and hard boundaries

  frame_0375:
    CPU:
      PC:  0x5020574F
      SR:  0x2011
      D0: 0x00000000  D1: 0x00000041  D2: 0x00005250  D3: 0xFFFF0214
      D4: 0xFFFF000C  D5: 0xFFFFFFFF  D6: 0x0000000F  D7: 0x00000F3F
      A0: 0x0003C24D  A1: 0x50205743  A2: 0x00C01C18  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FF0000  A6: 0xFFFFFFFF  A7: 0x00F70C72
      USP: 0xFFFFFFFF  SSP: 0x00F6FC96
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0000
      entries 0-15: 0x0000 0x0000 0x0020 0x064E 0x0000 0x0020 0x064E 0x0000
                    0x0000 0x0020 0x064E 0x0000 0x0020 0x0000 0x064E 0x0000
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: black upper field + repeating green/magenta clustered rows in lower region (~35% coverage)
    Plane Viewer:
      Layer A: dense red/green repeating rows with horizontal banding
      Layer B: sparse diagonal red/green motifs on black upper region with gray lower region

  frame_0390:
    CPU:
      PC:  0x00000200
      SR:  0x2011
      D0: 0x00000000  D1: 0x00000041  D2: 0x00005250  D3: 0xFFFF0214
      D4: 0xFFFF000C  D5: 0xFFFFFFFF  D6: 0x0000000F  D7: 0x00000F3F
      A0: 0x0003C24D  A1: 0x50205743  A2: 0x00C01C18  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FF0000  A6: 0xFFFFFFFF  A7: 0x00EDD7A2
      USP: 0xFFFFFFFF  SSP: 0x00EDD7A2
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0000
      entries 0-15: 0x0000 0x0000 0x0020 0x0666 0x0000 0x0020 0x0666 0x0000
                    0x0000 0x0020 0x0666 0x0000 0x0020 0x0000 0x0666 0x0000
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: black top band + green border around magenta repeating block field; lower ~65% covered
    Plane Viewer:
      Layer A: dense red/green repeating rows with horizontal banding
      Layer B: structured magenta/green motif rows in upper region with mixed black/gray lower region

  frame_0405:
    CPU:
      PC:  0x5020578D
      SR:  0x0011
      D0: 0x00000000  D1: 0x00000041  D2: 0x00005250  D3: 0xFFFF0214
      D4: 0xFFFF000C  D5: 0xFFFFFFFF  D6: 0x0000000F  D7: 0x00000F3F
      A0: 0x0003C24D  A1: 0x50205743  A2: 0x00C01C18  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FF0000  A6: 0xFFFFFFFF  A7: 0x00E6D028
      USP: 0xFFFFFFFF  SSP: 0x00E6C6EA
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0000
      entries 0-15: 0x0000 0x0000 0x0020 0x0682 0x0000 0x0020 0x0682 0x0000
                    0x0000 0x0020 0x0682 0x0000 0x0020 0x0000 0x0682 0x0000
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: near-black field with sparse faint structured traces near lower edge
    Plane Viewer:
      Layer A: dense red/green repeating rows with horizontal banding
      Layer B: structured magenta/green motif rows in upper region with mixed black/gray lower region

  frame_0420:
    CPU:
      PC:  0x00000200
      SR:  0x2619
      D0: 0x00000011  D1: 0x00000041  D2: 0x00005250  D3: 0xFFFF0214
      D4: 0xFFFF000C  D5: 0xFFFFFFFF  D6: 0x0000000F  D7: 0x00000F3F
      A0: 0x0003B327  A1: 0x50205743  A2: 0x00C01C18  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FEA1C1  A6: 0xFFFFFFFF  A7: 0x00DDFCA6
      USP: 0xFFFFFFFF  SSP: 0x00DDFCA6
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0000
      entries 0-15: 0x0000 0x0020 0x06A4 0x0000 0x0020 0x06A4 0x0000 0x0020
                    0x06A4 0x0000 0x0020 0x06A4 0x0000 0x0020 0x06A4 0x0000
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: black upper half + dense green repeating horizontal/diagonal pattern in lower half
    Plane Viewer:
      Layer A: dense green repeating motifs with horizontal banding
      Layer B: dense green repeating motifs with horizontal banding

  frame_0435:
    CPU:
      PC:  0x00000200
      SR:  0x2619
      D0: 0x00000011  D1: 0x00000041  D2: 0x00005250  D3: 0xFFFF0214
      D4: 0xFFFF000C  D5: 0xFFFFFFFF  D6: 0x0000000F  D7: 0x00000F3F
      A0: 0x00032F12  A1: 0x50205743  A2: 0x00C01C18  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FC916D  A6: 0xFFFFFFFF  A7: 0x00DBA95E
      USP: 0xFFFFFFFF  SSP: 0x00DBA95E
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0000
      entries 0-15: 0x0000 0x0020 0x06A4 0x0000 0x0020 0x06A4 0x0000 0x0020
                    0x06A4 0x0000 0x0020 0x06A4 0x0000 0x0020 0x06A4 0x0000
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: black upper half + dense green repeating horizontal/diagonal pattern in lower half
    Plane Viewer:
      Layer A: dense green repeating motifs with horizontal banding
      Layer B: dense green repeating motifs with horizontal banding

  frame_0450:
    CPU:
      PC:  0x0007002A
      SR:  0x2600
      D0: 0x00000001  D1: 0x00000034  D2: 0x00008134  D3: 0xFFFF0214
      D4: 0xFFFF000C  D5: 0xFFFFFFFF  D6: 0x0000000F  D7: 0x00000F3F
      A0: 0x0002D99B  A1: 0x50205743  A2: 0x00C01C18  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FB3B91  A6: 0xFFFFFFFF  A7: 0x00D8FD12
      USP: 0xFFFFFFFF  SSP: 0x00D8FD12
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0000
      entries 0-15: 0x0000 0x0020 0x06A4 0x0000 0x0020 0x06A4 0x0000 0x0020
                    0x06A4 0x0000 0x0020 0x06A4 0x0000 0x0020 0x06A4 0x0000
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: near-black full field with very faint sparse lower traces
    Plane Viewer:
      Layer A: dense green repeating motifs with horizontal banding
      Layer B: dense green repeating motifs with horizontal banding

  frame_0465:
    CPU:
      PC:  0x0007002A
      SR:  0x2600
      D0: 0x00000001  D1: 0x00000034  D2: 0x00008134  D3: 0xFFFF0214
      D4: 0xFFFF000C  D5: 0xFFFFFFFF  D6: 0x0000000F  D7: 0x00000F3F
      A0: 0x0002D92C  A1: 0x50205743  A2: 0x00C01C18  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FB39D5  A6: 0xFFFFFFFF  A7: 0x00D8F816
      USP: 0xFFFFFFFF  SSP: 0x00D8F816
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0000
      entries 0-15: 0x0000 0x0020 0x06A4 0x0000 0x0020 0x06A4 0x0000 0x0020
                    0x06A4 0x0000 0x0020 0x06A4 0x0000 0x0020 0x06A4 0x0000
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: uniform black field; no visible structured content
    Plane Viewer:
      Layer A: dense green repeating motifs with horizontal banding
      Layer B: dense green repeating motifs with horizontal banding

  frame_0480:
    CPU:
      PC:  0x0007002A
      SR:  0x2600
      D0: 0x00000001  D1: 0x00000034  D2: 0x00008134  D3: 0xFFFF0214
      D4: 0xFFFF000C  D5: 0xFFFFFFFF  D6: 0x0000000F  D7: 0x00000F3F
      A0: 0x0002D88F  A1: 0x50205743  A2: 0x00C01C18  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FB3761  A6: 0xFFFFFFFF  A7: 0x00D8F10A
      USP: 0xFFFFFFFF  SSP: 0x00D8F10A
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0000
      entries 0-15: 0x0000 0x0020 0x06A4 0x0000 0x0020 0x06A4 0x0000 0x0020
                    0x06A4 0x0000 0x0020 0x06A4 0x0000 0x0020 0x06A4 0x0000
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: uniform black field; no visible structured content
    Plane Viewer:
      Layer A: dense green repeating motifs with horizontal banding
      Layer B: dense green repeating motifs with horizontal banding

  frame_0495:
    CPU:
      PC:  0x0007002A
      SR:  0x2600
      D0: 0x00000001  D1: 0x00000034  D2: 0x00008134  D3: 0xFFFF0214
      D4: 0xFFFF000C  D5: 0xFFFFFFFF  D6: 0x0000000F  D7: 0x00000F3F
      A0: 0x0002D80B  A1: 0x50205743  A2: 0x00C01C18  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FB3551  A6: 0xFFFFFFFF  A7: 0x00D8EB16
      USP: 0xFFFFFFFF  SSP: 0x00D8EB16
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0000
      entries 0-15: 0x0000 0x0020 0x06A4 0x0000 0x0020 0x06A4 0x0000 0x0020
                    0x06A4 0x0000 0x0020 0x06A4 0x0000 0x0020 0x06A4 0x0000
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: uniform black field; no visible structured content
    Plane Viewer:
      Layer A: dense green repeating motifs with horizontal banding
      Layer B: dense green repeating motifs with horizontal banding

  frame_0510:
    CPU:
      PC:  0x0007002A
      SR:  0x2600
      D0: 0x00000001  D1: 0x00000034  D2: 0x00008134  D3: 0xFFFF0214
      D4: 0xFFFF000C  D5: 0xFFFFFFFF  D6: 0x0000000F  D7: 0x00000F3F
      A0: 0x0002D7DE  A1: 0x50205743  A2: 0x00C01C18  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FB349D  A6: 0xFFFFFFFF  A7: 0x00D8E90E
      USP: 0xFFFFFFFF  SSP: 0x00D8E90E
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0000
      entries 0-15: 0x0000 0x0020 0x06A4 0x0000 0x0020 0x06A4 0x0000 0x0020
                    0x06A4 0x0000 0x0020 0x06A4 0x0000 0x0020 0x06A4 0x0000
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: uniform black field; no visible structured content
    Plane Viewer:
      Layer A: dense green repeating motifs with horizontal banding
      Layer B: dense green repeating motifs with horizontal banding

  frame_0525:
    CPU:
      PC:  0x0007002A
      SR:  0x2600
      D0: 0x00000001  D1: 0x00000034  D2: 0x00008134  D3: 0xFFFF0214
      D4: 0xFFFF000C  D5: 0xFFFFFFFF  D6: 0x0000000F  D7: 0x00000F3F
      A0: 0x0002D72C  A1: 0x50205743  A2: 0x00C01C18  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FB31D5  A6: 0xFFFFFFFF  A7: 0x00D8E10A
      USP: 0xFFFFFFFF  SSP: 0x00D8E10A
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0000
      entries 0-15: 0x0000 0x0020 0x06A4 0x0000 0x0020 0x06A4 0x0000 0x0020
                    0x06A4 0x0000 0x0020 0x06A4 0x0000 0x0020 0x06A4 0x0000
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: uniform black field; no visible structured content
    Plane Viewer:
      Layer A: dense green repeating motifs with horizontal banding
      Layer B: dense green repeating motifs with horizontal banding

  frame_0540:
    CPU:
      PC:  0x0007002A
      SR:  0x2600
      D0: 0x00000001  D1: 0x00000034  D2: 0x00008134  D3: 0xFFFF0214
      D4: 0xFFFF000C  D5: 0xFFFFFFFF  D6: 0x0000000F  D7: 0x00000F3F
      A0: 0x0002D6BD  A1: 0x50205743  A2: 0x00C01C18  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FB3019  A6: 0xFFFFFFFF  A7: 0x00D8DC0E
      USP: 0xFFFFFFFF  SSP: 0x00D8DC0E
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0000
      entries 0-15: 0x0000 0x0020 0x06A4 0x0000 0x0020 0x06A4 0x0000 0x0020
                    0x06A4 0x0000 0x0020 0x06A4 0x0000 0x0020 0x06A4 0x0000
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: uniform black field; no visible structured content
    Plane Viewer:
      Layer A: dense green repeating motifs with horizontal banding
      Layer B: dense green repeating motifs with horizontal banding

  frame_0555:
    CPU:
      PC:  0x0007002A
      SR:  0x2600
      D0: 0x00000001  D1: 0x00000034  D2: 0x00008134  D3: 0xFFFF0214
      D4: 0xFFFF000C  D5: 0xFFFFFFFF  D6: 0x0000000F  D7: 0x00000F3F
      A0: 0x0002D64E  A1: 0x50205743  A2: 0x00C01C18  A3: 0xFFFFFFFF
      A4: 0xFFFFFFFF  A5: 0x00FB2E5D  A6: 0xFFFFFFFF  A7: 0x00D8D712
      USP: 0xFFFFFFFF  SSP: 0x00D8D712
    VDP registers:
      Plane A base: 0x0E000
      Plane B base: 0x0C000
      Pattern base: 0x00000  ← read from frame, not assumed
      Window base:  0x0F000
    CRAM line 0:
      entry 0 (bg color): 0x0000
      entries 0-15: 0x0000 0x0020 0x06A4 0x0000 0x0020 0x06A4 0x0000 0x0020
                    0x06A4 0x0000 0x0020 0x06A4 0x0000 0x0020 0x06A4 0x0000
      additional visible line: unreadable
    Nametable 0xE000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xE000 row not visible)
      pattern: not assessed (0xE000 row not visible)
      decoded: not extracted (0xE000 row not visible)
    Nametable 0xC000 (16 entries):
      visible: NO — 0xDFC8-0xE784
      raw: not extracted (0xC000 row not visible)
      pattern: not assessed (0xC000 row not visible)
      decoded: not extracted (0xC000 row not visible)
    VRAM tile samples:
      pattern_base used: 0x00000 (from 4B, not assumed)
      no tile samples (no 0xE000 or 0xC000 nametable entries available for index selection)
    VDP Image: uniform black field; no visible structured content
    Plane Viewer:
      Layer A: dense green repeating motifs with horizontal banding
      Layer B: dense green repeating motifs with horizontal banding

Phase 5 — Cross-frame evolution:
  Frame    | PC           | A1           | E000 state                 | CRAM[0] | VDP Image
  ---------|--------------|--------------|----------------------------|---------|----------
  0165     | 0x00070112 | 0xFFFFFFFF | not visible (0xDFC8-0xE784) | 0x0EEE | black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
  0180     | 0x00070022 | 0x0003B2FB | not visible (0xDFC8-0xE784) | 0x0EEE | black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
  0195     | 0x0007001C | 0x0003B2FB | not visible (0xDFC8-0xE784) | 0x0EEE | black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
  0210     | 0x0007001C | 0x0003B2FB | not visible (0xDFC8-0xE784) | 0x0EEE | black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
  0225     | 0x00070022 | 0x0003B2FB | not visible (0xDFC8-0xE784) | 0x0EEE | black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
  0240     | 0x00070022 | 0x0003B2FB | not visible (0xDFC8-0xE784) | 0x0EEE | black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
  0255     | 0x00070022 | 0x0003C0BC | not visible (0xDFC8-0xE784) | 0x0EEE | black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
  0270     | 0x00070022 | 0x0003C0BC | not visible (0xDFC8-0xE784) | 0x0EEE | black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
  0285     | 0x0007001C | 0x0003C0BC | not visible (0xDFC8-0xE784) | 0x0EEE | black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
  0300     | 0x00070022 | 0x0003C0BC | not visible (0xDFC8-0xE784) | 0x0EEE | black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
  0315     | 0x00070022 | 0x0003C0BC | not visible (0xDFC8-0xE784) | 0x0EEE | black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
  0330     | 0x00070022 | 0x0003C0BC | not visible (0xDFC8-0xE784) | 0x0EEE | black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
  0345     | 0x00070022 | 0x0003C0BC | not visible (0xDFC8-0xE784) | 0x0EEE | black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
  0360     | 0x00000200 | 0x50205743 | not visible (0xDFC8-0xE784) | 0x0EEE | black upper band + uniform light-gray lower field; horizontal split, lower ~70% filled
  0375     | 0x5020574F | 0x50205743 | not visible (0xDFC8-0xE784) | 0x0000 | black upper field + repeating green/magenta clustered rows in lower region (~35% coverage)
  0390     | 0x00000200 | 0x50205743 | not visible (0xDFC8-0xE784) | 0x0000 | black top band + green border around magenta repeating block field; lower ~65% covered
  0405     | 0x5020578D | 0x50205743 | not visible (0xDFC8-0xE784) | 0x0000 | near-black field with sparse faint structured traces near lower edge
  0420     | 0x00000200 | 0x50205743 | not visible (0xDFC8-0xE784) | 0x0000 | black upper half + dense green repeating horizontal/diagonal pattern in lower half
  0435     | 0x00000200 | 0x50205743 | not visible (0xDFC8-0xE784) | 0x0000 | black upper half + dense green repeating horizontal/diagonal pattern in lower half
  0450     | 0x0007002A | 0x50205743 | not visible (0xDFC8-0xE784) | 0x0000 | near-black full field with very faint sparse lower traces
  0465     | 0x0007002A | 0x50205743 | not visible (0xDFC8-0xE784) | 0x0000 | uniform black field; no visible structured content
  0480     | 0x0007002A | 0x50205743 | not visible (0xDFC8-0xE784) | 0x0000 | uniform black field; no visible structured content
  0495     | 0x0007002A | 0x50205743 | not visible (0xDFC8-0xE784) | 0x0000 | uniform black field; no visible structured content
  0510     | 0x0007002A | 0x50205743 | not visible (0xDFC8-0xE784) | 0x0000 | uniform black field; no visible structured content
  0525     | 0x0007002A | 0x50205743 | not visible (0xDFC8-0xE784) | 0x0000 | uniform black field; no visible structured content
  0540     | 0x0007002A | 0x50205743 | not visible (0xDFC8-0xE784) | 0x0000 | uniform black field; no visible structured content
  0555     | 0x0007002A | 0x50205743 | not visible (0xDFC8-0xE784) | 0x0000 | uniform black field; no visible structured content

STOP triggered: NO

Files created:
  states/screenshots/build_38/ (563 frames)
  docs/design/Cody_vdp_ground_truth_build38.md

AGENTS_LOG.md: APPENDED
