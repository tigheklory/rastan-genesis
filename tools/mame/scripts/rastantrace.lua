local frame_count = 0
local log_path = nil
local summary_path = nil
local error_logged = false
local cpu = nil
local prog = nil
local tap_refs = {}
local window_snapshots = {}
local last_scene = nil
local last_exec_label = nil
local last_pc = nil
local last_state = nil

_G.rastantrace_reset_subscription = nil
_G.rastantrace_stop_subscription = nil
_G.rastantrace_frame_subscription = nil

local MODE_BASE = 0x10c000
local SAMPLE_PC_EVERY = 30

local EXEC_RANGES = {
	{name = "startup_common", start_addr = 0x03AE86, end_addr = 0x03B05B},
	{name = "helper_title_credit_trim", start_addr = 0x03A552, end_addr = 0x03A565},
	{name = "frontend_title_cluster", start_addr = 0x03A79C, end_addr = 0x03AB58},
	{name = "helper_fill_words", start_addr = 0x03AD3C, end_addr = 0x03AD4B},
	{name = "helper_d000_init", start_addr = 0x03AD72, end_addr = 0x03ADBB},
	{name = "helper_cfg_copy", start_addr = 0x03B0C2, end_addr = 0x03B102},
	{name = "title_init_block", start_addr = 0x03B098, end_addr = 0x03C483},
	{name = "helper_200000_init", start_addr = 0x03B9F8, end_addr = 0x03BA87},
	{name = "helper_3f084_reg_write", start_addr = 0x03F084, end_addr = 0x03F09B},
	{name = "table_4eaf6", start_addr = 0x04EAF6, end_addr = 0x04F0F5},
	{name = "table_4fe62", start_addr = 0x04FE62, end_addr = 0x04FE81},
	{name = "helper_5b512_rts", start_addr = 0x05B512, end_addr = 0x05B519},
	{name = "helper_5ffa2_5ffb2", start_addr = 0x05FFA2, end_addr = 0x05FFFF},
}

local TOUCH_WINDOWS = {
	{name = "workram_10c000", start_addr = 0x10C000, end_addr = 0x10FFFF},
	{name = "palette_200000", start_addr = 0x200000, end_addr = 0x203FFF},
	{name = "tile_c00000", start_addr = 0xC00000, end_addr = 0xC03FFF},
	{name = "tile_c04000", start_addr = 0xC04000, end_addr = 0xC07FFF},
	{name = "tile_c08000", start_addr = 0xC08000, end_addr = 0xC0BFFF},
	{name = "tile_c0c000", start_addr = 0xC0C000, end_addr = 0xC0FFFF},
	{name = "c20000", start_addr = 0xC20000, end_addr = 0xC20003},
	{name = "c40000", start_addr = 0xC40000, end_addr = 0xC40003},
	{name = "c50000", start_addr = 0xC50000, end_addr = 0xC50001},
	{name = "d00000", start_addr = 0xD00000, end_addr = 0xD007FF},
	{name = "d01bfe", start_addr = 0xD01BFE, end_addr = 0xD01BFF},
	{name = "reg_350008", start_addr = 0x350008, end_addr = 0x350009},
	{name = "reg_380000", start_addr = 0x380000, end_addr = 0x380001},
	{name = "dip_390009", start_addr = 0x390008, end_addr = 0x390009},
	{name = "dip_39000b", start_addr = 0x39000A, end_addr = 0x39000B},
	{name = "reg_3c0000", start_addr = 0x3C0000, end_addr = 0x3C0001},
	{name = "reg_3e0001", start_addr = 0x3E0000, end_addr = 0x3E0001},
	{name = "reg_3e0003", start_addr = 0x3E0002, end_addr = 0x3E0003},
}

local exec_hits = {}
local touch_stats = {}

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

local function is_rastan_set(name)
	return string.match(name or "", "^rastan") ~= nil
end

local function read_u16(space, addr)
	return space:read_u16(addr)
end

local function file_safe(text)
	return (text or "unknown"):gsub("[^%w_%-%.]+", "_")
end

local function current_pc()
	if not cpu or not cpu.state or not cpu.state["PC"] then
		return nil
	end
	return cpu.state["PC"].value
end

local function find_exec_range(pc)
	local i

	if not pc then
		return nil
	end

	for i = 1, #EXEC_RANGES do
		local entry = EXEC_RANGES[i]
		if pc >= entry.start_addr and pc <= entry.end_addr then
			return entry
		end
	end

	return nil
end

local function read_mode_state(space)
	return {
		page0 = read_u16(space, MODE_BASE + 0x0000),
		page2 = read_u16(space, MODE_BASE + 0x0002),
		mode4 = read_u16(space, MODE_BASE + 0x0004),
		credits = read_u16(space, MODE_BASE + 0x0012),
		stage = read_u16(space, MODE_BASE + 0x013E),
		ctrl_13aa = read_u16(space, 0x10D3AA),
		ctrl_13ac = read_u16(space, 0x10D3AC),
		ctrl_13ae = read_u16(space, 0x10D3AE),
		ctrl_13b0 = read_u16(space, 0x10D3B0),
	}
end

local function scene_label(state)
	if state.mode4 == 0 then
		if state.credits > 0 then
			return "frontend_credit_ready"
		elseif state.page0 == 0 and state.page2 == 0 then
			return "frontend_title_or_attract"
		else
			return string.format("frontend_%04x_%04x", state.page0, state.page2)
		end
	elseif state.mode4 == 1 then
		return "wait_for_play"
	elseif state.ctrl_13aa >= 1 and state.ctrl_13aa <= 8 then
		return string.format("death_continue_%02d", state.ctrl_13aa)
	elseif state.ctrl_13aa >= 9 and state.ctrl_13aa <= 13 then
		return string.format("round_presentation_%02d", state.ctrl_13aa)
	elseif state.stage ~= 0 then
		return string.format("runtime_%04x", state.stage)
	else
		return string.format("runtime_mode_%04x", state.mode4)
	end
end

local function log_scene_change(state, pc)
	local scene = scene_label(state)
	append_log(string.format(
		"[frame %06d] scene=%s pc=%06x page0=%04x page2=%04x mode4=%04x credits=%04x stage=%04x 13aa=%04x 13ac=%04x 13ae=%04x 13b0=%04x",
		frame_count,
		scene,
		pc or 0,
		state.page0,
		state.page2,
		state.mode4,
		state.credits,
		state.stage,
		state.ctrl_13aa,
		state.ctrl_13ac,
		state.ctrl_13ae,
		state.ctrl_13b0
	))
end

local function log_pc_sample(pc, label)
	append_log(string.format(
		"[frame %06d] pc=%06x exec=%s",
		frame_count,
		pc or 0,
		label or "other"
	))
end

local function ensure_touch_stat(name)
	if not touch_stats[name] then
		touch_stats[name] = {
			read_count = 0,
			write_count = 0,
			first_read_pc = nil,
			first_write_pc = nil,
			last_read_pc = nil,
			last_write_pc = nil,
			first_read_frame = nil,
			first_write_frame = nil,
			last_read_frame = nil,
			last_write_frame = nil,
			read_examples = {},
			write_examples = {},
			tap_mode = "unavailable",
			poll_mode = "disabled",
			poll_change_count = 0,
			first_poll_frame = nil,
			last_poll_frame = nil,
			first_poll_pc = nil,
			last_poll_pc = nil,
			poll_examples = {},
		}
	end
	return touch_stats[name]
end

local function push_example(list_ref, text)
	if #list_ref < 8 then
		list_ref[#list_ref + 1] = text
	end
end

local function record_touch(name, mode, addr, data, mem_mask)
	local stat = ensure_touch_stat(name)
	local pc = current_pc() or 0
	local example = string.format("frame=%d pc=%06x addr=%06x data=%04x mask=%04x", frame_count, pc, addr, data or 0, mem_mask or 0)

	if mode == "read" then
		stat.read_count = stat.read_count + 1
		if not stat.first_read_pc then
			stat.first_read_pc = pc
			stat.first_read_frame = frame_count
			append_log(string.format("[frame %06d] first_read %s pc=%06x addr=%06x data=%04x mask=%04x", frame_count, name, pc, addr, data or 0, mem_mask or 0))
		end
		stat.last_read_pc = pc
		stat.last_read_frame = frame_count
		push_example(stat.read_examples, example)
	else
		stat.write_count = stat.write_count + 1
		if not stat.first_write_pc then
			stat.first_write_pc = pc
			stat.first_write_frame = frame_count
			append_log(string.format("[frame %06d] first_write %s pc=%06x addr=%06x data=%04x mask=%04x", frame_count, name, pc, addr, data or 0, mem_mask or 0))
		end
		stat.last_write_pc = pc
		stat.last_write_frame = frame_count
		push_example(stat.write_examples, example)
	end
end

local function install_window_taps()
	local i

	if not prog then
		return
	end

	tap_refs = {}
	for i = 1, #TOUCH_WINDOWS do
		local window = TOUCH_WINDOWS[i]
		local stat = ensure_touch_stat(window.name)
		stat.tap_mode = "failed"

		local ok_read, read_tap = pcall(function()
			return prog:install_read_tap(
				window.start_addr,
				window.end_addr,
				"rastantrace_" .. window.name .. "_r",
				function(offset, data, mem_mask)
					record_touch(window.name, "read", offset, data, mem_mask)
					return data
				end
			)
		end)

		local ok_write, write_tap = pcall(function()
			return prog:install_write_tap(
				window.start_addr,
				window.end_addr,
				"rastantrace_" .. window.name .. "_w",
				function(offset, data, mem_mask)
					record_touch(window.name, "write", offset, data, mem_mask)
					return data
				end
			)
		end)

		if ok_read then
			tap_refs[#tap_refs + 1] = read_tap
		end
		if ok_write then
			tap_refs[#tap_refs + 1] = write_tap
		end

		if ok_read or ok_write then
			stat.tap_mode = "installed"
		end
	end
end

local function snapshot_window(window)
	local words = {}
	local addr = window.start_addr

	while addr <= window.end_addr do
		words[#words + 1] = read_u16(prog, addr)
		addr = addr + 2
	end

	return words
end

local function record_polled_change(name, addr, before, after)
	local stat = ensure_touch_stat(name)
	local pc = current_pc() or 0
	local example = string.format("frame=%d pc=%06x addr=%06x before=%04x after=%04x", frame_count, pc, addr, before or 0, after or 0)

	stat.poll_mode = "diff"
	stat.poll_change_count = stat.poll_change_count + 1
	if not stat.first_poll_frame then
		stat.first_poll_frame = frame_count
		stat.first_poll_pc = pc
		append_log(string.format("[frame %06d] first_diff %s pc=%06x addr=%06x before=%04x after=%04x", frame_count, name, pc, addr, before or 0, after or 0))
	end
	stat.last_poll_frame = frame_count
	stat.last_poll_pc = pc
	push_example(stat.poll_examples, example)
end

local function poll_window_changes()
	local i

	if not prog then
		return
	end

	for i = 1, #TOUCH_WINDOWS do
		local window = TOUCH_WINDOWS[i]
		local before = window_snapshots[window.name]
		local after = snapshot_window(window)
		local stat = ensure_touch_stat(window.name)
		local idx

		if not before then
			window_snapshots[window.name] = after
			if stat.poll_mode == "disabled" then
				stat.poll_mode = "primed"
			end
		else
			for idx = 1, #after do
				if before[idx] ~= after[idx] then
					record_polled_change(window.name, window.start_addr + ((idx - 1) * 2), before[idx], after[idx])
				end
			end
			window_snapshots[window.name] = after
		end
	end
end

local function bump_exec_hit(label, pc)
	local hit = exec_hits[label]
	if not hit then
		hit = {
			count = 0,
			first_frame = frame_count,
			last_frame = frame_count,
			first_pc = pc,
			last_pc = pc,
		}
		exec_hits[label] = hit
	end
	hit.count = hit.count + 1
	hit.last_frame = frame_count
	hit.last_pc = pc
end

local function write_summary()
	local fh
	local i

	if not summary_path then
		return
	end

	fh = io.open(summary_path, "w")
	if not fh then
		return
	end

	fh:write(string.format("frames=%d\n", frame_count))
	fh:write("\n[execution_ranges]\n")
	for i = 1, #EXEC_RANGES do
		local entry = EXEC_RANGES[i]
		local hit = exec_hits[entry.name]
		if hit then
			fh:write(string.format(
				"%s count=%d first_frame=%d last_frame=%d first_pc=%06x last_pc=%06x\n",
				entry.name,
				hit.count,
				hit.first_frame,
				hit.last_frame,
				hit.first_pc or 0,
				hit.last_pc or 0
			))
		else
			fh:write(string.format("%s count=0\n", entry.name))
		end
	end

	fh:write("\n[touch_windows]\n")
	for i = 1, #TOUCH_WINDOWS do
		local window = TOUCH_WINDOWS[i]
		local stat = ensure_touch_stat(window.name)
		fh:write(string.format(
			"%s mode=%s reads=%d writes=%d first_read_pc=%s first_write_pc=%s last_read_pc=%s last_write_pc=%s\n",
			window.name,
			stat.tap_mode,
			stat.read_count,
			stat.write_count,
			stat.first_read_pc and string.format("%06x", stat.first_read_pc) or "-",
			stat.first_write_pc and string.format("%06x", stat.first_write_pc) or "-",
			stat.last_read_pc and string.format("%06x", stat.last_read_pc) or "-",
			stat.last_write_pc and string.format("%06x", stat.last_write_pc) or "-"
		))
		for _, example in ipairs(stat.read_examples) do
			fh:write("  read " .. example .. "\n")
		end
		for _, example in ipairs(stat.write_examples) do
			fh:write("  write " .. example .. "\n")
		end
	end

	fh:close()
end

local function reset_state()
	frame_count = 0
	last_scene = nil
	last_exec_label = nil
	last_pc = nil
	last_state = nil
	exec_hits = {}
	touch_stats = {}
	tap_refs = {}
	window_snapshots = {}
	error_logged = false
end

local function arm_trace()
	cpu = manager.machine.devices[":maincpu"]
	if not cpu then
		append_log("arm: maincpu not found")
		return
	end
	prog = cpu.spaces["program"]
	if not prog then
		append_log("arm: maincpu program space not found")
		return
	end
	install_window_taps()
	append_log("arm: trace state armed")
end

if not is_rastan_set(emu.romname()) then
	emu.print_info("rastantrace: skipped for rom " .. tostring(emu.romname()))
	return
end

local home = manager.machine.options.entries.homepath:value():match("([^;]+)")
local trace_dir = home .. "/rastantrace"
os.execute(string.format("mkdir -p '%s'", trace_dir))
log_path = trace_dir .. "/rastan_exec_trace.log"
summary_path = trace_dir .. "/rastan_exec_summary.txt"

append_log(string.format("==== rastantrace start rom=%s game=%s ====", emu.romname(), emu.gamename()))
emu.print_info("rastantrace script loaded")

_G.rastantrace_reset_subscription = emu.add_machine_reset_notifier(function ()
	reset_state()
	arm_trace()
end)

_G.rastantrace_stop_subscription = emu.add_machine_stop_notifier(function ()
	write_summary()
	append_log("==== rastantrace stop ====")
end)

_G.rastantrace_frame_subscription = emu.add_machine_frame_notifier(function ()
	local ok, err = pcall(function ()
		local pc
		local exec_entry
		local exec_label
		local state
		local scene

		frame_count = frame_count + 1
		if not cpu or not prog then
			return
		end

		pc = current_pc()
		exec_entry = find_exec_range(pc)
		exec_label = exec_entry and exec_entry.name or "other"
		bump_exec_hit(exec_label, pc or 0)

		state = read_mode_state(prog)
		scene = scene_label(state)
		poll_window_changes()

		if scene ~= last_scene then
			log_scene_change(state, pc)
			last_scene = scene
		end

		if exec_label ~= last_exec_label then
			append_log(string.format("[frame %06d] exec_enter pc=%06x range=%s", frame_count, pc or 0, exec_label))
			last_exec_label = exec_label
		end

		if (pc ~= last_pc) and ((frame_count % SAMPLE_PC_EVERY) == 0) then
			log_pc_sample(pc, exec_label)
		end

		last_pc = pc
		last_state = state
	end)

	if not ok and not error_logged then
		error_logged = true
		append_log("error: " .. tostring(err))
		emu.print_error("rastantrace: " .. tostring(err))
	end
end)

reset_state()
arm_trace()
