--[[
rastanjumptrace.lua  (v2)
=========================
Traces the Rastan arcade maincpu to find every point
where the 68000 PC enters the C-Window range
0xC00000-0xC0FFFF during normal title screen operation.

PURPOSE
-------
The Genesis port crashes because the arcade frontend
tick uses C-Window RAM as executable memory. This
script runs against the ARCADE ROM in MAME (not the
Genesis ROM) to build a complete list of every
C-Window execution site so they can all be replaced
with opcode patches.

WHAT IT LOGS
------------
1. Every indirect branch (JMP/JSR through register)
   whose computed target lands in C-Window range,
   with source PC and target address.
2. Every opcode fetch directly from C-Window range
   (PC itself is in C-Window) caught via read tap.
3. Frame boundaries so we know which frame each
   event occurs in.
4. A summary of all unique C-Window PCs seen.

OUTPUT
------
build/mame/home/rastanjumptrace/
  rastan_cwin_exec_trace.log   -- full event log
  rastan_cwin_exec_summary.txt -- unique addresses

RUN
---
tools/mame/run_rastan_jumptrace_wsl.sh

DURATION
--------
Auto-stops after MAX_FRAMES (default 1800 = ~30 sec).
Close MAME manually to stop earlier.
Summary is written on stop.
--]]

local MAX_FRAMES        = 1800
local LOG_INDIRECT      = true
local LOG_CWIN_EXEC     = true
local MAX_LOG_LINES     = 5000
local FRAME_LOG_STRIDE  = 60

local C_WINDOW_BASE = 0xC00000
local C_WINDOW_END  = 0xC0FFFF

local function in_cwindow(addr)
    return addr >= C_WINDOW_BASE and addr <= C_WINDOW_END
end

local frame_count    = 0
local log_path       = nil
local summary_path   = nil
local cpu            = nil
local prog           = nil
local tap_refs       = {}
local error_logged   = false
local done           = false
local log_lines      = 0
local cwin_exec_sites = {}

_G.rastanjumptrace_reset_sub = nil
_G.rastanjumptrace_stop_sub  = nil
_G.rastanjumptrace_frame_sub = nil

local function is_rastan_set(name)
    return string.match(name or "", "^rastan") ~= nil
end

local function append_log(line)
    if not log_path then return end
    if log_lines >= MAX_LOG_LINES then return end
    local fh = io.open(log_path, "a")
    if fh then
        fh:write(line)
        fh:write("\n")
        fh:close()
        log_lines = log_lines + 1
        if log_lines == MAX_LOG_LINES then
            local fh2 = io.open(log_path, "a")
            if fh2 then
                fh2:write("[LOG LIMIT REACHED]\n")
                fh2:close()
            end
        end
    end
end

local function record_cwin_site(addr, src_pc)
    local site = cwin_exec_sites[addr]
    if not site then
        cwin_exec_sites[addr] = {
            count       = 1,
            first_frame = frame_count,
            first_src   = src_pc or 0,
        }
    else
        site.count = site.count + 1
    end
end

local function current_pc()
    if not cpu or not cpu.state or not cpu.state["PC"] then
        return nil
    end
    return cpu.state["PC"].value & 0xFFFFFF
end

local function reg_an(n)
    local key = "A" .. tostring(n)
    if cpu and cpu.state and cpu.state[key] then
        return cpu.state[key].value & 0xFFFFFFFF
    end
    return nil
end

local function read16(addr)
    if not prog then return 0 end
    local ok, v = pcall(function() return prog:read_u16(addr) end)
    if ok then return v or 0 end
    return 0
end

local function read32(addr)
    if not prog then return 0 end
    local ok, v = pcall(function() return prog:read_u32(addr) end)
    if ok then return v or 0 end
    return 0
end

local function sign_extend_16(v)
    v = v & 0xFFFF
    if v >= 0x8000 then return v - 0x10000 end
    return v
end

local function sign_extend_8(v)
    v = v & 0xFF
    if v >= 0x80 then return v - 0x100 end
    return v
end

local function decode_indirect_branch(pc)
    local op = read16(pc)
    local mnem, target, rn

    if op >= 0x4E90 and op <= 0x4E97 then
        rn = op & 0x07
        local an = reg_an(rn)
        if an then mnem = string.format("JSR (A%d)", rn); target = an & 0xFFFFFF end
    elseif op >= 0x4EA8 and op <= 0x4EAF then
        rn = op & 0x07
        local an = reg_an(rn)
        if an then mnem = string.format("JSR (d16,A%d)", rn)
            target = (an + sign_extend_16(read16(pc+2))) & 0xFFFFFF end
    elseif op >= 0x4EB0 and op <= 0x4EB7 then
        rn = op & 0x07
        local an = reg_an(rn)
        if an then mnem = string.format("JSR (d8,A%d,Xn)", rn)
            target = (an + sign_extend_8(read16(pc+2) & 0xFF)) & 0xFFFFFF end
    elseif op == 0x4EB8 then
        mnem = "JSR abs.w"
        target = sign_extend_16(read16(pc+2)) & 0xFFFFFF
    elseif op == 0x4EB9 then
        mnem = "JSR abs.l"
        target = read32(pc+2) & 0xFFFFFF
    elseif op >= 0x4ED0 and op <= 0x4ED7 then
        rn = op & 0x07
        local an = reg_an(rn)
        if an then mnem = string.format("JMP (A%d)", rn); target = an & 0xFFFFFF end
    elseif op >= 0x4EE8 and op <= 0x4EEF then
        rn = op & 0x07
        local an = reg_an(rn)
        if an then mnem = string.format("JMP (d16,A%d)", rn)
            target = (an + sign_extend_16(read16(pc+2))) & 0xFFFFFF end
    elseif op >= 0x4EF0 and op <= 0x4EF7 then
        rn = op & 0x07
        local an = reg_an(rn)
        if an then mnem = string.format("JMP (d8,A%d,Xn)", rn)
            target = (an + sign_extend_8(read16(pc+2) & 0xFF)) & 0xFFFFFF end
    elseif op == 0x4EF8 then
        mnem = "JMP abs.w"
        target = sign_extend_16(read16(pc+2)) & 0xFFFFFF
    elseif op == 0x4EF9 then
        mnem = "JMP abs.l"
        target = read32(pc+2) & 0xFFFFFF
    end

    return mnem, target
end

local function install_cwin_tap()
    if not prog then return end
    local ok, tap = pcall(function()
        return prog:install_read_tap(
            C_WINDOW_BASE, C_WINDOW_END,
            "rastanjumptrace_cwin",
            function(offset, data, mask)
                local pc = current_pc() or 0
                if in_cwindow(pc) and LOG_CWIN_EXEC then
                    record_cwin_site(pc, nil)
                    append_log(string.format(
                        "[frame %06d] CWIN_PC  pc=0x%06X  off=0x%04X",
                        frame_count, pc, pc - C_WINDOW_BASE))
                end
                return data
            end
        )
    end)
    if ok and tap then
        tap_refs[#tap_refs+1] = tap
        append_log("C-Window tap installed")
    else
        append_log("C-Window tap FAILED - frame sample only")
    end
end

local function inspect_frame()
    local pc = current_pc()
    if not pc then return end

    if in_cwindow(pc) and LOG_CWIN_EXEC then
        record_cwin_site(pc, nil)
        append_log(string.format(
            "[frame %06d] CWIN_PC_SAMPLE  pc=0x%06X  off=0x%04X",
            frame_count, pc, pc - C_WINDOW_BASE))
    end

    if LOG_INDIRECT then
        local mnem, target = decode_indirect_branch(pc)
        if mnem and target and in_cwindow(target) then
            record_cwin_site(target, pc)
            append_log(string.format(
                "[frame %06d] INDIRECT_BRANCH  src=0x%06X  %s  ->  0x%06X  off=0x%04X",
                frame_count, pc, mnem, target, target - C_WINDOW_BASE))
        end
    end
end

local function write_summary()
    if not summary_path then return end
    local fh = io.open(summary_path, "w")
    if not fh then return end

    local count = 0
    for _ in pairs(cwin_exec_sites) do count = count + 1 end

    fh:write(string.format("frames_run=%d\n", frame_count))
    fh:write(string.format("unique_cwin_exec_sites=%d\n\n", count))
    fh:write("UNIQUE C-WINDOW EXECUTION SITES\n")
    fh:write("(sorted by address)\n")
    fh:write(string.format("%-10s %-8s %-8s %-12s %-10s\n",
        "address", "offset", "count", "first_frame", "first_src"))
    fh:write(string.rep("-", 56) .. "\n")

    local sites = {}
    for addr, info in pairs(cwin_exec_sites) do
        sites[#sites+1] = {addr=addr, info=info}
    end
    table.sort(sites, function(a, b) return a.addr < b.addr end)

    for _, entry in ipairs(sites) do
        local a = entry.addr
        local i = entry.info
        fh:write(string.format("0x%06X   0x%04X   %-8d %-12d 0x%06X\n",
            a, a - C_WINDOW_BASE, i.count, i.first_frame, i.first_src))
    end

    fh:write("\n")
    fh:write("Each address above is a C-Window location the arcade\n")
    fh:write("68000 executes from. Each needs an opcode replacement\n")
    fh:write("patch to redirect to Genesis-native code.\n")
    fh:close()
end

local function arm()
    cpu = manager.machine.devices[":maincpu"]
    if not cpu then append_log("ERROR: :maincpu not found"); return end
    prog = cpu.spaces["program"]
    if not prog then append_log("ERROR: program space not found"); return end
    tap_refs = {}
    install_cwin_tap()
    append_log(string.format("armed — watching 0x%06X-0x%06X",
        C_WINDOW_BASE, C_WINDOW_END))
end

local function reset_state()
    frame_count = 0; log_lines = 0; tap_refs = {}
    error_logged = false; done = false; cwin_exec_sites = {}
end

if not is_rastan_set(emu.romname()) then
    emu.print_info("rastanjumptrace: skipped for " .. tostring(emu.romname()))
    return
end

do
    local home = manager.machine.options.entries
        .homepath:value():match("([^;]+)")
    local d = home .. "/rastanjumptrace"
    os.execute(string.format("mkdir -p '%s'", d))
    log_path     = d .. "/rastan_cwin_exec_trace.log"
    summary_path = d .. "/rastan_cwin_exec_summary.txt"
end

append_log(string.format("==== rastanjumptrace v2 start rom=%s ====",
    tostring(emu.romname())))
emu.print_info("rastanjumptrace v2 loaded")

_G.rastanjumptrace_reset_sub = emu.add_machine_reset_notifier(function()
    reset_state(); arm(); append_log("---- reset ----")
end)

_G.rastanjumptrace_stop_sub = emu.add_machine_stop_notifier(function()
    write_summary()
    append_log("==== rastanjumptrace v2 stop ====")
end)

_G.rastanjumptrace_frame_sub = emu.add_machine_frame_notifier(function()
    if done then return end
    local ok, err = pcall(function()
        frame_count = frame_count + 1
        if not cpu or not prog then return end
        if (frame_count % FRAME_LOG_STRIDE) == 0 then
            append_log(string.format("[frame %06d] --- FRAME ---", frame_count))
        end
        inspect_frame()
        if frame_count >= MAX_FRAMES then
            done = true
            append_log(string.format("[frame %06d] MAX_FRAMES reached", frame_count))
            write_summary()
        end
    end)
    if not ok and not error_logged then
        error_logged = true
        append_log("ERROR: " .. tostring(err))
        emu.print_error("rastanjumptrace: " .. tostring(err))
    end
end)

reset_state()
arm()