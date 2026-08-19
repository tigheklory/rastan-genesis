-- teardown_validate.lua : PC090OJ teardown validation (headless, no video).
-- Signals: (1) no crash-handler entry (PC never in the high .crash section),
--          (2) sprites still staged (live staged_sprite_sat nonzero) per scene.
local CRASH_LO, CRASH_HI = 0x185000, 0x186000
local SAT_BASE = 0x00FF61CC
local SCENE_ID = 0x00FF707C
local frame=0
local cpu, prog
local crash_seen=false
local crash_pc=0
local crash_frame=-1
local sat_max_by_scene={}
local scene_frames={}

local function root() return os.getenv("GENESISTAN_ROOT") or "." end

local function body()
  frame = frame + 1
  if not cpu or not prog then return end
  local pcst = cpu.state["PC"] or cpu.state["CURPC"]
  local pc = pcst and (pcst.value & 0xFFFFFF) or 0
  if pc >= CRASH_LO and pc < CRASH_HI and not crash_seen then
    crash_seen=true; crash_pc=pc; crash_frame=frame
  end
  local scene = prog:read_u8(SCENE_ID)
  local nz=0
  for a=SAT_BASE, SAT_BASE+0x280, 2 do
    if (prog:read_u16(a) & 0xFFFF) ~= 0 then nz=nz+1 end
  end
  scene_frames[scene]=(scene_frames[scene] or 0)+1
  if nz > (sat_max_by_scene[scene] or 0) then sat_max_by_scene[scene]=nz end
end

_G.tv_reset_sub = emu.add_machine_reset_notifier(function()
  cpu = manager.machine.devices[":maincpu"]
  if cpu then prog = cpu.spaces["program"] end
end)

_G.tv_frame_sub = emu.add_machine_frame_notifier(function()
  local ok,err = pcall(body)
  if not ok then emu.print_error("teardown_validate body: "..tostring(err)) end
end)

_G.tv_stop_sub = emu.add_machine_stop_notifier(function()
  os.execute("mkdir -p '"..root().."/build/mame/home/teardown_validate'")
  local fh=io.open(root().."/build/mame/home/teardown_validate/summary.txt","w")
  fh:write(string.format("frames=%d\n", frame))
  fh:write(string.format("crash_seen=%s crash_pc=0x%06x crash_frame=%d\n",
    tostring(crash_seen), crash_pc, crash_frame))
  local ids={}
  for k in pairs(scene_frames) do ids[#ids+1]=k end
  table.sort(ids)
  for _,s in ipairs(ids) do
    fh:write(string.format("scene=%d frames=%d sat_nonzero_words_max=%d\n",
      s, scene_frames[s], sat_max_by_scene[s] or 0))
  end
  fh:write(string.format("VERDICT=%s\n", crash_seen and "CRASH_DETECTED" or "NO_CRASH"))
  fh:close()
  emu.print_info(string.format("teardown_validate: crash=%s frames=%d", tostring(crash_seen), frame))
end)

emu.print_info("teardown_validate loaded")
cpu = manager.machine.devices[":maincpu"]
if cpu then prog = cpu.spaces["program"] end
