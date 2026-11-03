-- buffer_dump_315.lua
-- Dumps the actual non-zero tile values from pc080sn_fg_buffer at key frames.

local root = os.getenv("GENESISTAN_ROOT") or "."
dofile(root .. "/tools/mame/scripts/genesistrace.lua")

local frame_count = 0
local cpu = nil
local prog = nil
local log_path = nil
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

local function init()
    cpu = manager.machine.devices[":maincpu"]
    prog = cpu.spaces["program"]
    local trace_dir = root .. "/build/mame/home/genesistrace"
    os.execute(string.format("mkdir -p '%s'", trace_dir))
    log_path = trace_dir .. "/buffer_dump.txt"
    local f = io.open(log_path, "w")
    if f then f:write("buffer_dump_315\n"); f:close() end

    for tag, port in pairs(manager.machine.ioport.ports) do
        for fname, field in pairs(port.fields) do
            if fname == "P1 Start" then start_field = field end
        end
    end
end

local function append_log(line)
    local f = io.open(log_path, "a")
    if f then f:write(line .. "\n"); f:close() end
end

local fg_addr = nil
local dumped = {}

emu.register_frame_done(function()
    frame_count = frame_count + 1

    if frame_count == 1 then
        init()
        fg_addr = find_symbol("pc080sn_fg_buffer")
        append_log(string.format("fg_buffer_addr=0x%06X", fg_addr or 0))
    end

    -- Inject START at frames 120-125
    if start_field and frame_count >= 120 and frame_count <= 125 then
        start_field:set_value(1)
    elseif start_field and frame_count == 126 then
        start_field:set_value(0)
    end

    -- Dump non-zero entries at frame 750
    if frame_count == 750 and fg_addr and not dumped[750] then
        dumped[750] = true
        append_log(string.format("--- frame %d FG buffer non-zero entries ---", frame_count))
        for row = 0, 31 do
            for col = 0, 63 do
                local offset = (row * 64 + col) * 2
                local val = prog:read_u16(fg_addr + offset)
                if val ~= 0 then
                    local tile_idx = val & 0x07FF
                    local pal = (val >> 13) & 0x3
                    local pri = (val >> 15) & 0x1
                    local vf = (val >> 12) & 0x1
                    local hf = (val >> 11) & 0x1
                    append_log(string.format(
                        "  row=%2d col=%2d val=0x%04X tile=%d pal=%d pri=%d vf=%d hf=%d",
                        row, col, val, tile_idx, pal, pri, vf, hf))
                end
            end
        end
        append_log("--- end ---")
    end
end)
