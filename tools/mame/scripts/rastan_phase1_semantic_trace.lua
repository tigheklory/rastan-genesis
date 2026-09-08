--[[
rastan_phase1_semantic_trace.lua
================================
GENESIS NTSC human-played Round 1 Phase 1 semantic trace (reads-only).

Tighe plays Round 1 Phase 1 normally; this harness records, once per arcade-owned frame, the
relationship among:  camera/scroll X/Y  ->  entering rows/columns  ->  map-segment progression  ->
Genesis residency packages  ->  Plane A publication.  It also lets Tighe flag visible Layer-A
corruption with a keypress.

It is READS-ONLY inside emu.register_frame_done (no memory taps, no writes), so it is safe under the
MAME 68000 DRC and does not alter gameplay or timing beyond the per-frame read cost.  It captures no
code addresses (call-level tracing is unreliable under DRC); map-segment / package / publication
activity is inferred from the authoritative WRAM state each frame.

Outputs (into $TRACE_DIR):
  trace_metadata.txt      ROM/symbol/harness identity + summary
  phase1_frames.tsv       continuous per-frame state
  phase1_events.tsv       discrete semantic events (segment/package/boundary/dual-axis/user mark)

Env: TRACE_DIR, SYMFILE, ROM_NAME, ROM_SHA, SYMFILE_SHA, HARNESS_SHA, MARKER_KEY (default KEYCODE_M).
--]]

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing program space")

local trace_dir = assert(os.getenv("TRACE_DIR"), "TRACE_DIR required")
local symfile   = assert(os.getenv("SYMFILE"), "SYMFILE required")
local marker_token = os.getenv("MARKER_KEY") or "KEYCODE_M"

local S = {}
do
  for line in assert(io.lines(symfile)) do
    local name, addr = line:match("^%s*([%w_]+)%s+(0x[0-9A-Fa-f]+)")
    if name and addr then S[name] = tonumber(addr) end
  end
end
for _, n in ipairs({"genesistan_current_scene_id","active_record","active_package",
    "staged_scroll_x_fg","staged_scroll_y_fg","fg_row_dirty","fg_narrow_desc_count",
    "staged_fg_buffer","arcade_record"}) do
  assert(S[n], "missing trace symbol: " .. n)
end

local function r8(a)  return program:read_u8(a)  & 0xff end
local function r16(a) return program:read_u16(a) & 0xffff end
local function r32(a) return program:read_u32(a) & 0xffffffff end
local function s16(v) v = v & 0xffff; if v >= 0x8000 then v = v - 0x10000 end; return v end
local function pop(x) local c=0; while x~=0 do c=c+(x&1); x=x>>1 end return c end

-- signed per-frame delta of a 16-bit scroll value
local function sdelta(cur, prev) return s16((cur - prev) & 0xffff) end

-- checksum of the staged Plane-A name buffer (2048 words): sum + rolling xor
local function fg_checksum()
  local base = S.staged_fg_buffer
  local sum, x = 0, 0
  for i = 0, 2047 do
    local w = r16(base + i * 2)
    sum = (sum + w) & 0xffffffff
    x = x ~ w
  end
  return sum, x
end

os.execute('mkdir -p "' .. trace_dir .. '" 2>/dev/null')
local frames = assert(io.open(trace_dir .. "/phase1_frames.tsv", "w"))
local events = assert(io.open(trace_dir .. "/phase1_events.tsv", "w"))
local meta   = assert(io.open(trace_dir .. "/trace_metadata.txt", "w"))

meta:write(string.format("capture=rastan_genesis_round1_phase1_human_trace\n"))
meta:write(string.format("machine=%s\n", tostring(machine.system.name)))
meta:write(string.format("rom_name=%s\n", os.getenv("ROM_NAME") or "?"))
meta:write(string.format("rom_sha256=%s\n", os.getenv("ROM_SHA") or "?"))
meta:write(string.format("symbol_file=%s\n", symfile))
meta:write(string.format("symbol_file_sha256=%s\n", os.getenv("SYMFILE_SHA") or "?"))
meta:write(string.format("harness_sha256=%s\n", os.getenv("HARNESS_SHA") or "?"))
meta:write(string.format("marker_key=%s\n", marker_token))
meta:write(string.format("started=%s\n", os.date("!%Y-%m-%dT%H:%M:%SZ")))
meta:flush()

frames:write(table.concat({
  "frame","scene","arcade_record","active_record","active_package","active_variant",
  "pending_record","pending_package","epoch_trans","pattern_dma_trans","selector",
  "strip_index","strip_group","tileset","scene_a0",
  "scroll_x_fg","scroll_y_fg","dx_fg","dy_fg","scroll_x_bg","scroll_y_bg",
  "tiles_dirty","bg_rows","bg_mask","fg_rows","fg_mask","fg_narrow","fg_narrow_pend",
  "fg_owner","reseed","slots_ret","slots_reass","miss_a","miss_b",
  "fg_sum","fg_xor","lut034C"
}, "\t") .. "\n")
events:write("frame\tevent\tdetail\n")

local function ev(frame, name, detail)
  events:write(string.format("%d\t%s\t%s\n", frame, name, detail or ""))
  events:flush()
end

-- optional symbol reads (guarded)
local function rs16(n) return S[n] and r16(S[n]) or 0 end
local function rs8(n)  return S[n] and r8(S[n]) or 0 end
local function rs32(n) return S[n] and r32(S[n]) or 0 end

local input = machine.input
local marker_code = nil
do local ok, c = pcall(function() return input:code_from_token(marker_token) end); if ok then marker_code = c end end
local marker_prev = false

local frame = 0
local prev = { rec = -1, pkg = -1, sx = 0, sy = 0, txf = -1, tyf = -1, init = false }

emu.register_frame_done(function()
  frame = frame + 1
  local scene   = r8(S.genesistan_current_scene_id)
  local arec    = r16(S.arcade_record)
  local rec     = r16(S.active_record)
  local pkg     = r16(S.active_package)
  local sx_fg   = r16(S.staged_scroll_x_fg)
  local sy_fg   = r16(S.staged_scroll_y_fg)
  local sx_bg   = rs16("staged_scroll_x_bg")
  local sy_bg   = rs16("staged_scroll_y_bg")
  local fg_mask = r32(S.fg_row_dirty)
  local bg_mask = rs32("bg_row_dirty")
  local narrow  = r16(S.fg_narrow_desc_count)
  local fg_rows = pop(fg_mask)
  local bg_rows = pop(bg_mask)

  local dx = prev.init and sdelta(sx_fg, prev.sx) or 0
  local dy = prev.init and sdelta(sy_fg, prev.sy) or 0
  local sum, xr = fg_checksum()
  local lut034C = S.active_lut and r16(S.active_lut + 0x034C * 2) or 0

  frames:write(table.concat({
    frame, scene, arec, rec, pkg, rs16("active_variant"),
    rs16("pending_record"), rs16("pending_package"), rs32("epoch_transitions"),
    rs32("pattern_dma_transitions"), rs16("selector"), rs16("strip_index"),
    rs16("strip_group"), rs8("genesistan_current_tileset_id"),
    string.format("%08X", (rs32("scene_a0_lo"))),
    sx_fg, sy_fg, dx, dy, sx_bg, sy_bg,
    rs8("tiles_dirty"), bg_rows, string.format("%08X", bg_mask),
    fg_rows, string.format("%08X", fg_mask), narrow, rs16("fg_narrow_pending_rows"),
    rs8("fg_native_gameplay_owner"), rs8("reseed_pending"),
    rs32("slots_retained"), rs32("slots_reassigned"), rs32("miss_a"), rs32("miss_b"),
    string.format("%08X", sum), string.format("%04X", xr), string.format("%04X", lut034C)
  }, "\t") .. "\n")

  -- discrete events
  if prev.init and rec ~= prev.rec then
    ev(frame, "MAP_SEGMENT_CHANGE", string.format(
      "old=%d new=%d arcade_record=%d pkg=%d scroll_x_fg=%d scroll_y_fg=%d selector=%d",
      prev.rec, rec, arec, pkg, sx_fg, sy_fg, rs16("selector")))
  end
  if prev.init and pkg ~= prev.pkg then
    ev(frame, "RESIDENCY_PACKAGE_CHANGE", string.format(
      "old=%d new=%d map_segment=%d scroll_x_fg=%d scroll_y_fg=%d epoch_trans=%d",
      prev.pkg, pkg, rec, sx_fg, sy_fg, rs32("epoch_transitions")))
  end

  -- tile-boundary crossings (8px cells)
  local txf = sx_fg >> 3
  local tyf = sy_fg >> 3
  local x_cross = prev.init and (txf ~= prev.txf)
  local y_cross = prev.init and (tyf ~= prev.tyf)
  if x_cross then
    ev(frame, "X_BOUNDARY_CROSS", string.format(
      "scroll_x_fg=%d dx=%d fg_narrow=%d fg_rows=%d map_segment=%d pkg=%d", sx_fg, dx, narrow, fg_rows, rec, pkg))
  end
  if y_cross then
    ev(frame, "Y_BOUNDARY_CROSS", string.format(
      "scroll_y_fg=%d dy=%d fg_rows=%d fg_mask=%08X narrow=%d map_segment=%d pkg=%d",
      sy_fg, dy, fg_rows, fg_mask, narrow, rec, pkg))
  end
  if x_cross and y_cross then
    ev(frame, "DUAL_AXIS_CROSS", string.format(
      "dx=%d dy=%d fg_rows=%d fg_narrow=%d fg_mask=%08X map_segment=%d pkg=%d -- combined H+V (Plane-A bug regime)",
      dx, dy, fg_rows, narrow, fg_mask, rec, pkg))
  end
  -- combined publication in the same frame (row + column), the special-interest case
  if fg_rows > 0 and narrow > 0 then
    ev(frame, "DUAL_AXIS_PUBLICATION", string.format(
      "fg_rows=%d fg_mask=%08X fg_narrow=%d dx=%d dy=%d map_segment=%d pkg=%d",
      fg_rows, fg_mask, narrow, dx, dy, rec, pkg))
  end

  -- user visual-corruption marker
  if marker_code then
    local down = false
    local ok = pcall(function() down = input:code_pressed(marker_code) end)
    if ok and down and not marker_prev then
      ev(frame, "USER_MARK", string.format(
        "scene=%d map_segment=%d pkg=%d scroll_x_fg=%d scroll_y_fg=%d fg_rows=%d fg_narrow=%d fg_sum=%08X",
        scene, rec, pkg, sx_fg, sy_fg, fg_rows, narrow, sum))
    end
    marker_prev = (ok and down) or false
  end

  prev.rec, prev.pkg, prev.sx, prev.sy, prev.txf, prev.tyf, prev.init =
    rec, pkg, sx_fg, sy_fg, txf, tyf, true

  if frame % 300 == 0 then frames:flush() end
end)

local function finish()
  frames:flush(); events:flush()
  meta:write(string.format("ended=%s\n", os.date("!%Y-%m-%dT%H:%M:%SZ")))
  meta:write(string.format("total_frames=%d\n", frame))
  meta:close(); frames:close(); events:close()
end
_G.rastan_phase1_stop_sub = emu.add_machine_stop_notifier(function() pcall(finish) end)
emu.print_info("rastan_phase1_semantic_trace armed (marker key " .. marker_token .. ")")
