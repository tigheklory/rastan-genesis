-- GENESIS NTSC player-palette runtime probe (TOOLING, PROMT-ID-0112).
--
-- Reaches steady R1 gameplay via the established coin/start cadence, then captures the authoritative
-- runtime player-palette evidence for the §6 four-link proof:
--   * staged_palette_words  (WRAM CRAM shadow)      -> STAGED_PALETTE_ADDR env (resolve from symbol.txt)
--   * ACTUAL VDP CRAM        (64 words, 4 lines)      -> via VDP control/data port reads
--   * ACTUAL VDP VRAM        (0x8000 words)           -> player tile pixels actually uploaded
--   * staged Genesis SAT     (80 x 8 bytes)           -> SAT_ADDR env; per-line histogram + entries
--   * scene/round/player-state meta
--
-- No hard-coded WRAM: every staging symbol comes from the environment (the runner resolves it from the
-- CURRENT apps/rastan-direct/out/symbol.txt). Output dir = TRACE_DIR; capture frame = CAP_FRAME.
local m = manager.machine
local p = assert(m.devices[":maincpu"].spaces["program"], "missing program space")
local screen = nil; for _, s in pairs(m.screens) do screen = s; break end
local out        = assert(os.getenv("TRACE_DIR"))
local staged     = tonumber(assert(os.getenv("STAGED_PALETTE_ADDR")))
local sat        = tonumber(assert(os.getenv("SAT_ADDR")))
local scene_addr = tonumber(assert(os.getenv("SCENE_ID_ADDR")))
local cap_frame  = tonumber(os.getenv("CAP_FRAME") or "840")

local fields = {}
for _, port in pairs(m.ioport.ports) do for n, f in pairs(port.fields) do fields[n] = f end end
local function key(n, on) if fields[n] then fields[n]:set_value(on and 1 or 0) end end
local function r16(a) return p:read_u16(a) & 0xffff end
local function dump_words(path, words)
  local f = assert(io.open(path, "wb"))
  for _, w in ipairs(words) do f:write(string.char((w >> 8) & 255, w & 255)) end
  f:close()
end
local function vdp_read_cmd(a, c)
  p:write_u16(0xc00004, (a & 0x3fff) | ((c & 3) << 14))
  p:write_u16(0xc00004, ((a >> 14) & 3) | ((c & 0x3c) << 2))
end

local function capture(frame)
  if screen then pcall(function() screen:snapshot(out .. "/player_frame.png") end) end
  -- staged CRAM shadow
  local sw = {}; for i = 0, 63 do sw[#sw + 1] = r16(staged + i * 2) end
  dump_words(out .. "/staged_cram.bin", sw)
  -- actual VDP CRAM (code 8 = CRAM read) from address 0
  vdp_read_cmd(0, 8); local cw = {}; for _ = 0, 63 do cw[#cw + 1] = r16(0xc00000) end
  dump_words(out .. "/actual_cram.bin", cw)
  -- actual VDP VRAM (code 0 = VRAM read) from address 0
  p:write_u16(0xc00004, 0x8f02); vdp_read_cmd(0, 0)
  local vf = assert(io.open(out .. "/actual_vram.bin", "wb"))
  for _ = 0, 0x7fff do local w = r16(0xc00000); vf:write(string.char((w >> 8) & 255, w & 255)) end
  vf:close()
  -- staged Genesis SAT: 80 entries x 8 bytes
  local sf = assert(io.open(out .. "/sat.tsv", "w"))
  sf:write("idx\ty\tsizelink\tattr\tx\tpal\ttile\tpri\n")
  local hist = {0, 0, 0, 0}
  for i = 0, 79 do
    local b = sat + i * 8
    local y = r16(b); local sl = r16(b + 2); local attr = r16(b + 4); local x = r16(b + 6)
    local pal = (attr >> 13) & 3; local tile = attr & 0x07FF; local pri = (attr >> 15) & 1
    if y ~= 0 then hist[pal + 1] = hist[pal + 1] + 1 end
    sf:write(string.format("%d\t%04X\t%04X\t%04X\t%04X\t%d\t%04X\t%d\n", i, y, sl, attr, x, pal, tile, pri))
  end
  sf:close()
  local meta = assert(io.open(out .. "/runtime.tsv", "w"))
  meta:write("frame\tround_ff1242\tscene_id\tplayer_state_ff10e8\tsat_l0\tsat_l1\tsat_l2\tsat_l3\n")
  meta:write(string.format("%d\t%04X\t%02X\t%04X\t%d\t%d\t%d\t%d\n",
    frame, r16(0xff1242), p:read_u8(scene_addr) & 255, r16(0xff10e8),
    hist[1], hist[2], hist[3], hist[4]))
  meta:close()
  emu.print_info("GENESIS PLAYER PALETTE PROBE captured frame " .. frame .. " -> " .. out)
  m:exit()
end

local frame = 0
emu.register_frame_done(function()
  frame = frame + 1
  key("Coin 1", frame >= 120 and frame <= 132); key("P1 A", frame >= 120 and frame <= 132)
  key("1 Player Start", frame >= 175 and frame <= 187); key("P1 Start", frame >= 175 and frame <= 187)
  if frame == cap_frame then capture(frame) end
end)
