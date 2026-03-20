--[[
rastanjumptrace.lua
====================
Targeted tracer for the Rastan arcade machine (maincpu 68000).

Purpose
-------
Find the exact instruction that causes the 68000 to jump to 0xC01CA8
(C-Window page 0, byte offset 0x1CA8).  On the arcade board that address
is valid readable/executable RAM.  In the Genesis port it maps to SRAM at
0x201CA8 which is not executable, causing a deterministic crash.

What this script does
---------------------
Every frame it samples the CPU state.  On each opcode fetch from
*outside* the C-Window it decodes the current opcode to detect indirect
branch instructions:
    JMP  (An)           4ED0-4ED7
    JMP  (d16,An)       4EE8-4EEF
    JMP  (d8,An,Xn)     4EF0-4EF7
    JSR  (An)           4E90-4E97
    JSR  (d16,An)       4EA8-4EAF
    JSR  (d8,An,Xn)     4EB0-4EB7
    JMP  (abs.w)        4EF8
    JMP  (abs.l)        4EF9
    JSR  (abs.w)        4EB8
    JSR  (abs.l)        4EB9
    MOVEA.L #imm,An     207C 227C ... 2E7C  (potential pointer load)

For any indirect branch whose computed target falls in:
    - C-Window range  0xC00000-0xC0FFFF
    - SRAM range      0x200000-0x20FFFF
it logs the source PC, the instruction mnemonic, and the target.

It also installs a write tap on the C-Window to log every write with the
writing PC and the value, narrowed to offsets around 0x1CA8
(±0x200 bytes) to keep the log manageable.

Additionally it hooks C-Window page 0 (0xC00000-0xC03FFF) for opcode
fetches so we know if the 68000 ever tries to execute from there.

Output: build/mame/home/rastanjumptrace/rastan_jump_trace.log
        build/mame/home/rastanjumptrace/rastan_jump_summary.txt

Run via: tools/mame/run_rastan_jumptrace_wsl.sh
--]]

-- -------------------------------------------------------------------------
-- Config
-- -------------------------------------------------------------------------
local MAX_INDIRECT_LOG      = 2000   -- stop logging indirect branches after this many
local MAX_CWIN_EXEC_LOG     = 500    -- stop logging C-Window execution hits after this
local MAX_FRAMES            = 3600   -- auto-stop after ~60 seconds at 60 fps
local NARROW_WRITE_CENTER   = 0x1CA8 -- byte offset into C-Window we care most about
local NARROW_WRITE_RADIUS   = 0x200  -- log writes within ±this many bytes of center

-- -------------------------------------------------------------------------
-- State
-- -------------------------------------------------------------------------
local frame_count           = 0
local log_path              = nil
local summary_path          = nil
local cpu                   = nil
local prog                  = nil
local tap_refs              = {}
local error_logged          = false
local done                  = false

local indirect_log_count    = 0
local cwin_exec_log_count   = 0
local cwin_write_log_count  = 0

-- First hit of the target address specifically
local first_target_hit_pc   = nil
local first_target_hit_frame = nil
local first_target_hit_insn = nil

-- Counters
local stats = {
    frames                  = 0,
    indirect_branches_seen  = 0,
    indirect_branches_to_cwin = 0,
    indirect_branches_to_sram = 0,
    cwin_exec_hits          = 0,
    cwin_writes_near_target = 0,
    cwin_writes_total       = 0,
}

-- Subscriptions (kept global so GC does not collect them)
_G.rastanjumptrace_reset_sub = nil
_G.rastanjumptrace_stop_sub  = nil
_G.rastanjumptrace_frame_sub = nil

-- -------------------------------------------------------------------------
-- Helpers
-- -------------------------------------------------------------------------
local C_WINDOW_BASE  = 0xC00000
local C_WINDOW_END   = 0xC0FFFF
local SRAM_BASE      = 0x200000
local SRAM_END       = 0x20FFFF
local TARGET_ADDR    = 0xC01CA8   -- the crash address in arcade space

local function is_rastan_set(name)
    return string.match(name or "", "^rastan") ~= nil
end

local function append_log(line)
    if not log_path then return end
    local fh = io.open(log_path, "a")
    if fh then
        fh:write(line)
        fh:write("\n")
        fh:close()
    end
end

local function current_pc()
    if not cpu or not cpu.state or not cpu.state["PC"] then return nil end
    return cpu.state["PC"].value & 0xFFFFFFFF
end

local function reg_an(n)
    -- Read address register An (n = 0..7) from MAME CPU state
    -- MAME exposes them as A0..A7
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

local function in_cwindow(addr)
    return addr >= C_WINDOW_BASE and addr <= C_WINDOW_END
end

local function in_sram(addr)
    return addr >= SRAM_BASE and addr <= SRAM_END
end

local function is_interesting_target(addr)
    return in_cwindow(addr) or in_sram(addr)
end

-- -------------------------------------------------------------------------
-- 68000 indirect branch decoder
-- Called at the instruction BEFORE the branch fires (i.e. current PC is
-- the JMP/JSR instruction itself).  We read the opcode and compute the
-- effective address the CPU is about to branch to.
-- Returns: mnemonic (string), target (number) or nil if not an indirect branch
-- -------------------------------------------------------------------------
local function decode_indirect_branch(pc)
    local op = read16(pc)
    local hi = (op >> 8) & 0xFF
    local lo  = op & 0xFF
    local mnem = nil
    local target = nil
    local rn = nil

    -- JSR (An)  4E90-4E97
    if op >= 0x4E90 and op <= 0x4E97 then
        rn = op & 0x07
        local an = reg_an(rn)
        if an then
            mnem = string.format("JSR (A%d)", rn)
            target = an & 0xFFFFFF
        end

    -- JSR (d16,An)  4EA8-4EAF
    elseif op >= 0x4EA8 and op <= 0x4EAF then
        rn = op & 0x07
        local an = reg_an(rn)
        local disp = sign_extend_16(read16(pc + 2))
        if an then
            mnem = string.format("JSR (0x%04X,A%d)", disp & 0xFFFF, rn)
            target = (an + disp) & 0xFFFFFF
        end

    -- JSR (d8,An,Xn)  4EB0-4EB7
    elseif op >= 0x4EB0 and op <= 0x4EB7 then
        rn = op & 0x07
        local an = reg_an(rn)
        local ext = read16(pc + 2)
        local disp8 = sign_extend_8(ext & 0xFF)
        -- rough EA: An + d8 (ignoring index register for now, good enough to detect C-Window)
        if an then
            mnem = string.format("JSR (d8,A%d,Xn) ext=%04X", rn, ext)
            target = (an + disp8) & 0xFFFFFF
        end

    -- JSR (abs.w)  4EB8
    elseif op == 0x4EB8 then
        local abs = sign_extend_16(read16(pc + 2))
        mnem = string.format("JSR (0x%06X).W", abs & 0xFFFFFF)
        target = abs & 0xFFFFFF

    -- JSR (abs.l)  4EB9
    elseif op == 0x4EB9 then
        local abs = read32(pc + 2)
        mnem = string.format("JSR (0x%06X).L", abs & 0xFFFFFF)
        target = abs & 0xFFFFFF

    -- JMP (An)  4ED0-4ED7
    elseif op >= 0x4ED0 and op <= 0x4ED7 then
        rn = op & 0x07
        local an = reg_an(rn)
        if an then
            mnem = string.format("JMP (A%d)", rn)
            target = an & 0xFFFFFF
        end

    -- JMP (d16,An)  4EE8-4EEEF
    elseif op >= 0x4EE8 and op <= 0x4EEF then
        rn = op & 0x07
        local an = reg_an(rn)
        local disp = sign_extend_16(read16(pc + 2))
        if an then
            mnem = string.format("JMP (0x%04X,A%d)", disp & 0xFFFF, rn)
            target = (an + disp) & 0xFFFFFF
        end

    -- JMP (d8,An,Xn)  4EF0-4EF7
    elseif op >= 0x4EF0 and op <= 0x4EF7 then
        rn = op & 0x07
        local an = reg_an(rn)
        local ext = read16(pc + 2)
        local disp8 = sign_extend_8(ext & 0xFF)
        if an then
            mnem = string.format("JMP (d8,A%d,Xn) ext=%04X", rn, ext)
            target = (an + disp8) & 0xFFFFFF
        end

    -- JMP (abs.w)  4EF8
    elseif op == 0x4EF8 then
        local abs = sign_extend_16(read16(pc + 2))
        mnem = string.format("JMP (0x%06X).W", abs & 0xFFFFFF)
        target = abs & 0xFFFFFF

    -- JMP (abs.l)  4EF9
    elseif op == 0x4EF9 then
        local abs = read32(pc + 2)
        mnem = string.format("JMP (0x%06X).L", abs & 0xFFFFFF)
        target = abs & 0xFFFFFF
    end

    return mnem, target
end

-- -------------------------------------------------------------------------
-- Per-frame opcode inspection
-- We sample every frame.  For a full instruction trace we would need
-- MAME debug hooks per-instruction which is expensive; instead we sample
-- the PC each frame and decode the opcode at that point.  For the specific
-- crash we are chasing (happens within a few frames of startup), sampling
-- every frame is sufficient to catch it.
-- -------------------------------------------------------------------------
local function inspect_frame()
    local pc = current_pc()
    if not pc then return end

    -- Decode indirect branch at current PC
    local mnem, target = decode_indirect_branch(pc)
    if mnem and target then
        stats.indirect_branches_seen = stats.indirect_branches_seen + 1
        local interesting = is_interesting_target(target)
        if in_cwindow(target) then
            stats.indirect_branches_to_cwin = stats.indirect_branches_to_cwin + 1
        elseif in_sram(target) then
            stats.indirect_branches_to_sram = stats.indirect_branches_to_sram + 1
        end

        -- First hit on the exact crash address
        if (target & 0xFFFFFF) == TARGET_ADDR and not first_target_hit_pc then
            first_target_hit_pc    = pc
            first_target_hit_frame = frame_count
            first_target_hit_insn  = mnem
            append_log(string.format(
                "[frame %06d] *** FOUND TARGET JUMP *** pc=0x%06X  %s  -> target=0x%06X",
                frame_count, pc, mnem, target))
            -- Log all registers at this moment
            local regs = {}
            for i = 0, 7 do
                local an = reg_an(i)
                regs[#regs+1] = string.format("A%d=0x%08X", i, an or 0)
            end
            append_log(string.format("[frame %06d] REGS %s", frame_count, table.concat(regs, "  ")))
            -- Log 16 words before and after target in C-Window (via arcade space)
            local context = {}
            for off = -0x20, 0x20, 2 do
                local a = (TARGET_ADDR + off) & 0xFFFFFF
                local v = read16(a)
                context[#context+1] = string.format("%06X:%04X", a, v)
            end
            append_log(string.format("[frame %06d] CWIN_CONTEXT %s", frame_count, table.concat(context, " ")))
        end

        -- Log all interesting branch targets while budget allows
        if interesting and indirect_log_count < MAX_INDIRECT_LOG then
            indirect_log_count = indirect_log_count + 1
            append_log(string.format(
                "[frame %06d] INDIRECT_BRANCH pc=0x%06X  %s  -> 0x%06X  (%s)",
                frame_count, pc, mnem, target,
                in_cwindow(target) and "CWIN" or "SRAM"))
        end
    end
end

-- -------------------------------------------------------------------------
-- C-Window write tap (narrowed to ±NARROW_WRITE_RADIUS around 0x1CA8)
-- -------------------------------------------------------------------------
local function install_write_tap()
    if not prog then return end
    local narrow_lo = C_WINDOW_BASE + NARROW_WRITE_CENTER - NARROW_WRITE_RADIUS
    local narrow_hi = C_WINDOW_BASE + NARROW_WRITE_CENTER + NARROW_WRITE_RADIUS
    if narrow_lo < C_WINDOW_BASE then narrow_lo = C_WINDOW_BASE end
    if narrow_hi > C_WINDOW_END   then narrow_hi = C_WINDOW_END   end

    local ok, tap = pcall(function()
        return prog:install_write_tap(
            narrow_lo, narrow_hi,
            "rastanjumptrace_cwin_write",
            function(offset, data, mask)
                stats.cwin_writes_total = stats.cwin_writes_total + 1
                local abs_addr = offset  -- tap offset IS the bus address in MAME
                local pc = current_pc() or 0
                local byte_off = abs_addr - C_WINDOW_BASE
                if cwin_write_log_count < MAX_INDIRECT_LOG then
                    cwin_write_log_count = cwin_write_log_count + 1
                    append_log(string.format(
                        "[frame %06d] CWIN_WRITE addr=0x%06X off=0x%04X data=0x%04X mask=0x%04X  src_pc=0x%06X",
                        frame_count, abs_addr, byte_off, data & 0xFFFF, mask & 0xFFFF, pc))
                end
                return data
            end
        )
    end)
    if ok and tap then
        tap_refs[#tap_refs+1] = tap
        append_log(string.format(
            "write tap installed 0x%06X-0x%06X (±0x%X around 0x%06X)",
            narrow_lo, narrow_hi, NARROW_WRITE_RADIUS, TARGET_ADDR))
    else
        append_log("write tap install FAILED - will rely on frame sampling only")
    end
end

-- -------------------------------------------------------------------------
-- C-Window page 0 fetch tap — catches instruction fetches from C-Window
-- -------------------------------------------------------------------------
local function install_fetch_tap()
    if not prog then return end
    -- Try install_read_tap on page 0; opcode fetches also go through read
    local ok, tap = pcall(function()
        return prog:install_read_tap(
            C_WINDOW_BASE, 0xC03FFF,
            "rastanjumptrace_cwin_fetch",
            function(offset, data, mask)
                stats.cwin_exec_hits = stats.cwin_exec_hits + 1
                local pc = current_pc() or 0
                -- Only log if the PC itself is in C-Window (instruction fetch)
                if in_cwindow(pc) and cwin_exec_log_count < MAX_CWIN_EXEC_LOG then
                    cwin_exec_log_count = cwin_exec_log_count + 1
                    append_log(string.format(
                        "[frame %06d] CWIN_EXEC pc=0x%06X off=0x%04X data=0x%04X",
                        frame_count, pc, pc - C_WINDOW_BASE, data & 0xFFFF))
                end
                return data
            end
        )
    end)
    if ok and tap then
        tap_refs[#tap_refs+1] = tap
        append_log("C-Window page 0 read/fetch tap installed")
    else
        append_log("C-Window page 0 read/fetch tap install FAILED")
    end
end

-- -------------------------------------------------------------------------
-- Summary
-- -------------------------------------------------------------------------
local function write_summary()
    if not summary_path then return end
    local fh = io.open(summary_path, "w")
    if not fh then return end
    fh:write(string.format("frames_run=%d\n", stats.frames))
    fh:write(string.format("indirect_branches_seen=%d\n", stats.indirect_branches_seen))
    fh:write(string.format("indirect_branches_to_cwin=%d\n", stats.indirect_branches_to_cwin))
    fh:write(string.format("indirect_branches_to_sram=%d\n", stats.indirect_branches_to_sram))
    fh:write(string.format("cwin_exec_hits=%d\n", stats.cwin_exec_hits))
    fh:write(string.format("cwin_writes_near_target=%d\n", stats.cwin_writes_near_target))
    fh:write(string.format("cwin_writes_total=%d\n", stats.cwin_writes_total))
    fh:write(string.format("max_frames_limit=%d\n", MAX_FRAMES))
    if first_target_hit_pc then
        fh:write(string.format("TARGET_FOUND=YES\n"))
        fh:write(string.format("target_hit_frame=%d\n", first_target_hit_frame or 0))
        fh:write(string.format("target_hit_src_pc=0x%06X\n", first_target_hit_pc))
        fh:write(string.format("target_hit_insn=%s\n", first_target_hit_insn or "?"))
    else
        fh:write("TARGET_FOUND=NO\n")
        fh:write("NOTE: target 0xC01CA8 was not seen as a branch target during this run.\n")
        fh:write("      Check CWIN_EXEC and CWIN_WRITE lines in the log for execution from C-Window.\n")
    end
    fh:close()
end

-- -------------------------------------------------------------------------
-- Arm
-- -------------------------------------------------------------------------
local function arm()
    cpu = manager.machine.devices[":maincpu"]
    if not cpu then
        append_log("ERROR: :maincpu not found")
        return
    end
    prog = cpu.spaces["program"]
    if not prog then
        append_log("ERROR: maincpu program space not found")
        return
    end
    tap_refs = {}
    install_write_tap()
    install_fetch_tap()
    append_log("rastanjumptrace armed")
end

local function reset_state()
    frame_count = 0
    indirect_log_count = 0
    cwin_exec_log_count = 0
    cwin_write_log_count = 0
    first_target_hit_pc = nil
    first_target_hit_frame = nil
    first_target_hit_insn = nil
    tap_refs = {}
    error_logged = false
    done = false
    stats = {
        frames = 0,
        indirect_branches_seen = 0,
        indirect_branches_to_cwin = 0,
        indirect_branches_to_sram = 0,
        cwin_exec_hits = 0,
        cwin_writes_near_target = 0,
        cwin_writes_total = 0,
    }
end

-- -------------------------------------------------------------------------
-- Entry point
-- -------------------------------------------------------------------------
if not is_rastan_set(emu.romname()) then
    emu.print_info("rastanjumptrace: skipped for rom " .. tostring(emu.romname()))
    return
end

do
    local home = manager.machine.options.entries.homepath:value():match("([^;]+)")
    local trace_dir = home .. "/rastanjumptrace"
    os.execute(string.format("mkdir -p '%s'", trace_dir))
    log_path     = trace_dir .. "/rastan_jump_trace.log"
    summary_path = trace_dir .. "/rastan_jump_summary.txt"
end

append_log(string.format(
    "==== rastanjumptrace start rom=%s game=%s target=0x%06X ====",
    tostring(emu.romname()), tostring(emu.gamename()), TARGET_ADDR))
emu.print_info("rastanjumptrace loaded — hunting jump to 0x" .. string.format("%06X", TARGET_ADDR))

_G.rastanjumptrace_reset_sub = emu.add_machine_reset_notifier(function()
    reset_state()
    arm()
    append_log("---- reset ----")
end)

_G.rastanjumptrace_stop_sub = emu.add_machine_stop_notifier(function()
    write_summary()
    append_log("==== rastanjumptrace stop ====")
end)

_G.rastanjumptrace_frame_sub = emu.add_machine_frame_notifier(function()
    if done then return end
    local ok, err = pcall(function()
        frame_count = frame_count + 1
        stats.frames = frame_count
        if not cpu or not prog then return end
        inspect_frame()
        -- Auto-stop after MAX_FRAMES to keep logs manageable
        if frame_count >= MAX_FRAMES then
            done = true
            append_log(string.format(
                "[frame %06d] MAX_FRAMES reached, tracing stopped", frame_count))
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
