-- fg_state_sampler.lua : ORIGINAL ARCADE Rastan FG state-machine runtime sampler.
-- Analysis-only. Samples the arcade FG-engine WRAM state block during attract-demo
-- Stage-1 gameplay to confirm the static Part-2 model. No production effect.
-- arcade a5 = 0x0010C000; FG state block = a5 + 0x10xx (absolute 0x0010D0xx).
local A5 = 0x0010C000
local F = {
  selector = A5 + 0x10A8,   -- 0x0010D0A8
  strip    = A5 + 0x10CA,   -- 0x0010D0CA
  group    = A5 + 0x10CC,   -- 0x0010D0CC
  dir      = A5 + 0x10D0,   -- 0x0010D0D0  direction bitmask
  yacc     = A5 + 0x10BA,   -- 0x0010D0BA  Y strip accumulator
  xacc     = A5 + 0x10B8,   -- 0x0010D0B8  X strip accumulator
  fgx      = A5 + 0x10AE,   -- 0x0010D0AE  FG X scroll
  fgy      = A5 + 0x10B0,   -- 0x0010D0B0  FG Y scroll
  mode     = A5 + 0x10E8,   -- 0x0010D0E8  (=7 for selector 4/5/6 per static model)
  stage    = A5 + 0x013E,   -- 0x0010C13E  stage id (sanity)
  pageptr  = A5 + 0x10C6,   -- 0x0010D0C6  page pointer (u32)
}
local frame=0
local cpu, prog
local last = {}
local selector_hist = {}    -- value -> count
local mode_hist = {}
local strip_transitions = {} -- "a->b" -> count
local group_max = 0
local group_min = 0xFFFF
local events = {}            -- transition log (bounded)
local MAXEV = 400

local function root() return os.getenv("GENESISTAN_ROOT") or "." end
local function u16(a) return prog:read_u16(a) & 0xFFFF end
local function u32(a) return prog:read_u32(a) & 0xFFFFFFFF end

local function logev(s) if #events < MAXEV then events[#events+1]=s end end

local function body()
  frame = frame + 1
  if not cpu or not prog then return end
  local sel=u16(F.selector); local st=u16(F.strip); local gr=u16(F.group)
  local dir=u16(F.dir); local mo=u16(F.mode); local stg=u16(F.stage)
  selector_hist[sel]=(selector_hist[sel] or 0)+1
  mode_hist[mo]=(mode_hist[mo] or 0)+1
  if gr < group_min then group_min=gr end
  if gr > group_max then group_max=gr end
  -- transitions
  if last.sel ~= nil and sel ~= last.sel then
    logev(string.format("f%06d selector %d->%d (mode=%d stage=%d group=%d)", frame, last.sel, sel, mo, stg, gr))
  end
  if last.st ~= nil and st ~= last.st then
    local key=string.format("%d->%d", last.st & 0xFF, st & 0xFF)
    strip_transitions[key]=(strip_transitions[key] or 0)+1
    -- capture accumulators + direction bitmask AT a strip advance (publication event)
    logev(string.format("f%06d STRIP %d->%d  yacc(0x10BA)=%d xacc(0x10B8)=%d dir(0x10D0)=0x%02x fgx=%d fgy=%d",
      frame, last.st & 0xFF, st & 0xFF, u16(F.yacc), u16(F.xacc), dir, u16(F.fgx), u16(F.fgy)))
  end
  if last.gr ~= nil and gr ~= last.gr then
    logev(string.format("f%06d group %d->%d (strip=%d selector=%d fgx=%d fgy=%d)", frame, last.gr, gr, st, sel, u16(F.fgx), u16(F.fgy)))
  end
  if last.mo ~= nil and mo ~= last.mo then
    logev(string.format("f%06d mode(0x10E8) %d->%d (selector=%d)", frame, last.mo, mo, sel))
  end
  last.sel=sel; last.st=st; last.gr=gr; last.mo=mo
end

local function summary()
  local dir_c = root().."/build/mame/home/fg_state_sampler"
  os.execute("mkdir -p '"..dir_c.."'")
  local fh=io.open(dir_c.."/summary.txt","w")
  fh:write(string.format("ORIGINAL ARCADE rastan FG state sampler  %s\n", os.date()))
  fh:write(string.format("frames=%d\n", frame))
  fh:write("\n== selector (a5@0x10A8 / 0x0010D0A8) value histogram ==\n")
  local keys={} for k in pairs(selector_hist) do keys[#keys+1]=k end table.sort(keys)
  for _,k in ipairs(keys) do fh:write(string.format("  selector=%d : %d frames\n", k, selector_hist[k])) end
  fh:write("\n== mode (a5@0x10E8 / 0x0010D0E8) value histogram ==\n")
  keys={} for k in pairs(mode_hist) do keys[#keys+1]=k end table.sort(keys)
  for _,k in ipairs(keys) do fh:write(string.format("  mode=%d : %d frames\n", k, mode_hist[k])) end
  fh:write(string.format("\n== group/page (a5@0x10CC) range: min=%d max=%d ==\n", group_min, group_max))
  fh:write("\n== strip-index (a5@0x10CA) transitions ==\n")
  keys={} for k in pairs(strip_transitions) do keys[#keys+1]=k end table.sort(keys)
  for _,k in ipairs(keys) do fh:write(string.format("  %s : %d\n", k, strip_transitions[k])) end
  fh:write("\n== transition event log (selector/group/mode, bounded) ==\n")
  for _,e in ipairs(events) do fh:write("  "..e.."\n") end
  fh:close()
  emu.print_info(string.format("fg_state_sampler: frames=%d selectors=%d", frame, #keys))
end

_G.fg_reset = emu.add_machine_reset_notifier(function()
  cpu = manager.machine.devices[":maincpu"]; if cpu then prog = cpu.spaces["program"] end
end)
_G.fg_frame = emu.add_machine_frame_notifier(function()
  local ok,err=pcall(body); if not ok then emu.print_error("fg body: "..tostring(err)) end
end)
_G.fg_stop = emu.add_machine_stop_notifier(function() summary() end)
emu.print_info("fg_state_sampler loaded")
cpu = manager.machine.devices[":maincpu"]; if cpu then prog = cpu.spaces["program"] end
