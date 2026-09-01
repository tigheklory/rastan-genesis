-- GENESIS Build-0327 ACTOR-RECORD provenance + corrected rendered-count trace (TOOLING, non-shipping).
-- Reads the arcade actor pools (a5=0xFF0000) the native dispatchers scan, per record (stride 64):
--   +0 active, +1 class, +0x16 X, +0x1A Y, +0x1E code, +0x27 attr(bank nibble), +0x38 family.
-- Blocks: 0xFF02C8 (41dae enemy), 0xFF05C8 (41dae middle / 45dfa enemy), 0xFF0748 (effect), 0xFF08C8
-- (45dfa middle). Also records the CORRECT rendered count pc090oj_emitted_count (0xFFBFA0), the six lane
-- counts (0xFFB8C0..CA), and emit_pass calls/frame (write-tap on emitted_count). NEVER uses full-SAT Y!=0.
-- Duplication signal: same source (code) active in >1 block, or same (X,Y) with two codes (base+anim/hit).
local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"]); local prog = cpu.spaces["program"]
local out = os.getenv("GEN_ACT_OUT") or "."
local BLOCKS = {{name="enemyA",base=0xFF02C8,n=16},{name="midB",base=0xFF05C8,n=12},
                {name="effect",base=0xFF0748,n=12},{name="midD",base=0xFF08C8,n=8}}
local EMIT=0xFFBFA0
local LANES={hud=0xFFB8C0,fx=0xFFB8C2,pf=0xFFB8C4,mid=0xFFB8C6,pb=0xFFB8C8,be=0xFFB8CA}
local emit_calls=0
prog:install_write_tap(EMIT, EMIT+1, "ec", function() emit_calls=emit_calls+1 end)

local frames=assert(io.open(out.."/actor_frames.csv","w"))
frames:write("frame,emit_calls,emitted,hud,fx,pf,mid,pb,be,act_enemyA,act_midB,act_effect,act_midD,dup_code_multiblock,dup_pos_multicode\n")
local recs=assert(io.open(out.."/actor_records.log","w"))
recs:write("frame block idx active class code bank x y family\n")
local rec_budget=200000
local f=0
_G._act=emu.add_machine_frame_notifier(function()
  f=f+1
  local actcnt={}; local bycode={}; local bypos={}
  for _,B in ipairs(BLOCKS) do
    local c=0
    for i=0,B.n-1 do
      local a=B.base+i*64
      local active=prog:read_u8(a) & 0xff
      if active~=0 then
        local cls=prog:read_u8(a+1)&0xff
        local code=prog:read_u16(a+0x1E)&0x0FFF
        local bank=0x30 | (prog:read_u8(a+0x27)&0x0F)
        local x=prog:read_u16(a+0x16)&0xffff
        local y=prog:read_u16(a+0x1A)&0xffff
        local fam=prog:read_u8(a+0x38)&0xff
        if code~=0 then
          c=c+1
          bycode[code]=bycode[code] or {}; bycode[code][B.name]=true
          local pk=x*65536+y; bypos[pk]=bypos[pk] or {}; bypos[pk][code]=true
          if rec_budget>0 then recs:write(string.format("%d %s %d %d %d %d 0x%02X %d %d %d\n",f,B.name,i,active,cls,code,bank,x,y,fam)); rec_budget=rec_budget-1 end
        end
      end
    end
    actcnt[B.name]=c
  end
  local dup_mb=0; for _,bs in pairs(bycode) do local n=0; for _ in pairs(bs) do n=n+1 end; if n>1 then dup_mb=dup_mb+1 end end
  local dup_pos=0; for _,cs in pairs(bypos) do local n=0; for _ in pairs(cs) do n=n+1 end; if n>1 then dup_pos=dup_pos+1 end end
  local em=prog:read_u16(EMIT)&0xffff
  local L=function(k) return prog:read_u16(LANES[k])&0xffff end
  frames:write(string.format("%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",
    f,emit_calls,em,L("hud"),L("fx"),L("pf"),L("mid"),L("pb"),L("be"),
    actcnt.enemyA,actcnt.midB,actcnt.effect,actcnt.midD,dup_mb,dup_pos))
  frames:flush(); emit_calls=0
  if f%300==0 then recs:flush() end
end)
emu.print_info("ACTOR PROVENANCE TRACE ARMED -> "..out)
