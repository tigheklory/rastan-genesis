-- ordering_probe.lua
-- Phase 1 runtime ordering proof.
-- Injects menu navigation to reach SCREEN_FRONTEND_LIVE, then captures
-- the ordering of block-A write (producer) vs block-A read (renderer).

local probe_seq = 0
local events = {}
local MAX_EVENTS = 400
local frame_count = 0
local cpu = nil
local prog = nil
local tap_refs = {}
local log_path = nil
local error_logged = false
local nav_done = false

-- Navigation timing (controller 0xA10003 active low)
-- Start navigation at frame 120, 12x DOWN presses at even offsets, confirm at frame 165
local NAV_START = 120
local NAV_DOWN_PRESSES = 12   -- item 0 -> item 12
local NAV_CONFIRM_FRAME = 165 -- press A/B after DOWN presses complete
local NAV_END = 180           -- stop injecting after this frame

local function find_repo_root()
    local env_root = os.getenv("GENESISTAN_ROOT")
    if env_root and #env_root > 0 then return env_root end
    local home = manager.machine.options.entries.homepath:value():match("([^;]+)")
    if home then
        local root = home:gsub("/build/mame/home$", "")
        if root ~= home then return root end
    end
    return "."
end

local root = find_repo_root()
local trace_dir = root .. "/build/mame/home/genesistrace"
os.execute(string.format("mkdir -p '%s'", trace_dir))
log_path = trace_dir .. "/ordering_proof.txt"

local function append_log(line)
    local fh = io.open(log_path, "a")
    if fh then fh:write(line .. "\n") fh:close() end
end

-- Clear log
do
    local fh = io.open(log_path, "w")
    if fh then fh:close() end
end

local function get_pc()
    if cpu and cpu.state and cpu.state["PC"] then
        return cpu.state["PC"].value & 0xFFFFFF
    end
    return 0
end

local function record_event(name, addr, data)
    if #events >= MAX_EVENTS then return end
    probe_seq = probe_seq + 1
    local pc = get_pc()
    local ev = {seq=probe_seq, frame=frame_count, pc=pc, name=name, addr=addr & 0xFFFFFF, data=data & 0xFFFF}
    table.insert(events, ev)
    append_log(string.format("seq=%03d frame=%06d pc=%06X name=%-20s addr=%06X data=%04X",
        ev.seq, ev.frame, ev.pc, ev.name, ev.addr, ev.data))
end

-- Controller input injection: active low, bit1=Down, bit4=A(TH=0)/B(TH=1)
local function fake_pad_byte(original_data)
    if frame_count < NAV_START or frame_count > NAV_END then
        return original_data
    end
    local offset = frame_count - NAV_START
    -- DOWN presses: frames NAV_START, NAV_START+2, ..., NAV_START+(2*11)
    -- Each "press" frame has even offset 0,2,4,...,22
    if offset < NAV_DOWN_PRESSES * 2 and (offset % 2) == 0 then
        append_log(string.format("input_inject frame=%06d DOWN_press offset=%d", frame_count, offset))
        return original_data & 0xFD  -- bit1 (Down) = 0 = pressed
    end
    -- Confirm: frame NAV_CONFIRM_FRAME
    if frame_count == NAV_CONFIRM_FRAME then
        append_log(string.format("input_inject frame=%06d CONFIRM", frame_count))
        return original_data & 0xEF  -- bit4 (A/B) = 0 = pressed
    end
    return original_data
end

local function arm_probe()
    cpu = manager.machine.devices[":maincpu"]
    if not cpu then
        append_log("ERROR: maincpu not found")
        return
    end
    prog = cpu.spaces["program"]
    if not prog then
        append_log("ERROR: program space not found")
        return
    end

    tap_refs = {}

    -- WRITE tap: 0xFF11FE-0xFF121D (block-A clear by producer, 32 bytes)
    local ok1, t1 = pcall(function()
        return prog:install_write_tap(0xFF11FE, 0xFF121D, "block_a_write",
            function(addr, data, mask)
                record_event("block_a_write", addr, data)
            end)
    end)
    if ok1 and t1 then
        tap_refs[#tap_refs+1] = t1
        append_log("tap installed: block_a_write 0xFF11FE-0xFF121D")
    else
        append_log(string.format("WARN: block_a_write tap failed: %s", tostring(t1)))
    end

    -- READ tap: 0xFF11FE-0xFF121D (read by renderer as part of sprite block 0 scan)
    local ok2, t2 = pcall(function()
        return prog:install_read_tap(0xFF11FE, 0xFF121D, "block_a_read",
            function(addr, data, mask)
                record_event("block_a_read", addr, data)
                return data
            end)
    end)
    if ok2 and t2 then
        tap_refs[#tap_refs+1] = t2
        append_log("tap installed: block_a_read 0xFF11FE-0xFF121D")
    else
        append_log(string.format("WARN: block_a_read tap failed: %s", tostring(t2)))
    end

    -- READ tap: 0xA10002-0xA10003 (full word range for Genesis pad 1 register)
    -- MAME requires even start + odd end for word-range taps.
    -- Controller state is in the low byte (0xA10003). Callback handles both addr cases.
    local ok3, t3 = pcall(function()
        return prog:install_read_tap(0xA10002, 0xA10003, "pad1_inject",
            function(addr, data, mask)
                if addr == 0xA10002 then
                    local faked = fake_pad_byte(data & 0xFF)
                    return (data & 0xFF00) | (faked & 0xFF)
                else
                    return fake_pad_byte(data & 0xFF) & 0xFF
                end
            end)
    end)
    if ok3 and t3 then
        tap_refs[#tap_refs+1] = t3
        append_log("tap installed: pad1_inject 0xA10002")
    else
        append_log(string.format("WARN: pad1_inject tap failed: %s", tostring(t3)))
    end

    append_log(string.format("arm: taps_installed=%d frame=%d", #tap_refs, frame_count))
end

local function write_summary()
    append_log("")
    append_log("=== ORDERING SUMMARY ===")
    append_log(string.format("total_events=%d total_frames=%d", #events, frame_count))

    local first_write = nil
    local first_read = nil
    for _, ev in ipairs(events) do
        if not first_write and ev.name == "block_a_write" then
            first_write = ev
        end
        if not first_read and ev.name == "block_a_read" then
            first_read = ev
        end
        if first_write and first_read then break end
    end

    if first_write then
        append_log(string.format("FIRST_WRITE (producer region): seq=%d frame=%d pc=0x%06X addr=0x%06X data=0x%04X",
            first_write.seq, first_write.frame, first_write.pc, first_write.addr, first_write.data))
    else
        append_log("FIRST_WRITE (producer region): NOT OBSERVED")
    end

    if first_read then
        append_log(string.format("FIRST_READ (renderer region): seq=%d frame=%d pc=0x%06X addr=0x%06X data=0x%04X",
            first_read.seq, first_read.frame, first_read.pc, first_read.addr, first_read.data))
    else
        append_log("FIRST_READ (renderer region): NOT OBSERVED")
    end

    if first_write and first_read then
        if first_write.seq < first_read.seq then
            append_log("VERDICT: PRODUCER BEFORE RENDERER -- ORDERING CORRECT (Phase 1 fix verified)")
        elseif first_read.seq < first_write.seq then
            append_log("VERDICT: RENDERER BEFORE PRODUCER -- ORDERING INCORRECT (bug still present)")
        else
            append_log("VERDICT: SAME SEQ -- INDETERMINATE")
        end
    else
        append_log("VERDICT: INCOMPLETE -- one or both events not observed")
    end

    local write_count = 0
    local read_count = 0
    for _, ev in ipairs(events) do
        if ev.name == "block_a_write" then write_count = write_count + 1 end
        if ev.name == "block_a_read" then read_count = read_count + 1 end
    end
    append_log(string.format("total_write_events=%d total_read_events=%d", write_count, read_count))
end

_G.ordering_probe_reset_sub = emu.add_machine_reset_notifier(function()
    frame_count = 0
    probe_seq = 0
    events = {}
    error_logged = false
    nav_done = false
    arm_probe()
end)

_G.ordering_probe_frame_sub = emu.add_machine_frame_notifier(function()
    local ok, err = pcall(function()
        frame_count = frame_count + 1
        if frame_count % 60 == 0 then
            local current_screen_val = 0
            if prog then current_screen_val = prog:read_u16(0xFF6DCC) end
            append_log(string.format("heartbeat frame=%06d current_screen=%d", frame_count, current_screen_val))
        end
    end)
    if not ok and not error_logged then
        error_logged = true
        append_log("frame_error: " .. tostring(err))
    end
end)

_G.ordering_probe_stop_sub = emu.add_machine_stop_notifier(function()
    write_summary()
    append_log("==== ordering_probe stop ====")
end)

arm_probe()
append_log(string.format("ordering_probe loaded root=%s", root))
