-- ORIGINAL ARCADE Rastan reusable marker capture harness (read-only; no ROM/RAM/input writes).
--
-- ONE capture that records, at user-marked frames during a single manual play session, the complete
-- evidence needed to resolve warrior weapon variants (hammer/axe) AND every R1-S2 tile/sprite hazard
-- (floor spikes, moving wooden gate, moving spiked traps, falling water, pit flames). It does NOT decide
-- identities -- it preserves the raw owner/write evidence so the owner/table can be followed in the
-- existing Ghidra/decompilation workflow afterward.
--
-- Reuses established repo facts (do NOT re-derive):
--   * actor array (arcade_actor_renderer_verify.lua): A5=0x10c000; blocks at +0x2c8(9)/+0x508(2)/
--     +0x5c8(6)/+0x748(11)/+0x8c8(5), slot stride 0x40; fields anim+01, facing+02, state+03, rtype+06,
--     subframe+0b, x+16, y+1a, base+1e, mirror+20, +21, attr+27, compositor+38, family+3e, +752.
--   * PC090OJ object RAM at 0xD00000; per-piece record = [control(word0), Y(word1), code(word2), X(word3)]
--     (Andy RG006); word0 low nibble = palette line; flip/priority live in word0 (preserved raw).
--   * PC080SN name RAM 0xC00000-0xC0FFFF (arcade_subround_cheat_probe.lua): Plane A >=0xC08000, else Plane B.
--   * Palette/CRAM shadow at 0x200000 (bank*32 + index*2), banks 0x30-0x3f used by sprites.
--   * marker-key edge detection + install_write_tap (r1s2_resident_oracle_arcade.lua).
--
-- Env:
--   TRACE_DIR                 (required) output directory.
--   CAPTURE_MARKER_KEY        marker key token (default KEYCODE_M).
--   CAPTURE_ROLL_FRAMES       rolling pre-marker history window in frames (default 180 ~ 3s).
--   CAPTURE_AUTO_MARK_FRAMES  comma list of frames to auto-fire a marker (SMOKE TEST ONLY; no human input).
--   CAPTURE_COLLISION_ADDR    optional hex absolute addr of a collision/state word to sample at markers.
--   CAPTURE_MAX_FRAMES        stop after N frames (0 = run until MAME exits).

local m = manager.machine
assert(m.system.name == "rastan", "requires the ORIGINAL ARCADE machine 'rastan' (not the Genesis target)")
local cpu = assert(m.devices[":maincpu"])
local p = assert(cpu.spaces["program"])

local td = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")
local MARKER_TOKEN = os.getenv("CAPTURE_MARKER_KEY") or "KEYCODE_M"
local ROLL = tonumber(os.getenv("CAPTURE_ROLL_FRAMES") or "180") or 180
local MAX_FRAMES = tonumber(os.getenv("CAPTURE_MAX_FRAMES") or "0") or 0
local COLLISION_ADDR = tonumber(os.getenv("CAPTURE_COLLISION_ADDR") or "0") or 0
local AUTO = {}
for s in (os.getenv("CAPTURE_AUTO_MARK_FRAMES") or ""):gmatch("%d+") do AUTO[tonumber(s)] = true end

local A5  = 0x0010c000
local OBJ = 0x00d00000
local FG_A = 0x00c08000               -- Plane A base; Plane B is 0xC00000..0xC07FFF
local PAL = 0x00200000

local function r8(a)  local ok,v = pcall(function() return p:read_u8(a)  end); return ok and (v & 0xff)     or 0 end
local function r16(a) local ok,v = pcall(function() return p:read_u16(a) end); return ok and (v & 0xffff)   or 0 end
local function r32(a) local ok,v = pcall(function() return p:read_u32(a) end); return ok and (v & 0xffffffff) or 0 end
local function hx(v,n) return string.format("%0"..n.."X", v & ((1 << (n*4)) - 1)) end
local function pc() local s = cpu.state["PC"]; return s and (s.value & 0xffffff) or 0 end

-- Established actor blocks (reused verbatim from arcade_actor_renderer_verify.lua).
local blocks = { {"actor_2c8",0x02c8,9}, {"actor_508",0x0508,2}, {"actor_5c8",0x05c8,6},
                 {"actor_748",0x0748,11}, {"actor_8c8",0x08c8,5} }
local function owned_range(name, index, boss)
  if boss then
    if name == "actor_5c8" then return 140 + math.min(index,3)*10 + math.max(index-3,0)*20, (index<3) and 10 or 20 end
    if name == "actor_748" then return 46 + index*6, 6 end
    if name == "actor_8c8" then return 96 + index*4, 4 end
  else
    if name == "actor_2c8" then return 140 + index*10, (index==8) and 19 or 10 end
    if name == "actor_508" then return 57 + index*13, 13 end
    if name == "actor_5c8" then return 96 + index*4, 4 end
    if name == "actor_748" then return 46 + index, 1 end
  end
  return -1, 0
end
local compositor_tables = {[0]=0x3d09e,[1]=0x4771c,[2]=0x3f0ce,[3]=0x40004,[4]=0x4002c}

local function state_text()
  return table.concat({
    "round="..hx(r8(A5+0x118),2), "progression_13e="..hx(r16(A5+0x13e),4),
    "renderer_mode="..hx(r16(A5+0x2a2),4), "selector="..hx(r16(A5+0x10a8),4),
    "player_x="..hx(r16(A5+0x10be),4), "player_y="..hx(r16(A5+0x10c0),4),
    "fg_y="..hx(r16(A5+0x10b0),4)
  }, ";")
end

-- Output files.
local meta    = assert(io.open(td.."/metadata.txt", "w"))
local markers = assert(io.open(td.."/markers.tsv", "w"))
local actors  = assert(io.open(td.."/actors.tsv", "w"))
local objs    = assert(io.open(td.."/pc090oj.tsv", "w"))
local p80      = assert(io.open(td.."/pc080sn_writes.tsv", "w"))
local cram    = assert(io.open(td.."/cram_writes.tsv", "w"))
local coll    = assert(io.open(td.."/collision.tsv", "w"))

meta:write("platform=ORIGINAL ARCADE MAME\nmachine=rastan\n")
meta:write("purpose=reusable marker capture: actor records + PC090OJ records + PC080SN writes + CRAM writes\n")
meta:write("input_policy=manual only; read-only; no ROM/RAM/controller writes\n")
meta:write("marker_key="..MARKER_TOKEN.."\nroll_frames="..ROLL.."\n")
meta:write("actor_array=A5(0x10c000)+{0x2c8*9,0x508*2,0x5c8*6,0x748*11,0x8c8*5} stride 0x40; raw64 preserved\n")
meta:write("pc090oj=0xD00000 rec*8 = [control(w0),Y(w1),code(w2),X(w3)]; line=w0&0x0f; flip in w0\n")
meta:write("pc080sn=0xC00000-0xC0FFFF; PlaneA>=0xC08000 else PlaneB; cell=attr(w0)+tile(w1)\n")
meta:write("cram=0x200000 bank*32+idx*2 (banks 0x30-0x3f sprites)\n")
meta:write("started="..os.date("!%Y-%m-%dT%H:%M:%SZ").."\n")
markers:write("marker_index\tframe\tpc\tstate\n")
actors:write("marker_index\tframe\tblock\tindex\tactor_addr\talive\tbase_1e\tanim_01\tstate_03\tstate_05\tfacing_02\tmode_family_3e\tf21\tattr_27\tmirror_20\tcompositor_38\tx_16\ty_1a\tprogram_ptr\traw64\n")
objs:write("marker_index\tframe\towner_block\towner_index\towner_addr\trecord\tcontrol_w0\tline\thflip\tvflip\tcode_w2\ty_w1\tx_w3\traw4\n")
p80:write("marker_index\tframe\tpc\tlayer\tabs_addr\tphys_row\tphys_col\tword_sel\tattr_w0\ttile_w1\tnew\tfg_y\tselector\n")
cram:write("marker_index\tframe\tpc\tbank\tindex\tabs_addr\tnew_word\n")
coll:write("marker_index\tframe\tkind\taddr\tvalue\tnote\n")

-- Rolling history (pruned every frame to the last ROLL frames) so the pre-marker transition is preserved.
local roll_p80, roll_cram = {}, {}
local frame = 0
local marker_index = 0
local marker_down = false
local closed = false
local taps = {}

local function prune(buf)
  local cut = frame - ROLL
  while buf[1] and buf[1].f < cut do table.remove(buf, 1) end
end

-- Full snapshot of live actors + their emitted PC090OJ records, correlated by owner.
local function snapshot(mi)
  local boss = r16(A5 + 0x2a2) == 2
  for _, b in ipairs(blocks) do
    for index = 0, b[3]-1 do
      local a = A5 + b[2] + index*0x40
      local alive = r8(a) ~= 0
      local base = r16(a + 0x1e)
      if alive and base ~= 0 then
        local comp = r8(a + 0x38)
        local tbl = compositor_tables[comp]
        local ptr = tbl and (tbl + r16(tbl + r8(a+1)*2)) or 0
        local raw = {}
        for i=0,63 do raw[#raw+1] = hx(r8(a+i),2) end
        actors:write(table.concat({mi, frame, b[1], index, hx(a,6), "1", hx(base,4),
          hx(r8(a+1),2), hx(r8(a+3),2), hx(r8(a+5),2), hx(r8(a+2),2), hx(r8(a+0x3e),2),
          hx(r8(a+0x21),2), hx(r8(a+0x27),2), hx(r8(a+0x20),2), hx(comp,2),
          hx(r16(a+0x16),4), hx(r16(a+0x1a),4), hx(ptr,6), table.concat(raw)}, "\t"), "\n")
        local start, count = owned_range(b[1], index, boss)
        if start >= 0 then
          for rec = start, start+count-1 do
            local q = OBJ + rec*8
            local w0,w1,w2,w3 = r16(q), r16(q+2), r16(q+4), r16(q+6)
            objs:write(table.concat({mi, frame, b[1], index, hx(a,6), rec,
              hx(w0,4), hx(w0 & 0x0f,1), (w0 & 0x4000)~=0 and 1 or 0, (w0 & 0x8000)~=0 and 1 or 0,
              hx(w2 & 0x0fff,3), hx(w1,4), hx(w3,4),
              string.format("%04X:%04X:%04X:%04X", w0,w1,w2,w3)}, "\t"), "\n")
          end
        end
      end
    end
  end
  actors:flush(); objs:flush()
end

local function do_marker(auto)
  marker_index = marker_index + 1
  markers:write(table.concat({marker_index, frame, hx(pc(),6),
    (auto and "AUTO;" or "USER;")..state_text()}, "\t"), "\n"); markers:flush()
  snapshot(marker_index)
  -- flush rolling pre-marker history, tagged with this marker.
  prune(roll_p80); prune(roll_cram)
  for _, e in ipairs(roll_p80)  do p80:write(marker_index.."\t"..e.t.."\n")  end
  for _, e in ipairs(roll_cram) do cram:write(marker_index.."\t"..e.t.."\n") end
  p80:flush(); cram:flush()
  -- global state + optional collision/state word for tile-hazard correlation.
  coll:write(table.concat({marker_index, frame, "global_state", hx(A5+0x13e,6),
    hx(r16(A5+0x13e),4), state_text()}, "\t"), "\n")
  if COLLISION_ADDR ~= 0 then
    coll:write(table.concat({marker_index, frame, "collision_word", hx(COLLISION_ADDR,6),
      hx(r16(COLLISION_ADDR),4), "CAPTURE_COLLISION_ADDR"}, "\t"), "\n")
  end
  coll:flush()
  emu.print_info(string.format("arcade_marker_capture: marker #%d at frame %d (%s)",
    marker_index, frame, auto and "auto/smoke" or "user"))
end

-- PC080SN name-RAM write tap (both planes).
taps[#taps+1] = p:install_write_tap(0x00c00000, 0x00c0ffff, "marker_pc080sn", function(off, data, mask)
  local rel = off - 0x00c00000
  local layer = (off >= FG_A) and "A" or "B"
  local base = layer == "A" and FG_A or 0x00c00000
  local lrel = off - base
  local row = (lrel >> 8) & 63
  local col = (lrel >> 2) & 63
  local wsel = (lrel >> 1) & 1
  local t = table.concat({frame, hx(pc(),6), layer, hx(off,6), row, col, wsel,
    hx(r16((base) + ((row<<8)|(col<<2))),4), hx(r16((base) + ((row<<8)|(col<<2)) + 2),4),
    hx(data & 0xffff,4), hx(r16(A5+0x10b0),4), hx(r16(A5+0x10a8),4)}, "\t")
  roll_p80[#roll_p80+1] = {f = frame, t = t}
  return data
end)

-- Palette/CRAM shadow write tap.
taps[#taps+1] = p:install_write_tap(PAL, PAL + 0x07ff, "marker_cram", function(off, data, mask)
  local rel = off - PAL
  local bank = (rel >> 5) & 0x3f
  local idx = (rel >> 1) & 0x0f
  local t = table.concat({frame, hx(pc(),6), hx(bank,2), hx(idx,1), hx(off,6), hx(data & 0xffff,4)}, "\t")
  roll_cram[#roll_cram+1] = {f = frame, t = t}
  return data
end)
_G.arcade_marker_capture_taps = taps

local marker = assert(m.input:code_from_token(MARKER_TOKEN))

local function close()
  if closed then return end
  closed = true
  meta:write("ended="..os.date("!%Y-%m-%dT%H:%M:%SZ").."\nframes="..frame.."\nmarkers="..marker_index.."\n")
  for _, f in ipairs({meta, markers, actors, objs, p80, cram, coll}) do f:flush(); f:close() end
end

emu.register_frame_done(function()
  frame = frame + 1
  prune(roll_p80); prune(roll_cram)
  local down = false
  pcall(function() down = m.input:code_pressed(marker) end)
  if down and not marker_down then do_marker(false) end
  marker_down = down
  if AUTO[frame] then do_marker(true) end
  if frame % 120 == 0 then p80:flush(); cram:flush() end
  if MAX_FRAMES > 0 and frame >= MAX_FRAMES then close(); m:exit() end
end)
_G.arcade_marker_capture_stop = emu.add_machine_stop_notifier(close)
emu.print_info("arcade_marker_capture armed: play ORIGINAL ARCADE Rastan; press "..MARKER_TOKEN..
  " to mark each duck/weapon pose and each full hazard cycle.")
