-- RG-019 Genesis subround functional probe: latch the STAGE INDEX (a5@0x1242 = 0x00FF1242)
-- at first appearance (state2==3, player_state in 1..3).  The stage index -- not the round
-- counter -- is the authoritative selection result (confirmed on the arcade: R6 -> 0x73).
local machine=manager.machine
local prog=assert(machine.devices[":maincpu"].spaces["program"])
local td=assert(os.getenv("TRACE_DIR"))
local exp_stage=tonumber(os.getenv("EXPECT_STAGE") or "-1")
local maxf=tonumber(os.getenv("MAX_FRAMES") or "1400")
local function envaddr(name) return assert(tonumber(assert(os.getenv(name))),name) end
local scene_addr=envaddr("SCENE_ADDR"); local ready_addr=envaddr("READY_ADDR")
local active_record_addr=envaddr("ACTIVE_RECORD_ADDR"); local active_package_addr=envaddr("ACTIVE_PACKAGE_ADDR")
local active_round_addr=envaddr("ACTIVE_ROUND_ADDR"); local miss_a_addr=envaddr("MISS_A_ADDR"); local miss_b_addr=envaddr("MISS_B_ADDR")
local miss_pc=tonumber(os.getenv("MISS_A_PC") or "")
if miss_pc then
  local lut_addr=envaddr("ACTIVE_LUT_ADDR")
  local miss_condition=string.format("w@(%X+((d3&3fff)*2))==0",lut_addr)
  assert(pcall(function()
    machine.devices[":maincpu"].debug:bpset(miss_pc,miss_condition,
      'logerror "RG021_MISS_A code=%04X stage=%04X seg=%04X package=%04X\\n",d3,w@ff1242,w@ff013e,w@' ..
      string.format("%X",active_package_addr) .. '; g')
  end),"MISS_A breakpoint install failed")
  machine.debugger:command("go")
end
local fields={}; for _,p in pairs(machine.ioport.ports) do for n,f in pairs(p.fields) do fields[n]=f end end
local function si(n,a) if fields[n] then fields[n]:set_value(a and 1 or 0) end end
local function r16(a) return prog:read_u16(a)&0xffff end
local function r8(a) return prog:read_u8(a)&0xff end
local function md_vram_nonzero(base)
  -- Terminal-only read of real Mega Drive VRAM.  :gen_vdp's Lua videoram
  -- space is the 16 KiB Mode-4 compatibility window, not m_vram.
  prog:write_u16(0x00c00004,0x8f02)
  prog:write_u16(0x00c00004,base&0x3fff)
  prog:write_u16(0x00c00004,(base>>14)&3)
  local n=0; for _=0,2047 do if (prog:read_u16(0x00c00000)&0xffff)~=0 then n=n+1 end end; return n
end
local frame=0; local latched=nil; local appeared=nil
emu.register_frame_done(function()
  frame=frame+1
  si("Coin 1", frame>=120 and frame<=132); si("P1 A", frame>=120 and frame<=132)
  si("1 Player Start", frame>=175 and frame<=187); si("P1 Start", frame>=175 and frame<=187)
  si("P1 Right", appeared~=nil)
  local s2=r16(0x00FF0002); local ps=r16(0x00FF10E8)
  if appeared==nil and r16(0x00FF0000)==2 and s2==3 and ps>=1 and ps<=3 then
    appeared=frame
    latched=string.format("APPEAR@%d stage=0x%04X seg=0x%04X round=%02X scene=%d ready=%d active_record=0x%04X active_package=0x%04X native_round=%d miss_a=%d miss_b=%d px=0x%04X cfg5FF9F=0x%02X",
      frame, r16(0x00FF1242), r16(0x00FF013E), r8(0x00FF0118), r8(scene_addr), r8(ready_addr),
      r16(active_record_addr), r16(active_package_addr), r16(active_round_addr),
      prog:read_u32(miss_a_addr), prog:read_u32(miss_b_addr), r16(0x00FF10BE), r8(0x0005FF9F))
  end
  if frame>=maxf then
    local o=assert(io.open(td.."/probe.tsv","w"))
    local got = latched and tonumber(latched:match("stage=0x(%x+)"),16) or -1
    local res = (exp_stage<0) and "N/A" or ((got==exp_stage) and "PASS" or "FAIL")
    local va=md_vram_nonzero(0xe000); local vb=md_vram_nonzero(0xc000)
    o:write(string.format("expect_stage=0x%04X %s vram_a_nonzero=%d vram_b_nonzero=%d result=%s\n",
      (exp_stage<0 and 0 or exp_stage),latched or "NO-APPEARANCE",va,vb,res))
    o:close(); machine:exit()
  end
end)
