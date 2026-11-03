-- Build 0530, read-only, human-driven R1-S2 first-bad-write capture.
-- This script never writes game memory or controller input.  It records every
-- staged Plane-A write and full resident rows around genuine materialization.

local m = manager.machine
assert(m.system.name == "genesis", "requires GENESIS NTSC machine 'genesis'")
local cpu = assert(m.devices[":maincpu"])
local p = assert(cpu.spaces["program"])
local vdp = assert(m.devices[":gen_vdp"])
local vram = assert(vdp.spaces["videoram"])
local td = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")

local function envnum(name)
  local value = assert(os.getenv(name), name .. " missing")
  return assert(tonumber(value), name .. " invalid")
end
local A5 = 0x00ff0000
local STAGED = envnum("R1S2_STAGED_FG_ADDR")
local DIRTY = envnum("R1S2_FG_ROW_DIRTY_ADDR")
local PROVENANCE = envnum("R1S2_PROVENANCE_ADDR")
local SRC_REF = envnum("R1S2_SRC_REF_ADDR")
local FG_COMMIT = envnum("R1S2_PC_FG_COMMIT")
local SCROLL_COMMIT = envnum("R1S2_PC_SCROLL_COMMIT")
local MAT_ENTRY = 0x00070f16
local MAT_PRECOMPILED = 0x00070f9a
local MAT_CURRENT = 0x00070fa4
local MAT_PREV_SEL0 = 0x00070fae
local MAT_DYNAMIC_WRITE = 0x00071016
local MAT_SUFFIX_SETUP = 0x00071068
local MAT_SUFFIX_COPY = 0x0007108c
local MAT_MARK_DIRTY = 0x00071092
local MAT_EXIT = 0x000710b8
local PC_SELECTOR0 = envnum("R1S2_PC_SELECTOR0")
local PC_SELECTOR12 = envnum("R1S2_PC_SELECTOR12")
local PC_FG_FILL = envnum("R1S2_PC_FG_FILL")
local PC_PHASE3 = envnum("R1S2_PC_PHASE3")
local PLANE_A_BASE = 0x0000e000
local MAX_FRAMES = tonumber(os.getenv("TRACE_MAX_FRAMES") or "0") or 0

local function r8(a) return p:read_u8(a) & 0xff end
local function r16(a) return p:read_u16(a) & 0xffff end
local function r32(a) return p:read_u32(a) & 0xffffffff end
local function vr16(a)
  return (((vram:read_u8(a) & 0xff) << 8) | (vram:read_u8(a + 1) & 0xff)) & 0xffff
end
local function reg(name)
  local state = cpu.state[name]
  return state and (state.value & 0xffffffff) or 0
end
local function hx(v, digits) return string.format("%0" .. digits .. "X", v) end
local function hash(words)
  local h = 2166136261
  for _, word in ipairs(words) do h = ((h ~ word) * 16777619) & 0xffffffff end
  return h
end
local function row_words(space, row)
  local words = {}
  local base = row * 0x80
  for col = 0, 63 do
    words[#words + 1] = space == "staged" and r16(STAGED + base + col * 2)
      or vr16(PLANE_A_BASE + base + col * 2)
  end
  return words
end
local function words_text(words)
  local out = {}
  for i, word in ipairs(words) do out[i] = hx(word, 4) end
  return table.concat(out, ",")
end
local function dirty_bit(row) return ((r32(DIRTY) >> row) & 1) end
local function relation(logical, tag)
  if tag == 0 then return "invalid" end
  local owner = (tag - 1) & 63
  if owner == logical then return "exact_owner" end
  if owner == ((logical + 32) & 63) then return "N+32_alias" end
  if owner == ((logical - 32) & 63) then return "N-32_alias" end
  return "other"
end
local function state_text()
  return table.concat({
    "fg_y=" .. hx(r16(A5 + 0x10b0), 4),
    "record=" .. hx(r16(A5 + 0x013e), 4),
    "selector=" .. hx(r16(A5 + 0x10a8), 4),
    "completed_selector=" .. hx(r16(A5 + 0x132c), 4),
    "strip=" .. hx(r16(A5 + 0x10ca), 4),
    "group=" .. hx(r16(A5 + 0x10cc), 4),
    "ring_front=" .. tostring(((r16(A5 + 0x10cc) & 15) * 4 + (r16(A5 + 0x10ca) & 3)) & 63),
    "player_x=" .. hx(r16(A5 + 0x10be), 4),
    "player_y=" .. hx(r16(A5 + 0x10c0), 4)
  }, ";")
end

local rows = assert(io.open(td .. "/rows.tsv", "w"))
local writes = assert(io.open(td .. "/ordered_writes.tsv", "w"))
local events = assert(io.open(td .. "/events.tsv", "w"))
local frames = assert(io.open(td .. "/frames.tsv", "w"))
local markers = assert(io.open(td .. "/markers.tsv", "w"))
local meta = assert(io.open(td .. "/metadata.txt", "w"))
rows:write("frame\tevent_id\tphase\tlogical\tphysical\towner_tag\trelation\tdirty\thash\twords_64\tstate\n")
writes:write("sequence\tframe\tevent_id\twriter\tpc\tphysical\tcolumn\told_word\tnew_word\towner_before\tdirty_before\tstate\n")
events:write("sequence\tframe\tevent_id\tevent\tpc\tlogical\tphysical\tdetail\tregisters\tstate\n")
frames:write("frame\tfg_y\tdelta\tdirection\trecord\tselector\tcompleted_selector\tstrip\tgroup\trow_dirty\n")
markers:write("frame\tevent_id\tfg_y\trecord\tselector\tplayer_x\tplayer_y\n")
meta:write("platform=GENESIS NTSC MAME\nmachine=genesis\n")
meta:write("purpose=Build 0530 first incorrect Plane-A write, pre-write resident evidence\n")
meta:write("input_policy=manual only; no game-memory, ROM, or controller writes\n")
meta:write("rom=" .. (os.getenv("ROM_NAME") or "UNKNOWN") .. "\n")
meta:write("rom_sha256=" .. (os.getenv("ROM_SHA") or "UNKNOWN") .. "\n")
meta:write("rom_source_commit=" .. (os.getenv("ROM_SOURCE_COMMIT") or "UNKNOWN") .. "\n")
meta:write("marker_key=M\nstarted=" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\n")

local frame, sequence, event_id = 0, 0, 0
local active = nil
local last_y = nil
local closed = false
local taps = {}
local marker = assert(m.input:code_from_token("KEYCODE_M"))
local marker_down = false
local debuglog = m.debugger and m.debugger.consolelog or nil
local debug_index = debuglog and #debuglog or 0

local function registers()
  return table.concat({
    "D0=" .. hx(reg("D0"), 8), "D1=" .. hx(reg("D1"), 8),
    "D2=" .. hx(reg("D2"), 8), "D7=" .. hx(reg("D7"), 8),
    "A0=" .. hx(reg("A0"), 8), "A4=" .. hx(reg("A4"), 8),
    "A6=" .. hx(reg("A6"), 8), "src_ref=" .. hx(r16(SRC_REF), 4)
  }, ";")
end
local function emit_event(name, logical, physical, detail)
  sequence = sequence + 1
  events:write(table.concat({sequence, frame, active and active.id or 0, name,
    hx(reg("PC") & 0xffffff, 6), logical or "", physical or "", detail or "",
    registers(), state_text()}, "\t"), "\n")
end
local function emit_row(phase, logical, physical)
  local tag = r8(PROVENANCE + physical)
  local sw = row_words("staged", physical)
  rows:write(table.concat({frame, active and active.id or 0, phase, logical, physical,
    hx(tag, 2), relation(logical, tag), dirty_bit(physical), hx(hash(sw), 8),
    words_text(sw), state_text()}, "\t"), "\n")
end
local function emit_vdp_row(phase, logical, physical)
  local tag = r8(PROVENANCE + physical)
  local vw = row_words("vdp", physical)
  rows:write(table.concat({frame, active and active.id or 0, phase, logical, physical,
    hx(tag, 2), relation(logical, tag), dirty_bit(physical), hx(hash(vw), 8),
    words_text(vw), state_text()}, "\t"), "\n")
end
local function on_materialize_entry(forced_logical)
  event_id = event_id + 1
  local logical = forced_logical or (reg("D0") & 63)
  local physical = logical & 31
  active = {id=event_id, logical=logical, physical=physical}
  emit_row("PRE_STAGED", logical, physical)
  emit_vdp_row("PRE_VDP", logical, physical)
  local tag = r8(PROVENANCE + physical)
  emit_event("MATERIALIZE_ENTRY", logical, physical,
    "owner_tag=" .. hx(tag, 2) .. ";relation=" .. relation(logical, tag))
end
local function branch(name)
  local logical = active and active.logical or (reg("D0") & 63)
  local physical = active and active.physical or (logical & 31)
  emit_event(name, logical, physical, "materializer decision")
end
local function on_materialize_exit()
  if not active then return end
  emit_row("POST_STAGED", active.logical, active.physical)
  emit_event("MATERIALIZE_EXIT", active.logical, active.physical,
    "owner_tag=" .. hx(r8(PROVENANCE + active.physical), 2) ..
    ";dirty=" .. dirty_bit(active.physical))
end
local function on_commit(name)
  emit_event(name, active and active.logical or nil, active and active.physical or nil, "publication ordering")
  if name == "SCROLL_COMMIT" and active then
    emit_vdp_row("POST_PUBLICATION_VDP", active.logical, active.physical)
    active = nil
  end
end
local function writer(pc)
  if pc >= 0x070f16 and pc <= 0x0710b8 then return "no_publication_materializer" end
  if pc >= PC_SELECTOR0 and pc < PC_SELECTOR12 then return "selector0" end
  if pc >= PC_SELECTOR12 and pc < 0x070af2 then return "selector12" end
  if pc >= PC_FG_FILL and pc < PC_PHASE3 then return "fg_fill" end
  if pc >= PC_PHASE3 and pc < PC_PHASE3 + 0x400 then return "phase3_animation" end
  return "other"
end

local execution_points = {
  {MAT_ENTRY,"MATERIALIZE_ENTRY"},
  {MAT_PRECOMPILED,"SOURCE_PRECOMPILED_COPY"}, {MAT_CURRENT,"SOURCE_CURRENT_DYNAMIC"},
  {MAT_PREV_SEL0,"SOURCE_PREVIOUS_SELECTOR0"}, {MAT_DYNAMIC_WRITE,"DYNAMIC_CELL_WRITE"},
  {MAT_SUFFIX_SETUP,"PREDECESSOR_SUFFIX_SETUP"}, {MAT_SUFFIX_COPY,"PREDECESSOR_SUFFIX_COPY"},
  {MAT_MARK_DIRTY,"MARK_DIRTY_AND_OWNER"}, {MAT_EXIT,"MATERIALIZE_EXIT"},
  {FG_COMMIT,"PLANE_A_COMMIT"}, {SCROLL_COMMIT,"SCROLL_COMMIT"}
}
local execute_mechanism
if type(p.install_execute_tap) == "function" then
  execute_mechanism = "execute_tap"
  for _, item in ipairs(execution_points) do
    local pc, name = item[1], item[2]
    taps[#taps + 1] = p:install_execute_tap(pc, pc, "r1s2_" .. name, function()
      if name == "MATERIALIZE_ENTRY" then on_materialize_entry()
      elseif name == "MATERIALIZE_EXIT" then on_materialize_exit()
      elseif name == "PLANE_A_COMMIT" or name == "SCROLL_COMMIT" then on_commit(name)
      else branch(name) end
    end)
  end
else
  execute_mechanism = "debugger_breakpoints_plus_prewrite_tap"
  assert(debuglog, "this MAME needs -debug -debugger none for execution events")
  for _, item in ipairs(execution_points) do
    cpu.debug:bpset(item[1], "1", string.format('printf "R1S2FIRST,%s,%%06X\\n",pc; g', item[2]))
  end
  m.debugger:command("go")
end
meta:write("execution_event_mechanism=" .. execute_mechanism .. "\n")

local function drain_debug()
  if not debuglog then return end
  for i = debug_index + 1, #debuglog do
    local name, pc = tostring(debuglog[i]):match("^R1S2FIRST,([A-Z0-9_]+),([0-9A-Fa-f]+)")
    if name then
      sequence = sequence + 1
      events:write(table.concat({sequence,frame,active and active.id or 0,name,pc,"","",
        "debugger execution event (ordered within debugger stream)","captured_by_debugger",state_text()},"\t"),"\n")
    end
  end
  debug_index = #debuglog
end

taps[#taps + 1] = p:install_write_tap(STAGED, STAGED + 0x0fff, "r1s2_all_staged_writes", function(off, data, mask)
  local rel = off - STAGED
  local physical, column = (rel >> 7) & 31, (rel >> 1) & 63
  local old = r16(off & 0xfffffe)
  local pc = reg("PC") & 0xffffff
  if not active and pc >= MAT_ENTRY and pc <= MAT_EXIT then
    -- On MAME versions without execute taps, SP points at this helper's two
    -- local words at each actual row store; word 0 is the requested logical row.
    on_materialize_entry(r16(reg("SP")) & 63)
  end
  sequence = sequence + 1
  writes:write(table.concat({sequence, frame, active and active.id or 0, writer(pc), hx(pc, 6),
    physical, column, hx(old, 4), hx(data & 0xffff, 4), hx(r8(PROVENANCE + physical), 2),
    dirty_bit(physical), state_text()}, "\t"), "\n")
  return data
end)
taps[#taps + 1] = p:install_write_tap(PROVENANCE, PROVENANCE + 31, "r1s2_owner_writes", function(off,data,mask)
  local pc = reg("PC") & 0xffffff
  if active and pc >= MAT_ENTRY and pc <= MAT_EXIT and (off - PROVENANCE) == active.physical then
    emit_row("POST_STAGED_PRE_OWNER_STORE", active.logical, active.physical)
    emit_event("MATERIALIZER_OWNER_STORE", active.logical, active.physical,
      "old_tag="..hx(r8(off),2)..";new_tag="..hx(data&0xff,2)..";dirty="..dirty_bit(active.physical))
  end
  return data
end)
_G.r1s2_first_bad_genesis_taps = taps

local function close()
  if closed then return end
  closed = true
  meta:write("ended=" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\nframes=" .. frame .. "\nevents=" .. event_id .. "\n")
  for _, f in ipairs({rows,writes,events,frames,markers,meta}) do f:flush(); f:close() end
end
emu.register_frame_done(function()
  frame = frame + 1
  drain_debug()
  local y = r16(A5 + 0x10b0)
  local delta = last_y and (((y - last_y + 0x8000) & 0xffff) - 0x8000) or 0
  local direction = delta < 0 and "up" or (delta > 0 and "down" or "none")
  frames:write(table.concat({frame,hx(y,4),delta,direction,hx(r16(A5+0x013e),4),
    hx(r16(A5+0x10a8),4),hx(r16(A5+0x132c),4),hx(r16(A5+0x10ca),4),
    hx(r16(A5+0x10cc),4),hx(r32(DIRTY),8)}, "\t"), "\n")
  last_y = y
  local down = false
  pcall(function() down = m.input:code_pressed(marker) end)
  if down and not marker_down then
    markers:write(table.concat({frame,active and active.id or 0,hx(y,4),hx(r16(A5+0x013e),4),
      hx(r16(A5+0x10a8),4),hx(r16(A5+0x10be),4),hx(r16(A5+0x10c0),4)}, "\t"), "\n")
    emit_event("USER_MARK", active and active.logical or nil, active and active.physical or nil, "M pressed")
    emu.print_info("R1-S2 first-bad-write marker recorded at frame " .. frame)
  end
  marker_down = down
  if active then
    -- Frame-done occurs after VBlank publication.  Preserve the exact staged
    -- result and actual Plane-A row before associating the next event.
    emit_row("FRAME_END_STAGED", active.logical, active.physical)
    emit_vdp_row("FRAME_END_VDP", active.logical, active.physical)
    emit_event("FRAME_END_AFTER_PUBLICATION", active.logical, active.physical, "active materialization completed this frame")
    active = nil
  end
  if frame % 60 == 0 then for _, f in ipairs({rows,writes,events,frames,markers}) do f:flush() end end
  if MAX_FRAMES > 0 and frame >= MAX_FRAMES then close(); m:exit() end
end)
_G.r1s2_first_bad_genesis_stop = emu.add_machine_stop_notifier(close)
emu.print_info("Build 0530 first-bad-write trace armed; play manually and press M when corruption first appears")
