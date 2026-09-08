--[[
genesis_crash_capture.lua
=========================
GENESIS NTSC target crash-evidence capture.

PURPOSE
-------
The rastan-direct ROM installs a screenshot-first crash handler
(apps/rastan-direct/src/crash_handler.s) that, on ANY 68000 exception,
snapshots the full register file, stacked PC/SR, and fault address into a
fixed WRAM record at 0x00FF6800 and sets CRASH_ACTIVE_FLAG.

The on-screen crash report omits the one thing needed to root-cause a WILD
CONTROL-FLOW transfer (PC wandering into a data table): the pre-crash STACK,
i.e. the JSR/BSR return-address trail of the call chain that mis-jumped.

This script runs against the GENESIS target during live play. It is
READS-ONLY inside a frame notifier (no memory taps), so it is safe under the
MAME 68000 DRC and imposes ~zero overhead -- the user can play at full speed
to the scene that crashes (e.g. stage-1 cave segment 5 on the display-off
"_do" build). When CRASH_ACTIVE_FLAG goes non-zero it dumps:

  * the full crash record (vector, SR, PC, fault addr, all D/A regs)
  * the current scene/segment/tileset (to confirm WHERE it crashed)
  * a raw dump of the stack from the exception frame upward, with every
    longword that looks like a valid return address annotated with the
    caller instruction preceding it (0x4EB9 jsr.l / 0x4EBA jsr(d16,pc) /
    0x61xx bsr) -- this reconstructs the call chain.

OUTPUT
------
build/mame/home/genesis_crash_capture/
  genesis_crash_capture.log

RUN
---
tools/mame/run_genesis_crash_capture_wsl.sh <path-to-_do-rom>
then play to the crashing scene. The dump is written the instant the crash
handler fires; MAME can be closed afterwards.
--]]

local CRASH_BASE          = 0x00FF6800
local CRASH_ACTIVE_FLAG   = 0x00FF6800   -- byte
local CRASH_EXCEPTION_TYPE = 0x00FF6802  -- word (vector number)
local CRASH_STACKED_SR    = 0x00FF6804   -- word
local CRASH_STACKED_PC    = 0x00FF6806   -- long
local CRASH_FRAME_SP      = 0x00FF680C   -- long
local CRASH_USP           = 0x00FF6810   -- long
local CRASH_D0            = 0x00FF6814   -- 15 longs: D0..D7, A0..A6
local CRASH_FAULT_ADDR    = 0x00FF6850   -- long
local CRASH_ACCESS_WORD   = 0x00FF6854   -- word
local CRASH_INSTR_REG     = 0x00FF6856   -- word

-- Game-flow state (same addresses genesistrace.lua reads).
local SCENE_ID_ADDR       = 0x00FF707C   -- byte
local SEG_ADDR            = 0x00FF013E   -- word
local PAGE_ADDR           = 0x00FF10C6   -- word
local TILESET_ID_ADDR     = 0x00FF707D   -- byte

-- Genesis-PC classification ranges (from address_map.json / crash_handler.s).
local MAP_ARCADE_START    = 0x00117E
local MAP_ARCADE_END      = 0x0600F4
local MAP_ROM_END         = 0x184A34

local STACK_LONGS         = 64           -- how far above the frame SP to walk

local cpu, prog
local log_path = nil
local dumped   = false
local frame_count = 0

local function homedir()
    local ok, home = pcall(function ()
        return manager.machine.options.entries.homepath:value():match("([^;]+)")
    end)
    if ok and home then return home end
    return "."
end

local function open_log()
    local dir = homedir() .. "/genesis_crash_capture"
    os.execute('mkdir -p "' .. dir .. '" 2>/dev/null')
    log_path = dir .. "/genesis_crash_capture.log"
    -- truncate so each run starts with a clean log
    local f = io.open(log_path, "w")
    if f then f:close() end
end

local function logln(s)
    if not log_path then open_log() end
    local f = io.open(log_path, "a")
    if f then f:write(s .. "\n"); f:close() end
    emu.print_info(s)
end

local function ru8(a)  return prog:read_u8(a)  & 0xFF end
local function ru16(a) return prog:read_u16(a) & 0xFFFF end
local function ru32(a) return prog:read_u32(a) & 0xFFFFFFFF end

local function is_code_addr(a)
    a = a & 0xFFFFFF
    if (a & 1) ~= 0 then return false end          -- code is word-aligned
    if a >= MAP_ARCADE_START and a < MAP_ROM_END then return true end
    return false
end

-- If longword R is a return address, the instruction just before it is the
-- call. Return a description of that caller instruction, or nil.
local function caller_desc(ret)
    ret = ret & 0xFFFFFF
    -- jsr.l abs (0x4EB9) : 6 bytes -> ret-6 holds 0x4EB9, ret-4..ret-1 = target
    if ru16(ret - 6) == 0x4EB9 then
        return string.format("jsr 0x%06X", ru32(ret - 4) & 0xFFFFFF)
    end
    -- jsr (d16,pc) (0x4EBA) : 4 bytes
    if ru16(ret - 4) == 0x4EBA then
        return string.format("jsr (%d,pc)", ru16(ret - 2))
    end
    -- jsr (An)/(d16,An) forms 0x4E90..0x4EAF : 2 or 4 bytes; check 2-byte reg form
    local w2 = ru16(ret - 2)
    if w2 >= 0x4E90 and w2 <= 0x4E97 then
        return string.format("jsr (a%d)", w2 & 7)
    end
    -- bsr.w (0x6100) : 4 bytes
    if ru16(ret - 4) == 0x6100 then
        return string.format("bsr.w -> 0x%06X", (ret - 2 + ru16(ret - 2)) & 0xFFFFFF)
    end
    -- bsr.b (0x61xx, xx!=00) : 2 bytes
    local wb = ru16(ret - 2)
    if (wb & 0xFF00) == 0x6100 and (wb & 0x00FF) ~= 0 then
        local disp = wb & 0xFF
        if disp >= 0x80 then disp = disp - 0x100 end
        return string.format("bsr.b -> 0x%06X", (ret + disp) & 0xFFFFFF)
    end
    return nil
end

local function dump_crash()
    logln("")
    logln("================ GENESIS CRASH CAPTURE ================")
    logln(string.format("frame=%d  rom=%s", frame_count, tostring(emu.romname())))
    local vec = ru16(CRASH_EXCEPTION_TYPE)
    logln(string.format("vector=%d  stacked_SR=%04X  stacked_PC=%06X",
        vec, ru16(CRASH_STACKED_SR), ru32(CRASH_STACKED_PC) & 0xFFFFFF))
    logln(string.format("fault_addr=%08X  access_word=%04X  instr_reg=%04X",
        ru32(CRASH_FAULT_ADDR), ru16(CRASH_ACCESS_WORD), ru16(CRASH_INSTR_REG)))
    local frame_sp = ru32(CRASH_FRAME_SP)
    logln(string.format("frame_SP=%08X  USP=%08X", frame_sp, ru32(CRASH_USP)))

    -- registers
    local names = {"D0","D1","D2","D3","D4","D5","D6","D7",
                   "A0","A1","A2","A3","A4","A5","A6"}
    for i = 0, 14 do
        local v = ru32(CRASH_D0 + i * 4)
        logln(string.format("  %s = %08X", names[i + 1], v))
    end

    -- scene / segment context
    logln(string.format("scene_id=%02X  seg=%04X  page=%04X  tileset_id=%02X",
        ru8(SCENE_ID_ADDR), ru16(SEG_ADDR), ru16(PAGE_ADDR), ru8(TILESET_ID_ADDR)))

    -- stack trail: from the exception frame upward
    logln(string.format("--- stack from frame_SP=%08X upward (%d longs) ---",
        frame_sp, STACK_LONGS))
    for i = 0, STACK_LONGS - 1 do
        local a = (frame_sp + i * 4) & 0xFFFFFF
        local v = ru32(a)
        local note = ""
        if is_code_addr(v) then
            local cd = caller_desc(v)
            if cd then
                note = string.format("   <- RET after [%s]", cd)
            else
                note = "   (code-range addr)"
            end
        end
        logln(string.format("  +%03X  %08X : %08X%s", i * 4, a, v, note))
    end
    logln("================ END CRASH CAPTURE ====================")
end

local function on_frame()
    frame_count = frame_count + 1
    if dumped then return end
    if not cpu or not prog then return end
    local ok, active = pcall(ru8, CRASH_ACTIVE_FLAG)
    if ok and active ~= 0 then
        dumped = true
        local ok2, err = pcall(dump_crash)
        if not ok2 then emu.print_error("crash_capture dump error: " .. tostring(err)) end
    end
end

local function arm()
    cpu = manager.machine.devices[":maincpu"]
    if not cpu then emu.print_error("crash_capture: maincpu not found"); return end
    prog = cpu.spaces["program"]
    if not prog then emu.print_error("crash_capture: program space not found"); return end
    open_log()
    logln(string.format("==== genesis_crash_capture armed rom=%s machine=%s ====",
        tostring(emu.romname()), tostring(manager.machine.system.name)))
    logln("Play to the crashing scene; the dump is written the instant the crash handler fires.")
end

emu.print_info("genesis_crash_capture script loaded")
_G.gcc_reset_sub = emu.add_machine_reset_notifier(function () arm() end)
_G.gcc_frame_sub = emu.add_machine_frame_notifier(function ()
    local ok, err = pcall(on_frame)
    if not ok then emu.print_error("genesis_crash_capture: " .. tostring(err)) end
end)
-- If the machine is already running when the script loads, arm now.
if manager and manager.machine and manager.machine.devices[":maincpu"] then arm() end
