-- ORIGINAL ARCADE Rastan — USER-DRIVEN Flying Demon evidence trace (collection only).
-- Tighe plays manually (coin=5, start=1). No auto-drive, no stage forcing, no analysis.
-- Records live actor states (incl. aux blocks 0x748/0x8c8), PC090OJ emitted records, and marks
-- encounters at Section 9/Record 8 and Section 14/Record 13. Reuses arcade_enemy_sweep.lua field layout.
local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "Rastan maincpu unavailable")
local program = assert(cpu.spaces["program"], "Rastan maincpu program space unavailable")
local out_dir = assert(os.getenv("FD_OUT"), "FD_OUT is required")
local A5, OBJ = 0x0010c000, 0x00d00000

local obs = assert(io.open(out_dir .. "/observations.csv", "w"))
local enc = assert(io.open(out_dir .. "/encounters.tsv", "w"))
local meta = assert(io.open(out_dir .. "/metadata.txt", "w"))

local function r8(a) local ok,v=pcall(function() return program:read_u8(a) end); return ok and (v&0xff) or 0 end
local function r16(a) local ok,v=pcall(function() return program:read_u16(a) end); return ok and (v&0xffff) or 0 end

local blocks = {
  {name="actor_2c8", offset=0x02c8, count=9}, {name="actor_508", offset=0x0508, count=2},
  {name="actor_5c8", offset=0x05c8, count=6}, {name="actor_748", offset=0x0748, count=11},
  {name="actor_8c8", offset=0x08c8, count=5},
}
local function owned_range(block, index, boss_mode)
  if boss_mode then
    if block=="actor_5c8" then return 140+math.min(index,3)*10+math.max(index-3,0)*20,(index<3) and 10 or 20
    elseif block=="actor_748" then return 46+index*6,6 elseif block=="actor_8c8" then return 96+index*4,4 end
    return -1,0 end
  if block=="actor_2c8" then return 140+index*10,(index==8) and 19 or 10
  elseif block=="actor_508" then return 57+index*13,13
  elseif block=="actor_5c8" then return 96+index*4,4
  elseif block=="actor_748" then return 46+index,1 end
  return -1,0
end
local function record_string(sr, cnt)
  if sr<0 or cnt<=0 then return "" end
  local p={}
  for record=sr,sr+cnt-1 do
    local b=OBJ+record*8; local w0,y,code,x=r16(b),r16(b+2),r16(b+4),r16(b+6)
    if ((w0|y|code|x)~=0) and y~=0x0180 then p[#p+1]=string.format("%d:%04X:%04X:%04X:%04X",record,w0,y,code,x) end
  end
  return table.concat(p,"|")
end

obs:write("frame,scene,round,record,renderer_mode,block,actor_index,actor_address,active,class,state,anim,mode3e,flags38,752,attr27,base_code,world_x,world_y,owned_start,owned_count,piece_records\n")
enc:write("frame\ttarget\trecord\tscene\tround\tnote\n")

local frame=0
local seen={}
local enc8_first,enc8_last,enc13_first,enc13_last
local closed=false
local function sample()
  frame=frame+1
  local scene=r8(0x00ff707c)          -- gameplay scene id (mirror per prior work)
  local round_byte=r8(A5+0x0118)
  local record=r16(A5+0x013e)
  local renderer_mode=r16(A5+0x02a2)
  local boss_mode=renderer_mode==2
  -- encounter markers (gameplay + target record)
  if record==8 then enc8_first=enc8_first or frame; enc8_last=frame
    if frame%30==0 then enc:write(string.format("%d\tSECTION9_RECORD8\t%d\t%02X\t%02X\tin-record\n",frame,record,scene,round_byte)) end
  elseif record==13 then enc13_first=enc13_first or frame; enc13_last=frame
    if frame%30==0 then enc:write(string.format("%d\tSECTION14_RECORD13\t%d\t%02X\t%02X\tin-record\n",frame,record,scene,round_byte)) end
  end
  for _,block in ipairs(blocks) do
    for index=0,block.count-1 do
      local actor=A5+block.offset+index*0x40
      local active=r8(actor); local state=r8(actor+5)
      local base_code=r16(actor+0x1e)
      local sr,cnt=owned_range(block.name,index,boss_mode)
      local pieces=record_string(sr,cnt)
      if active~=0 and state~=0 and (base_code~=0 or pieces~="") then
        -- dedup by (record,block,index,3e,base,attr,state,pieces) so distinct states are kept, size bounded
        local key=table.concat({record,block.name,index,r8(actor+0x3e),base_code,r8(actor+0x27),state,pieces},":")
        if not seen[key] then
          seen[key]=true
          obs:write(table.concat({frame,string.format("%02X",scene),string.format("%02X",round_byte),
            record,string.format("%04X",renderer_mode),block.name,index,string.format("%06X",actor),
            string.format("%02X",active),string.format("%02X",r8(actor+1)),string.format("%02X",state),
            string.format("%04X",r16(actor+0x16)),string.format("%02X",r8(actor+0x3e)),
            string.format("%02X",r8(actor+0x38)),string.format("%02X",r8(actor+0x752)),
            string.format("%02X",r8(actor+0x27)),string.format("%04X",base_code),
            string.format("%04X",r16(actor+0x1a)),string.format("%04X",r16(actor+0x22)),
            sr,cnt,pieces},","),"\n")
        end
      end
    end
  end
  if frame%120==0 then obs:flush(); enc:flush() end
end
local function close()
  if closed then return end; closed=true
  meta:write("finished="..os.date("!%Y-%m-%dT%H:%M:%SZ").."\n")
  meta:write("frames="..frame.."\n")
  meta:write("section9_record8_frames="..tostring(enc8_first).."-"..tostring(enc8_last).."\n")
  meta:write("section14_record13_frames="..tostring(enc13_first).."-"..tostring(enc13_last).."\n")
  meta:write("distinct_actor_states="..(function() local n=0; for _ in pairs(seen) do n=n+1 end; return n end)().."\n")
  obs:flush(); enc:flush(); meta:flush(); obs:close(); enc:close(); meta:close()
end
meta:write("started="..os.date("!%Y-%m-%dT%H:%M:%SZ").."\nmachine=rastan (ORIGINAL ARCADE)\ndriver=USER (Tighe)\n")
meta:write("A5=0x0010C000 OBJ(PC090OJ)=0x00D00000\ntargets=Section9/Record8, Section14/Record13\n")
meta:flush()
_G.fd_frame = emu.add_machine_frame_notifier(function()
  local ok,msg=pcall(sample); if not ok then emu.print_error("FD trace: "..tostring(msg)) end end)
_G.fd_stop = emu.add_machine_stop_notifier(close)
emu.print_info("Flying Demon USER-DRIVEN trace ACTIVE -> "..out_dir)
