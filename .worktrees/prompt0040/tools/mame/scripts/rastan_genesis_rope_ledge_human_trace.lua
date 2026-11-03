-- GENESIS NTSC Rastan Build 0373: human-played missing rope-side ledge capture.
-- No game input is generated. Press M once at the exact comparison location.
-- The first rising edge of M is the authoritative USER_MARK; only 120 frames
-- before and after it are retained.

local machine = manager.machine
assert(machine.system.name == "genesis", "this trace requires GENESIS NTSC machine 'genesis'")

local cpu = assert(machine.devices[":maincpu"], "missing :maincpu")
local program = assert(cpu.spaces["program"], "missing maincpu program space")
local vdp = assert(machine.devices[":gen_vdp"], "missing :gen_vdp")
local vram = assert(vdp.spaces["videoram"], "missing Genesis VRAM space")
local trace_dir = assert(os.getenv("TRACE_DIR"), "TRACE_DIR is required")

local A5 = 0x00FF0000
local STAGED_FG = 0x00FF50A0
local STAGED_SCROLL_X_FG = 0x00FF409A
local STAGED_SCROLL_Y_FG = 0x00FF409E
local COLLISION = 0x00FF1E00
local PLANE_A_VRAM = 0x0000E000
local PRE_FRAMES, POST_FRAMES = 120, 120

local function r16(address) return program:read_u16(address) & 0xffff end
local function r32(address) return program:read_u32(address) & 0xffffffff end
local function v16(address) return vram:read_u16(address) & 0xffff end
local function cpu_value(name)
  local state = cpu.state[name]
  return state and (state.value & 0xffffffff) or 0
end

local frames = assert(io.open(trace_dir .. "/rope_ledge_frames.tsv", "w"))
local marks = assert(io.open(trace_dir .. "/rope_ledge_user_mark.tsv", "w"))
local terrain = assert(io.open(trace_dir .. "/rope_ledge_terrain.tsv", "w"))
local metadata = assert(io.open(trace_dir .. "/trace_metadata.txt", "w"))

local core_header = table.concat({
  "frame", "USER_MARK", "event", "pc", "a5_register",
  "a5_013E", "a5_10A8", "a5_10CA", "a5_10CC",
  "retained_fg_scroll_x", "retained_fg_scroll_y",
  "native_fg_scroll_x", "native_fg_scroll_y",
  "player_screen_x", "player_screen_y",
  "retained_world_ring_x", "retained_world_ring_y",
  "native_world_ring_x", "native_world_ring_y",
  "collision_probe_row", "collision_probe_col", "collision_probe_word"
}, "\t")

frames:write(core_header, "\n")
marks:write(core_header, "\n")
terrain:write(table.concat({
  "frame", "USER_MARK", "role", "rel_row", "rel_col",
  "logical_row", "logical_col", "physical_plane_row",
  "row_group", "col_block", "live_row_source_ptr", "source_delta_blocks",
  "source_entry_arcade", "source_entry_genesis", "descriptor_attr", "metatile",
  "metatile_cell", "staged_plane_a_word", "final_vram_plane_a_word",
  "collision_address", "collision_word"
}, "\t"), "\n")

metadata:write("platform=GENESIS NTSC MAME\n")
metadata:write("machine=genesis\n")
metadata:write("capture=human_play_missing_rope_side_ledge\n")
metadata:write("baseline_build=0373\n")
metadata:write("rom=" .. (os.getenv("ROM_NAME") or "rastan_direct_video_test_build_0373.bin") .. "\n")
metadata:write("rom_sha256=" .. (os.getenv("ROM_SHA") or "4bece179504e3ce7a83bc7d2ca392ba4a4aba4cadb1386e2f4f72431b573c2cc") .. "\n")
metadata:write("marker_key=M\nmarker_event=USER_MARK\n")
metadata:write("pre_frames=120\npost_frames=120\n")
metadata:write("a5_base=0x00FF0000\n")
metadata:write("retained_fg_scroll=a5+0x10AE/a5+0x10B0\n")
metadata:write("native_fg_scroll=0x00FF409A/0x00FF409E\n")
metadata:write("player_screen_raw=a5+0x10BE/a5+0x10C0\n")
metadata:write("staged_plane_a=0x00FF50A0\nfinal_plane_a_vram=0xE000\n")
metadata:write("collision_grid=0x00FF1E00\n")
metadata:write("started=" .. os.date("!%Y-%m-%dT%H:%M:%SZ") .. "\n")
metadata:flush()

local marker_code = assert(machine.input:code_from_token("KEYCODE_M"), "KEYCODE_M unavailable")
local marker_prev, marked, closed = false, false, false
local frame, mark_frame, post_remaining = 0, -1, 0
local pre = {}

local function sample_state(is_mark)
  local screen_x, screen_y = r16(A5 + 0x10BE), r16(A5 + 0x10C0)
  local retained_x, retained_y = r16(A5 + 0x10AE), r16(A5 + 0x10B0)
  local native_x, native_y = r16(STAGED_SCROLL_X_FG), r16(STAGED_SCROLL_Y_FG)
  local retained_ring_x = (screen_x - retained_x) & 0x01ff
  local retained_ring_y = (screen_y - retained_y) & 0x01ff
  local native_ring_x = (screen_x - native_x) & 0x01ff
  local native_ring_y = (screen_y - native_y) & 0x01ff

  -- Original 0x53A2E collision address arithmetic uses retained arcade scroll.
  local collision_col = ((((retained_ring_x >> 1) + 8) & 0x00fc) >> 2) & 0x3f
  local collision_row = (retained_ring_y >> 3) & 0x3f
  local collision_word = r16(COLLISION + collision_row * 0x80 + collision_col * 2)

  return {
    frame=frame, mark=is_mark and 1 or 0, event=is_mark and "USER_MARK" or "",
    pc=cpu_value("PC") & 0xffffff, a5=cpu_value("A5") & 0xffffff,
    segment=r16(A5+0x013E), selector=r16(A5+0x10A8),
    strip=r16(A5+0x10CA), group=r16(A5+0x10CC),
    retained_x=retained_x, retained_y=retained_y, native_x=native_x, native_y=native_y,
    screen_x=screen_x, screen_y=screen_y,
    retained_ring_x=retained_ring_x, retained_ring_y=retained_ring_y,
    native_ring_x=native_ring_x, native_ring_y=native_ring_y,
    collision_row=collision_row, collision_col=collision_col, collision_word=collision_word,
  }
end

local function format_core(s)
  return table.concat({
    tostring(s.frame), tostring(s.mark), s.event,
    string.format("%06X",s.pc), string.format("%06X",s.a5),
    string.format("%04X",s.segment), string.format("%04X",s.selector),
    string.format("%04X",s.strip), string.format("%04X",s.group),
    string.format("%04X",s.retained_x), string.format("%04X",s.retained_y),
    string.format("%04X",s.native_x), string.format("%04X",s.native_y),
    string.format("%04X",s.screen_x), string.format("%04X",s.screen_y),
    string.format("%03X",s.retained_ring_x), string.format("%03X",s.retained_ring_y),
    string.format("%03X",s.native_ring_x), string.format("%03X",s.native_ring_y),
    tostring(s.collision_row), tostring(s.collision_col), string.format("%04X",s.collision_word)
  }, "\t")
end

local function resolve_source_cell(s, row, col)
  row, col = row & 0x3f, col & 0x3f
  local physical_row = row & 0x1f
  local row_group, col_block = (row >> 2) & 0x0f, (col >> 2) & 0x0f
  local live_ptr = r32(A5 + 0x1000 + row_group * 4) & 0xffffff
  local current_group = s.group & 0x0f
  local front_col = current_group * 4 + (s.strip & 3)
  local delta = col_block - current_group
  if col > front_col then delta = delta - 16 end
  local source_arcade = (live_ptr + delta * 4) & 0xffffff
  local source_genesis = source_arcade + 0x200
  local attr = r16(source_genesis)
  local metatile = r16(source_genesis + 2)
  local metatile_cell = r16(0x00000200 + metatile + (row & 3) * 8 + (col & 3) * 2)
  local plane_index = physical_row * 64 + col
  local collision_address = COLLISION + (row * 64 + col) * 2
  return physical_row, row_group, col_block, live_ptr, delta, source_arcade,
    source_genesis, attr, metatile, metatile_cell,
    r16(STAGED_FG + plane_index * 2), v16(PLANE_A_VRAM + plane_index * 2),
    collision_address, r16(collision_address)
end

local function write_terrain(s)
  -- Native Plane-A display position is selected by the native staged scroll.
  local player_row = (s.native_ring_y >> 3) & 0x3f
  local player_col = (s.native_ring_x >> 3) & 0x3f
  for dr=-2,2 do
    for dc=-2,2 do
      local row, col = (player_row+dr)&0x3f, (player_col+dc)&0x3f
      local role = (dr==0 and dc==0) and "PLAYER_CELL" or "NEAR_PLAYER"
      if row==s.collision_row and col==s.collision_col then role=role.."+COLLISION_PROBE" end
      local pr,rg,cb,live,delta,srca,srcg,attr,meta,source_cell,stage,final,ca,cw =
        resolve_source_cell(s,row,col)
      terrain:write(table.concat({
        tostring(s.frame),"USER_MARK",role,tostring(dr),tostring(dc),
        tostring(row),tostring(col),tostring(pr),tostring(rg),tostring(cb),
        string.format("%06X",live),tostring(delta),string.format("%06X",srca),
        string.format("%06X",srcg),string.format("%04X",attr),string.format("%04X",meta),
        string.format("%04X",source_cell),string.format("%04X",stage),string.format("%04X",final),
        string.format("%06X",ca),string.format("%04X",cw)
      },"\t"),"\n")
    end
  end

  local dr=(s.collision_row-player_row)&0x3f; if dr>31 then dr=dr-64 end
  local dc=(s.collision_col-player_col)&0x3f; if dc>31 then dc=dc-64 end
  if math.abs(dr)>2 or math.abs(dc)>2 then
    local row,col=s.collision_row,s.collision_col
    local pr,rg,cb,live,delta,srca,srcg,attr,meta,source_cell,stage,final,ca,cw =
      resolve_source_cell(s,row,col)
    terrain:write(table.concat({
      tostring(s.frame),"USER_MARK","COLLISION_PROBE",tostring(dr),tostring(dc),
      tostring(row),tostring(col),tostring(pr),tostring(rg),tostring(cb),
      string.format("%06X",live),tostring(delta),string.format("%06X",srca),
      string.format("%06X",srcg),string.format("%04X",attr),string.format("%04X",meta),
      string.format("%04X",source_cell),string.format("%04X",stage),string.format("%04X",final),
      string.format("%06X",ca),string.format("%04X",cw)
    },"\t"),"\n")
  end
  terrain:flush()
end

emu.register_frame_done(function()
  frame=frame+1
  local down=false
  local ok=pcall(function() down=machine.input:code_pressed(marker_code) end)
  local is_mark=ok and down and not marker_prev and not marked
  marker_prev=(ok and down) or false
  local s=sample_state(is_mark)
  local line=format_core(s)

  if is_mark then
    marked=true; mark_frame=frame
    for _,old in ipairs(pre) do frames:write(old,"\n") end
    frames:write(line,"\n"); marks:write(line,"\n")
    write_terrain(s)
    frames:flush(); marks:flush()
    post_remaining=POST_FRAMES
    metadata:write("USER_MARK_frame="..tostring(frame).."\n"); metadata:flush()
    emu.print_info(string.format(
      "USER_MARK frame=%d segment=%04X selector=%04X strip=%04X group=%04X "..
      "screen=%04X,%04X native_world_ring=%03X,%03X collision=%d,%d:%04X",
      frame,s.segment,s.selector,s.strip,s.group,s.screen_x,s.screen_y,
      s.native_ring_x,s.native_ring_y,s.collision_row,s.collision_col,s.collision_word))
  elseif marked and post_remaining>0 then
    frames:write(line,"\n"); post_remaining=post_remaining-1
    if post_remaining==0 then
      frames:flush(); emu.print_info("USER_MARK capture window complete; stop MAME when ready")
    end
  elseif not marked then
    pre[#pre+1]=line
    if #pre>PRE_FRAMES then table.remove(pre,1) end
  end
end)

local function finish()
  if closed then return end
  closed=true
  metadata:write("ended="..os.date("!%Y-%m-%dT%H:%M:%SZ").."\n")
  metadata:write("total_frames="..tostring(frame).."\n")
  metadata:write("USER_MARK_seen="..(marked and "YES" or "NO").."\n")
  if marked then metadata:write("USER_MARK_frame="..tostring(mark_frame).."\n") end
  frames:flush(); marks:flush(); terrain:flush(); metadata:flush()
  frames:close(); marks:close(); terrain:close(); metadata:close()
end

_G.rastan_genesis_rope_ledge_human_trace_stop = emu.add_machine_stop_notifier(function()
  pcall(finish)
end)

emu.print_info("GENESIS NTSC Build 0373 rope-ledge trace armed: press M once for USER_MARK")
