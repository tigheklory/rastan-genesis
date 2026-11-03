-- Original Rastan, read-only, human-driven PC080SN resident-row oracle.
-- No ROM, RAM, or input writes.  An initial 64x64 name-RAM image plus every
-- later write permits exact reconstruction at any captured semantic event.

local m = manager.machine
assert(m.system.name == "rastan", "requires original arcade machine 'rastan'")
local cpu = assert(m.devices[":maincpu"])
local p = assert(cpu.spaces["program"])
local td = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")
local A5 = 0x0010c000
local FG = 0x00c08000
local MAX_FRAMES = tonumber(os.getenv("TRACE_MAX_FRAMES") or "0") or 0
local PCs = {
  NO_PUBLICATION_UP=0x055704,
  NO_PUBLICATION_DOWN=0x055790,
  RECORD_ADVANCE=0x0558e0,
  RECORD_ADVANCE_COMMIT=0x0558e8,
  ORDINARY_ROW_AUTHOR=0x055a14
}

local function r8(a) return p:read_u8(a) & 0xff end
local function r16(a) return p:read_u16(a) & 0xffff end
local function r32(a) return p:read_u32(a) & 0xffffffff end
local function reg(name)
  local state = cpu.state[name]
  return state and (state.value & 0xffffffff) or 0
end
local function hx(v, n) return string.format("%0" .. n .. "X", v) end
local function state_text()
  local y = r16(A5 + 0x10b0)
  local visible_top = (((-y + 8) & 0x01ff) >> 3) & 63
  return table.concat({
    "fg_y=" .. hx(y,4), "visible_top=" .. visible_top,
    "record=" .. hx(r16(A5+0x013e),4), "selector=" .. hx(r16(A5+0x10a8),4),
    "completed_selector=" .. hx(r16(A5+0x132c),4),
    "strip=" .. hx(r16(A5+0x10ca),4), "group=" .. hx(r16(A5+0x10cc),4),
    "ring_front=" .. tostring(((r16(A5+0x10cc)&15)*4+(r16(A5+0x10ca)&3))&63),
    "player_x=" .. hx(r16(A5+0x10be),4), "player_y=" .. hx(r16(A5+0x10c0),4)
  }, ";")
end
local function registers()
  return table.concat({"D0="..hx(reg("D0"),8),"D1="..hx(reg("D1"),8),
    "D2="..hx(reg("D2"),8),"A0="..hx(reg("A0"),8),"A1="..hx(reg("A1"),8),
    "A2="..hx(reg("A2"),8)}, ";")
end

local events = assert(io.open(td .. "/events.tsv", "w"))
local writes = assert(io.open(td .. "/ordered_name_ram_writes.tsv", "w"))
local markers = assert(io.open(td .. "/markers.tsv", "w"))
local rows = assert(io.open(td .. "/marker_rows.tsv", "w"))
local meta = assert(io.open(td .. "/metadata.txt", "w"))
events:write("sequence\tframe\tevent\tpc\tregisters\tstate\n")
writes:write("sequence\tframe\tpc\tphysical_row\tcolumn\tcell_word\told_word\tnew_word\tstate\n")
markers:write("frame\tsequence\tstate\n")
rows:write("frame\tphysical_row\thash\tcells_64_attr_tile\tstate\n")
meta:write("platform=ORIGINAL ARCADE MAME\nmachine=rastan\n")
meta:write("purpose=authoritative PC080SN C08000 resident-row oracle\n")
meta:write("input_policy=manual only; no ROM, RAM, or controller writes\n")
meta:write("name_ram=0xC08000-0xC0BFFF; 64 rows x 64 cells x attr/tile words\n")
meta:write("marker_key=M\nstarted=" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\n")

local frame, sequence = 0, 0
local closed, baseline = false, false
local taps = {}
local marker = assert(m.input:code_from_token("KEYCODE_M"))
local marker_down = false
local debuglog = m.debugger and m.debugger.consolelog or nil
local debug_index = debuglog and #debuglog or 0

local function snapshot_binary(name)
  local f = assert(io.open(td .. "/" .. name, "wb"))
  local chunk = {}
  for offset = 0, 0x3fff do
    chunk[#chunk + 1] = string.char(r8(FG + offset))
    if #chunk == 4096 then f:write(table.concat(chunk)); chunk = {} end
  end
  if #chunk > 0 then f:write(table.concat(chunk)) end
  f:close()
end
local function row_cells(row)
  local cells, h = {}, 2166136261
  for col = 0, 63 do
    local base = FG + row * 0x100 + col * 4
    local attr, tile = r16(base), r16(base + 2)
    cells[#cells + 1] = hx(attr,4) .. ":" .. hx(tile,4)
    h = ((h ~ attr) * 16777619) & 0xffffffff
    h = ((h ~ tile) * 16777619) & 0xffffffff
  end
  return table.concat(cells, ","), h
end
local function dump_rows()
  for row = 0, 63 do
    local cells, h = row_cells(row)
    rows:write(table.concat({frame,row,hx(h,8),cells,state_text()}, "\t"), "\n")
  end
  rows:flush()
end
local function ensure_baseline(reason)
  if baseline then return end
  baseline = true
  snapshot_binary("initial_pc080sn_c08000.bin")
  sequence = sequence + 1
  events:write(table.concat({sequence,frame,"BASELINE_SNAPSHOT_"..reason,hx(reg("PC")&0xffffff,6),registers(),state_text()},"\t"),"\n")
end
local function semantic_event(name)
  -- R1-S2 retained records begin at 16.  Do not create a large R1-S1 oracle;
  -- the user still plays there naturally, but capture begins at the target range.
  if not baseline and r16(A5 + 0x013e) < 16 then return end
  ensure_baseline(name)
  sequence = sequence + 1
  events:write(table.concat({sequence,frame,name,hx(reg("PC")&0xffffff,6),registers(),state_text()},"\t"),"\n")
end

if type(p.install_execute_tap) == "function" then
  meta:write("execution_event_mechanism=execute_tap\n")
  for name, pc in pairs(PCs) do
    local event_name = name
    taps[#taps + 1] = p:install_execute_tap(pc, pc, "r1s2_arcade_"..name,
      function() semantic_event(event_name) end)
  end
else
  assert(debuglog, "this MAME needs -debug -debugger none for execution events")
  meta:write("execution_event_mechanism=debugger_breakpoints\n")
  for name, pc in pairs(PCs) do
    cpu.debug:bpset(pc, "1", string.format('printf "R1S2ARC,%s,%%06X\\n",pc; g', name))
  end
  m.debugger:command("go")
end

local function drain_debug()
  if not debuglog then return end
  for i = debug_index + 1, #debuglog do
    local name, pc = tostring(debuglog[i]):match("^R1S2ARC,([A-Z0-9_]+),([0-9A-Fa-f]+)")
    if name and (baseline or r16(A5 + 0x013e) >= 16) then
      ensure_baseline(name)
      sequence = sequence + 1
      events:write(table.concat({sequence,frame,name,pc,"captured_by_debugger",state_text()},"\t"),"\n")
    end
  end
  debug_index = #debuglog
end
taps[#taps + 1] = p:install_write_tap(FG, FG + 0x3fff, "r1s2_arcade_fg_writes", function(off,data,mask)
  if not baseline and r16(A5 + 0x013e) >= 16 then ensure_baseline("RECORD_16") end
  if baseline then
    local rel = off - FG
    local row, col, cell_word = (rel >> 8) & 63, (rel >> 2) & 63, (rel >> 1) & 1
    sequence = sequence + 1
    writes:write(table.concat({sequence,frame,hx(reg("PC")&0xffffff,6),row,col,cell_word,
      hx(r16(off & 0xfffffe),4),hx(data&0xffff,4),state_text()},"\t"),"\n")
  end
  return data
end)
_G.r1s2_arcade_oracle_taps = taps

local function close()
  if closed then return end
  closed = true
  if baseline then snapshot_binary("final_pc080sn_c08000.bin") end
  meta:write("ended="..os.date("!%Y-%m-%dT%H:%M:%SZ").."\nframes="..frame.."\nsequence="..sequence.."\n")
  for _, f in ipairs({events,writes,markers,rows,meta}) do f:flush(); f:close() end
end
emu.register_frame_done(function()
  frame = frame + 1
  drain_debug()
  local down = false
  pcall(function() down = m.input:code_pressed(marker) end)
  if down and not marker_down then
    ensure_baseline("USER_MARK")
    sequence = sequence + 1
    markers:write(table.concat({frame,sequence,state_text()},"\t"),"\n")
    semantic_event("USER_MARK")
    dump_rows()
    emu.print_info("Original-arcade resident oracle marker and all 64 rows captured at frame "..frame)
  end
  marker_down = down
  if frame % 60 == 0 then events:flush(); writes:flush(); markers:flush() end
  if MAX_FRAMES > 0 and frame >= MAX_FRAMES then close(); m:exit() end
end)
_G.r1s2_arcade_oracle_stop = emu.add_machine_stop_notifier(close)
emu.print_info("Original Rastan resident-row oracle armed; play manually and press M at corresponding R1-S2 traversal points")
