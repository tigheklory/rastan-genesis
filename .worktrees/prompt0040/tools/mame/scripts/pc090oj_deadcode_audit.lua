-- pc090oj_deadcode_audit.lua
-- PC090OJ zero-debt audit backstop (Build 0297 task).
--
-- Capability (new, reusable): a per-frame census of the virtual PC090OJ object
-- table (pc090oj_object_ram) and its diagnostic counters across a full GENESIS
-- NTSC attract cycle, to PROVE the frontend object-RAM scan emits zero sprites
-- in every frontend scene (i.e. no live semantic consumer remains) before the
-- compatibility infrastructure is removed.
--
-- Ground truth: a record is decoded/emitted by .Lpc090oj_decode_record only when
-- its code word (record*8 + 4) masked 0x1FFF is nonzero AND < 0x1000. This walks
-- all 256 records every frame and tracks, per scene id, the max count of such
-- "drawable-candidate" code words. If that max is 0 for every scene across the
-- whole attract sweep, the object-RAM path renders nothing.
--
-- Output: build/mame/home/pc090oj_deadcode_audit/summary.txt
--
local OBJRAM      = 0xFF6F9A          -- pc090oj_object_ram, 256 * 8 bytes
local OBJRAM_ROWS = 256
local SCENE_ID    = 0xFF78B0          -- genesistan_current_scene_id (u8)
local PROD_WRITE  = 0xFF77BA          -- pc090oj_producer_write_count (u16)
local PROD_OOB    = 0xFF77B8          -- pc090oj_producer_oob_count (u16)
local EMITTED     = 0xFF77B0          -- pc090oj_emitted_count (u16)
local DRAWABLE    = 0xFF77AE          -- pc090oj_drawable_count (u16)
local STAGE       = 0xFF0118          -- arcade title substage (a5+0x118)
local TITEMS      = 0xFF68B4          -- transient_items_active (item page marker)

local frame_count = 0
local cpu, prog

local scene_stats = {}
local scene_seq = {}
local last_scene = -1
local last_stage = -1
-- object-scan-path exercise proof:
local scan_path_frames = 0            -- frames where .Lnq_frontend_object_scan runs
local scan_path_max_candidates = 0    -- max drawable candidates while ON the scan path
local titems_frames = 0               -- frames with the item page active
local scene_gt1_frames = 0            -- frames with scene id > 1
local global_max_candidates = 0
local global_max_candidate_scene = -1
local global_max_candidate_frame = -1
local max_prod_write = 0
local max_prod_oob = 0
local max_emitted = 0
local max_drawable = 0

local function scene_entry(id)
	local s = scene_stats[id]
	if not s then
		s = {frames = 0, max_candidates = 0, max_rawnonzero = 0,
		     first_frame = frame_count, last_frame = frame_count}
		scene_stats[id] = s
	end
	return s
end

local function census_frame()
	frame_count = frame_count + 1
	if not cpu or not prog then return end

	local scene = prog:read_u8(SCENE_ID)
	local stage = prog:read_u16(STAGE) & 0xFFFF

	if scene ~= last_scene or stage ~= last_stage then
		table.insert(scene_seq, string.format("frame %06d  scene=%d  stage=%04x  titems=%d",
			frame_count, scene, stage, prog:read_u16(TITEMS) & 0xFFFF))
		last_scene = scene
		last_stage = stage
	end

	-- Would pc090oj_native_emit_pass take the object-RAM scan this frame?
	-- (scene==0 && stage!=0)  OR  (scene!=0 && scene!=1)
	local on_scan_path = ((scene == 0 and stage ~= 0) or (scene ~= 0 and scene ~= 1))
	if on_scan_path then scan_path_frames = scan_path_frames + 1 end
	if scene > 1 then scene_gt1_frames = scene_gt1_frames + 1 end
	if (prog:read_u16(TITEMS) & 0xFFFF) ~= 0 then titems_frames = titems_frames + 1 end

	local candidates = 0
	local rawnonzero = 0
	local base = OBJRAM
	for r = 0, OBJRAM_ROWS - 1 do
		local rb = base + r * 8
		local w0 = prog:read_u16(rb)
		local w1 = prog:read_u16(rb + 2)
		local code = prog:read_u16(rb + 4) & 0x1FFF
		local w3 = prog:read_u16(rb + 6)
		if code ~= 0 and code < 0x1000 then
			candidates = candidates + 1
		end
		if (w0 ~= 0) or (w1 ~= 0) or (prog:read_u16(rb+4) ~= 0) or (w3 ~= 0) then
			rawnonzero = rawnonzero + 1
		end
	end

	local s = scene_entry(scene)
	s.frames = s.frames + 1
	s.last_frame = frame_count
	if candidates > s.max_candidates then s.max_candidates = candidates end
	if rawnonzero > s.max_rawnonzero then s.max_rawnonzero = rawnonzero end

	if candidates > global_max_candidates then
		global_max_candidates = candidates
		global_max_candidate_scene = scene
		global_max_candidate_frame = frame_count
	end
	if on_scan_path and candidates > scan_path_max_candidates then
		scan_path_max_candidates = candidates
	end

	local pw = prog:read_u16(PROD_WRITE) & 0xFFFF
	local po = prog:read_u16(PROD_OOB) & 0xFFFF
	local em = prog:read_u16(EMITTED) & 0xFFFF
	local dr = prog:read_u16(DRAWABLE) & 0xFFFF
	if pw > max_prod_write then max_prod_write = pw end
	if po > max_prod_oob then max_prod_oob = po end
	if em > max_emitted then max_emitted = em end
	if dr > max_drawable then max_drawable = dr end
end

local function write_summary()
	local root = os.getenv("GENESISTAN_ROOT") or "."
	local dir = root .. "/build/mame/home/pc090oj_deadcode_audit"
	os.execute("mkdir -p '" .. dir .. "'")
	local fh = io.open(dir .. "/summary.txt", "w")
	if not fh then return end
	fh:write(string.format("PC090OJ dead-code audit  %s\n", os.date("%Y-%m-%d %H:%M:%S")))
	fh:write(string.format("total_frames=%d\n", frame_count))
	fh:write("\n== scenes visited (transitions) ==\n")
	for _, line in ipairs(scene_seq) do fh:write(line .. "\n") end
	fh:write("\n== per-scene object_ram census ==\n")
	fh:write("scene  frames  max_drawable_candidate_codes  max_raw_nonzero_records  first_frame  last_frame\n")
	local ids = {}
	for id in pairs(scene_stats) do table.insert(ids, id) end
	table.sort(ids)
	for _, id in ipairs(ids) do
		local s = scene_stats[id]
		fh:write(string.format("%-5d  %-6d  %-28d  %-23d  %-11d  %d\n",
			id, s.frames, s.max_candidates, s.max_rawnonzero, s.first_frame, s.last_frame))
	end
	fh:write("\n== scan-path exercise proof ==\n")
	fh:write(string.format("frontend_object_scan_path_frames=%d\n", scan_path_frames))
	fh:write(string.format("scan_path_max_drawable_candidate_codes=%d\n", scan_path_max_candidates))
	fh:write(string.format("item_page_active_frames=%d\n", titems_frames))
	fh:write(string.format("scene_gt1_frames=%d\n", scene_gt1_frames))
	fh:write("\n== global ==\n")
	fh:write(string.format("GLOBAL_MAX_DRAWABLE_CANDIDATE_CODES=%d (scene=%d frame=%d)\n",
		global_max_candidates, global_max_candidate_scene, global_max_candidate_frame))
	fh:write(string.format("max_producer_write_count=%d\n", max_prod_write))
	fh:write(string.format("max_producer_oob_count=%d\n", max_prod_oob))
	fh:write(string.format("max_emitted_count=%d (incl native HUD)\n", max_emitted))
	fh:write(string.format("max_drawable_count=%d\n", max_drawable))
	local verdict = (global_max_candidates == 0) and "PASS_OBJECT_RAM_ALWAYS_EMPTY" or "FAIL_LIVE_OBJECT_RAM_CONTENT"
	fh:write(string.format("VERDICT=%s\n", verdict))
	fh:close()
	emu.print_info("pc090oj_deadcode_audit: " .. verdict ..
		" global_max_candidates=" .. global_max_candidates)
end

emu.print_info("pc090oj_deadcode_audit loaded")

_G.pc090oj_audit_reset = emu.add_machine_reset_notifier(function ()
	cpu = manager.machine.devices[":maincpu"]
	if cpu then prog = cpu.spaces["program"] end
end)

_G.pc090oj_audit_stop = emu.add_machine_stop_notifier(function ()
	write_summary()
end)

_G.pc090oj_audit_frame = emu.add_machine_frame_notifier(function ()
	local ok, err = pcall(census_frame)
	if not ok then emu.print_error("pc090oj_audit frame error: " .. tostring(err)) end
end)

cpu = manager.machine.devices[":maincpu"]
if cpu then prog = cpu.spaces["program"] end
