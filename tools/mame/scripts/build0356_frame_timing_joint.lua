-- Read-only Build 0356 full IRQ6/VBlank-chain timing trace.
-- Production code is not instrumented: debugger breakpoints report physical
-- beam position, interrupt state, and the copied arcade handler boundaries.

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
local taps = {}
local log = machine.debugger and machine.debugger.consolelog or nil
local log_index = 0

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

local function write_row(event, frame, beamy, beamx, pc, sr, sp,
                         stack_sr, stack_pc, state0, state2, state4,
                         scene, hvc, value, notes)
    output:write(string.format(
        "%s,%d,%d,%d,%06X,%04X,%d,%08X,%04X,%08X,%04X,%04X,%04X,%02X,%04X,%04X,%s\n",
        event, frame, beamy, beamx, pc & 0xFFFFFF, sr & 0xFFFF,
        (sr >> 8) & 7, sp & 0xFFFFFFFF, stack_sr & 0xFFFF,
        stack_pc & 0xFFFFFFFF, state0 & 0xFFFF, state2 & 0xFFFF,
        state4 & 0xFFFF, scene & 0xFF, hvc & 0xFFFF,
        value & 0xFFFF, notes or ""))
end

output:write(string.format("META,width=%d,height=%d,refresh=%.12f,max_frames=%d\n",
    screen_value("width"), screen_value("height"), screen_value("refresh"), max_frames))
output:write("event,frame,beamy,beamx,pc,sr,ipm,sp,stack_sr,stack_pc,state0,state2,state4,scene,hvc,value,notes\n")

local function read_u16(address)
    return ((prog:read_u8(address) << 8) | prog:read_u8(address + 1)) & 0xFFFF
end

local function read_u32(address)
    return ((read_u16(address) << 16) | read_u16(address + 2)) & 0xFFFFFFFF
end

local function trace_point(name)
    local sr = cpu_value("SR")
    local sp = cpu_value("SP") & 0xFFFFFF
    local count_addresses = {
        NATIVE_LANE_HUD = 0xFFB7F4,
        NATIVE_LANE_FRONT_EFFECT = 0xFFB7F6,
        NATIVE_LANE_PLAYER_FRONT = 0xFFB7F8,
        NATIVE_LANE_MIDDLE = 0xFFB7FA,
        NATIVE_LANE_PLAYER_BODY = 0xFFB7FC,
        NATIVE_LANE_BACK_ENEMY = 0xFFB7FE,
    }
    local value = 0
    if count_addresses[name] then
        value = read_u16(count_addresses[name])
    elseif name == "NATIVE_DONE_SCAN" then
        value = cpu_value("D5")
    elseif name == "NATIVE_FINALIZER_RTS" then
        value = read_u16(0xFFBED4)
    end
    write_row(name, current_frame(), screen_value("vpos"), screen_value("hpos"),
        cpu_value("PC"), sr, sp, read_u16(sp), read_u32(sp + 2),
        read_u16(0xFF0000), read_u16(0xFF0002), read_u16(0xFF0004),
        prog:read_u8(0xFFBFE0), read_u16(0xC00008), value, "execute_tap")
end

local function debugger_action(name)
    local count_expressions = {
        NATIVE_LANE_HUD = "w@FFB7F4",
        NATIVE_LANE_FRONT_EFFECT = "w@FFB7F6",
        NATIVE_LANE_PLAYER_FRONT = "w@FFB7F8",
        NATIVE_LANE_MIDDLE = "w@FFB7FA",
        NATIVE_LANE_PLAYER_BODY = "w@FFB7FC",
        NATIVE_LANE_BACK_ENEMY = "w@FFB7FE",
        NATIVE_DONE_SCAN = "d5",
        NATIVE_FINALIZER_RTS = "w@FFBED4",
    }
    local value_expression = count_expressions[name] or "0"
    return string.format(
        'printf "J356,%s,%%d,%%d,%%d,%%06X,%%04X,%%08X,%%04X,%%08X,%%04X,%%04X,%%04X,%%02X,%%04X,%%04X\\n",frame,beamy,beamx,pc,sr,sp,w@sp,d@(sp+2),w@FF0000,w@FF0002,w@FF0004,b@FFBFE0,w@C00008,%s; g',
        name, value_expression)
end

local function breakpoint(address, name)
    if type(prog.install_execute_tap) == "function" then
        taps[#taps + 1] = prog:install_execute_tap(address, address,
            "build0356_joint_" .. name, function() trace_point(name) end)
    else
        assert(log, "MAME lacks execute taps; launch with -debug")
        cpu.debug:bpset(address, "1", debugger_action(name))
    end
end

-- Final numbered-ROM PCs, established from build/genesis_postpatch.disasm.txt.
-- Native wrapper address space is runtime_genesis_pc; copied-handler PCs are
-- also runtime_genesis_pc and require address_map.json for arcade correlation.
local points = {
    {0x0700C2, "IRQ6_SERVICE_ENTRY"},
    {0x072244, "INPUT_ENTRY"},
    {0x073E2C, "PREPARE_ENTRY"},
    {0x0700CE, "PUBLISH_CALL_SITE"},
    {0x070250, "PUBLISH_ENTRY"},
    {0x0702D2, "PUBLISH_RTS"},
    {0x0700D2, "PUBLISH_RETURN"},
    {0x0700D6, "ARCADE_TAIL_JUMP"},
    {0x03A208, "ARCADE_IRQ_ENTRY"},
    {0x03A228, "ARCADE_OPTIONAL_CALL"},
    {0x03A22C, "ARCADE_OPTIONAL_RETURN"},
    {0x03A23A, "ARCADE_UPDATE_CALL"},
    {0x03A23E, "ARCADE_PREFIX_END"},
    {0x03A242, "ARCADE_3AD7C_END"},
    {0x03A246, "ARCADE_3ADE2_END"},
    {0x03A24A, "ARCADE_3A2A8_END"},
    {0x03A24E, "ARCADE_3F0FA_END"},
    {0x03A252, "ARCADE_DISPATCH_ENTRY"},
    {0x03A274, "ARCADE_DISPATCH_RETURN"},
    {0x03A27A, "ARCADE_TAIL_CALL_RETURN"},
    {0x03A27E, "ARCADE_RTE"},

    -- Coarse return-site hierarchy for the dominant copied arcade update.
    -- These remain runtime Genesis PCs; address_map.json maps 0x04210E and
    -- 0x042130 to arcade PCs 0x041F0E and 0x041F30 respectively.
    {0x04210E, "GAMEPLAY_CORE_ENTRY"},
    {0x042114, "CORE_51210_END"},
    {0x042118, "CORE_40D66_END"},
    {0x04211C, "CORE_422E6_END"},
    {0x042120, "CORE_445E0_END"},
    {0x042124, "CORE_44BB4_END"},
    {0x042128, "CORE_452D8_END"},
    {0x04212E, "CORE_4A1A6_END"},
    {0x042130, "UPDATE_42130_ENTRY"},
    {0x042136, "UPDATE_55B96_END"},
    {0x04213A, "UPDATE_45F72_END"},
    {0x042140, "UPDATE_5996E_END"},
    {0x042146, "UPDATE_59964_END"},
    {0x04214A, "UPDATE_47204_END"},
    {0x04214E, "UPDATE_FRAME_BEGIN_END"},
    {0x04215C, "UPDATE_PLAYER_END"},

    -- Build 0356 native gameplay-sprite hierarchy. These are read-only
    -- execution boundaries in the already-built ROM; lane events store their
    -- queue count in the CSV value column, and NATIVE_DONE_SCAN stores D5.
    -- These addresses come from disassembling the final numbered Build 0356
    -- ROM. The current prepatch ELF symbols are 0x10 later in this block.
    {0x072F00, "NATIVE_41DAE_ENTRY"},
    {0x07309A, "NATIVE_STAGE41_ENTRY"},
    {0x073156, "NATIVE_STAGE41_RTS"},
    {0x073762, "NATIVE_FINALIZER_ENTRY"},
    {0x0739F2, "NATIVE_GAMEPLAY_ENTRY"},
    {0x073A24, "NATIVE_LANE_HUD"},
    {0x073A34, "NATIVE_LANE_FRONT_EFFECT"},
    {0x073A44, "NATIVE_LANE_PLAYER_FRONT"},
    {0x073A54, "NATIVE_LANE_MIDDLE"},
    {0x073A64, "NATIVE_LANE_PLAYER_BODY"},
    {0x073A74, "NATIVE_LANE_BACK_ENEMY"},
    {0x073A84, "NATIVE_GAMEOVER_ENTRY"},
    {0x073DB4, "NATIVE_DONE_SCAN"},
    {0x073DE8, "NATIVE_FINALIZER_RTS"},
    {0x072F24, "NATIVE_41DAE_RTS"},
}
for _, point in ipairs(points) do breakpoint(point[1], point[2]) end

-- Observe only register-1 commands at the VDP control port. Both 0x8134 and
-- 0x8174 keep VINT enabled; any value with bit 5 clear is evidence otherwise.
local function inspect_vdp_word(word, raw)
    if (word & 0xFF00) ~= 0x8100 then return end
    local sr = cpu_value("SR")
    local sp = cpu_value("SP")
    local scene = prog:read_u8(0xFFBFE0)
    write_row("VDP_REG1_WRITE", current_frame(), screen_value("vpos"),
        screen_value("hpos"), cpu_value("PC"), sr, sp, 0, 0,
        read_u16(0xFF0000), read_u16(0xFF0002),
        read_u16(0xFF0004), scene, read_u16(0xC00008), word,
        string.format("raw=%08X;vint=%d;display=%d", raw & 0xFFFFFFFF,
            (word >> 5) & 1, (word >> 6) & 1))
end

local function vdp_write(_, data, mem_mask)
    local raw = data or 0
    if raw > 0xFFFF then
        inspect_vdp_word((raw >> 16) & 0xFFFF, raw)
        inspect_vdp_word(raw & 0xFFFF, raw)
    else
        inspect_vdp_word(raw & 0xFFFF, raw)
    end
end
taps[#taps + 1] = prog:install_write_tap(0xC00004, 0xC00007,
    "build0356_joint_vdp_reg1", vdp_write)

local function drain_log()
    if not log then return end
    for index = log_index + 1, #log do
        local line = tostring(log[index])
        local payload = line:match("^J356,(.*)$")
        if payload then
            local values = {}
            for field in payload:gmatch("[^,]+") do values[#values + 1] = field end
            if #values == 8 then
                write_row(values[1], tonumber(values[2]), tonumber(values[3]),
                    tonumber(values[4]), 0, 0, 0, 0, 0,
                    tonumber(values[5], 16), tonumber(values[6], 16),
                    tonumber(values[7], 16), tonumber(values[8], 16), 0, 0,
                    "debugger_bp")
            elseif #values == 14 then
                write_row(values[1], tonumber(values[2]), tonumber(values[3]),
                    tonumber(values[4]), tonumber(values[5], 16), tonumber(values[6], 16),
                    tonumber(values[7], 16), tonumber(values[8], 16), tonumber(values[9], 16),
                    tonumber(values[10], 16), tonumber(values[11], 16),
                    tonumber(values[12], 16), tonumber(values[13], 16),
                    tonumber(values[14], 16), 0, "debugger_bp")
            elseif #values == 15 then
                write_row(values[1], tonumber(values[2]), tonumber(values[3]),
                    tonumber(values[4]), tonumber(values[5], 16), tonumber(values[6], 16),
                    tonumber(values[7], 16), tonumber(values[8], 16), tonumber(values[9], 16),
                    tonumber(values[10], 16), tonumber(values[11], 16),
                    tonumber(values[12], 16), tonumber(values[13], 16),
                    tonumber(values[14], 16), tonumber(values[15], 16), "debugger_bp")
            end
        elseif line:match("[Ee]rror") or line:match("[Ii]nvalid") then
            output:write("META_DEBUG_LOG," .. line:gsub("[,\r\n]", ";") .. "\n")
        end
    end
    log_index = #log
end

emu.register_frame_done(function()
    host_frame = host_frame + 1
    set_input("P1 A", host_frame >= 120 and host_frame <= 132)
    set_input("P1 Start", host_frame >= 175 and host_frame <= 187)
    set_input("P1 Right", host_frame >= right_start)
    set_input("P1 C", host_frame >= jump_start and host_frame < jump_end and
        ((host_frame - jump_start) % 90) < 12)
    drain_log()
    local sr = cpu_value("SR")
    local sp = cpu_value("SP")
    write_row("EXTERNAL_FRAME_DONE", current_frame(), screen_value("vpos"),
        screen_value("hpos"), cpu_value("PC"), sr, sp, 0, 0,
        read_u16(0xFF0000), read_u16(0xFF0002), read_u16(0xFF0004),
        prog:read_u8(0xFFBFE0), read_u16(0xC00008), host_frame,
        "mame_frame_callback")
    output:flush()
    if host_frame >= max_frames then
        output:write(string.format("META,host_frames=%d\n", host_frame))
        output:flush()
        output:close()
        machine:exit()
    end
end)
