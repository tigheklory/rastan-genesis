-- Prompt 0018: read-only selector-0 cycle sampler for matching Genesis NTSC runs.
local m=manager.machine
local cpu=assert(m.devices[":maincpu"])
local p=assert(cpu.spaces["program"])
local out=assert(os.getenv("TRACE_DIR"))
local entry=assert(tonumber(os.getenv("SEL0_ENTRY"),16))
local finish=assert(tonumber(os.getenv("SEL0_FINISH"),16))
local log=assert(m.debugger and m.debugger.consolelog,"requires -debug -debugger none")
cpu.debug:bpset(entry,"1",'printf "RG18,S,%d,%d\\n",totalcycles,frame; g')
cpu.debug:bpset(finish,"1",'printf "RG18,E,%d,%d\\n",totalcycles,frame; g')
local fields={}; for _,port in pairs(m.ioport.ports) do for n,f in pairs(port.fields) do fields[n]=f end end
local function key(n,on) if fields[n] then fields[n]:set_value(on and 1 or 0) end end
local function r16(a) return p:read_u16(a)&0xffff end
local frame,index,appeared,start=0,#log,nil,nil
local samples={}
local function drain()
  for i=index+1,#log do
    local kind,cycles=tostring(log[i]):match("^RG18,([SE]),(%d+),%d+")
    cycles=tonumber(cycles)
    if kind=="S" then start=cycles elseif kind=="E" and start then samples[#samples+1]=cycles-start; start=nil end
  end
  index=#log
end
local function close()
  drain(); local f=assert(io.open(out.."/selector0_cycles.tsv","w")); f:write("sample\tcycles\n")
  for i,v in ipairs(samples) do f:write(string.format("%d\t%d\n",i,v)) end; f:close()
end
emu.register_frame_done(function()
  frame=frame+1; drain()
  key("Coin 1",frame>=120 and frame<=132); key("P1 A",frame>=120 and frame<=132)
  key("1 Player Start",frame>=175 and frame<=187); key("P1 Start",frame>=175 and frame<=187)
  if not appeared and r16(0xff0000)==2 and r16(0xff0002)==3 then appeared=frame end
  if appeared then local t=frame-appeared; key("P1 Right",true); key("P1 B",(t%45)<8); key("P1 C",(t%100)>=55 and (t%100)<68) end
  if (appeared and frame-appeared>=840) or frame>=1800 then close(); m:exit() end
end)
