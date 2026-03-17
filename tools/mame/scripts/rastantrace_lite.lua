local frame_count = 0
local log_path = nil
local summary_path = nil
local error_logged = false
local cpu = nil
local prog = nil
local last_scene = nil
local last_exec_label = nil
local last_pc = nil
local scan_index = 1

_G.rastantrace_lite_reset_subscription = nil
_G.rastantrace_lite_stop_subscription = nil
_G.rastantrace_lite_frame_subscription = nil

local MODE_BASE = 0x10c000
local SAMPLE_PC_EVERY = 60
local WINDOW_SCAN_STRIDE = 5

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

local WATCH_WINDOWS = {
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
local window_state = {}

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
	append_log(string.format("[frame %06d] pc=%06x exec=%s", frame_count, pc or 0, label or "other"))
end

local function window_signature(window)
	local addr = window.start_addr
	local sig = 0
	local words = 0
	local first_nonzero_addr = nil
	local first_nonzero_value = nil

	while addr <= window.end_addr do
		local value = read_u16(prog, addr)
		sig = ((sig * 131) + value) % 0x100000000
		words = words + 1
		if (not first_nonzero_addr) and (value ~= 0) then
			first_nonzero_addr = addr
			first_nonzero_value = value
		end
		addr = addr + 2
	end

	return {
		sig = sig,
		words = words,
		first_nonzero_addr = first_nonzero_addr,
		first_nonzero_value = first_nonzero_value,
	}
end

local function ensure_window_state(name)
	if not window_state[name] then
		window_state[name] = {
			primed = false,
			last_sig = nil,
			change_count = 0,
			first_change_frame = nil,
			last_change_frame = nil,
			first_change_pc = nil,
			last_change_pc = nil,
			first_nonzero_addr = nil,
			first_nonzero_value = nil,
		}
	end
	return window_state[name]
end

local function scan_one_window()
	local window = WATCH_WINDOWS[scan_index]
	local sig
	local state
	local pc

	if not prog then
		return
	end

	sig = window_signature(window)
	state = ensure_window_state(window.name)
	pc = current_pc() or 0

	if not state.primed then
		state.primed = true
		state.last_sig = sig.sig
		state.first_nonzero_addr = sig.first_nonzero_addr
		state.first_nonzero_value = sig.first_nonzero_value
	elseif state.last_sig ~= sig.sig then
		state.change_count = state.change_count + 1
		if not state.first_change_frame then
			state.first_change_frame = frame_count
			state.first_change_pc = pc
			append_log(string.format(
				"[frame %06d] first_window_change %s pc=%06x first_nonzero_addr=%s first_nonzero_value=%s",
				frame_count,
				window.name,
				pc,
				sig.first_nonzero_addr and string.format("%06x", sig.first_nonzero_addr) or "-",
				sig.first_nonzero_value and string.format("%04x", sig.first_nonzero_value) or "-"
			))
		else
			append_log(string.format("[frame %06d] window_change %s pc=%06x", frame_count, window.name, pc))
		end
		state.last_change_frame = frame_count
		state.last_change_pc = pc
		state.last_sig = sig.sig
	end

	scan_index = scan_index + 1
	if scan_index > #WATCH_WINDOWS then
		scan_index = 1
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

	fh:write("\n[windows]\n")
	for i = 1, #WATCH_WINDOWS do
		local window = WATCH_WINDOWS[i]
		local state = ensure_window_state(window.name)
		fh:write(string.format(
			"%s changes=%d first_change_frame=%s first_change_pc=%s last_change_frame=%s last_change_pc=%s first_nonzero_addr=%s first_nonzero_value=%s\n",
			window.name,
			state.change_count,
			state.first_change_frame or "-",
			state.first_change_pc and string.format("%06x", state.first_change_pc) or "-",
			state.last_change_frame or "-",
			state.last_change_pc and string.format("%06x", state.last_change_pc) or "-",
			state.first_nonzero_addr and string.format("%06x", state.first_nonzero_addr) or "-",
			state.first_nonzero_value and string.format("%04x", state.first_nonzero_value) or "-"
		))
	end

	fh:close()
end

local function reset_state()
	frame_count = 0
	last_scene = nil
	last_exec_label = nil
	last_pc = nil
	scan_index = 1
	exec_hits = {}
	window_state = {}
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
	append_log("arm: lite trace state armed")
end

if not is_rastan_set(emu.romname()) then
	emu.print_info("rastantrace_lite: skipped for rom " .. tostring(emu.romname()))
	return
end

local home = manager.machine.options.entries.homepath:value():match("([^;]+)")
local trace_dir = home .. "/rastantrace_lite"
os.execute(string.format("mkdir -p '%s'", trace_dir))
log_path = trace_dir .. "/rastan_exec_trace_lite.log"
summary_path = trace_dir .. "/rastan_exec_summary_lite.txt"

append_log(string.format("==== rastantrace_lite start rom=%s game=%s ====", emu.romname(), emu.gamename()))
emu.print_info("rastantrace_lite script loaded")

_G.rastantrace_lite_reset_subscription = emu.add_machine_reset_notifier(function ()
	reset_state()
	arm_trace()
end)

_G.rastantrace_lite_stop_subscription = emu.add_machine_stop_notifier(function ()
	write_summary()
	append_log("==== rastantrace_lite stop ====")
end)

_G.rastantrace_lite_frame_subscription = emu.add_machine_frame_notifier(function ()
	local ok, err = pcall(function ()
		local pc
		local exec_entry
		local exec_label
		local state
		local scene
		local i

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

		for i = 1, WINDOW_SCAN_STRIDE do
			scan_one_window()
		end

		last_pc = pc
	end)

	if not ok and not error_logged then
		error_logged = true
		append_log("error: " .. tostring(err))
		emu.print_error("rastantrace_lite: " .. tostring(err))
	end
end)

reset_state()
arm_trace()
