-- Build 0417 A-0154 bounded runtime boundary proof.
--
-- Genesis NTSC MAME, normal coin/start, continuous RIGHT.  The script waits
-- for progression record 11 and the known segment-11 X44/Y38 Layer-A cell to
-- be both staged as 0x6468 and inside the live 320x224 viewport.  It then
-- performs terminal reads through the real Mega Drive VDP data/control ports:
-- tile slot 0x0468, the corresponding Plane-A name cell, and CRAM Line 3.
-- The port reads intentionally occur only after the final frame and MAME exits
-- immediately, so they cannot perturb gameplay used as evidence.

local m = manager.machine
local cpu = assert(m.devices[":maincpu"])
local p = assert(cpu.spaces["program"])
local outdir = assert(os.getenv("A0154_OUTDIR"), "A0154_OUTDIR required")
os.execute('mkdir -p "' .. outdir .. '"')

local A_PROGRESS = 0x00ff013e
local A_PLAYER_X = 0x00ff10be
local A_PLAYER_Y = 0x00ff10c0
local A_SCROLL_X = 0x00ff409a
local A_SCROLL_Y = 0x00ff409e
local A_STAGED = 0x00ff50a0
local A_PALETTE = 0x00ff60a0
local A_LINE3 = A_PALETTE + 3 * 32
local A_EDITOR_LINE3 = 0x00084284

local TARGET_X = 44
local TARGET_Y = 38
local TARGET_ROW = TARGET_Y & 31
local TARGET_STAGED = A_STAGED + 2 * (TARGET_ROW * 64 + TARGET_X)
local TARGET_VRAM_NAME = 0xe000 + 2 * (TARGET_ROW * 64 + TARGET_X)
local TARGET_TILE_VRAM = 0x0468 * 32

local fields = {}
for _, port in pairs(m.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function key(name, on)
  local f = fields[name]
  if f then f:set_value(on and 1 or 0) end
end
local function r16(a) return p:read_u16(a) & 0xffff end
local function pc() return cpu.state["PC"].value & 0xffffff end

local frame = -1
local last_line3_write = nil
local line3_writes = {}
local tap = p:install_write_tap(A_LINE3, A_LINE3 + 31,
  "build0417_A0154_line3_writer", function(offset, data, mask)
    local rec = {frame=frame, pc=pc(), address=offset & 0xffffff,
                 data=data & 0xffff, mask=(mask or 0xffff) & 0xffff}
    last_line3_write = rec
    line3_writes[#line3_writes + 1] = rec
    return data
  end)
_G.build0417_A0154_line3_tap = tap

local function vdp_read_cmd(address, code)
  local first = (address & 0x3fff) | ((code & 3) << 14)
  local second = ((address >> 14) & 3) | ((code & 0x3c) << 2)
  p:write_u16(0x00c00004, first)
  p:write_u16(0x00c00004, second)
end

local function read_vram_bytes(address, count)
  p:write_u16(0x00c00004, 0x8f02)
  vdp_read_cmd(address, 0)
  local out = {}
  for _ = 1, count // 2 do
    local w = p:read_u16(0x00c00000) & 0xffff
    out[#out + 1] = (w >> 8) & 0xff
    out[#out + 1] = w & 0xff
  end
  return out
end

local function read_vram_word(address)
  p:write_u16(0x00c00004, 0x8f02)
  vdp_read_cmd(address, 0)
  return p:read_u16(0x00c00000) & 0xffff
end

local function read_cram_line3()
  p:write_u16(0x00c00004, 0x8f02)
  vdp_read_cmd(0x60, 8) -- CRAM read, byte address 3*32
  local out = {}
  for i = 0, 15 do out[i] = p:read_u16(0x00c00000) & 0x0eee end
  return out
end

local function hex_bytes(t)
  local s = {}
  for _, v in ipairs(t) do s[#s + 1] = string.format("%02x", v) end
  return table.concat(s)
end

local function dump(xscreen, yscreen)
  local tile = read_vram_bytes(TARGET_TILE_VRAM, 32)
  local name = read_vram_word(TARGET_VRAM_NAME)
  local cram = read_cram_line3()
  local f = assert(io.open(outdir .. "/runtime_boundary.txt", "w"))
  f:write(string.format("platform=MAME Genesis NTSC\nframe=%d\n", frame))
  f:write(string.format("progress=0x%04X\n", r16(A_PROGRESS)))
  f:write(string.format("player_x=0x%04X\nplayer_y=0x%04X\n", r16(A_PLAYER_X), r16(A_PLAYER_Y)))
  f:write(string.format("scroll_x=0x%04X\nscroll_y=0x%04X\n", r16(A_SCROLL_X), r16(A_SCROLL_Y)))
  f:write(string.format("logical_cell=X%d/Y%d\nphysical_cell=col%d/row%d\n", TARGET_X, TARGET_Y, TARGET_X, TARGET_ROW))
  f:write(string.format("screen_x=%d\nscreen_y=%d\n", xscreen, yscreen))
  f:write(string.format("staged_address=0x%06X\nstaged_word=0x%04X\n", TARGET_STAGED, r16(TARGET_STAGED)))
  f:write(string.format("vram_tile_address=0x%04X\nvram_tile_bytes=%s\n", TARGET_TILE_VRAM, hex_bytes(tile)))
  f:write(string.format("vram_name_address=0x%04X\nvram_name_word=0x%04X\n", TARGET_VRAM_NAME, name))
  for i = 0, 15 do
    f:write(string.format("cram_line3_%02d=0x%04X\n", i, cram[i]))
  end
  for i = 0, 15 do
    f:write(string.format("staged_line3_%02d=0x%04X\n", i, r16(A_LINE3 + i * 2)))
  end
  for i = 0, 15 do
    f:write(string.format("editor_line3_%02d=0x%04X\n", i, r16(A_EDITOR_LINE3 + i * 2)))
  end
  if last_line3_write then
    f:write(string.format("last_line3_writer_frame=%d\nlast_line3_writer_pc=0x%06X\nlast_line3_writer_address=0x%06X\nlast_line3_writer_data=0x%04X\n",
      last_line3_write.frame, last_line3_write.pc, last_line3_write.address, last_line3_write.data))
  else
    f:write("last_line3_writer=NONE_OBSERVED\n")
  end
  f:write(string.format("line3_write_count=%d\n", #line3_writes))
  f:close()

  local w = assert(io.open(outdir .. "/line3_writers.tsv", "w"))
  w:write("frame\tpc\taddress\tdata\tmask\n")
  for _, rec in ipairs(line3_writes) do
    w:write(string.format("%d\t%06X\t%06X\t%04X\t%04X\n",
      rec.frame, rec.pc, rec.address, rec.data, rec.mask))
  end
  w:close()
  m:exit()
end

emu.register_frame_done(function()
  frame = frame + 1
  key("Coin 1", frame >= 120 and frame <= 132)
  key("P1 A", frame >= 120 and frame <= 132)
  key("1 Player Start", frame >= 175 and frame <= 187)
  key("P1 Start", frame >= 175 and frame <= 187)
  key("P1 Right", frame >= 360)
  -- Continuous RIGHT alone stops at progression 0x0003.  Reuse the existing
  -- native_sprite_fullgame_closeout natural-route pulses to cross that
  -- unrelated traversal blocker; no emulated state is injected or modified.
  key("P1 B", frame >= 500 and frame % 70 < 10)
  key("P1 C", frame >= 520 and frame % 45 < 8)

  if r16(A_PROGRESS) == 0x000b and r16(TARGET_STAGED) == 0x6468 then
    local sx, sy = r16(A_SCROLL_X), r16(A_SCROLL_Y)
    local xscreen = (TARGET_X * 8 - sx + 16) & 0x1ff
    local yscreen = (TARGET_Y * 8 - sy + 8) & 0xff
    if xscreen <= 319 and yscreen <= 223 then dump(xscreen, yscreen) end
  end
  if frame >= 30000 then
    local f = assert(io.open(outdir .. "/runtime_boundary.txt", "w"))
    f:write(string.format("result=TARGET_NOT_REACHED\nframe=%d\nprogress=0x%04X\nstaged_word=0x%04X\n",
      frame, r16(A_PROGRESS), r16(TARGET_STAGED)))
    f:close()
    m:exit()
  end
end)

print(string.format("[build0417_A0154] waiting for record 0x0B X44/Y38; output=%s", outdir))
