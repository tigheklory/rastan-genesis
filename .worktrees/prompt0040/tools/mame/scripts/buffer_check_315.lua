-- buffer_check_315.lua
-- Injects START at frame 120 to reach arcade mode, then checks
-- whether pc080sn_fg_buffer and pc080sn_bg_buffer contain non-zero data.

local root = os.getenv("GENESISTAN_ROOT") or "."
dofile(root .. "/tools/mame/scripts/genesistrace.lua")

local frame_count = 0
local cpu = nil
local prog = nil
local log_path = nil
local checked_frames = {200, 300, 400, 500, 600, 700, 800, 1000}
local checked = {}
local start_field = nil

local function find_symbol(name)
    local sym_path = root .. "/apps/rastan/out/symbol.txt"
    local f = io.open(sym_path, "r")
    if not f then return nil end
    for line in f:lines() do
        local addr, typ, sym = line:match("^(%x+)%s+([%a])%s+(.+)$")
        if sym == name then
            f:close()
            return tonumber(addr, 16) & 0x00FFFFFF
        end
    end
    f:close()
    return nil
end

local function count_nonzero_words(base_addr, count)
    local nz = 0
    for i = 0, count - 1 do
        local val = prog:read_u16(base_addr + i * 2)
        if val ~= 0 then
            nz = nz + 1
        end
    end
    return nz
end

local function init()
    cpu = manager.machine.devices[":maincpu"]
    prog = cpu.spaces["program"]
    local trace_dir = root .. "/build/mame/home/genesistrace"
    os.execute(string.format("mkdir -p '%s'", trace_dir))
    log_path = trace_dir .. "/buffer_verify.txt"
    local f = io.open(log_path, "w")
    if f then
        f:write("buffer_check_315 started\n")
        f:close()
    end

    -- Find P1 Start ioport field for input injection
    for tag, port in pairs(manager.machine.ioport.ports) do
        for fname, field in pairs(port.fields) do
            if fname == "P1 Start" then
                start_field = field
            end
        end
    end
end

local function append_log(line)
    local f = io.open(log_path, "a")
    if f then
        f:write(line .. "\n")
        f:close()
    end
end

local bg_addr = nil
local fg_addr = nil

emu.register_frame_done(function()
    frame_count = frame_count + 1

    if frame_count == 1 then
        init()
        bg_addr = find_symbol("pc080sn_bg_buffer")
        fg_addr = find_symbol("pc080sn_fg_buffer")
        if bg_addr then
            append_log(string.format("bg_buffer_addr=0x%06X", bg_addr))
        else
            append_log("ERROR: pc080sn_bg_buffer symbol not found")
        end
        if fg_addr then
            append_log(string.format("fg_buffer_addr=0x%06X", fg_addr))
        else
            append_log("ERROR: pc080sn_fg_buffer symbol not found")
        end
    end

    -- Inject START press at frames 120-125 to trigger request_start_rastan()
    if start_field and frame_count >= 120 and frame_count <= 125 then
        start_field:set_value(1)
        if frame_count == 120 then
            append_log("frame 120: injected P1 Start")
        end
    elseif start_field and frame_count == 126 then
        start_field:set_value(0)
    end

    for _, target_frame in ipairs(checked_frames) do
        if frame_count == target_frame and not checked[target_frame] then
            checked[target_frame] = true
            if bg_addr and fg_addr then
                local bg_nz = count_nonzero_words(bg_addr, 2048)
                local fg_nz = count_nonzero_words(fg_addr, 2048)
                append_log(string.format(
                    "frame=%d bg_nonzero=%d/2048 fg_nonzero=%d/2048",
                    frame_count, bg_nz, fg_nz))
            end
        end
    end
end)
