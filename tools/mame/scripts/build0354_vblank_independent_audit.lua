-- Read-only VBlank audit using debugger PC breakpoints. Build 0354 remains the
-- default address profile; environment overrides allow shifted candidate ROMs
-- to be measured with the same physical-beam method.
-- Breakpoint actions log MAME's monotonic (frame, beam Y, beam X) tuple.  This
-- avoids the ROM diagnostic's lossy 8-bit V-counter subtraction.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"])
local screen = assert(machine.screens:at(1))
local output = assert(io.open(assert(os.getenv("DUMP_OUT")), "w"))
local max_frames = tonumber(os.getenv("TRACE_FRAMES") or "1800")
local right_start = tonumber(os.getenv("RIGHT_START") or "700")
local jump_start = tonumber(os.getenv("JUMP_START") or "1000")
local jump_end = tonumber(os.getenv("JUMP_END") or "1400")
local log = assert(machine.debugger.consolelog)
local log_index = 0
local host_frame = 0
local breakpoints = {}

local function env_hex(name, default)
    local value = os.getenv(name)
    if not value or value == "" then return default end
    return assert(tonumber(value), "invalid address in " .. name)
end

local function env_optional_hex(name, default)
    local value = os.getenv(name)
    if value == "NONE" then return nil end
    return env_hex(name, default)
end

local worklist_count_addr = env_hex("WORKLIST_COUNT_ADDR", 0xFFB884)
local emitted_count_addr = env_hex("EMITTED_COUNT_ADDR", 0xFFBF70)
local frame_ready_addr = env_hex("FRAME_READY_ADDR", 0xFFB740)
local worklist_addr = env_hex("WORKLIST_ADDR", 0xFFB854)

local fields = {}
for _, port in pairs(machine.ioport.ports) do
    for name, field in pairs(port.fields) do fields[name] = field end
end

local function set_input(name, active)
    if fields[name] then fields[name]:set_value(active and 1 or 0) end
end

local function screen_value(name)
    local value = screen[name]
    if type(value) == "function" then return tonumber(value(screen)) end
    return tonumber(value) or -1
end

output:write(string.format("META,width=%d,height=%d,refresh=%.9f\n",
    screen_value("width"), screen_value("height"), screen_value("refresh")))
output:write("event,frame,beamy,beamx,state0,state2,state4,worklist_count,emitted_count,frame_ready,d4,d6\n")

local function action(name)
    return string.format(
        'printf "B354,%s,%%d,%%d,%%d,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X\\n",frame,beamy,beamx,w@FF0000,w@FF0002,w@FF0004,w@%06X,w@%06X,w@%06X,d4,d6; g',
        name, worklist_count_addr, emitted_count_addr, frame_ready_addr)
end

local function set_breakpoint(address, name)
    breakpoints[#breakpoints + 1] = cpu.debug:bpset(address, "1", action(name))
end

-- Numbered main-ROM addresses, established by direct binary disassembly.
local points = {
    {0x070250, "PUB_ENTRY"},
    {0x070254, "MARK0_START"}, {0x070262, "MARK0_END"},
    {0x07034C, "PALETTE_ENTRY"}, {0x070266, "PALETTE_END_MARK1_START"}, {0x070274, "MARK1_END"},
    {0x0700DC, "TILES_ENTRY"}, {0x070278, "TILES_END_MARK2_START"}, {0x070286, "MARK2_END"},
    {0x070106, "PLANE_B_ENTRY"}, {0x07028A, "PLANE_B_END_MARK3_START"}, {0x070298, "MARK3_END"},
    {0x0725DE, "PLANE_A_ENTRY"}, {0x07029C, "PLANE_A_END_MARK4_START"}, {0x0702AA, "MARK4_END"},
    {env_hex("SPRITE_ENTRY_PC", 0x073EEC), "SPRITE_ENTRY"},
    {env_hex("SPRITE_TILE_ENTRY_PC", 0x073F28), "SPRITE_TILE_ENTRY"},
    {env_hex("PATTERN_DMA_CALL_PC", 0x073F88), "PATTERN_DMA_CALL"},
    {env_hex("PATTERN_DMA_END_PC", 0x073F8C), "PATTERN_DMA_END"},
    {env_hex("SPRITE_TILE_END_PC", 0x073EF4), "SPRITE_TILE_END"},
    {env_optional_hex("SPRITE_PALETTE_ENTRY_PC", 0x073E6C), "SPRITE_PALETTE_ENTRY"},
    {env_optional_hex("SPRITE_PALETTE_END_PC", 0x073F18), "SPRITE_PALETTE_END"},
    {env_hex("SPRITE_SAT_ENTRY_PC", 0x073FD2), "SPRITE_SAT_ENTRY"},
    {env_hex("SPRITE_SAT_END_PC", 0x073F1C), "SPRITE_SAT_END"},
    {0x0702AE, "SPRITE_END_MARK5_START"}, {0x0702BC, "MARK5_END"},
    {0x07018E, "SCROLL_ENTRY"}, {0x0702C0, "SCROLL_END_MARK6_START"}, {0x0702CE, "MARK6_END"},
    {0x0702D2, "PUB_EXIT"}
}
for _, point in ipairs(points) do
    if point[1] then set_breakpoint(point[1], point[2]) end
end

-- Dump the complete bounded 12-entry worklist at sprite-commit entry, before reset.
local worklist_words = {}
for offset = 0, 46, 2 do
    worklist_words[#worklist_words + 1] = string.format("w@%06X", worklist_addr + offset)
end
cpu.debug:bpset(env_hex("SPRITE_ENTRY_PC", 0x073EEC), "1",
    'printf "B354W,%d,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X\\n",frame,' .. table.concat(worklist_words, ",") .. '; g')

local function drain_log()
    for index = log_index + 1, #log do
        local line = tostring(log[index])
        local event = line:match("^B354,(.*)$")
        local worklist = line:match("^B354W,(.*)$")
        if event then output:write(event .. "\n") end
        if worklist then output:write("WORKLIST," .. worklist .. "\n") end
    end
    log_index = #log
    output:flush()
end

emu.register_frame_done(function()
    host_frame = host_frame + 1
    set_input("P1 A", host_frame >= 120 and host_frame <= 132)
    set_input("P1 Start", host_frame >= 175 and host_frame <= 187)
    set_input("P1 Right", host_frame >= right_start)
    set_input("P1 C", host_frame >= jump_start and host_frame < jump_end and ((host_frame - jump_start) % 90) < 12)
    drain_log()
    if host_frame >= max_frames then
        output:write(string.format("META,host_frames=%d\n", host_frame))
        output:flush()
        output:close()
        machine:exit()
    end
end)
