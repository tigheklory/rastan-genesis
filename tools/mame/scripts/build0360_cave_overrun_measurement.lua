-- Read-only Build 0359 native-sprite finalizer measurement for the manually
-- played first-cave Segment-1 no-kill workload. Debugger breakpoint actions
-- only print state: they do not write emulated memory, inject input, or alter
-- the ROM. Launch with -debug and a debugscript containing `g`.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"])
local output = assert(io.open(assert(os.getenv("DUMP_OUT")), "w"))
local metadata = assert(io.open(assert(os.getenv("META_OUT")), "w"))
local log = assert(machine.debugger.consolelog)
local log_index = 0
local sequence = 0
local closed = false
local breakpoints = {}

-- Exact instruction addresses in the preserved numbered Build 0359 ROM.
local points = {
    {0x073AC8, "BACK_START"},
    {0x073AD8, "BACK_END"},
    {0x073BE0, "ENTRY_START"},
    {0x073C6A, "BBOX_START"},
    {0x073CC4, "REVERSE_START"},
    {0x073D06, "REVERSE_MISS"},
    {0x073D0E, "VICTIM_LOOP"},
    {0x073D1A, "NO_FREE"},
    {0x073D54, "QUEUE_FULL"},
    {0x073E58, "HIT"},
    {0x073F00, "ENTRY_RTS"},
    {0x073F36, "FINALIZER_RTS"},
}

local function action(name)
    return string.format(
        'printf "B360,%s,%%d,%%d,%%d,%%06X,%%08X,%%08X,%%08X,%%08X,%%08X,%%08X,%%08X,%%08X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X\\n",frame,beamy,beamx,pc,d0,d1,d2,d3,d4,d5,d6,d7,w@FF0000,w@FF0002,w@FF0004,w@FF013E,w@FF10E8,w@FF10BE,w@FF10C0,w@FF10AE,w@FF10B0,w@FF10EC,w@FF10EE,w@FFC554,w@FFB7F4,w@FFB7F6,w@FFB7F8,w@FFB7FA,w@FFB7FC,w@FFB7FE,w@FFB7E8,w@FFBED6; g',
        name)
end

for _, point in ipairs(points) do
    breakpoints[#breakpoints + 1] = cpu.debug:bpset(point[1], "1", action(point[2]))
end

output:write(table.concat({
    "sequence", "event", "screen_frame", "beamy", "beamx", "pc",
    "d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7",
    "state0", "state2", "state4", "segment", "player_mode",
    "player_x", "player_y", "fg_x", "fg_y", "bg_x", "bg_y", "scene",
    "hud_count", "front_effect_count", "player_front_count", "middle_count",
    "player_body_count", "back_enemy_count", "tile_dma_count", "dropped_count",
}, ","), "\n")

local function drain_log()
    for index = log_index + 1, #log do
        local payload = tostring(log[index]):match("^B360,(.*)$")
        if payload then
            sequence = sequence + 1
            output:write(tostring(sequence), ",", payload, "\n")
        end
    end
    log_index = #log
    output:flush()
end

metadata:write("purpose=Build 0359 first-cave Segment-1 no-kill measurement\n")
metadata:write("rom=dist/rastan-direct/rastan_direct_video_test_build_0359.bin\n")
metadata:write("sha256=ca3844e6e3d0e175c0c0b5d14dd55bb4c8161d4619f14214e29d2a3d82b819cd\n")
metadata:write("mode=read-only debugger breakpoints; no input injection; no emulated-memory writes\n")
metadata:write("physical_beam=262 lines x 488 dots; phase origin at VBlank line 224\n")
metadata:write("cave_filter=state 2/3, A5+0x013E map record 2; operator-confirmed first-cave Segment-1 route\n")
metadata:write("started=" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\n")
metadata:flush()

_G.build0360_cave_frame = emu.add_machine_frame_notifier(drain_log)

local function close_files()
    if closed then return end
    closed = true
    drain_log()
    metadata:write("finished=" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\n")
    metadata:write("events=" .. tostring(sequence) .. "\n")
    metadata:close()
    output:close()
end

_G.build0360_cave_stop = emu.add_machine_stop_notifier(close_files)
emu.print_info("Build 0360 read-only cave overrun measurement ACTIVE")
