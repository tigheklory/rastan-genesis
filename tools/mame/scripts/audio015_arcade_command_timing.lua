-- AUDIO-015 ORIGINAL ARCADE sound-command timing evidence.
-- Reuses the deterministic coin/start/right route and stock invincibility cheat
-- from arcade_rope_attach_reference_benchmark.lua.  This observes the real
-- PC060HA command stream relative to the retained gameplay state; it does not
-- inject commands or alter game state.

local machine = manager.machine
local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing maincpu program space")
local audiocpu = assert(machine.devices[":audiocpu"], "missing :audiocpu")
local audio_program = assert(audiocpu.spaces["program"], "missing audiocpu program space")
local trace_dir = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")
local max_frames = tonumber(os.getenv("AUDIO015_ARCADE_MAX_FRAMES") or "1800")
local coin_frame = tonumber(os.getenv("AUDIO015_ARCADE_COIN_FRAME") or "600")
local start_press_frame = tonumber(os.getenv("AUDIO015_ARCADE_START_FRAME") or "655")
local A5 = 0x10c000

local cheat_api = assert(emu.plugin and emu.plugin.cheat,
  "MAME cheat plugin unavailable; launch with -cheat")
local invincibility = nil
for index, description in pairs(cheat_api.list()) do
  if description == "Invincibility" then
    invincibility = assert(cheat_api.get(index), "Invincibility cheat unavailable")
    invincibility.set_enabled(true)
    break
  end
end
assert(invincibility, "stock rastan Invincibility cheat not found")

local fields = {}
for _, port in pairs(machine.ioport.ports) do
  for name, field in pairs(port.fields) do fields[name] = field end
end
assert(fields["Coin 1"], "missing Coin 1 input")
assert(fields["1 Player Start"], "missing 1 Player Start input")
assert(fields["P1 Right"], "missing P1 Right input")
local function set_input(name, active)
  fields[name]:set_value(active and 1 or 0)
end
local function r8(address) return program:read_u8(address) & 0xff end
local function r16(address) return program:read_u16(address) & 0xffff end
local function pc() return cpu.state["PC"].value & 0xffffff end
local function audio_pc() return audiocpu.state["PC"].value & 0xffff end
local function ar8(address) return audio_program:read_u8(address) & 0xff end

local frame = 0
local appearance_frame = nil
local nibble = nil
local commands = {}
local taps = {}
local ring_snapshot = {}
for address = 0x8e80, 0x8ea1 do ring_snapshot[address] = ar8(address) end
for address = 0x8f00, 0x8f11 do ring_snapshot[address] = ar8(address) end

local function record_command(command, source, source_pc)
  commands[#commands + 1] = {
    frame = frame,
    command = command,
    pc = source_pc,
    source = source,
    state0 = r16(A5 + 0x0000),
    state2 = r16(A5 + 0x0002),
    state4 = r16(A5 + 0x0004),
    sound_enable = r16(A5 + 0x0034),
    player_record = r16(A5 + 0x013e),
    player_state = r16(A5 + 0x10e8),
    player_x = r16(A5 + 0x10be),
    controller = r16(A5 + 0x13aa),
    transition = r16(A5 + 0x1394),
  }
end

-- Retain the 68000 hardware-port observation for early, pre-DRC writes.
taps[#taps + 1] = program:install_write_tap(0x003e0002, 0x003e0003,
  "audio015_arcade_pc060ha_commands", function(address, data, _)
    local value = data & 0x0f
    if nibble == nil then
      nibble = {frame = frame, value = value, pc = pc()}
    else
      local command = nibble.value | (value << 4)
      local saved_frame = frame
      frame = nibble.frame
      record_command(command, "68000_port", nibble.pc)
      frame = saved_frame
      nibble = nil
    end
    return data
  end)

-- The authoritative post-PC060HA boundary.  The NMI receiver writes every
-- external command into the primary Z80 ring at 0x8F02..0x8F11.  Internal
-- sequence/control republishing uses the same ring and is deliberately
-- distinguished by the writer PC.
taps[#taps + 1] = audio_program:install_write_tap(0x8f02, 0x8f11,
  "audio015_arcade_z80_primary_ring", function(address, data, _)
    local writer = audio_pc()
    record_command(data & 0xff,
      (writer >= 0x0066 and writer < 0x00c0) and "external_nmi" or "internal_z80",
      writer)
    return data
  end)

local function write_result()
  local out = assert(io.open(trace_dir .. "/arcade_command_timing.tsv", "w"))
  out:write("platform\tORIGINAL ARCADE\n")
  out:write(string.format("frames\t%d\n", frame))
  out:write(string.format("appearance_frame\t%s\n", appearance_frame or "NONE"))
  out:write(string.format("invincibility\t%s\n",
    invincibility.get_enabled() and "YES" or "NO"))
  out:write("frame\tcommand\tsource\tsource_pc\tstate0\tstate2\tstate4\tsound_enable\tplayer_record\tplayer_state\tplayer_x\tcontroller_13aa\ttransition_1394\n")
  for _, event in ipairs(commands) do
    out:write(string.format("%d\t%02X\t%s\t%06X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\t%04X\n",
      event.frame, event.command, event.source, event.pc, event.state0, event.state2,
      event.state4, event.sound_enable, event.player_record,
      event.player_state, event.player_x, event.controller, event.transition))
  end
  out:close()
  machine:exit()
end

emu.register_frame_done(function()
  frame = frame + 1
  set_input("Coin 1", frame >= coin_frame and frame <= coin_frame + 12)
  set_input("1 Player Start", frame >= start_press_frame and frame <= start_press_frame + 12)

  local appeared = r16(A5 + 0x0000) == 2 and
                   r16(A5 + 0x0002) == 3 and
                   r16(A5 + 0x0004) == 0 and
                   r8(A5 + 0x3865) == 1 and
                   r16(A5 + 0x10be) == 0x0020 and
                   r16(A5 + 0x10e8) >= 1 and r16(A5 + 0x10e8) <= 3
  if appearance_frame == nil and appeared then appearance_frame = frame end
  set_input("P1 Right", appearance_frame ~= nil)

  -- MAME's DRC can bypass Lua memory taps after warm-up.  Polling the ring
  -- storage once per frame provides durable corroboration: consumed slots
  -- retain their last byte, so a command remains observable after head/tail
  -- have already advanced within the frame.
  for address = 0x8f02, 0x8f11 do
    local value = ar8(address)
    if value ~= ring_snapshot[address] then
      record_command(value, string.format("primary_ring_poll_%04X", address), audio_pc())
      ring_snapshot[address] = value
    end
  end
  for address = 0x8e82, 0x8ea1 do
    local value = ar8(address)
    if value ~= ring_snapshot[address] then
      record_command(value, string.format("secondary_ring_poll_%04X", address), audio_pc())
      ring_snapshot[address] = value
    end
  end
  ring_snapshot[0x8f00] = ar8(0x8f00)
  ring_snapshot[0x8f01] = ar8(0x8f01)
  ring_snapshot[0x8e80] = ar8(0x8e80)
  ring_snapshot[0x8e81] = ar8(0x8e81)

  if frame >= max_frames then write_result() end
end)
