-- plane_a_xy_trace.lua  (READ-ONLY external trace; no ROM/WRAM modification)
-- Purpose: capture the intermittent Plane-A misplaced-8x8-cell defect that occurs during
-- COMBINED horizontal + vertical camera scrolling (Build 0398). Tighe plays normally and
-- presses M once when he SEES a bad Plane-A tile; a rolling buffer preserves the streaming
-- history BEFORE the keypress so the original bad event is not lost.
--
-- Mechanism (per-frame sampling = always playable, no per-instruction cost) plus guarded
-- per-producer-PC hooks (intra-frame front + order) if the MAME build exposes cpu:add_exec.
--
-- Established project conventions reused: KEYCODE_M marker (rastan_genesis_rope_ledge_human_trace),
-- homepath output dir (genesistrace), :gen_vdp videoram read (dump_genesis_vram).

local PRE_FRAMES  = 180      -- rolling history retained before the marker
local POST_FRAMES = 30       -- frames captured after the marker
local MAX_ISECT   = 24       -- cap intersection staged-vs-VRAM samples per frame

-- Genesis runtime addresses (A5 = 0x00FF0000). From apps/rastan-direct/out/symbol.txt + tilemap_hooks.s.
local A_SCROLL_X   = 0x00FF409A   -- staged_scroll_x_fg (word)
local A_SCROLL_Y   = 0x00FF409E   -- staged_scroll_y_fg (word)
local A_STRIP_GRP  = 0x00FF10CC   -- arcade strip_group  (a5@0x10CC, word) = horizontal front block
local A_STRIP_IDX  = 0x00FF10CA   -- arcade strip_index  (a5@0x10CA, word) = front cell-in-block
local A_SRC_REF    = 0x00FF61F4   -- plane_a_src_ref_block (word)  16 => resident/vertical mode
local A_COL_DIRTY  = 0x00FF61EC   -- fg_col_dirty (two longs, 64 cols)
local A_ROW_DIRTY  = 0x00FF4006   -- fg_row_dirty (one long, 32 rows)
local A_STAGED     = 0x00FF50A0   -- staged_fg_buffer (32 rows x 64 cols words)
local VRAM_PLANE_A = 0x0000E000   -- Plane-A name table base (videoram space)

-- Producer / publication runtime PCs (symbol.txt). Hooked only if cpu:add_exec exists.
local PRODUCER = {
  [0x00070418] = "Hsel0",   -- genesistan_hook_tilemap_plane_a_selector0_native (horizontal column)
  [0x00070554] = "Hsel12",  -- genesistan_hook_tilemap_plane_a_selector12_native (horizontal column)
  [0x00070688] = "Vup",     -- genesistan_plane_a_pan_publish_entering_rows_up   (vertical row)
  [0x000706e0] = "Vdown",   -- genesistan_plane_a_pan_publish_entering_rows_down (vertical row)
  [0x00072922] = "COMMIT",  -- vdp_commit_fg_narrow_strips (publication boundary)
}

local mac  = manager.machine
local cpu  = mac.devices[":maincpu"]
local prog = cpu.spaces["program"]
-- NOTE: this MAME genesis build does NOT expose Plane-A VRAM to Lua. The :gen_vdp "videoram"
-- space is a 16KB stub (address_mask 0x3FFF) that reads all-zero; the real 64KB VRAM is kept
-- internal to the 315_5313 device. So we do NOT read VRAM. The staged_fg_buffer (WRAM) IS the
-- intended Plane-A content the VBlank DMA publishes, and it is fully readable; the discriminator
-- is built on staging alone (see the staged-grid dump).

local function rd16(a) return prog:read_u16(a) & 0xFFFF end
local function rd32(a) return prog:read_u32(a) & 0xFFFFFFFF end
local function st16(a) return prog:read_u16(a) & 0xFFFF end  -- staged buffer lives in WRAM (program space)

local outdir = (mac.options.entries.homepath:value():match("([^;]+)") or ".") .. "/plane_a_xy"
os.execute('mkdir -p "' .. outdir .. '" 2>/dev/null')

-- Primary marker is M. A secondary key (comma) is accepted too, so a stuck/odd M mapping
-- cannot silently block a capture. assert() surfaces an invalid token loudly (mirrors the
-- proven rastan_genesis_rope_ledge_human_trace marker setup) instead of failing silently.
local marker_code  = assert(mac.input:code_from_token("KEYCODE_M"),     "KEYCODE_M unavailable")
local marker_code2 = assert(mac.input:code_from_token("KEYCODE_COMMA"), "KEYCODE_COMMA unavailable")
local marker_prev, marked, post_left, marked_frame = false, false, 0, 0

local ring, ring_head, ring_n = {}, 1, 0     -- rolling buffer of PRE_FRAMES frame records
local frame_no = 0
local cur_events = {}                         -- intra-frame producer events (from add_exec)
local last_front = -1

-- Guarded per-producer-PC capture (intra-frame front + order). Zero cost if unsupported.
local exec_hook_note = "per-PC hooks: not installed (per-frame sampling only)"
if type(cpu.add_exec) == "function" then
  local ok = pcall(function()
    cpu:add_exec(function()
      local pc = cpu.state["PC"].value & 0xFFFFFF
      local tag = PRODUCER[pc]
      if tag then
        cur_events[#cur_events + 1] = {
          tag = tag,
          grp = rd16(A_STRIP_GRP),
          idx = rd16(A_STRIP_IDX),
          ref = rd16(A_SRC_REF),
        }
      end
    end)
  end)
  exec_hook_note = ok and "per-PC hooks: INSTALLED (intra-frame front/order captured)"
                      or  "per-PC hooks: add_exec present but failed; per-frame sampling only"
end

local function dirty_cols()
  local lo, hi, t = rd32(A_COL_DIRTY), rd32(A_COL_DIRTY + 4), {}
  for c = 0, 31 do if (lo >> c) & 1 == 1 then t[#t+1] = c end end
  for c = 0, 31 do if (hi >> c) & 1 == 1 then t[#t+1] = c + 32 end end
  return t
end
local function dirty_rows()
  local w, t = rd32(A_ROW_DIRTY), {}
  for r = 0, 31 do if (w >> r) & 1 == 1 then t[#t+1] = r end end
  return t
end

local last_sx, last_sy = -1, -1

local function snapshot()
  frame_no = frame_no + 1
  local grp, idx = rd16(A_STRIP_GRP), rd16(A_STRIP_IDX)
  local front = (grp << 16) | idx
  local cols, rows = dirty_cols(), dirty_rows()
  local sx, sy = rd16(A_SCROLL_X), rd16(A_SCROLL_Y)
  -- Real combined-motion indicator: BOTH scroll axes moved vs the previous frame. (The old
  -- same-frame col+row-dirty gate never fires here because H and V dirty on separate frames.)
  local dx = (last_sx >= 0) and (sx ~= last_sx)
  local dy = (last_sy >= 0) and (sy ~= last_sy)
  local cmotion = dx and dy
  local any_dirty = (#cols > 0) or (#rows > 0)

  local rec = {
    f = frame_no,
    sx = sx, sy = sy,
    grp = grp, idx = idx, ref = rd16(A_SRC_REF),
    ncol = #cols, nrow = #rows, cmotion = cmotion,
    front_advanced = (last_front >= 0 and front ~= last_front),
    events = cur_events,
    isect = nil,
  }

  -- On any frame that dirties a column OR row, record the dirty location(s) and the live front
  -- + producer mode (ref) that staged them. (H and V never share a frame, so this shows which
  -- producer touched which cells during the combined window.) Bounded to MAX_ISECT entries.
  if any_dirty then
    local evs, n = {}, 0
    for _, c in ipairs(cols) do
      if n >= MAX_ISECT then break end
      evs[#evs+1] = { kind = "COL", at = c }; n = n + 1
    end
    for _, r in ipairs(rows) do
      if n >= MAX_ISECT then break end
      evs[#evs+1] = { kind = "ROW", at = r }; n = n + 1
    end
    rec.dirty = evs
  end

  last_front = front
  last_sx, last_sy = sx, sy
  cur_events = {}
  return rec
end

-- push a pre-marker record into the rolling ring (keep last PRE_FRAMES); post-marker
-- records go to post_tail instead, so the two never overlap/duplicate.
local function ring_push(rec)
  ring[ring_head] = rec
  ring_head = (ring_head % PRE_FRAMES) + 1
  if ring_n < PRE_FRAMES then ring_n = ring_n + 1 end
end

local function ring_in_order()
  local out = {}
  local start = (ring_n < PRE_FRAMES) and 1 or ring_head
  for i = 0, ring_n - 1 do out[#out+1] = ring[((start - 1 + i) % PRE_FRAMES) + 1] end
  return out
end

local post_tail = {}

-- Full staged_fg_buffer grid captured NOW (at dump time), 32 rows x 64 cols of name words.
-- This is the intended Plane-A content the VBlank DMA publishes. Because the defect persists
-- statically after motion stops, the misplaced cell shows up here as a word that breaks the
-- local terrain pattern -- IF the bug is in the producer (CASE A). If the staged grid is clean
-- at the visibly-wrong on-screen cell, the staging was correct and the DMA/commit mis-published
-- it (CASE B). VRAM itself is not readable in this MAME, so the screenshot is the "actual".
local PLANE_ROWS, PLANE_COLS = 32, 64
local function read_staged_grid()
  local g = {}
  for r = 0, PLANE_ROWS - 1 do
    local row = {}
    for c = 0, PLANE_COLS - 1 do
      row[c] = st16(A_STAGED + (r * PLANE_COLS + c) * 2)
    end
    g[r] = row
  end
  return g
end

local function emit(path, list, grid, sx, sy)
  local f = io.open(path, "w")
  if not f then return end
  f:write(string.format("# plane_a_xy marker trace  (marker_frame=%d)\n", marked_frame))
  f:write("# " .. exec_hook_note .. "\n")
  f:write("# VRAM is NOT readable in this MAME build; discriminator uses the staged_fg_buffer only.\n")
  f:write("# columns: FRAME sx sy grp idx ref ncol nrow CMOTION front_adv | dirty(COL/ROW at)\n")
  f:write("#   CMOTION = both scroll axes moved vs previous frame (true combined H+V motion)\n")
  f:write("#   ref: 10(hex)=16 resident/vertical ring-unwrap; else horizontal leading-edge (= strip_group)\n\n")
  -- Full staged grid at the marker instant. scroll (sx,sy) lets a screen position (e.g. "upper
  -- right") be mapped to a physical ring cell: col0 = (sx>>3) & 63, row0 = (sy>>3) & 31.
  f:write(string.format("## STAGED_FG_BUFFER grid at marker (sx=%04X sy=%04X -> screen top-left ring cell row%d col%d)\n",
    sx, sy, (sy >> 3) & 31, (sx >> 3) & 63))
  f:write("## rows R00..R31 down, cols C00..C63 across; each entry is the Plane-A name word.\n")
  f:write("##        " )
  for c = 0, PLANE_COLS - 1 do f:write(string.format("%02d   ", c)) end
  f:write("\n")
  for r = 0, PLANE_ROWS - 1 do
    f:write(string.format("## R%02d  ", r))
    for c = 0, PLANE_COLS - 1 do f:write(string.format("%04X ", grid[r][c])) end
    f:write("\n")
  end
  f:write("\n")
  for _, r in ipairs(list) do
    f:write(string.format("F%-7d sx=%04X sy=%04X grp=%02X idx=%X ref=%X col=%d row=%d %s%s",
      r.f, r.sx, r.sy, r.grp, r.idx, r.ref, r.ncol, r.nrow,
      r.cmotion and "CMOTION " or "", r.front_advanced and "FRONT_ADV " or ""))
    if r.events and #r.events > 0 then
      f:write(" | ev:")
      for _, e in ipairs(r.events) do f:write(string.format(" %s(g%02X,i%X,r%X)", e.tag, e.grp, e.idx, e.ref)) end
    end
    if r.dirty and #r.dirty > 0 then
      f:write(" | dirty:")
      for _, d in ipairs(r.dirty) do f:write(string.format(" %s%d", d.kind, d.at)) end
    end
    f:write("\n")
  end
  f:close()
end

-- dump() is safe to call at any time after a mark: it writes whatever pre-history +
-- post-tail exists NOW. It is called immediately on the M press (pre-history, so nothing
-- is lost if MAME is paused/closed before the post-roll), again when the post-roll
-- completes, and once more from the machine-stop notifier as a backstop.
local function dump(phase)
  local list = ring_in_order()
  for _, r in ipairs(post_tail) do list[#list+1] = r end
  local base = string.format("%s/plane_a_xy_marker_%d", outdir, marked_frame)
  local mark_sx, mark_sy = rd16(A_SCROLL_X), rd16(A_SCROLL_Y)
  local grid = read_staged_grid()
  emit(base .. ".txt", list, grid, mark_sx, mark_sy)

  -- short summary
  local s = io.open(base .. "_summary.txt", "w")
  if s then
    local cmot, fadv, ndirty = 0, 0, 0
    for _, r in ipairs(list) do
      if r.cmotion then cmot = cmot + 1 end
      if r.front_advanced then fadv = fadv + 1 end
      if r.dirty then ndirty = ndirty + #r.dirty end
    end
    s:write(string.format("marker_frame             : %d\n", marked_frame))
    s:write(string.format("retained frames          : %d (pre %d + post %d)\n", #list, ring_n, #post_tail))
    s:write(string.format("marker scroll            : sx=%04X sy=%04X  (screen top-left ring cell row%d col%d)\n",
      mark_sx, mark_sy, (mark_sy >> 3) & 31, (mark_sx >> 3) & 63))
    s:write(string.format("combined-motion frames   : %d  (both scroll axes moved)\n", cmot))
    s:write(string.format("front-advanced frames    : %d\n", fadv))
    s:write(string.format("dirty col/row events     : %d\n", ndirty))
    s:write("# VRAM is not readable in this MAME; the full STAGED_FG_BUFFER grid is in the .txt.\n")
    s:write("# Find the on-screen bad cell in that grid (map 'upper right' via the scroll above):\n")
    s:write("#   staged word is wrong/out-of-pattern there = CASE A (producer); staged word is\n")
    s:write("#   correct there but the screenshot shows it wrong = CASE B (DMA/commit).\n")
    s:write("# " .. exec_hook_note .. "\n")
    s:close()
  end
  print(string.format("[plane_a_xy] %s frame %d -> %s.txt (+_summary.txt)  [pre %d + post %d]",
    phase or "MARK", marked_frame, base, ring_n, #post_tail))
end

local function on_frame()
  local rec = snapshot()

  if marked then
    post_tail[#post_tail+1] = rec
    post_left = post_left - 1
    if post_left <= 0 then
      dump("MARK (final)")
      marked = false          -- allow another mark later in the same session
      post_tail = {}
    end
    return
  end

  -- not yet marked: this is pre-marker history (the mark frame itself is the last pre frame).
  ring_push(rec)

  local down = false
  local ok = pcall(function()
    down = mac.input:code_pressed(marker_code) or mac.input:code_pressed(marker_code2)
  end)
  if ok and down and not marker_prev then
    marked, marked_frame, post_left, post_tail = true, frame_no, POST_FRAMES, {}
    -- Save the pre-history IMMEDIATELY so a pause/quit before the post-roll cannot lose it.
    dump("MARK (pre)")
    print(string.format("[plane_a_xy] M at frame %d; pre-history saved, capturing %d more frames...",
      frame_no, POST_FRAMES))
  end
  marker_prev = ok and down or false
end

-- Poll via register_frame_done: this fires AFTER MAME polls physical input each frame, so
-- code_pressed reflects the live key state. The proven rastan_genesis_rope_ledge_human_trace
-- marker (which produced real USER_MARK captures) uses register_frame_done; the earlier
-- add_machine_frame_notifier fires before the input poll and never saw the keypress.
local frame_hook_note
if type(emu.register_frame_done) == "function" then
  emu.register_frame_done(on_frame)
  frame_hook_note = "frame hook: register_frame_done (input-live)"
else
  emu.add_machine_frame_notifier(on_frame)
  frame_hook_note = "frame hook: add_machine_frame_notifier (fallback)"
end

-- Backstop: if MAME closes while a mark is still mid-post-roll, flush what we have.
pcall(function()
  emu.add_machine_stop_notifier(function()
    if marked then dump("MARK (on-stop)") end
  end)
end)

print("[plane_a_xy] READY. Play normally. Press M once when you SEE a misplaced Plane-A tile.")
print("[plane_a_xy] SELF-TEST FIRST: click the MAME window, tap M once now. You should see a")
print("[plane_a_xy]   'MARK (pre) frame N -> ...' line here immediately. If you do NOT, keys are")
print("[plane_a_xy]   not reaching MAME (focus/keyboard) -- fix that before the real capture.")
print("[plane_a_xy]   (If M does nothing on your keyboard, the COMMA key ',' also marks.)")
print("[plane_a_xy] output dir: " .. outdir .. "   (F12 screenshot lands here too)")
print("[plane_a_xy] " .. frame_hook_note)
print("[plane_a_xy] " .. exec_hook_note)
