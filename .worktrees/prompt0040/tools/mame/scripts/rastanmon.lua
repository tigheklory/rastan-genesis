local frame_count = 0
local log_path = nil
local snapshot_dir = nil
local last_mode_key = nil
local last_scene_label = nil
local last_state = nil
local palette_snapshot = {}
local scene_snapshots_written = {}
local error_logged = false
_G.rastanmon_reset_subscription = nil
_G.rastanmon_stop_subscription = nil
_G.rastanmon_frame_subscription = nil

local MODE_BASE = 0x10c000
local PAL_BASE = 0x200000
local PAL_BLOCK_SIZE = 0x20
local PAL_BLOCK_COUNT = 72
local HEARTBEAT_FRAMES = 300

local function is_rastan_set(name)
	return string.match(name or "", "^rastan") ~= nil
end

local function append_log(line)
	if not log_path then
		return
	end
	local fh = io.open(log_path, "a")
	if fh then
		fh:write(line)
		fh:write("\n")
		fh:close()
	end
end

local function file_safe(text)
	return (text or "unknown"):gsub("[^%w_%-%.]+", "_")
end

local function read_u16(space, addr)
	return space:read_u16(addr)
end

local function read_mode_state(space)
	return {
		page0 = read_u16(space, MODE_BASE + 0x0000),
		page2 = read_u16(space, MODE_BASE + 0x0002),
		mode4 = read_u16(space, MODE_BASE + 0x0004),
		credits = read_u16(space, MODE_BASE + 0x0012),
		stage = read_u16(space, MODE_BASE + 0x013e),
		player_sel = read_u16(space, MODE_BASE + 0x0118),
		player_latch_28 = read_u16(space, MODE_BASE + 0x0028),
		player_latch_2a = read_u16(space, MODE_BASE + 0x002a),
		timer_2c = read_u16(space, MODE_BASE + 0x002c),
		gameplay_flag_34 = read_u16(space, MODE_BASE + 0x0034),
		startup_sel_46 = read_u16(space, MODE_BASE + 0x0046),
		meta_timer_1392 = read_u16(space, 0x10d392),
		meta_enable_1394 = read_u16(space, 0x10d394),
		ctrl_13aa = read_u16(space, 0x10d3aa),
		ctrl_13ac = read_u16(space, 0x10d3ac),
		ctrl_13ae = read_u16(space, 0x10d3ae),
		ctrl_13b0 = read_u16(space, 0x10d3b0)
	}
end

local function mode4_label(mode4)
	if mode4 == 0 then
		return "frontend_title"
	elseif mode4 == 1 then
		return "wait_for_play"
	elseif mode4 >= 2 then
		return "runtime_transition_or_gameplay"
	end
	return "unknown"
end

local function ctrl13aa_label(val)
	if val >= 1 and val <= 8 then
		return "death_game_over_continue"
	elseif val >= 9 and val <= 13 then
		return "round_stage_presentation"
	end
	return "other"
end

local function scene_label(state)
	if state.mode4 == 0 then
		if state.credits > 0 then
			return "frontend_credit_ready"
		elseif state.page0 == 0 and state.page2 == 0 then
			return "frontend_title_or_attract"
		else
			return string.format("frontend_page_%04x_%04x", state.page0, state.page2)
		end
	elseif state.mode4 == 1 then
		return "wait_for_play"
	elseif state.mode4 >= 2 then
		if state.ctrl_13aa >= 1 and state.ctrl_13aa <= 8 then
			return string.format("death_game_over_continue_%02d", state.ctrl_13aa)
		elseif state.ctrl_13aa >= 9 and state.ctrl_13aa <= 13 then
			return string.format("round_stage_presentation_%02d", state.ctrl_13aa)
		elseif state.stage ~= 0 then
			return string.format("active_runtime_stage_%02x", state.stage)
		else
			return "runtime_other"
		end
	end
	return "unknown"
end

local function mode_key(state)
	return string.format(
		"%04x:%04x:%04x:%04x:%04x:%04x:%04x:%04x:%04x:%04x:%04x:%04x:%04x:%04x",
		state.page0,
		state.page2,
		state.mode4,
		state.credits,
		state.stage,
		state.player_sel,
		state.player_latch_28,
		state.player_latch_2a,
		state.gameplay_flag_34,
		state.startup_sel_46,
		state.meta_timer_1392,
		state.meta_enable_1394,
		state.ctrl_13aa,
		state.ctrl_13ac,
		state.ctrl_13ae,
		state.ctrl_13b0
	)
end

local function log_mode_change(state)
	append_log(string.format(
		"[frame %06d] mode scene=%s page0=%04x page2=%04x mode4=%04x(%s) credits=%04x stage=%04x sel118=%04x latch28=%04x latch2a=%04x t2c=%04x flag34=%04x sel46=%04x 1392=%04x 1394=%04x 13aa=%04x(%s) 13ac=%04x 13ae=%04x 13b0=%04x",
		frame_count,
		scene_label(state),
		state.page0,
		state.page2,
		state.mode4,
		mode4_label(state.mode4),
		state.credits,
		state.stage,
		state.player_sel,
		state.player_latch_28,
		state.player_latch_2a,
		state.timer_2c,
		state.gameplay_flag_34,
		state.startup_sel_46,
		state.meta_timer_1392,
		state.meta_enable_1394,
		state.ctrl_13aa,
		ctrl13aa_label(state.ctrl_13aa),
		state.ctrl_13ac,
		state.ctrl_13ae,
		state.ctrl_13b0
	))
end

local function log_heartbeat(state, active_blocks)
	append_log(string.format(
		"[frame %06d] heartbeat scene=%s mode4=%04x credits=%04x stage=%04x 13aa=%04x 13ac=%04x 13ae=%04x active_pal=%d",
		frame_count,
		scene_label(state),
		state.mode4,
		state.credits,
		state.stage,
		state.ctrl_13aa,
		state.ctrl_13ac,
		state.ctrl_13ae,
		#active_blocks
	))
end

local function read_palette_block(space, block_index)
	local words = {}
	local base = PAL_BASE + (block_index * PAL_BLOCK_SIZE)
	for i = 0, 15 do
		words[#words + 1] = read_u16(space, base + (i * 2))
	end
	return words
end

local function block_changed(old_block, new_block)
	if not old_block then
		return true
	end
	for i = 1, #new_block do
		if old_block[i] ~= new_block[i] then
			return true
		end
	end
	return false
end

local function block_is_all_zero(words)
	for i = 1, #words do
		if words[i] ~= 0 then
			return false
		end
	end
	return true
end

local function block_words_text(words)
	local out = {}
	for i = 1, #words do
		out[#out + 1] = string.format("%04x", words[i])
	end
	return table.concat(out, " ")
end

local function block_list_text(blocks)
	local out = {}
	for i = 1, #blocks do
		out[#out + 1] = string.format("%02x", blocks[i])
	end
	return table.concat(out, ",")
end

local function active_palette_blocks()
	local active = {}
	for block = 0, PAL_BLOCK_COUNT - 1 do
		local words = palette_snapshot[block]
		if words and (not block_is_all_zero(words)) then
			active[#active + 1] = block
		end
	end
	return active
end

local function scan_palette(space)
	local changed_blocks = {}
	for block = 0, PAL_BLOCK_COUNT - 1 do
		local words = read_palette_block(space, block)
		if block_changed(palette_snapshot[block], words) then
			if (not palette_snapshot[block]) and block_is_all_zero(words) then
				palette_snapshot[block] = words
			else
				palette_snapshot[block] = words
				changed_blocks[#changed_blocks + 1] = block
			end
		end
	end
	return changed_blocks, active_palette_blocks()
end

local function log_palette_details(changed_blocks)
	for i = 1, #changed_blocks do
		local block = changed_blocks[i]
		local words = palette_snapshot[block]
		local base = PAL_BASE + (block * PAL_BLOCK_SIZE)
		append_log(string.format(
			"[frame %06d] palblk %02x @%06x %s",
			frame_count,
			block,
			base,
			block_words_text(words)
		))
	end
end

local function write_scene_snapshot(scene, state, active_blocks)
	if (not snapshot_dir) or (#active_blocks == 0) then
		return
	end
	local name = string.format(
		"%s/frame_%06d_%s_stage_%04x_mode_%04x.txt",
		snapshot_dir,
		frame_count,
		file_safe(scene),
		state.stage,
		state.mode4
	)
	local fh = io.open(name, "w")
	if not fh then
		return
	end
	fh:write(string.format(
		"scene=%s frame=%d page0=%04x page2=%04x mode4=%04x credits=%04x stage=%04x sel118=%04x latch28=%04x latch2a=%04x t2c=%04x flag34=%04x sel46=%04x 1392=%04x 1394=%04x 13aa=%04x 13ac=%04x 13ae=%04x 13b0=%04x\n",
		scene,
		frame_count,
		state.page0,
		state.page2,
		state.mode4,
		state.credits,
		state.stage,
		state.player_sel,
		state.player_latch_28,
		state.player_latch_2a,
		state.timer_2c,
		state.gameplay_flag_34,
		state.startup_sel_46,
		state.meta_timer_1392,
		state.meta_enable_1394,
		state.ctrl_13aa,
		state.ctrl_13ac,
		state.ctrl_13ae,
		state.ctrl_13b0
	))
	for i = 1, #active_blocks do
		local block = active_blocks[i]
		fh:write(string.format("palblk %02x @%06x %s\n", block, PAL_BASE + (block * PAL_BLOCK_SIZE), block_words_text(palette_snapshot[block])))
	end
	fh:close()
end

local function log_field_changes(prev, state)
	if not prev then
		return
	end
	local fields = {
		{"credits", "credits"},
		{"stage", "stage"},
		{"page0", "page0"},
		{"page2", "page2"},
		{"mode4", "mode4"},
		{"player_latch_28", "latch28"},
		{"player_latch_2a", "latch2a"},
		{"gameplay_flag_34", "flag34"},
		{"startup_sel_46", "sel46"},
		{"meta_timer_1392", "1392"},
		{"meta_enable_1394", "1394"},
		{"ctrl_13aa", "13aa"},
		{"ctrl_13ac", "13ac"},
		{"ctrl_13ae", "13ae"},
		{"ctrl_13b0", "13b0"}
	}
	for i = 1, #fields do
		local key = fields[i][1]
		local label = fields[i][2]
		if prev[key] ~= state[key] then
			append_log(string.format(
				"[frame %06d] event %s %04x -> %04x",
				frame_count,
				label,
				prev[key],
				state[key]
			))
		end
	end
end

if not is_rastan_set(emu.romname()) then
	return
end

local home = manager.machine.options.entries.homepath:value():match("([^;]+)")
if not home or home == "" then
	home = "."
end
log_path = home .. "/rastanmon/rastan_monitor.log"
snapshot_dir = home .. "/rastanmon/snapshots"
append_log(string.format("==== rastanmon start rom=%s game=%s ====", emu.romname(), emu.gamename()))
emu.print_info("rastanmon script loaded")

_G.rastanmon_reset_subscription = emu.add_machine_reset_notifier(function ()
	frame_count = 0
	last_mode_key = nil
	last_scene_label = nil
	last_state = nil
	palette_snapshot = {}
	scene_snapshots_written = {}
	append_log("---- reset ----")
end)

_G.rastanmon_stop_subscription = emu.add_machine_stop_notifier(function ()
	append_log("==== rastanmon stop ====")
end)

_G.rastanmon_frame_subscription = emu.add_machine_frame_notifier(function ()
	local ok, err = pcall(function ()
		frame_count = frame_count + 1
		local cpu = manager.machine.devices[":maincpu"]
		if not cpu then
			return
		end
		local space = cpu.spaces["program"]
		if not space then
			return
		end

		local state = read_mode_state(space)
		local key = mode_key(state)
		local scene = scene_label(state)
		if key ~= last_mode_key then
			log_field_changes(last_state, state)
			last_mode_key = key
			log_mode_change(state)
		end

		local changed_blocks, active_blocks = scan_palette(space)
		if #changed_blocks > 0 then
			append_log(string.format(
				"[frame %06d] palchg count=%d blocks=%s active=%s",
				frame_count,
				#changed_blocks,
				block_list_text(changed_blocks),
				block_list_text(active_blocks)
			))
			if (#changed_blocks <= 8) or (scene ~= last_scene_label) or (not scene_snapshots_written[scene]) then
				log_palette_details(changed_blocks)
			end
		end
		if scene ~= last_scene_label then
			append_log(string.format("[frame %06d] scene %s", frame_count, scene))
			last_scene_label = scene
		end
		if (#active_blocks > 0) and (not scene_snapshots_written[scene]) then
			write_scene_snapshot(scene, state, active_blocks)
			scene_snapshots_written[scene] = true
		end
		if (frame_count % HEARTBEAT_FRAMES) == 0 then
			log_heartbeat(state, active_blocks)
		end
		last_state = state
	end)

	if (not ok) and (not error_logged) then
		error_logged = true
		append_log("ERROR " .. tostring(err))
		emu.print_error("rastanmon: " .. tostring(err))
	end
end)
