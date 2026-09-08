-- Read-only: per-frame Plane-A/B DMA volume attribution (dirty-row popcounts) + tile/narrow flags.
local mac=manager.machine
local cpu=assert(mac.devices[":maincpu"]); local pr=assert(cpu.spaces["program"])
local out=assert(io.open(os.getenv("DUMP_OUT"),"w"))
local function r8(a) return pr:read_u8(a)&0xff end
local function r16(a) return pr:read_u16(a)&0xffff end
local function r32(a) return pr:read_u32(a)&0xffffffff end
local function pop(x) local c=0 while x~=0 do c=c+(x&1) x=x>>1 end return c end
local fields={}
for _,port in pairs(mac.ioport.ports) do for n,f in pairs(port.fields) do fields[n]=f end end
local function setin(n,a) if fields[n] then fields[n]:set_value(a and 1 or 0) end end
local frame=0
-- histograms of rows published
local bgh={} local fgh={}
emu.register_frame_done(function()
  frame=frame+1
  setin("P1 A", frame>=120 and frame<=132)
  setin("P1 Start", frame>=175 and frame<=187)
  setin("P1 Right", frame>=360)
  if frame>=400 then
    local bg=pop(r32(0xFF4002)) local fg=pop(r32(0xFF4006))
    bgh[bg]=(bgh[bg] or 0)+1; fgh[fg]=(fgh[fg] or 0)+1
    if frame%120==0 then
      out:write(string.format("f=%d bg_rows=%d fg_rows=%d tiles_dirty=%d narrow=%d colmask=%08X:%08X\n",
        frame,bg,fg,r8(0xFF4000),r16(0xFF408C), 0, 0)); out:flush()
    end
  end
  if frame>=1200 then
    out:write("\nBG rows/frame histogram (rows:count): ")
    for k=0,32 do if bgh[k] then out:write(k..":"..bgh[k].." ") end end
    out:write("\nFG rows/frame histogram (rows:count): ")
    for k=0,32 do if fgh[k] then out:write(k..":"..fgh[k].." ") end end
    out:write("\n"); out:flush(); mac:exit()
  end
end)
