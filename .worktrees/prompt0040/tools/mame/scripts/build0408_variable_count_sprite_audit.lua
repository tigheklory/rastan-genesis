-- Build-0408 focused variable-count generated-sprite audit.
-- Host-only debugger breakpoints and controller input; no emulated-memory writes.

local m=manager.machine
local cpu=assert(m.devices[":maincpu"])
local p=assert(cpu.spaces["program"])
local log=assert(m.debugger and m.debugger.consolelog,"requires -debug -debugger none")
local outdir=assert(os.getenv("VC_SPRITE_OUTDIR"))
local max_frames=tonumber(os.getenv("VC_SPRITE_MAX_FRAMES") or "5000")
os.execute('mkdir -p "'..outdir..'"')
local out=assert(io.open(outdir.."/variable_count_events.tsv","w"))
out:write("message\n")

local function pc(name) return tonumber(os.getenv(name) or "") end
local points={
  {"FI",pc("VC_FINAL_ENTRY"),'printf "VC,FI,%d,%d,%X,%X,%X,%X,%X,%X,%X,%X\\n",totalcycles,frame,w@ffb7f4,w@ffb7f6,w@ffb7f8,w@ffb7fa,w@ffb7fc,w@ffb7fe,w@ffbed6,w@ffb7e8; g'},
  {"PE",pc("VC_PIECE_ENTRY"),'printf "VC,PE,%d,%d,%X,%X,%X,%X,%X,%X,%X\\n",totalcycles,frame,d1,d2,d3,d4,d5,w@ffbed6,w@ffb7e8; g'},
  {"PS",pc("VC_SAT_ENTRY"),'printf "VC,PS,%d,%d,%X,%X,%X,%X,%X,%X,%X,%X\\n",totalcycles,frame,d1,d2,d3,d4,d5,d0,w@ffbed6,w@ffb7e8; g'},
  {"PR",pc("VC_PIECE_RETURN"),'printf "VC,PR,%d,%d,%X,%X,%X\\n",totalcycles,frame,d5,w@ffbed6,w@ffb7e8; g'},
  {"FD",pc("VC_FINAL_DONE"),'printf "VC,FD,%d,%d,%X,%X,%X,%X\\n",totalcycles,frame,w@ffbed4,w@ffbed6,w@ffb7e8,w@ffb7fe; g'},
}
local optional={
  {"LE",pc("VC_LEVEL_ENTRY"),'printf "VC,LE,%d,%d,%X,%X,%X\\n",totalcycles,frame,a4,a3,a6; g'},
  {"LS",pc("VC_LEVEL_SUCCESS"),'printf "VC,LS,%d,%d,%X,%X,%X\\n",totalcycles,frame,a4,a3,a6; g'},
  {"UE",pc("VC_UNIV_ENTRY"),'printf "VC,UE,%d,%d,%X,%X,%X\\n",totalcycles,frame,a4,a3,a6; g'},
  {"US",pc("VC_UNIV_SUCCESS"),'printf "VC,US,%d,%d,%X,%X,%X\\n",totalcycles,frame,a4,a3,a6; g'},
  {"LF",pc("VC_LEVEL_FRAME"),'printf "VC,LF,%d,%d,%X,%X,%X,%X,%X,%X\\n",totalcycles,frame,a4,b@(a4+1),b@(a4+2),w@(a4+1e),d7,a0; g'},
  {"UF",pc("VC_UNIV_FRAME"),'printf "VC,UF,%d,%d,%X,%X,%X,%X,%X,%X\\n",totalcycles,frame,a4,b@(a4+1),b@(a4+2),w@(a4+1e),d7,a2; g'},
  {"FE",pc("VC_FAST_ENTRY"),'printf "VC,FE,%d,%d,%X,%X,%X,%X,%X,%X,%X,%X,%X,%X\\n",totalcycles,frame,a4,b@(a4+1),w@(a4+1e),a0,d7,w@a6,d1,d2,d3,d4; g'},
  {"FR",pc("VC_FAST_RETURN"),'printf "VC,FR,%d,%d,%X,%X,%X,%X,%X,%X\\n",totalcycles,frame,a4,b@(a4+1),w@(a4+1e),a0,d7,w@a6; g'},
}
for _,v in ipairs(optional) do if v[2] then points[#points+1]=v end end
for _,v in ipairs(points) do assert(v[2],v[1]);assert(pcall(function() cpu.debug:bpset(v[2],"1",v[3]) end),v[1]) end

local fields={}
for _,port in pairs(m.ioport.ports) do for n,f in pairs(port.fields) do fields[n]=f end end
local function key(n,on) if fields[n] then fields[n]:set_value(on and 1 or 0) end end
local li,frame=0,-1
local function drain()
  for i=li+1,#log do
    local s=tostring(log[i])
    if s:match("^VC,") then out:write(s,"\n") end
  end
  li=#log;out:flush()
end
emu.register_frame_done(function()
  frame=frame+1;drain()
  key("P1 A",frame>=120 and frame<=132);key("Coin 1",frame>=120 and frame<=132)
  key("P1 Start",frame>=175 and frame<=187);key("1 Player Start",frame>=175 and frame<=187)
  key("P1 Right",frame>=360);key("P1 C",frame>=360 and frame%90<12);key("P1 B",frame>=360 and frame%30<6)
  if frame>=max_frames then drain();out:close();m:exit() end
end)
print("[variable_count_audit] READY -> "..outdir)
