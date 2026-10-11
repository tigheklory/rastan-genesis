-- Build-0406/0407 focused native-sprite cost profiler.
-- Host-only debugger breakpoints; no emulated-memory writes except the established
-- deterministic energy hold used by frame_timing_trace.lua.

local m=manager.machine
local cpu=assert(m.devices[":maincpu"])
local p=assert(cpu.spaces["program"])
local log=assert(m.debugger and m.debugger.consolelog,"requires -debug -debugger none")
local outdir=assert(os.getenv("NATIVE_COST_OUTDIR"))
local max_frames=tonumber(os.getenv("NATIVE_COST_FRAMES") or "1200")
os.execute('mkdir -p "'..outdir..'"')

local function ep(name) return assert(tonumber(assert(os.getenv(name))),name) end
local points={
  ACT=ep("NPC_ACT"), AR=ep("NPC_ACT_RET"), LB=ep("NPC_LB"), LBI=ep("NPC_LB_INDEX"),
  LBF=ep("NPC_LB_FRAME"), LBP=ep("NPC_LB_PIECE"), LBS=ep("NPC_LB_SUCCESS"), LBM=ep("NPC_LB_MISS"),
  UN=ep("NPC_UN"), UNI=ep("NPC_UN_INDEX"), UNF=ep("NPC_UN_FRAME"), UNP=ep("NPC_UN_PIECE"),
  UNS=ep("NPC_UN_SUCCESS"), UNM=ep("NPC_UN_MISS"), QE=ep("NPC_QUEUE"), QR=ep("NPC_QUEUE_RET"),
  FI=ep("NPC_FINAL"), FD=ep("NPC_FINAL_DONE"), PE=ep("NPC_PIECE"), GE=ep("NPC_GEOM"),
  BB=ep("NPC_BBOX"), RE=ep("NPC_RES"), RM=ep("NPC_MISS"), AT=ep("NPC_TAKE"),
  SE=ep("NPC_SAT"), PR=ep("NPC_PIECE_RET"), CE=ep("NPC_CONTACT"), CR=ep("NPC_CONTACT_RET")
}
if os.getenv("NPC_FINAL_RTS") then points.FX=ep("NPC_FINAL_RTS") end
if os.getenv("NPC_LANE") then points.LE=ep("NPC_LANE") end
if os.getenv("NPC_SAT_Y") then
  points.SY=ep("NPC_SAT_Y");points.SL=ep("NPC_SAT_LINK")
  points.ST=ep("NPC_SAT_ATTR");points.SX=ep("NPC_SAT_X");points.SC=ep("NPC_SAT_COUNT")
end
if os.getenv("NPC_PRE_DIRECT") then
  points.PD=ep("NPC_PRE_DIRECT");points.PV=ep("NPC_PRE_VARIANT")
  points.PA=ep("NPC_PRE_DYNAMIC");points.PI=ep("NPC_PRE_VALIDATED")
  points.PO=ep("NPC_PRE_POINTER")
end
if os.getenv("NPC_VARIANT") then points.VE=ep("NPC_VARIANT") end
if os.getenv("NPC_FAST") then points.FT=ep("NPC_FAST");points.FR=ep("NPC_FAST_RET") end
for tag,pc in pairs(points) do
  local action=string.format('printf "NPC,%s,%%d,%%d\\n",totalcycles,frame; g',tag)
  if tag=="PE" then
    action='printf "NPC,PE,%d,%d,%X\\n",totalcycles,frame,d3; g'
  end
  assert(pcall(function() cpu.debug:bpset(pc,"1",action) end),tag)
end

local sums,calls={},{}
local armed=false
local function add(k,v) sums[k]=(sums[k] or 0)+v; calls[k]=(calls[k] or 0)+1 end
local piece,last_piece=nil,nil
local final_start,first_lane,last_piece_return,done_time=nil,nil,nil,nil
local act_start,queue_start,contact_start=nil,nil,nil
local fast_start=nil
local final_samples={}
local final_pre_done=nil
local variant_piece_count,direct_piece_count,raw_piece_count=0,0,0
local lb,un=nil,nil
local li=0
local function event(tag,cyc,d3)
  if not armed then return end
  if tag=="FI" then
    final_start=cyc;first_lane=nil;last_piece_return=nil;done_time=nil;final_pre_done=false
  elseif tag=="LE" and final_start then
    if not first_lane then add("finalizer_fixed_setup",cyc-final_start);first_lane=cyc end
  elseif tag=="FD" and final_start then
    if last_piece_return then add("finalizer_lane_count_tail",cyc-last_piece_return) end
    add("finalizer_to_done",cyc-final_start);done_time=cyc; final_pre_done=true
  elseif tag=="FX" and final_start then
    if done_time then add("finalizer_fixed_teardown",cyc-done_time) end
    local v=cyc-final_start; add("finalizer_full",v);final_samples[#final_samples+1]=v
    final_start=nil;final_pre_done=nil
  elseif tag=="ACT" then act_start=cyc elseif tag=="AR" and act_start then add("actor_total",cyc-act_start);act_start=nil
  elseif tag=="QE" then queue_start=cyc elseif tag=="QR" and queue_start then add("queue_construct",cyc-queue_start);queue_start=nil
  elseif tag=="FT" then fast_start=cyc elseif tag=="FR" and fast_start then add("fast_queue_construct",cyc-fast_start);fast_start=nil
  elseif tag=="CE" then contact_start=cyc elseif tag=="CR" and contact_start then add("contact",cyc-contact_start);contact_start=nil
  elseif tag=="LB" then lb={start=cyc,last=cyc,phase="class"}
  elseif lb and tag=="LBI" then add("classification",cyc-lb.last);lb.last=cyc;lb.phase="index"
  elseif lb and tag=="LBF" then add("index_lookup",cyc-lb.last);lb.last=cyc;lb.phase="header"
  elseif lb and tag=="LBP" then add(lb.phase=="header" and "frame_header" or "piece_iteration",cyc-lb.last);lb.last=cyc;lb.phase="piece"
  elseif lb and (tag=="LBS" or tag=="LBM") then add("levelb_total",cyc-lb.start); if lb.phase=="piece" then add("piece_iteration",cyc-lb.last) end;lb=nil
  elseif tag=="UN" then un={start=cyc,last=cyc,phase="class"}
  elseif un and tag=="UNI" then add("classification",cyc-un.last);un.last=cyc;un.phase="index"
  elseif un and tag=="UNF" then add("index_lookup",cyc-un.last);un.last=cyc;un.phase="header"
  elseif un and tag=="UNP" then add(un.phase=="header" and "frame_header" or "piece_iteration",cyc-un.last);un.last=cyc;un.phase="piece"
  elseif un and (tag=="UNS" or tag=="UNM") then add("universal_total",cyc-un.start);if un.phase=="piece" then add("piece_iteration",cyc-un.last) end;un=nil
  elseif tag=="PE" then
    if last_piece_return then add("finalizer_lane_queue_iteration",cyc-last_piece_return)
    elseif first_lane then add("finalizer_lane_queue_iteration",cyc-first_lane) end
    local v=tonumber(d3 or "0",16) or 0
    local kind=((v & 0x2000)~=0 and "variant") or ((v & 0x1000)~=0 and "direct") or "dynamic"
    piece={last=cyc,start=cyc,phase="pre",kind=kind}
  elseif piece and (tag=="PD" or tag=="PV" or tag=="PA") then
    add("pre_"..piece.kind.."_classify",cyc-piece.last);piece.last=cyc;piece.phase="identity"
  elseif piece and tag=="PI" then
    add("pre_"..piece.kind.."_identity",cyc-piece.last);piece.last=cyc;piece.phase="pointer"
  elseif piece and tag=="PO" then
    add("pre_"..piece.kind.."_bbox_pointer",cyc-piece.last);piece.last=cyc;piece.phase="y_normalize"
  elseif piece and tag=="GE" then
    if piece.phase=="y_normalize" then add("pre_"..piece.kind.."_y_normalize",cyc-piece.last) end
    add("final_pre_geometry",cyc-piece.start);piece.last=cyc;piece.phase="geometry"
  elseif piece and tag=="BB" then add("geometry_attrs",cyc-piece.last);piece.last=cyc;piece.phase="bbox"
  elseif piece and tag=="VE" then
    add("bounds_"..piece.kind.."_accepted",cyc-piece.last);piece.last=cyc;piece.phase="variant"
  elseif piece and tag=="RE" then
    if piece.phase=="variant" then add("variant_key_"..piece.kind,cyc-piece.last)
    else add("bbox_variant",cyc-piece.last) end
    piece.last=cyc;piece.phase="resident"
  elseif piece and tag=="RM" then add("residency_lookup",cyc-piece.last);piece.last=cyc;piece.phase="miss"
  elseif piece and tag=="AT" then add("victim_scan",cyc-piece.last);piece.last=cyc;piece.phase="alloc"
  elseif piece and tag=="SE" then
    if piece.phase=="resident" then add("residency_hit",cyc-piece.last)
    elseif piece.phase=="miss" then add("victim_scan",cyc-piece.last)
    elseif piece.phase=="alloc" then add("allocation_install",cyc-piece.last) end
    piece.last=cyc;piece.phase="sat"
  elseif piece and tag=="SY" then add("sat_slot_used",cyc-piece.last);piece.last=cyc;piece.phase="sat_y"
  elseif piece and tag=="SL" then add("sat_y_write",cyc-piece.last);piece.last=cyc;piece.phase="sat_link"
  elseif piece and tag=="ST" then add("sat_size_link",cyc-piece.last);piece.last=cyc;piece.phase="sat_attr"
  elseif piece and tag=="SX" then add("sat_tile_attributes",cyc-piece.last);piece.last=cyc;piece.phase="sat_x"
  elseif piece and tag=="SC" then add("sat_x_write",cyc-piece.last);piece.last=cyc;piece.phase="sat_count"
  elseif piece and tag=="PR" then
    if piece.phase=="sat_count" then add("sat_output_count",cyc-piece.last)
    elseif piece.phase=="bbox" and points.VE then add("bounds_"..piece.kind.."_rejected",cyc-piece.last)
    else add(piece.phase=="sat" and "sat_construct" or ("reject_"..piece.phase),cyc-piece.last) end
    last_piece_return=cyc;piece=nil
  end
end
local function drain()
 for i=li+1,#log do
   local line=tostring(log[i]);local t,c,_,d3=line:match("^NPC,(%u+),(%d+),(%d+),?([0-9A-Fa-f]*)")
   if t then
     if armed and t=="PE" and d3 and d3~="" then
       local v=tonumber(d3,16) or 0
       if (v & 0x2000)~=0 then variant_piece_count=variant_piece_count+1
       elseif (v & 0x1000)~=0 then direct_piece_count=direct_piece_count+1
       else raw_piece_count=raw_piece_count+1 end
     end
     event(t,tonumber(c),d3)
   end
 end
 li=#log
end

local function percentile(a,pct)
 if #a==0 then return 0 end
 local b={};for i,v in ipairs(a) do b[i]=v end;table.sort(b)
 return b[math.max(1,math.ceil(#b*pct/100))]
end

local fields={};for _,port in pairs(m.ioport.ports) do for n,f in pairs(port.fields) do fields[n]=f end end
local function key(n,v) if fields[n] then fields[n]:set_value(v and 1 or 0) end end
local frame,armed_frames=0,0
local A_SCENE=tonumber(os.getenv("NATIVE_COST_SCENE") or "0xFFC55C")
emu.register_frame_done(function()
 frame=frame+1;drain()
 key("P1 A",frame>=120 and frame<=132);key("P1 Start",frame>=175 and frame<=187)
 key("P1 Right",frame>=360);key("P1 C",frame>=360 and frame%90<12);key("P1 B",frame>=360 and frame%30<6)
 local gameplay=p:read_u8(A_SCENE)==1
 if gameplay then p:write_u16(0xff013a,0x30) end
 if not armed and gameplay and p:read_u16(0xff013e)==2 then armed=true end
 if armed and gameplay then armed_frames=armed_frames+1 end
 if armed_frames>=max_frames or frame>=7000 then
   drain();local f=assert(io.open(outdir.."/native_cost_summary.tsv","w"));f:write("bucket\tcalls\ttotal_cycles\tcycles_update\tcycles_call\n")
   local ks={};for k in pairs(sums) do ks[#ks+1]=k end;table.sort(ks)
   for _,k in ipairs(ks) do f:write(string.format("%s\t%d\t%d\t%.2f\t%.2f\n",k,calls[k],sums[k],sums[k]/math.max(1,armed_frames),sums[k]/calls[k])) end
   f:write(string.format("finalizer_distribution\t%d\t%d\t%d\t%d\n",#final_samples,
     percentile(final_samples,50),percentile(final_samples,95),percentile(final_samples,100)))
   f:write(string.format("piece_identity_counts\t%d\t%d\t%d\t0\n",
     variant_piece_count,direct_piece_count,raw_piece_count))
   f:write(string.format("armed_frames\t%d\t0\t0\t0\n",armed_frames));f:close();m:exit()
 end
end)
print("[native_cost] READY -> "..outdir)
