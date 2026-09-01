-- GENESIS NTSC sprite/SAT workload + duplication trace (TOOLING, non-shipping instrumentation).
-- Logs each frame during human play: active sprite count, per-palette-line histogram, and repeated-tile
-- (same VRAM tile index at >1 X) detection = duplication signal. Answers the Build-0327 duplication and
-- slowdown/performance questions (correlate count/dup vs when the game slows). Output file from GEN_SPR_OUT.
-- Reads staged_sprite_sat (0x00FFB26C): NATIVE_SAT_MAX(0x50)=80 entries x 8 bytes Genesis SAT:
--   +0 Y(word)  +2 size/link(word)  +4 attr(word: pri|pal(13:14)|flip|tile 0:10)  +6 X(word)
local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"])
local prog = assert(cpu.spaces["program"])
local out = os.getenv("GEN_SPR_OUT") or "genesis_sprite_trace.log"
local SAT = 0x00FFB26C
local N = 80
local f = assert(io.open(out, "w"))
f:write("frame,active,l0,l1,l2,l3,distinct_tiles,dup_tile_pieces\n")
local frame = 0
_G._sprtrace = emu.add_machine_frame_notifier(function()
  frame = frame + 1
  if (frame % 4) ~= 0 then return end          -- sample every 4th frame
  local active, l = 0, {0, 0, 0, 0}
  local tilecount = {}
  for i = 0, N - 1 do
    local b = SAT + i * 8
    local y = prog:read_u16(b) & 0xffff
    if y ~= 0 then
      local attr = prog:read_u16(b + 4) & 0xffff
      local pal = (attr >> 13) & 3
      local tile = attr & 0x07FF
      active = active + 1
      l[pal + 1] = l[pal + 1] + 1
      tilecount[tile] = (tilecount[tile] or 0) + 1
    end
  end
  local distinct, dup = 0, 0
  for _, c in pairs(tilecount) do
    distinct = distinct + 1
    if c > 1 then dup = dup + c end
  end
  f:write(string.format("%d,%d,%d,%d,%d,%d,%d,%d\n",
    frame, active, l[1], l[2], l[3], l[4], distinct, dup))
  f:flush()
end)
