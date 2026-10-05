-- frame_timing_trace.lua  (READ-ONLY; no ROM/WRAM modification)
-- Build 0400 EXACT frame-timing trace, repaired per Cody's re-audit
-- (docs/design/Cody_build0400_repaired_trace_independent_reaudit.md).
--
-- MECHANISMS (this MAME has NO install_execute_tap and NO cpu:total_cycles()):
--   * EXACT execution/cycles  -> MAME debugger breakpoints (launch with -debug -debugger none):
--       cpu.debug:bpset(pc,"1",'printf "...",totalcycles,frame,w@C00008; g'); drained from consolelog.
--       Points: PUB_ENTRY 0x70250, PUB_RTS 0x702D2, WORKER_ENTRY 0x3A208, WORKER_PRE_RTE 0x3A27E.
--   * EXACT publication ownership + VDP writes -> debugger execution breakpoints at PUB_ENTRY/PUB_RTS
--       and a debugger write watchpoint on 0xC00000..7.  Console events retain totalcycles/frame/HV,
--       writer PC, port, width and data.  VC_MARK 0..6 remains subphase evidence only.
--   * producer_completions -> write-tap 0xFFBED4 (emit finalizer; SEPARATE from worker/IRQ events).
--   * input cross-check -> write-tap 0xFF61F6 (update_inputs writes it once + 0xFF61F7 once per call).
--
-- EVIDENCE LABELS used in the report: [M] exact cycles/beam, [P] proxy, [S] static order, [U] unknown.
-- INTERVAL: all statistics reset when Tighe presses M in scene 1 and count only while armed (no
-- lifetime-global numerator over gameplay-only denominator). Zero denominators print N/A.
--
-- Build-0400 runtime PCs are hardcoded for THIS build only; future builds must resolve equivalents
-- from symbol.txt / address_map.json (see docs/design/Andy_build0400_timing_instrument_repair.md).

local mac  = manager.machine
local cpu  = mac.devices[":maincpu"]
local prog = cpu.spaces["program"]
local dbg  = mac.debugger
local log  = dbg and dbg.consolelog or nil
local input = mac.input
local arm_code = assert(input:code_from_token("KEYCODE_M"), "KEYCODE_M unavailable")
local function r8(a)  local v=0; pcall(function() v=prog:read_u8(a) end); return v & 0xFF end
local symbols={}
do
  local sf=os.getenv("FRAME_TIMING_SYMBOLS")
  if sf then
    local f=io.open(sf,"r")
    if f then
      for line in f:lines() do
        local a,n=line:match("^([0-9A-Fa-f]+)%s+%S%s+(.+)$")
        if a and n then symbols[#symbols+1]={tonumber(a,16),n} end
      end
      f:close(); table.sort(symbols,function(x,y) return x[1]<y[1] end)
    end
  end
end
local function owning_symbol(pc)
  local lo,hi,best=1,#symbols,"UNKNOWN"
  while lo<=hi do local mid=(lo+hi)//2
    if symbols[mid][1]<=pc then best=symbols[mid][2];lo=mid+1 else hi=mid-1 end end
  return best
end

local A_EMIT   = 0x00FFBED4
local A_INPUT  = 0x00FF61F6
local A_VC0    = 0x00FF61E4   -- vblank_vc[0]; marks 0..6 at vblank_vc+0..+6
local A_VC6    = 0x00FF61EA
local A_SCENE  = 0x00FFC554   -- genesistan_current_scene_id (1 = gameplay; 0 title, 2 end-round)
local VDP_LO, VDP_HI = 0x00C00000, 0x00C00007

-- ======== interval statistics (reset on ARM) ========
local S = {}
local function reset_interval()
  S = {
    armed_frames = 0,
    producer_completions = 0,
    input_writes = 0,
    -- exact cycle pairs (from debugger events), per serviced handler:
    pub_cycles = {}, worker_cycles = {}, irq_total_cycles = {},
    worker_entry_V = {}, worker_exit_V = {}, worker_frame_wraps = {},
    -- publication subphase beam V boundaries (from VC_MARK), per publication:
    vc = {{},{},{},{},{},{},{}},     -- vc[1..7] = beam V at marks 0..6
    -- publication-only VDP target command counts:
    tgt = {CRAM=0,VSRAM=0,planeB=0,planeA=0,SAT=0,HScroll=0,pattern=0,UNKNOWN=0},
    -- VDP ownership gate: writes outside exact PUB_ENTRY..PUB_RTS context (and armed):
    gate_viol = {}, gate_viol_total = 0,
    gate_examples = {},
    complete_handlers = 0,
    rejected_sequences = 0,
    orphan_events = 0,
    -- producer load buckets by emitted count:
    buckets = {},
    -- worker/IRQ cycles bucketed by THIS tick's emitted count (exact generation via WR's w@FFBED4):
    wbkt = {},
    -- (emitted, worker_cycles) pairs for an overall Pearson correlation:
    corr_n=0, corr_sx=0, corr_sy=0, corr_sxx=0, corr_syy=0, corr_sxy=0,
    -- per-handler time series (frame, emitted, worker_cyc, irq_cyc, pub_cyc, entryV, wraps) so the
    -- before->hurry-up-bats->sustained progression can be segmented and compared at equal emitted load:
    series = {},
    recent = {},   -- last N chronological events for boundary inspection
  }
  for i=0,8 do S.buckets[i] = {prod=0, maxemit=0, doneV={}} end
  for i=0,8 do S.wbkt[i] = {wcyc={}, irqcyc={}} end
end
reset_interval()
local armed = false
local run_started = false
local arm_down_last = false
local function push_recent(s) S.recent[#S.recent+1]=s; if #S.recent>24 then table.remove(S.recent,1) end end

-- ======== debugger breakpoints (exact cycles) ========
local have_dbg = (dbg ~= nil and cpu.debug ~= nil)
if have_dbg then
  local function act(tag) return string.format('printf "%s,%%d,%%d,%%d\\n",totalcycles,frame,w@C00008; g', tag) end
  assert(pcall(function() cpu.debug:bpset(0x070250,"1",act("PE")) end), "PUB_ENTRY breakpoint install failed")
  assert(pcall(function() cpu.debug:bpset(0x0702D2,"1",act("PR")) end), "PUB_RTS breakpoint install failed")
  assert(pcall(function() cpu.debug:bpset(0x03A208,"1",act("WE")) end), "WORKER_ENTRY breakpoint install failed")
  -- WR carries a 4th field: w@FFBED4 = THIS tick's emitted-sprite count (the producer wrote it at
  -- runtime 0x743A6 earlier in this same worker; the next write is the next IRQ6's worker), so the
  -- worker-cycle<->load association is exact and in-order (no off-by-one generation).
  assert(pcall(function() cpu.debug:bpset(0x03A27E,"1",
    'printf "WR,%d,%d,%d,%d\\n",totalcycles,frame,w@C00008,w@FFBED4; g') end), "WORKER_PRE_RTE breakpoint install failed")
  -- NOTE: the async debugger VDP WATCHPOINT ("VW") was REMOVED. Debugger watchpoint events and
  -- PE/PR breakpoint events are drained from one console log but are not guaranteed mutually
  -- chronological, which produced the false GATE FAIL / 100%-UNKNOWN artifact. VDP-write ownership
  -- (gate + target classification) is now owned by the REAL-TIME Lua VDP write tap gated by the
  -- REAL-TIME VC_MARK publication_active flag (both fire in true execution order). Debugger events
  -- own EXACT CYCLES only.
else
  error("frame_timing_trace.lua requires -debug -debugger none")
end

local FRAME_BUDGET = 128009   -- 68000 cycles per NTSC display frame (7.6705 MHz / 59.922 Hz)
local function bidx(e) return math.min(math.floor(e/10),8) end

-- Strict handler state machine (EXACT CYCLES only).  Metrics committed only after one complete
-- PE -> PR -> WE -> WR sequence; no event can pair across handlers.  WR carries this tick's emitted
-- count (w@FFBED4) so worker/IRQ cycles bucket by the SAME tick's load.
local cur = nil
local phase = "IDLE"
local function reject_sequence()
  if phase ~= "IDLE" then S.rejected_sequences = S.rejected_sequences + 1 end
  cur=nil; phase="IDLE"
end
local function on_event(tag, cyc, frame, hv, emit)
  local v = (hv >> 8) & 0xFF
  if not armed then return end
  push_recent(string.format("%s cyc=%d f=%d V=%d%s", tag, cyc, frame, v, emit and (" e="..emit) or ""))
  if tag=="PE" then
    if phase~="IDLE" then reject_sequence() end
    cur={pe=cyc,pe_f=frame}; phase="PE"
  elseif tag=="PR" and phase=="PE" then
    cur.pr=cyc; phase="PR"
  elseif tag=="WE" and phase=="PR" then
    cur.we=cyc; cur.we_v=v; cur.we_f=frame; phase="WE"
  elseif tag=="WR" and phase=="WE" then
    local wcyc = cyc-cur.we
    local icyc = cyc-cur.pe
    S.pub_cycles[#S.pub_cycles+1]=cur.pr-cur.pe
    S.worker_cycles[#S.worker_cycles+1]=wcyc
    S.irq_total_cycles[#S.irq_total_cycles+1]=icyc
    S.worker_entry_V[#S.worker_entry_V+1]=cur.we_v
    S.worker_exit_V[#S.worker_exit_V+1]=v
    S.worker_frame_wraps[#S.worker_frame_wraps+1]=frame-cur.we_f
    -- bucket worker/IRQ cycles by THIS tick's emitted count (exact generation)
    local e = emit or 0
    local wb = S.wbkt[bidx(e)]; wb.wcyc[#wb.wcyc+1]=wcyc; wb.irqcyc[#wb.irqcyc+1]=icyc
    -- accumulate Pearson correlation over (emitted, worker_cycles)
    S.corr_n=S.corr_n+1; S.corr_sx=S.corr_sx+e; S.corr_sy=S.corr_sy+wcyc
    S.corr_sxx=S.corr_sxx+e*e; S.corr_syy=S.corr_syy+wcyc*wcyc; S.corr_sxy=S.corr_sxy+e*wcyc
    S.series[#S.series+1]=string.format("%d,%d,%d,%d,%d,%d,%d",
      frame, e, wcyc, icyc, cur.pr-cur.pe, cur.we_v, frame-cur.we_f)
    S.complete_handlers=S.complete_handlers+1
    cur=nil; phase="IDLE"
  else
    S.orphan_events=S.orphan_events+1
    reject_sequence()
  end
end
local function drain()
  if not log then return end
  for i=(S._li or 0)+1,#log do
    local l = tostring(log[i])
    -- WR carries a 4th (emitted) field; PE/PR/WE carry 3. Accept only exact PE/PR/WE/WR tags.
    local tag,c,f,h,e = l:match("^(%u%u),(%d+),(%d+),(%d+),?(%d*)")
    if tag=="PE" or tag=="PR" or tag=="WE" or tag=="WR" then
      on_event(tag, tonumber(c), tonumber(f), tonumber(h), (e~="" and tonumber(e)) or nil)
    end
  end
  S._li = #log
end

-- ======== Real-time Lua taps (publication bracket + VDP ownership/classification, in true order) ========
local publication_active = false   -- owned by the REAL-TIME VC_MARK tap (mark0 => true, mark6 => false)
local ctrl_pending = nil
local function vram_target(a)
  if a>=0xFC00 and a<0x10000 then return "HScroll" end
  if a>=0xF800 and a<0xFC00  then return "SAT" end
  if a>=0xE000 and a<0xF000  then return "planeA" end
  if a>=0xC000 and a<0xE000  then return "planeB" end
  return "pattern"
end
local function classify_cmd(hi, lo)
  local cd=((hi>>14)&3)|(((lo>>4)&0x0F)<<2); local a=(hi&0x3FFF)|((lo&3)<<14); local cl=cd&7
  if cl==3 then S.tgt.CRAM=S.tgt.CRAM+1
  elseif cl==5 then S.tgt.VSRAM=S.tgt.VSRAM+1
  elseif cl==1 then local t=vram_target(a); S.tgt[t]=S.tgt[t]+1
  else S.tgt.UNKNOWN=S.tgt.UNKNOWN+1 end
end
-- REAL-TIME VDP write tap: classify publication targets while publication_active; a VDP write while
-- NOT publication_active (during armed gameplay) is a non-publication (gate) writer.
local function on_vdp_write(offset, data, mask)
  if not armed then return end
  local addr = offset or 0
  local is_ctrl = (addr & 0xFFFFFFFC)==0x00C00004
  if publication_active then
    if is_ctrl then
      local m = mask or 0xFFFFFFFF
      if m ~= 0xFFFFFFFF and m ~= 0x0000FFFF and m ~= 0xFFFF0000 then
        S.tgt.UNKNOWN=S.tgt.UNKNOWN+1; ctrl_pending=nil        -- byte/masked control write: not decodable
      elseif (data & 0xFFFF0000) ~= 0 and m==0xFFFFFFFF then
        classify_cmd((data>>16)&0xFFFF, data&0xFFFF); ctrl_pending=nil
      else
        local w = data & 0xFFFF
        if (w&0xE000)==0x8000 then ctrl_pending=nil             -- VDP register write
        elseif ctrl_pending==nil then ctrl_pending=w            -- first word of a two-word command
        else classify_cmd(ctrl_pending,w); ctrl_pending=nil end
      end
    end
    -- data-port (0xC00000) PIO payload inside publication is legitimate; not a target command.
  else
    local pc=0; pcall(function() pc=cpu.state["PC"].value & 0xFFFFFF end)
    local key=string.format("%06X",pc)
    S.gate_viol[key]=(S.gate_viol[key] or 0)+1; S.gate_viol_total=S.gate_viol_total+1
    if #S.gate_examples<24 then
      S.gate_examples[#S.gate_examples+1]=string.format("PC=%06X owner=%s port=%06X data=%X",
        pc, owning_symbol(pc), addr, data & 0xFFFFFFFF)
    end
  end
end

-- ======== VC_MARK subphase tap (also drives the real-time publication_active bracket) ========
local function on_vc_write(offset, data, mask)
  local a = offset or 0                      -- tap offset is the ABSOLUTE address
  if a==A_VC0 then publication_active=true; ctrl_pending=nil
  elseif a==A_VC6 then publication_active=false; ctrl_pending=nil end
  if armed and a>=A_VC0 and a<=A_VC6 then
    local i=(a-A_VC0)+1
    S.vc[i][#S.vc[i]+1]=(data or 0)&0xFF
  end
end
local function on_emit()
  if not armed then return end
  S.producer_completions = S.producer_completions + 1
  local e=0; pcall(function() e=prog:read_u16(A_EMIT) & 0xFFFF end)
  local hv=0; pcall(function() hv=prog:read_u16(0x00C00008) end)
  local b=math.min(math.floor(e/10),8); local bk=S.buckets[b]
  bk.prod=bk.prod+1; if e>bk.maxemit then bk.maxemit=e end
  bk.doneV[#bk.doneV+1] = (hv>>8)&0xFF
end
local function on_input() if armed then S.input_writes = S.input_writes + 1 end end

_G.ft={}
-- NOTE: install_write_tap requires the end address low bits SET; vblank_vc is 0xFF61E4..0xFF61EB.
_G.ft = _G.ft or {}
local vc_ok = pcall(function() _G.ft.vc = prog:install_write_tap(A_VC0, 0x00FF61EB, "vc", on_vc_write) end)
if not vc_ok then print("[frame_timing] WARNING: vblank_vc tap failed to install — publication bracket inactive!") end
assert(vc_ok, "vblank_vc subphase tap failed")
assert(pcall(function() _G.ft.vdp = prog:install_write_tap(VDP_LO, VDP_HI, "vdp", on_vdp_write) end), "VDP real-time tap failed")
assert(pcall(function() _G.ft.em  = prog:install_write_tap(A_EMIT, A_EMIT+1, "em", on_emit) end), "producer tap failed")
assert(pcall(function() _G.ft.in_ = prog:install_write_tap(A_INPUT, A_INPUT|1, "in", on_input) end), "input tap failed")

-- ======== report ========
local outdir = (mac.options.entries.homepath:value():match("([^;]+)") or ".") .. "/frame_timing"
os.execute('mkdir -p "'..outdir..'" 2>/dev/null')
local function pct(a,p) if #a==0 then return nil end local s={} for _,v in ipairs(a) do s[#s+1]=v end table.sort(s)
  return s[math.max(1,math.ceil(p/100*#s))] end
local function stat3(a) if #a==0 then return "N/A" end return string.format("%d / %d / %d", pct(a,50),pct(a,95),pct(a,100)) end
local function ratio(n,d) if (d or 0)==0 then return "N/A" end return string.format("%.4f", n/d) end
local FB = 128009
local function frac_over(a,thr) if #a==0 then return nil end local c=0 for _,v in ipairs(a) do if v>thr then c=c+1 end end return c/#a end
local function pctover(a,thr) local f=frac_over(a,thr); return f and string.format("%.1f%%",f*100) or "N/A" end
local function ms(c) return c/7670453*1000 end
local function pearson() -- over (emitted, worker_cycles)
  local n=S.corr_n; if n<2 then return "N/A" end
  local num=n*S.corr_sxy - S.corr_sx*S.corr_sy
  local den=math.sqrt((n*S.corr_sxx - S.corr_sx*S.corr_sx)*(n*S.corr_syy - S.corr_sy*S.corr_sy))
  if den==0 then return "N/A" end
  return string.format("%.3f", num/den)
end

local function dump()
  local f=io.open(outdir.."/frame_timing_summary.txt","w"); if not f then return end
  f:write("# Build 0400 EXACT frame-timing trace. READ-ONLY. Debugger PE/PR/WE/WR = exact cycles; WR carries\n")
  f:write("# this tick's emitted count (w@FFBED4). Real-time VC_MARK + Lua VDP tap own gate + target class.\n")
  f:write(string.format("# debugger available: %s   (exact worker/publication cycles require -debug -debugger none)\n", tostring(have_dbg)))
  f:write("# INTERVAL = first M press during scene-1 gameplay; all counters reset together; zero denominators = N/A.\n#\n")
  f:write(string.format("# armed gameplay display_frames:        %d\n", S.armed_frames))
  f:write(string.format("# producer_completions (emit; [M] count):%d\n", S.producer_completions))
  local input_status = (S.armed_frames==0) and "N/A" or
    ((S.input_writes%2==0) and string.format("%d complete input calls",S.input_writes/2) or
      "ODD => INCOMPLETE/CAPTURE BOUNDARY; handler count N/A")
  f:write(string.format("# input_writes (cross-check):            %d  (%s)\n", S.input_writes,input_status))
  f:write("#\n# --- EXACT CYCLE TIMING [M] (paired per serviced handler; partial pairs excluded) ---\n")
  f:write(string.format("# complete worker pairs:    %d\n", #S.worker_cycles))
  f:write(string.format("# rejected/incomplete sequences: %d   orphan/out-of-order events: %d   open phase: %s\n", S.rejected_sequences,S.orphan_events,phase))
  f:write(string.format("# publication cycles  (PUB_ENTRY->PUB_RTS)   med/p95/max: %s\n", stat3(S.pub_cycles)))
  f:write(string.format("# worker    cycles  (WORKER_ENTRY->pre_RTE)  med/p95/max: %s\n", stat3(S.worker_cycles)))
  f:write(string.format("# IRQ total cycles  (PUB_ENTRY->pre_RTE)      med/p95/max: %s\n", stat3(S.irq_total_cycles)))
  f:write(string.format("# worker entry beam V  med/p95/max: %s   (V<224 => past VBlank into active display)\n", stat3(S.worker_entry_V)))
  f:write(string.format("# worker pre-RTE beam V med/p95/max: %s\n", stat3(S.worker_exit_V)))
  f:write(string.format("# worker frame-wraps crossed (entry->pre-RTE) med/p95/max: %s\n", stat3(S.worker_frame_wraps)))
  f:write(string.format("# worker cycles > one frame budget (%d cyc): %s of handlers\n", FB, pctover(S.worker_cycles, FB)))
  f:write(string.format("# IRQ-total cycles > one frame budget: %s of handlers\n", pctover(S.irq_total_cycles, FB)))
  f:write("#\n# --- WORKER CYCLES BY EMITTED-SPRITE LOAD [M] (exact tick association via WR w@FFBED4) ---\n")
  f:write(string.format("# Pearson r(emitted, worker_cycles) = %s   (correlation, NOT causation)\n", pearson()))
  f:write("# bucket  samples   worker cyc med/p75/p95/max           ms med/p95   frame-mult med/p95   %>1frame\n")
  local wsum=0
  for i=0,8 do local wb=S.wbkt[i]; local a=wb.wcyc
    if #a>0 then wsum=wsum+#a; local lo=i*10; local rng=(i==8) and (lo.."+") or (lo.."-"..(lo+9))
      f:write(string.format("#  %-7s %7d   %7d/%7d/%7d/%8d    %5.1f/%5.1f    %4.2f/%4.2f        %s\n",
        rng, #a, pct(a,50),pct(a,75),pct(a,95),pct(a,100),
        ms(pct(a,50)),ms(pct(a,95)), pct(a,50)/FB, pct(a,95)/FB, pctover(a,FB))) end end
  f:write(string.format("#  (worker-cycle bucket sample total = %d; complete worker pairs = %d; must match)\n", wsum, #S.worker_cycles))
  f:write("# IRQ-total cycles by bucket (med/p95):\n")
  for i=0,8 do local wb=S.wbkt[i]; local a=wb.irqcyc
    if #a>0 then local lo=i*10; local rng=(i==8) and (lo.."+") or (lo.."-"..(lo+9))
      f:write(string.format("#   %-7s med/p95: %d / %d\n", rng, pct(a,50), pct(a,95))) end end
  f:write("#\n# --- PUBLICATION CYCLES BY LOAD: INTENTIONALLY UNBUCKETED ---\n")
  f:write("#   Publication commits the PREVIOUS tick's completed frame (N-1) while the worker produces N,\n")
  f:write("#   so associating publication cycles with THIS tick's emitted count would be an off-by-one\n")
  f:write("#   generation error. Reported only as the overall PE->PR distribution above.\n")
  f:write("#\n# --- RATIOS (same armed interval) ---\n")
  f:write(string.format("# producer_completions / armed_frames:  %s\n", ratio(S.producer_completions, S.armed_frames)))
  f:write(string.format("# worker_pairs / armed_frames:          %s\n", ratio(#S.worker_cycles, S.armed_frames)))
  f:write("#\n# --- PUBLICATION SUBPHASE boundary beam V [P] (VC_MARK 0..6: palette,tiles,PlaneB,PlaneA,sprites,scroll,end) ---\n")
  local names={"mark0_start","mark1_afterPalette","mark2_afterTiles","mark3_afterPlaneB","mark4_afterPlaneA","mark5_afterSprites","mark6_afterScroll"}
  for i=1,7 do f:write(string.format("#   %-22s beam V med/p95/max: %s\n", names[i], stat3(S.vc[i]))) end
  f:write("#\n# --- PUBLICATION-ONLY VDP TARGET COMMAND COUNTS [P] (NOT bytes/cycles/duration) ---\n")
  local tt=0 for _,v in pairs(S.tgt) do tt=tt+v end
  for _,k in ipairs({"planeB","planeA","SAT","HScroll","VSRAM","CRAM","pattern","UNKNOWN"}) do
    f:write(string.format("#   %-8s %8d  %s\n", k, S.tgt[k], (tt==0) and "N/A" or string.format("%.1f%%",S.tgt[k]/tt*100))) end
  f:write("#\n# --- PRODUCER LOAD by emitted count [M count] ---\n")
  for i=0,8 do local b=S.buckets[i]
    if b.prod>0 then local lo=i*10 local rng=(i==8) and (lo.."+") or (lo.."-"..(lo+9))
      f:write(string.format("#   emitted %-7s prodC=%d maxE=%d done-V med/p95: %s\n",rng,b.prod,b.maxemit,stat3(b.doneV))) end end
  f:write("#\n# --- VDP OWNERSHIP GATE (REAL-TIME VC_MARK bracket; a VDP write while publication_active=false) ---\n")
  if S.armed_frames==0 then f:write("#   GATE: N/A (no armed gameplay this capture)\n")
  elseif S.gate_viol_total==0 then f:write("#   GATE PASS: no VDP writes outside the VC_MARK0..6 publication bracket during gameplay.\n")
  else f:write(string.format("#   GATE FAIL: %d VDP writes outside publication. Top PCs:\n", S.gate_viol_total))
    local a={} for k,v in pairs(S.gate_viol) do a[#a+1]={k,v} end table.sort(a,function(x,y) return x[2]>y[2] end)
    for i=1,math.min(10,#a) do f:write(string.format("#     PC %s : %d\n", a[i][1], a[i][2])) end
    f:write("#   Exact offender examples:\n")
    for _,s in ipairs(S.gate_examples) do f:write("#     "..s.."\n") end end
  f:write("#\n# --- LAST EVENTS (boundary inspection) ---\n")
  for _,s in ipairs(S.recent) do f:write("#   "..s.."\n") end
  f:write("#\n# --- RENDER vs GAMEPLAY ATTRIBUTION (HEAVY = sustained dense enemies + hurry-up bats, invincible) ---\n")
  f:write("#   The worker includes enemy/actor updates + AI + collision + bookkeeping + native sprite\n")
  f:write("#   production, so a worker-cycle rise is NOT necessarily rendering. To attribute it: compare\n")
  f:write("#   worker cycles at EQUAL emitted-count across phases (per-bucket table above) and read the\n")
  f:write("#   per-handler time series (frame_timing_series.csv). If, at the same emitted bucket, worker\n")
  f:write("#   cycles jump when the bats appear, the rise is gameplay/AI, not sprite output. Pearson r\n")
  f:write("#   measures how much worker variance emitted alone explains (emitted & actor count co-vary).\n")
  f:write("#\n# NOTE: worker END is now EXACT (debugger WR breakpoint). serviced-handler deficit vs display is\n")
  f:write("#       CONSISTENT WITH one-pending-state VINT coalescing; not a direct VINT-assertion tap.\n")
  f:close()
  -- per-handler time series for phase segmentation (before -> bats -> sustained)
  local cf=io.open(outdir.."/frame_timing_series.csv","w")
  if cf then cf:write("frame,emitted,worker_cyc,irq_cyc,pub_cyc,worker_entry_V,frame_wraps\n")
    for _,s in ipairs(S.series) do cf:write(s.."\n") end cf:close() end
  print(string.format("[frame_timing] wrote summary (armed=%d worker_pairs=%d prodC=%d gate_viol=%d dbg=%s)",
    S.armed_frames, #S.worker_cycles, S.producer_completions, S.gate_viol_total, tostring(have_dbg)))
end

local total_display = 0
emu.register_frame_done(function()
  total_display = total_display + 1
  drain()
  local scene = r8(A_SCENE)
  local down=false; pcall(function() down=input:code_pressed(arm_code) end)
  if down and not arm_down_last and not run_started then
    if scene==1 then
      reset_interval(); S._li=(log and #log) or 0; run_started=true; armed=true
      cur=nil; phase="IDLE"; publication_active=false; ctrl_pending=nil
      emu.print_info("[frame_timing] CONTROLLED RUN ARMED at M; LIGHT/MEDIUM/HEAVY capture begins now")
    else emu.print_info("[frame_timing] M ignored: wait for gameplay scene 1") end
  end
  arm_down_last=down
  armed = run_started and (scene == 1)
  if armed then
    S.armed_frames = S.armed_frames + 1
  end
  if total_display % 300 == 0 then dump() end
end)
pcall(function() emu.add_machine_stop_notifier(function() drain(); dump() end) end)

print("[frame_timing] READY (Build 0400, debugger-exact). REQUIRES -debug -debugger none for cycle data.")
print("[frame_timing]   In gameplay, press M once to arm the controlled LIGHT/MEDIUM/HEAVY run.")
print("[frame_timing]   summary -> "..outdir.."/frame_timing_summary.txt")
