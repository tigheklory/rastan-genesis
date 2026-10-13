-- Build 0417 rope-area transparent-hole source identification.
--
-- Read-only terminal capture.  Follow the already-proven natural Round-1
-- route, wait until the segment-11 rope-side 4x4 rock descriptor is well
-- inside the viewport, save a screenshot, then read the real Mega Drive VDP
-- VRAM through the data/control ports.  The port reads are terminal: MAME
-- exits immediately afterward so they cannot affect the evidence frame.

local m = manager.machine
local cpu = assert(m.devices[":maincpu"])
local p = assert(cpu.spaces["program"])
local screen = m.screens:at(1)
local outdir = assert(os.getenv("ROPE_HOLE_OUTDIR"), "ROPE_HOLE_OUTDIR required")
os.execute('mkdir -p "' .. outdir .. '"')

local A_PROGRESS = 0x00ff013e
local A_PLAYER_X = 0x00ff10be
local A_PLAYER_Y = 0x00ff10c0
local A_SCROLL_X = 0x00ff409a
local A_SCROLL_Y = 0x00ff409e
local A_STAGED = 0x00ff50a0

-- Known disproven control cell, retained to anchor the same rope-side rock.
local CONTROL_X, CONTROL_Y = 44, 38
local CONTROL_STAGE = A_STAGED + 2 * ((CONTROL_Y & 31) * 64 + CONTROL_X)

local fields = {}
for _, port in pairs(m.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
local function key(name, on)
  local f = fields[name]
  if f then f:set_value(on and 1 or 0) end
end
local function r16(a) return p:read_u16(a) & 0xffff end

local function vdp_read_cmd(address, code)
  local first = (address & 0x3fff) | ((code & 3) << 14)
  local second = ((address >> 14) & 3) | ((code & 0x3c) << 2)
  p:write_u16(0x00c00004, first)
  p:write_u16(0x00c00004, second)
end

local function dump_actual_vram()
  local f = assert(io.open(outdir .. "/actual_vram.bin", "wb"))
  p:write_u16(0x00c00004, 0x8f02) -- auto-increment 2
  vdp_read_cmd(0, 0)
  for _ = 0, 0x7fff do
    local w = p:read_u16(0x00c00000) & 0xffff
    f:write(string.char((w >> 8) & 0xff, w & 0xff))
  end
  f:close()
end

local function dump_stage()
  local f = assert(io.open(outdir .. "/staged_plane_a.bin", "wb"))
  for i = 0, 0x0fff do f:write(string.char(p:read_u8(A_STAGED + i) & 0xff)) end
  f:close()
end

local frame = -1
local function capture(xscreen, yscreen)
  local meta = assert(io.open(outdir .. "/capture.txt", "w"))
  meta:write("platform=MAME Genesis NTSC\n")
  meta:write(string.format("frame=%d\nprogress=0x%04X\n", frame, r16(A_PROGRESS)))
  meta:write(string.format("player_x=0x%04X\nplayer_y=0x%04X\n", r16(A_PLAYER_X), r16(A_PLAYER_Y)))
  meta:write(string.format("scroll_x=0x%04X\nscroll_y=0x%04X\n", r16(A_SCROLL_X), r16(A_SCROLL_Y)))
  meta:write(string.format("control_logical=X%d/Y%d\ncontrol_screen_x=%d\ncontrol_screen_y=%d\n", CONTROL_X, CONTROL_Y, xscreen, yscreen))
  meta:write(string.format("control_staged_address=0x%06X\ncontrol_staged_word=0x%04X\n", CONTROL_STAGE, r16(CONTROL_STAGE)))
  meta:close()
  pcall(function() screen:snapshot(outdir .. "/rope_area.png") end)
  dump_stage()
  dump_actual_vram()
  m:exit()
end

emu.register_frame_done(function()
  frame = frame + 1
  key("Coin 1", frame >= 120 and frame <= 132)
  key("P1 A", frame >= 120 and frame <= 132)
  key("1 Player Start", frame >= 175 and frame <= 187)
  key("P1 Start", frame >= 175 and frame <= 187)
  key("P1 Right", frame >= 360)
  key("P1 B", frame >= 500 and frame % 70 < 10)
  key("P1 C", frame >= 520 and frame % 45 < 8)

  if r16(A_PROGRESS) == 0x000b and r16(CONTROL_STAGE) == 0x6468 then
    local sx, sy = r16(A_SCROLL_X), r16(A_SCROLL_Y)
    local xs = (CONTROL_X * 8 - sx + 16) & 0x1ff
    local ys = (CONTROL_Y * 8 - sy + 8) & 0xff
    -- Capture only after the complete 4x4 descriptor (X44..47/Y36..39)
    -- is comfortably on screen, not at the bottom-edge first-visibility frame.
    if xs <= 280 and ys >= 72 and ys <= 176 then capture(xs, ys) end
  end

  if frame >= 30000 then
    local f = assert(io.open(outdir .. "/capture.txt", "w"))
    f:write(string.format("result=TARGET_NOT_REACHED\nframe=%d\nprogress=0x%04X\ncontrol_word=0x%04X\n",
      frame, r16(A_PROGRESS), r16(CONTROL_STAGE)))
    f:close()
    m:exit()
  end
end)

print(string.format("[build0417_rope_hole_source] waiting for segment-11 rope viewport; output=%s", outdir))
