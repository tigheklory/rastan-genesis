local machine = manager.machine
local vdp = assert(machine.devices[":gen_vdp"])
local out = os.getenv("GEN_DUMP_OUT") or "."
local frame = 0
_G._pv = emu.add_machine_frame_notifier(function()
  frame = frame + 1
  if frame ~= 8 then return end
  local f = assert(io.open(out .. "/vram_probe.txt", "w"))
  local sp = vdp.spaces["videoram"]
  f:write("space videoram present: " .. tostring(sp ~= nil) .. "\n")
  if sp then
    local vals8, vals16 = {}, {}
    for a = 0xE000, 0xE01E, 2 do vals16[#vals16+1] = string.format("%04X", sp:read_u16(a) & 0xffff) end
    for a = 0xE000, 0xE00F do vals8[#vals8+1] = string.format("%02X", sp:read_u8(a) & 0xff) end
    f:write("read_u16@0xE000: " .. table.concat(vals16, " ") .. "\n")
    f:write("read_u8 @0xE000: " .. table.concat(vals8, " ") .. "\n")
    -- scan for any nonzero via u16
    local nz = 0
    for a = 0, 0xFFFE, 2 do if (sp:read_u16(a) & 0xffff) ~= 0 then nz = nz + 1 end end
    f:write("nonzero u16 words in VRAM: " .. nz .. "\n")
  end
  -- try memory shares
  local ok, mem = pcall(function() return vdp.memory end)
  if ok and mem then
    for shn, sh in pairs(mem.shares) do f:write("share " .. shn .. " size " .. tostring(sh.size) .. "\n") end
  end
  f:close()
  emu.print_info("VRAM READ PROBE done")
  machine:exit()
end)
