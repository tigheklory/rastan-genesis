-- ORIGINAL ARCADE Rastan — FULL R1/P1 sprite capture (collection only; Tighe plays).
-- Extends the accepted flying_demon_userplay_trace.lua capture to TOTAL sprite coverage:
--   (1) sweeps the ENTIRE PC090OJ object RAM (records 0..255) each frame so every emitted sprite is
--       captured regardless of producer (player, HUD, weapons, items, effects, enemies), and
--   (2) captures the actor-block + player-block states for semantic ownership.
-- No auto-drive, no stage forcing, no analysis. Reuses A5/OBJ addresses and field layout from the
-- accepted trace. Output: FD_OUT/full_observations.csv (emitted records) + owners.csv (actor states).
local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "Rastan maincpu unavailable")
local program = assert(cpu.spaces["program"], "Rastan maincpu program space unavailable")
local out_dir = assert(os.getenv("FD_OUT"), "FD_OUT is required")
local A5, OBJ = 0x0010c000, 0x00d00000

local emit = assert(io.open(out_dir .. "/full_observations.csv", "w"))
local own = assert(io.open(out_dir .. "/owners.csv", "w"))
local meta = assert(io.open(out_dir .. "/full_metadata.txt", "w"))

local function r8(a) local ok,v=pcall(function() return program:read_u8(a) end); return ok and (v&0xff) or 0 end
local function r16(a) local ok,v=pcall(function() return program:read_u16(a) end); return ok and (v&0xffff) or 0 end

-- actor blocks + PLAYER block (A5+0x11B2) for ownership; HUD/weapon/item sprites are captured by the
-- full OBJ sweep even where their producing block offset is unknown.
local blocks = {
  {name="actor_2c8", offset=0x02c8, count=9}, {name="actor_508", offset=0x0508, count=2},
  {name="actor_5c8", offset=0x05c8, count=6}, {name="actor_748", offset=0x0748, count=11},
  {name="actor_8c8", offset=0x08c8, count=5}, {name="player_11b2", offset=0x11b2, count=18},
}

emit:write("frame,section,round,renderer_mode,record,w0,y,code,x\n")
own:write("frame,section,round,block,index,actor_addr,active,class,state,mode3e,flags38,752,attr27,base_code\n")

local frame=0
local seen_emit={}
local seen_own={}
local closed=false
local function sample()
  frame=frame+1
  local section=r16(A5+0x013e)
  local round_byte=r8(A5+0x0118)
  local rmode=r16(A5+0x02a2)
  -- (1) full OBJ RAM sweep: every emitted sprite record
  for rec=0,255 do
    local b=OBJ+rec*8
    local w0,y,code,x=r16(b),r16(b+2),r16(b+4),r16(b+6)
    if ((w0|y|code|x)~=0) and y~=0x0180 and code~=0 then
      local key=table.concat({section,rec,w0,code,x&0x1ff},":")
      if not seen_emit[key] then seen_emit[key]=true
        emit:write(string.format("%d,%02X,%02X,%04X,%d,%04X,%04X,%04X,%04X\n",
          frame,section,round_byte,rmode,rec,w0,y,code,x))
      end
    end
  end
  -- (2) actor + player block ownership
  for _,blk in ipairs(blocks) do
    for i=0,blk.count-1 do
      local a=A5+blk.offset+i*0x40
      local active=r8(a); local state=r8(a+5); local base=r16(a+0x1e)
      if active~=0 and (base~=0 or state~=0) then
        local key=table.concat({section,blk.name,i,r8(a+0x3e),base,state},":")
        if not seen_own[key] then seen_own[key]=true
          own:write(string.format("%d,%02X,%02X,%s,%d,%06X,%02X,%02X,%02X,%02X,%02X,%02X,%02X,%04X\n",
            frame,section,round_byte,blk.name,i,a,active,r8(a+1),state,r8(a+0x3e),
            r8(a+0x38),r8(a+0x752),r8(a+0x27),base))
        end
      end
    end
  end
  if frame%120==0 then emit:flush(); own:flush() end
end
local function close()
  if closed then return end; closed=true
  meta:write("finished="..os.date("!%Y-%m-%dT%H:%M:%SZ").."\nframes="..frame.."\n")
  local ne=0; for _ in pairs(seen_emit) do ne=ne+1 end
  local no=0; for _ in pairs(seen_own) do no=no+1 end
  meta:write("distinct_emitted="..ne.."\ndistinct_owner_states="..no.."\n")
  emit:flush(); own:flush(); meta:flush(); emit:close(); own:close(); meta:close()
end
meta:write("started="..os.date("!%Y-%m-%dT%H:%M:%SZ").."\nmachine=rastan (ORIGINAL ARCADE)\ndriver=USER (Tighe)\n")
meta:write("A5=0x0010C000 OBJ=0x00D00000\ncapture=full OBJ RAM 0..255 + actor/player blocks\n")
meta:flush()
_G.fs_frame = emu.add_machine_frame_notifier(function()
  local ok,msg=pcall(sample); if not ok then emu.print_error("R1P1 full capture: "..tostring(msg)) end end)
_G.fs_stop = emu.add_machine_stop_notifier(close)
emu.print_info("R1/P1 FULL sprite capture ACTIVE -> "..out_dir)
