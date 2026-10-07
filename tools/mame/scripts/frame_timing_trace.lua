-- frame_timing_trace.lua  (no ROM or production-source modification)
-- Exact frame-timing trace, repaired per Cody's Build-0400 re-audit
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
-- Runtime PCs default to the Build-0400/0404-compatible values and may be supplied
-- by the runner after resolution from symbol.txt/address_map.json.

local mac  = manager.machine
local cpu  = mac.devices[":maincpu"]
local prog = cpu.spaces["program"]
local dbg  = mac.debugger
local log  = dbg and dbg.consolelog or nil
local input = mac.input
local arm_code = assert(input:code_from_token("KEYCODE_M"), "KEYCODE_M unavailable")
local trace_label = os.getenv("FRAME_TIMING_LABEL") or "Build 0400"
local autorun = os.getenv("FRAME_TIMING_AUTORUN") == "1"
local function envpc(name, fallback)
  local value=os.getenv(name); if not value then return fallback end
  return assert(tonumber(value), name.." is not a numeric PC")
end
local PC_PUB_ENTRY    = envpc("FRAME_TIMING_PUB_ENTRY", 0x070250)
local PC_PUB_RTS      = envpc("FRAME_TIMING_PUB_RTS", 0x0702D2)
local PC_WORKER_ENTRY = envpc("FRAME_TIMING_WORKER_ENTRY", 0x03A208)
local PC_WORKER_RTE   = envpc("FRAME_TIMING_WORKER_RTE", 0x03A27E)
local PC_GFX1_ENTRY   = envpc("FRAME_TIMING_GFX1_ENTRY", 0x0730E8)
local PC_GFX1_RETURN  = envpc("FRAME_TIMING_GFX1_RETURN", 0x07310C)
local PC_GFX2_ENTRY   = envpc("FRAME_TIMING_GFX2_ENTRY", 0x073120)
local PC_GFX2_RETURN  = envpc("FRAME_TIMING_GFX2_RETURN", 0x073134)
local PC_PLAYER_ENTRY = envpc("FRAME_TIMING_PLAYER_ENTRY", 0x073172)
local PC_PLAYER_HIT   = envpc("FRAME_TIMING_PLAYER_HIT", 0x073242)
local PC_PLAYER_MISS  = envpc("FRAME_TIMING_PLAYER_MISS", 0x07324A)
local PC_PLAYER2_ENTRY = envpc("FRAME_TIMING_PLAYER2_ENTRY", 0)
local PC_PLAYER2_RETURN = envpc("FRAME_TIMING_PLAYER2_RETURN", 0)
local PC_GENERIC_RET  = envpc("FRAME_TIMING_GENERIC_RET", 0x07358E)
local PC_RES_MISS     = envpc("FRAME_TIMING_RES_MISS", 0x0743EC)
local function r8(a)  local v=0; pcall(function() v=prog:read_u8(a) end); return v & 0xFF end
local function r16(a) local v=0; pcall(function() v=prog:read_u16(a) end); return v & 0xFFFF end
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
local A_RECORD = 0x00FF013E
local A_ENERGY = 0x00FF013A
local A_TILE_DMA_COUNT = 0x00FFB7E8
local A_TILE_DMA_WORK  = 0x00FFB7B8
local A_RESIDENT_CODE  = 0x00FFB756
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
    generic_hits = 0, generic_fallbacks = 0, residency_misses = 0,
    pattern_installs = 0, evictions = 0,
    graphics_cycles = {}, player_cycles = {},
    dma_words = {}, dma_pattern_words = {}, dma_sat_words = {},
    generic_families = {},
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
  assert(pcall(function() cpu.debug:bpset(PC_PUB_ENTRY,"1",act("PE")) end), "PUB_ENTRY breakpoint install failed")
  assert(pcall(function() cpu.debug:bpset(PC_PUB_RTS,"1",act("PR")) end), "PUB_RTS breakpoint install failed")
  assert(pcall(function() cpu.debug:bpset(PC_WORKER_ENTRY,"1",act("WE")) end), "WORKER_ENTRY breakpoint install failed")
  -- WR carries a 4th field: w@FFBED4 = THIS tick's emitted-sprite count (the producer wrote it at
  -- runtime 0x743A6 earlier in this same worker; the next write is the next IRQ6's worker), so the
  -- worker-cycle<->load association is exact and in-order (no off-by-one generation).
  assert(pcall(function() cpu.debug:bpset(PC_WORKER_RTE,"1",
    'printf "WR,%d,%d,%d,%d\\n",totalcycles,frame,w@C00008,w@FFBED4; g') end), "WORKER_PRE_RTE breakpoint install failed")
  local function nx(pc, kind, args)
    -- A zero PC disables an optional read-only probe.  Historical ROMs do not
    -- necessarily implement later native-hit/residency entry points, while
    -- still sharing the worker and semantic graphics timing boundaries.
    if pc == 0 then return end
    args=args or "0,0,0,0,0,0"
    assert(pcall(function() cpu.debug:bpset(pc,"1",string.format(
      'printf "NX,%d,%%d,%%X,%%X,%%X,%%X,%%X,%%X\\n",totalcycles,%s; g',kind,args)) end),
      string.format("native timing breakpoint %d install failed",kind))
  end
  nx(PC_GFX1_ENTRY,1); nx(PC_GFX1_RETURN,2)
  nx(PC_GFX2_ENTRY,3); nx(PC_GFX2_RETURN,4)
  nx(PC_PLAYER_ENTRY,5); nx(PC_PLAYER_HIT,6); nx(PC_PLAYER_MISS,7)
  nx(PC_GENERIC_RET,8,"d0,a4,b@(a4+5),b@(a4+6),w@(a4+1e),b@(a4+1)")
  nx(PC_RES_MISS,9)
  nx(PC_PLAYER2_ENTRY,10); nx(PC_PLAYER2_RETURN,11)
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
local gfx_start, player_start, player2_start = nil, nil, nil
local producer_metrics = {}
local publication_metrics = {}
local function family_key(a4, raw5, raw6, base, selector)
  return string.format("a4=%06X raw5=%02X raw6=%02X base=%04X selector=%02X",
    a4 & 0xFFFFFF, raw5 & 0xFF, raw6 & 0xFF, base & 0xFFFF, selector & 0xFF)
end
local function on_native_event(kind, cyc, d0, a4, raw5, raw6, base, selector)
  if not armed then return end
  if kind==1 or kind==3 then gfx_start=cyc
  elseif kind==2 or kind==4 then
    if gfx_start and cur then cur.graphics=(cur.graphics or 0)+(cyc-gfx_start) end
    gfx_start=nil
  elseif kind==5 then player_start=cyc
  elseif kind==6 or kind==7 then
    if player_start and cur then cur.player=(cur.player or 0)+(cyc-player_start) end
    player_start=nil
  elseif kind==8 and cur then
    if (d0 & 0xFF)~=0 then cur.gh=(cur.gh or 0)+1 else cur.gf=(cur.gf or 0)+1 end
    local key=family_key(a4,raw5,raw6,base,selector)
    local row=S.generic_families[key] or {hit=0,fallback=0}
    if (d0 & 0xFF)~=0 then row.hit=row.hit+1 else row.fallback=row.fallback+1 end
    S.generic_families[key]=row
  elseif kind==9 and cur then cur.rm=(cur.rm or 0)+1
  elseif kind==10 then player2_start=cyc
  elseif kind==11 then
    if player2_start and cur then cur.player=(cur.player or 0)+(cyc-player2_start) end
    player2_start=nil
  end
end
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
    cur.pr=cyc
    local dm=table.remove(publication_metrics,1) or {words=0,pattern=0,sat=0}
    cur.dma_words=dm.words; cur.dma_pattern_words=dm.pattern; cur.dma_sat_words=dm.sat
    phase="PR"
  elseif tag=="WE" and phase=="PR" then
    cur.we=cyc; cur.we_v=v; cur.we_f=frame
    cur.graphics=0; cur.player=0; cur.gh=0; cur.gf=0; cur.rm=0
    phase="WE"
  elseif tag=="WR" and phase=="WE" then
    local wcyc = cyc-cur.we
    local icyc = cyc-cur.pe
    S.pub_cycles[#S.pub_cycles+1]=cur.pr-cur.pe
    S.worker_cycles[#S.worker_cycles+1]=wcyc
    S.irq_total_cycles[#S.irq_total_cycles+1]=icyc
    S.worker_entry_V[#S.worker_entry_V+1]=cur.we_v
    S.worker_exit_V[#S.worker_exit_V+1]=v
    S.worker_frame_wraps[#S.worker_frame_wraps+1]=frame-cur.we_f
    local pm=table.remove(producer_metrics,1) or {installs=0,evictions=0}
    local graphics=(cur.graphics or 0)+(cur.player or 0)
    S.graphics_cycles[#S.graphics_cycles+1]=graphics
    S.player_cycles[#S.player_cycles+1]=cur.player or 0
    S.generic_hits=S.generic_hits+(cur.gh or 0)
    S.generic_fallbacks=S.generic_fallbacks+(cur.gf or 0)
    S.residency_misses=S.residency_misses+(cur.rm or 0)
    S.pattern_installs=S.pattern_installs+pm.installs
    S.evictions=S.evictions+pm.evictions
    S.dma_words[#S.dma_words+1]=cur.dma_words or 0
    S.dma_pattern_words[#S.dma_pattern_words+1]=cur.dma_pattern_words or 0
    S.dma_sat_words[#S.dma_sat_words+1]=cur.dma_sat_words or 0
    -- bucket worker/IRQ cycles by THIS tick's emitted count (exact generation)
    local e = emit or 0
    local wb = S.wbkt[bidx(e)]; wb.wcyc[#wb.wcyc+1]=wcyc; wb.irqcyc[#wb.irqcyc+1]=icyc
    -- accumulate Pearson correlation over (emitted, worker_cycles)
    S.corr_n=S.corr_n+1; S.corr_sx=S.corr_sx+e; S.corr_sy=S.corr_sy+wcyc
    S.corr_sxx=S.corr_sxx+e*e; S.corr_syy=S.corr_syy+wcyc*wcyc; S.corr_sxy=S.corr_sxy+e*wcyc
    S.series[#S.series+1]=string.format("%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d",
      frame, e, wcyc, icyc, cur.pr-cur.pe, cur.we_v, frame-cur.we_f,
      graphics,cur.player or 0,cur.gh or 0,cur.gf or 0,cur.rm or 0,
      pm.installs,pm.evictions,cur.dma_words or 0)
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
    local nk,nc,nd0,na4,n5,n6,nb,ns = l:match("^NX,(%d+),(%d+),(%x+),(%x+),(%x+),(%x+),(%x+),(%x+)")
    if nk then
      on_native_event(tonumber(nk),tonumber(nc),tonumber(nd0,16),tonumber(na4,16),
        tonumber(n5,16),tonumber(n6,16),tonumber(nb,16),tonumber(ns,16))
    else
    -- WR carries a 4th (emitted) field; PE/PR/WE carry 3. Accept only exact PE/PR/WE/WR tags.
    local tag,c,f,h,e = l:match("^(%u%u),(%d+),(%d+),(%d+),?(%d*)")
    if tag=="PE" or tag=="PR" or tag=="WE" or tag=="WR" then
      on_event(tag, tonumber(c), tonumber(f), tonumber(h), (e~="" and tonumber(e)) or nil)
    end
    end
  end
  S._li = #log
end

-- ======== Real-time Lua taps (publication bracket + VDP ownership/classification, in true order) ========
local publication_active = false   -- owned by the REAL-TIME VC_MARK tap (mark0 => true, mark6 => false)
local ctrl_pending = nil
local dma_len_lo, dma_len_hi = 0, 0
local pub_dma = {words=0,pattern=0,sat=0}
local function vram_target(a)
  if a>=0xFC00 and a<0x10000 then return "HScroll" end
  if a>=0xF800 and a<0xFC00  then return "SAT" end
  if a>=0xE000 and a<0xF000  then return "planeA" end
  if a>=0xC000 and a<0xE000  then return "planeB" end
  return "pattern"
end
local function classify_cmd(hi, lo)
  local cd=((hi>>14)&3)|(((lo>>4)&0x0F)<<2); local a=(hi&0x3FFF)|((lo&3)<<14); local cl=cd&7
  local target=nil
  if cl==3 then S.tgt.CRAM=S.tgt.CRAM+1
  elseif cl==5 then S.tgt.VSRAM=S.tgt.VSRAM+1
  elseif cl==1 then local t=vram_target(a); target=t; S.tgt[t]=S.tgt[t]+1
  else S.tgt.UNKNOWN=S.tgt.UNKNOWN+1 end
  if (lo & 0x0080)~=0 then
    local words=(dma_len_hi<<8)|dma_len_lo; if words==0 then words=0x10000 end
    pub_dma.words=pub_dma.words+words
    if target=="pattern" then pub_dma.pattern=pub_dma.pattern+words end
    if target=="SAT" then pub_dma.sat=pub_dma.sat+words end
  end
end
local function ctrl_word(w)
  if (w&0xE000)==0x8000 then
    local reg=(w>>8)&0x1F; local value=w&0xFF
    if reg==0x13 then dma_len_lo=value elseif reg==0x14 then dma_len_hi=value end
    ctrl_pending=nil
  elseif ctrl_pending==nil then ctrl_pending=w
  else classify_cmd(ctrl_pending,w); ctrl_pending=nil end
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
        ctrl_word((data>>16)&0xFFFF); ctrl_word(data&0xFFFF)
      else
        ctrl_word(data & 0xFFFF)
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
  if a==A_VC0 then
    publication_active=true; ctrl_pending=nil; pub_dma={words=0,pattern=0,sat=0}
  elseif a==A_VC6 then
    publication_active=false; ctrl_pending=nil
    publication_metrics[#publication_metrics+1]=pub_dma
  end
  if armed and a>=A_VC0 and a<=A_VC6 then
    local i=(a-A_VC0)+1
    S.vc[i][#S.vc[i]+1]=(data or 0)&0xFF
  end
end
local resident_snapshot={}
for i=0,48 do resident_snapshot[i]=r16(A_RESIDENT_CODE+i*2) end
local function on_emit()
  local installs,evictions=0,0
  local count=r16(A_TILE_DMA_COUNT)
  for i=0,math.min(count,12)-1 do
    local slot=r16(A_TILE_DMA_WORK+i*4)
    local code=r16(A_TILE_DMA_WORK+i*4+2)
    if code~=0xFFFF and slot<=48 then
      installs=installs+1
      local old=resident_snapshot[slot] or 0
      if old~=0 and old~=code then evictions=evictions+1 end
      resident_snapshot[slot]=code
    end
  end
  if not armed then return end
  producer_metrics[#producer_metrics+1]={installs=installs,evictions=evictions}
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
local outdir = os.getenv("FRAME_TIMING_OUTDIR") or
  ((mac.options.entries.homepath:value():match("([^;]+)") or ".") .. "/frame_timing")
os.execute('mkdir -p "'..outdir..'" 2>/dev/null')
local function pct(a,p) if #a==0 then return nil end local s={} for _,v in ipairs(a) do s[#s+1]=v end table.sort(s)
  return s[math.max(1,math.ceil(p/100*#s))] end
local function stat3(a) if #a==0 then return "N/A" end return string.format("%d / %d / %d", pct(a,50),pct(a,95),pct(a,100)) end
local function ratio(n,d) if (d or 0)==0 then return "N/A" end return string.format("%.4f", n/d) end
local FB = 128009
local function frac_over(a,thr) if #a==0 then return nil end local c=0 for _,v in ipairs(a) do if v>thr then c=c+1 end end return c/#a end
local function pctover(a,thr) local f=frac_over(a,thr); return f and string.format("%.1f%%",f*100) or "N/A" end
local function ms(c) return c/7670453*1000 end
local function mean(a) if #a==0 then return 0 end local n=0 for _,v in ipairs(a) do n=n+v end return n/#a end
local function pearson() -- over (emitted, worker_cycles)
  local n=S.corr_n; if n<2 then return "N/A" end
  local num=n*S.corr_sxy - S.corr_sx*S.corr_sy
  local den=math.sqrt((n*S.corr_sxx - S.corr_sx*S.corr_sx)*(n*S.corr_syy - S.corr_sy*S.corr_sy))
  if den==0 then return "N/A" end
  return string.format("%.3f", num/den)
end

local function dump()
  local f=io.open(outdir.."/frame_timing_summary.txt","w"); if not f then return end
  f:write(string.format("# %s EXACT frame-timing trace. %s. Debugger PE/PR/WE/WR = exact cycles; WR carries\n",
    trace_label, autorun and "CONTROLLED AUTORUN (host input + equal energy hold)" or "READ-ONLY MANUAL INPUT"))
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
  f:write("#\n# --- NATIVE GRAPHICS / RESIDENCY / DMA [M] ---\n")
  f:write(string.format("# graphics cycles (player compositor + generic dispatch/finalize) avg/max: %.2f / %d\n",
    mean(S.graphics_cycles),pct(S.graphics_cycles,100) or 0))
  f:write(string.format("# player compositor cycles avg/max: %.2f / %d\n",mean(S.player_cycles),pct(S.player_cycles,100) or 0))
  f:write(string.format("# generic native hits / fallbacks: %d / %d\n",S.generic_hits,S.generic_fallbacks))
  f:write(string.format("# residency misses / pattern installs / evictions: %d / %d / %d\n",
    S.residency_misses,S.pattern_installs,S.evictions))
  f:write(string.format("# DMA words/frame avg/max: %.2f / %d  pattern avg: %.2f  SAT avg: %.2f\n",
    mean(S.dma_words),pct(S.dma_words,100) or 0,mean(S.dma_pattern_words),mean(S.dma_sat_words)))
  f:write("# generic actor tuples (runtime discriminator evidence):\n")
  local fam={}; for k,v in pairs(S.generic_families) do fam[#fam+1]={k,v} end
  table.sort(fam,function(a,b) return (a[2].hit+a[2].fallback)>(b[2].hit+b[2].fallback) end)
  for _,row in ipairs(fam) do f:write(string.format("#   %s hit=%d fallback=%d\n",row[1],row[2].hit,row[2].fallback)) end
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
  if cf then cf:write("frame,emitted,worker_cyc,irq_cyc,pub_cyc,worker_entry_V,frame_wraps,graphics_cyc,player_cyc,generic_hits,generic_fallbacks,residency_misses,pattern_installs,evictions,dma_words\n")
    for _,s in ipairs(S.series) do cf:write(s.."\n") end cf:close() end
  print(string.format("[frame_timing] wrote summary (armed=%d worker_pairs=%d prodC=%d gate_viol=%d dbg=%s)",
    S.armed_frames, #S.worker_cycles, S.producer_completions, S.gate_viol_total, tostring(have_dbg)))
end

local total_display = 0
local auto_record = tonumber(os.getenv("FRAME_TIMING_AUTO_RECORD") or "2")
local auto_measure_frames = tonumber(os.getenv("FRAME_TIMING_AUTO_MEASURE_FRAMES") or "1200")
local auto_max_frames = tonumber(os.getenv("FRAME_TIMING_AUTO_MAX_FRAMES") or "7000")
local auto_armed_at = nil
local fields={}
for _,port in pairs(mac.ioport.ports) do for name,field in pairs(port.fields) do fields[name]=field end end
local function set_input(name,on) if fields[name] then fields[name]:set_value(on and 1 or 0) end end
emu.register_frame_done(function()
  total_display = total_display + 1
  drain()
  local scene = r8(A_SCENE)
  if autorun then
    local rel=auto_armed_at and (S.armed_frames or 0) or 0
    local gameplay=(scene==1)
    local pre_route=(not auto_armed_at and total_display>=360)
    local route=(auto_armed_at and rel<360)
    set_input("P1 A",total_display>=120 and total_display<=132)
    set_input("P1 Start",total_display>=175 and total_display<=187)
    set_input("P1 Right",pre_route or route)
    local active_route=pre_route or route
    set_input("P1 C",active_route and (total_display%90)<12)
    set_input("P1 B",active_route and (total_display%30)<6)
    if gameplay then pcall(function() prog:write_u16(A_ENERGY,0x0030) end) end
    if not auto_armed_at and gameplay and r16(A_RECORD)==auto_record then
      reset_interval(); S._li=(log and #log) or 0
      producer_metrics={}; publication_metrics={}; gfx_start=nil; player_start=nil; player2_start=nil
      run_started=true; armed=true; auto_armed_at=total_display
      emu.print_info(string.format("[frame_timing] AUTORUN ARMED frame=%d record=%d",total_display,auto_record))
    end
  end
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
  if autorun and ((auto_armed_at and S.armed_frames>=auto_measure_frames) or total_display>=auto_max_frames) then
    drain(); dump(); mac:exit()
  end
end)
pcall(function() emu.add_machine_stop_notifier(function() drain(); dump() end) end)

print(string.format("[frame_timing] READY (%s, debugger-exact). REQUIRES -debug -debugger none for cycle data.", trace_label))
print("[frame_timing]   In gameplay, press M once to arm the controlled LIGHT/MEDIUM/HEAVY run.")
print("[frame_timing]   summary -> "..outdir.."/frame_timing_summary.txt")
if autorun then print(string.format("[frame_timing]   AUTORUN: cold boot -> record %d; measure %d rendered frames",auto_record,auto_measure_frames)) end
