-- Original-arcade renderer-call evidence for the offline PC090OJ compositor.
-- Reuses the established selector/input method from arcade_enemy_sweep.lua.
-- The selector and keep-alive writes affect game progression only; actor,
-- compositor, SAT, and palette state are observed, never synthesized.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"])
local program = assert(cpu.spaces["program"])
local main_region = assert(machine.memory.regions[":maincpu"])
local samples = assert(io.open(assert(os.getenv("ACTOR_RENDER_OUT")), "w"))
local selector = assert(tonumber(assert(os.getenv("ACTOR_RENDER_SELECTOR"))))
local forced_round = tonumber(os.getenv("ACTOR_RENDER_ROUND") or "0")
local max_frames = tonumber(os.getenv("ACTOR_RENDER_FRAMES") or "5200")
local snapshot_frame = tonumber(os.getenv("ACTOR_RENDER_SNAPSHOT_FRAME") or "0")
local frame, closed = 0, false
local A5 = 0x10c000
local OBJ = 0xd00000

local fields = {}
for _, port in pairs(machine.ioport.ports) do
    for name, field in pairs(port.fields) do fields[name] = field end
end

local function set_input(name, active)
    if fields[name] then fields[name]:set_value(active and 1 or 0) end
end

local function r8(address)
    local ok, value = pcall(function() return program:read_u8(address) end)
    return ok and (value & 0xff) or 0
end

local function r16(address)
    local ok, value = pcall(function() return program:read_u16(address) end)
    return ok and (value & 0xffff) or 0
end

local function w8(address, value)
    pcall(function() program:write_u8(address, value & 0xff) end)
end

samples:write("frame,round,progression_13e,renderer_mode,block,index,actor_address,raw_00_3f,anim_01,facing_02,state_03,record_type_06,subframe_0b,x_16,y_adjust_18,y_1a,base_1e,mirror_20,attr_27,compositor_38,family_3e,variant_parallel_752,program_pointer,sat_records,palette_words\n")

local blocks = {
    {"actor_2c8", 0x02c8, 9}, {"actor_508", 0x0508, 2},
    {"actor_5c8", 0x05c8, 6}, {"actor_748", 0x0748, 11},
    {"actor_8c8", 0x08c8, 5},
}

local function owned_range(name, index, boss_mode)
    if boss_mode then
        if name == "actor_5c8" then return 140 + math.min(index, 3) * 10 + math.max(index - 3, 0) * 20, (index < 3) and 10 or 20 end
        if name == "actor_748" then return 46 + index * 6, 6 end
        if name == "actor_8c8" then return 96 + index * 4, 4 end
    else
        if name == "actor_2c8" then return 140 + index * 10, (index == 8) and 19 or 10 end
        if name == "actor_508" then return 57 + index * 13, 13 end
        if name == "actor_5c8" then return 96 + index * 4, 4 end
        if name == "actor_748" then return 46 + index, 1 end
    end
    return -1, 0
end

local compositor_tables = {[0]=0x3d09e, [1]=0x4771c, [2]=0x3f0ce, [3]=0x40004, [4]=0x4002c}
local seen = {}
local function hex_bytes(address, count)
    local out = {}
    for i = 0, count - 1 do out[#out + 1] = string.format("%02X", r8(address + i)) end
    return table.concat(out)
end

local function sample_actors()
    local round = r8(A5 + 0x118)
    local renderer_mode = r16(A5 + 0x2a2)
    for _, block in ipairs(blocks) do
        for index = 0, block[3] - 1 do
            local actor = A5 + block[2] + index * 0x40
            local base = r16(actor + 0x1e)
            if r8(actor) ~= 0 and base ~= 0 then
                local compositor = r8(actor + 0x38)
                local table_address = compositor_tables[compositor]
                local pointer = table_address and (table_address + r16(table_address + r8(actor + 1) * 2)) or 0
                local start, count = owned_range(block[1], index, renderer_mode == 2)
                local sat = {}
                if start >= 0 then
                    for record = start, start + count - 1 do
                        local p = OBJ + record * 8
                        sat[#sat + 1] = string.format("%d:%04X:%04X:%04X:%04X", record, r16(p), r16(p+2), r16(p+4), r16(p+6))
                    end
                end
                local palette = {}
                local line = r8(actor + 0x27) & 0x0f
                if start >= 0 then line = r16(OBJ + start * 8) & 0x0f end
                -- PC090OJ control supplies colour-bank 0x30; SAT word 0 supplies
                -- the low nibble. Read the effective hardware bank 0x30..0x3f.
                local effective_bank = 0x30 | line
                for word = 0, 15 do palette[#palette + 1] = string.format("%04X", r16(0x200000 + effective_bank * 32 + word * 2)) end
                local key = table.concat({block[1], index, hex_bytes(actor,64), table.concat(sat,"|")}, ":")
                if not seen[key] then
                    seen[key] = true
                    samples:write(table.concat({
                        tostring(frame), tostring(round), string.format("%04X",r16(A5+0x13e)), string.format("%04X",renderer_mode),
                        block[1], tostring(index), string.format("%06X",actor), hex_bytes(actor,64),
                        string.format("%02X",r8(actor+1)), string.format("%02X",r8(actor+2)), string.format("%02X",r8(actor+3)),
                        string.format("%02X",r8(actor+6)), string.format("%02X",r8(actor+0x0b)), string.format("%04X",r16(actor+0x16)),
                        string.format("%04X",r16(actor+0x18)), string.format("%04X",r16(actor+0x1a)), string.format("%04X",base),
                        string.format("%02X",r8(actor+0x20)), string.format("%02X",r8(actor+0x27)), string.format("%02X",compositor),
                        string.format("%02X",r8(actor+0x3e)), string.format("%02X",r8(actor+0x752)), string.format("%06X",pointer),
                        table.concat(sat,"|"), table.concat(palette,"|")
                    }, ","), "\n")
                end
            end
        end
    end
    samples:flush()
end

local function close()
    if closed then return end
    closed = true
    samples:close()
end

emu.register_frame_done(function()
    frame = frame + 1
    if frame <= 300 then
        pcall(function() main_region:write_u8(0x05ff9f, selector) end)
        pcall(function() program:write_u8(0x05ff9f, selector) end)
        if forced_round > 0 then w8(A5 + 0x0118, forced_round) end
    end
    set_input("Coin 1", frame >= 120 and frame <= 132)
    set_input("1 Player Start", frame >= 175 and frame <= 187)
    set_input("P1 Right", frame >= 480)
    set_input("P1 Button 1", frame >= 600 and (frame % 113) < 12)
    set_input("P1 Button 2", frame >= 600 and (frame % 157) < 14)
    if frame >= 200 then
        if forced_round > 0 then w8(A5 + 0x0118, forced_round) end
        w8(A5 + 0x0101, 3)
        w8(A5 + 0x013a, 0x30)
        if frame % 2 == 0 and (snapshot_frame == 0 or frame == snapshot_frame) then sample_actors() end
    end
    if frame >= max_frames then close(); machine:exit() end
end)

_G.arcade_actor_renderer_verify_stop = emu.add_machine_stop_notifier(close)
