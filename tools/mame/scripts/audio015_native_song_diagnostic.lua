-- AUDIO-015 native multi-song DIAGNOSTIC harness (GENESIS NTSC).
--
-- This is an EXPLICITLY LABELED DIAGNOSTIC: it injects the reserved diagnostic
-- selectors 0xC0-0xDF (which the running arcade program NEVER emits) into the
-- Z80 command ring and verifies that the permanent driver decodes the intended
-- authored stream.  It does NOT reproduce an authentic in-game music event and
-- must never be cited as proof of an authentic command->song mapping.  The only
-- proven authentic mapping remains 0x25 (player appearance -> Aggressive World).
--
-- For each diagnostic selector it confirms: driver goes ACTIVE, the stream
-- pointer advances, and the pointer sits inside that song's cartridge address
-- window (tying the selector to the correct stream).  Then it stops (0x00)
-- before the next song so each is observed independently.

local machine = manager.machine
local z80 = assert(machine.devices[":genesis_snd_z80"], "missing Genesis Z80")
local zprog = assert(z80.spaces["program"], "missing Z80 program space")
local trace_dir = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")
local settle_frames = tonumber(os.getenv("AUDIO015_DIAG_SETTLE") or "90")
local play_frames = tonumber(os.getenv("AUDIO015_DIAG_PLAY") or "150")

-- Driver / shared-RAM layout (see z80_driver.asm and sound_comm.s).
local SONGC, SONGT = 0x1DFF, 0x1E00
local CUR_LO, ACTIVE = 0x1FA0, 0x1FA3
local QHEAD, QTAIL, QDATA = 0x1FD0, 0x1FD1, 0x1FE0

local function z8(a) return zprog:read_u8(a) & 0xff end
local function cur24()
  return z8(CUR_LO) | (z8(CUR_LO + 1) << 8) | (z8(CUR_LO + 2) << 16)
end

-- Read the installed Z80 song table: 7 bytes/entry {cmd, start24, loop24}.
local function read_table()
  local count = z8(SONGC)
  local rows = {}
  for i = 0, count - 1 do
    local base = SONGT + i * 7
    rows[#rows + 1] = {
      command = z8(base),
      start = z8(base + 1) | (z8(base + 2) << 8) | (z8(base + 3) << 16),
      loop = z8(base + 4) | (z8(base + 5) << 8) | (z8(base + 6) << 16),
    }
  end
  return count, rows
end

-- Inject a command exactly as the 68000 bridge would (ring publish).
local function inject(cmd)
  local head = z8(QHEAD)
  zprog:write_u8(QDATA + head, cmd)
  zprog:write_u8(QHEAD, (head + 1) & 0x0F)
end

local results = {}
local frame = 0
local state = "boot"
local order, idx = {0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6}, 0
local phase_frame = 0
local table_count, table_rows = 0, {}
local cur_before, active_seen, cur_min, cur_max = 0, false, nil, nil

local function row_for(cmd)
  for _, r in ipairs(table_rows) do if r.command == cmd then return r end end
  return nil
end

local function finish()
  local out = assert(io.open(trace_dir .. "/native_song_diagnostic.tsv", "w"))
  out:write("platform\tGENESIS NTSC (DIAGNOSTIC INJECTION, not authentic gameplay)\n")
  out:write(string.format("song_table_rows\t%d\n", table_count))
  out:write("selector\tstart\tloop\tactive\tcur_advance\tin_window\tcur_min\tcur_max\tresult\n")
  local all_pass = (#results == #order)
  for _, r in ipairs(results) do
    if r.result ~= "PASS" then all_pass = false end
    out:write(string.format("0x%02X\t%06X\t%06X\t%d\t%d\t%s\t%06X\t%06X\t%s\n",
      r.selector, r.start, r.loop, r.active and 1 or 0, r.advance,
      r.in_window and "YES" or "NO", r.cur_min or 0, r.cur_max or 0, r.result))
  end
  out:write("result=" .. (all_pass and "PASS" or "FAIL") .. "\n")
  out:close()
  machine:exit()
end

local function start_song()
  idx = idx + 1
  if idx > #order then finish() return end
  local cmd = order[idx]
  local r = row_for(cmd)
  if not r then
    results[#results + 1] = {selector = cmd, start = 0, loop = 0, active = false,
      advance = 0, in_window = false, result = "FAIL(no table row)"}
    phase_frame = frame
    return
  end
  inject(cmd)
  cur_before = r.start
  active_seen, cur_min, cur_max = false, nil, nil
  phase_frame = frame
  state = "play:" .. cmd
end

emu.register_frame_done(function()
  frame = frame + 1
  if state == "boot" then
    table_count, table_rows = read_table()
    -- Wait until the 68000 has installed the full song table (8 rows).
    if table_count >= 8 and frame > settle_frames then
      state = "run"
      start_song()
    end
    return
  end
  if state == "run" then return end

  -- Observing a single injected song.
  local cmd = order[idx]
  local r = row_for(cmd)
  if z8(ACTIVE) ~= 0 then active_seen = true end
  local c = cur24()
  if c ~= 0 then
    cur_min = (cur_min == nil) and c or math.min(cur_min, c)
    cur_max = (cur_max == nil) and c or math.max(cur_max, c)
  end

  if frame - phase_frame >= play_frames then
    local advance = (cur_max or cur_before) - cur_before
    -- The stream pointer must sit inside this song's own cartridge window.
    local lo = math.min(r.start, r.loop ~= 0 and r.loop or r.start)
    local in_window = (cur_min ~= nil) and cur_min >= (lo - 0x10)
      and (cur_max ~= nil) and cur_max <= (r.start + 0x200000)
    local ok = active_seen and advance > 16 and in_window
    results[#results + 1] = {selector = cmd, start = r.start, loop = r.loop,
      active = active_seen, advance = advance, in_window = in_window,
      cur_min = cur_min, cur_max = cur_max,
      result = ok and "PASS" or "FAIL"}
    inject(0x00)                     -- stop before the next song
    state = "settle"
    phase_frame = frame
  end
end)

-- Small settle gap between songs, then advance.
emu.register_frame_done(function()
  if state == "settle" and frame - phase_frame >= 30 then
    state = "run"; start_song()
  end
end)
