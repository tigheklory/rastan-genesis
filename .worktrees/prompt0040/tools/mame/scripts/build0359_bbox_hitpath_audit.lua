-- Read-only per-entry timing bracket for the native PC090OJ finalizer.
-- Runtime PCs are supplied by the caller so the same script measures the
-- preserved baseline and the post-link candidate without source instrumentation.
-- Each PC must be an instruction boundary; MAME reports the post-instruction
-- PC in debugger printf actions.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"])
local screen = assert(machine.screens:at(1))
local prog = assert(cpu.spaces["program"])
local output = assert(io.open(assert(os.getenv("DUMP_OUT")), "w"))
local max_frames = tonumber(os.getenv("TRACE_FRAMES") or "1800")
local right_start = tonumber(os.getenv("RIGHT_START") or "700")
local jump_start = tonumber(os.getenv("JUMP_START") or "1000")
local jump_end = tonumber(os.getenv("JUMP_END") or "1400")
local host_frame = 0
local entry_id = 0
local finalizer_id = 0
local taps = {}
local log = machine.debugger and machine.debugger.consolelog or nil
local log_index = 0

local function env_pc(name)
    return assert(tonumber(assert(os.getenv(name), name .. " is required"), 16))
end

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

local function cpu_value(name)
    local state = cpu.state[name]
    return state and tonumber(state.value) or 0
end

local function current_frame()
    local value = screen.frame_number
    if type(value) == "function" then return tonumber(value(screen)) end
    return tonumber(value) or -1
end

local function read_u16(address)
    return ((prog:read_u8(address) << 8) | prog:read_u8(address + 1)) & 0xFFFF
end

local function row(event)
    output:write(string.format(
        "%s,%d,%d,%d,%d,%d,%06X,%04X,%04X,%04X,%04X,%04X,%04X,%04X,%04X\n",
        event, host_frame, current_frame(), screen_value("vpos"),
        screen_value("hpos"), entry_id, cpu_value("PC") & 0xFFFFFF,
        cpu_value("D1") & 0xFFFF, cpu_value("D2") & 0xFFFF,
        cpu_value("D3") & 0xFFFF, cpu_value("D4") & 0xFFFF,
        cpu_value("D5") & 0xFFFF, finalizer_id,
        read_u16(0xFF0000), read_u16(0xFF0002)))
end

local function point(address, name, action)
    if type(prog.install_execute_tap) == "function" then
        taps[#taps + 1] = prog:install_execute_tap(address, address,
            "build0359_bbox_" .. name, function()
                if action then action() end
                row(name)
            end)
    else
        assert(log, "MAME lacks execute taps; launch with -debug")
        cpu.debug:bpset(address, "1", string.format(
            'printf "B359,%s,%%d,%%d,%%d,%%06X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X,%%04X\\n",frame,beamy,beamx,pc,d1,d2,d3,d4,d5,w@FF0000,w@FF0002; g',
            name))
    end
end

output:write("event,host_frame,screen_frame,beamy,beamx,entry_id,pc,d1,d2,d3,d4,d5,finalizer_id,state0,state2\n")

point(env_pc("FINALIZER_ENTRY_PC"), "FINALIZER_ENTRY", function()
    finalizer_id = finalizer_id + 1
end)
point(env_pc("ENTRY_START_PC"), "ENTRY_START", function()
    entry_id = entry_id + 1
end)
point(env_pc("BBOX_START_PC"), "BBOX_START")
point(env_pc("BBOX_ORIENT_END_PC"), "BBOX_ORIENT_END")
point(env_pc("REVERSE_START_PC"), "REVERSE_START")
point(env_pc("REVERSE_MISS_PC"), "REVERSE_MISS")
point(env_pc("HIT_START_PC"), "HIT_START")
point(env_pc("ENTRY_RTS_PC"), "ENTRY_RTS")
point(env_pc("FINALIZER_DONE_PC"), "FINALIZER_DONE")
point(env_pc("FINALIZER_RTS_PC"), "FINALIZER_RTS")

local function drain_log()
    for index = log_index + 1, log and #log or 0 do
        local line = tostring(log[index])
        local payload = line:match("^B359,(.*)$")
        if payload then
            local values = {}
            for value in payload:gmatch("[^,]+") do values[#values + 1] = value end
            local event = values[1]
            if event == "FINALIZER_ENTRY" then finalizer_id = finalizer_id + 1 end
            if event == "ENTRY_START" then entry_id = entry_id + 1 end
            output:write(string.format(
                "%s,%s,%s,%s,%s,%d,%s,%s,%s,%s,%s,%s,%d,%s,%s\n",
                event, values[2], values[2], values[3], values[4], entry_id,
                values[5], values[6], values[7], values[8], values[9], values[10],
                finalizer_id, values[11], values[12]))
        end
    end
    if log then log_index = #log end
end

emu.register_frame_done(function()
    host_frame = host_frame + 1
    set_input("P1 A", host_frame >= 120 and host_frame <= 132)
    set_input("P1 Start", host_frame >= 175 and host_frame <= 187)
    set_input("P1 Right", host_frame >= right_start)
    set_input("P1 C", host_frame >= jump_start and host_frame < jump_end and
        ((host_frame - jump_start) % 90) < 12)
    drain_log()
    output:flush()
    if host_frame >= max_frames then
        output:close()
        machine:exit()
    end
end)
