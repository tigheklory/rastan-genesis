-- Probe: enumerate genesis devices + VDP memory access so we can dump VRAM/CRAM from a save state.
local machine = manager.machine
local out = os.getenv("GEN_DUMP_OUT") or "."
local frame = 0
_G._probe = emu.add_machine_frame_notifier(function()
  frame = frame + 1
  if frame ~= 5 then return end
  local f = assert(io.open(out .. "/vdp_probe.txt", "w"))
  for tag, dev in pairs(machine.devices) do
    if tag:find("vdp") or tag:find("315") or tag:find("gen") then
      f:write("DEVICE " .. tag .. "\n")
      local ok, spaces = pcall(function() return dev.spaces end)
      if ok and spaces then for sn,_ in pairs(spaces) do f:write("  space: "..sn.."\n") end end
      local ok2, ms = pcall(function() return dev.memory end)
      if ok2 and ms then
        local ok3, shares = pcall(function() return ms.shares end)
        if ok3 and shares then for sh,_ in pairs(shares) do f:write("  share: "..sh.."\n") end end
        local ok4, regions = pcall(function() return ms.regions end)
        if ok4 and regions then for rg,_ in pairs(regions) do f:write("  region: "..rg.."\n") end end
      end
    end
  end
  f:close()
  emu.print_info("VDP PROBE written")
  machine:exit()
end)
