local frame_count = 0
local log_path = nil
local summary_path = nil
local agents_log_path = nil
local error_logged = false
local cpu = nil
local prog = nil
local last_pc = nil
local last_exec_label = nil
local tap_refs = {}
local write_watch_stats = {}

_G.genesistrace_reset_subscription = nil
_G.genesistrace_stop_subscription = nil
_G.genesistrace_frame_subscription = nil

local SAMPLE_PC_EVERY = 30
local SAMPLE_WINDOW_EVERY = 30
local SYMBOL_SAMPLE_EVERY = 1
local RESET_HELPER_PC_0 = 0x039FA8
local RESET_HELPER_PC_1 = 0x03A1A8
local DISPATCH_PC_0 = 0x03A05C
local DISPATCH_PC_1 = 0x03A06A

local EXEC_BASES = {0x000000, 0x000200, 0x200000}
local EXEC_RANGE_TEMPLATES = {
	{name = "startup_common", start_addr = 0x03AE86, end_addr = 0x03B05B},
	{name = "helper_fill_words", start_addr = 0x03AD3C, end_addr = 0x03AD4B},
	{name = "helper_d000_init", start_addr = 0x03AD72, end_addr = 0x03ADBB},
	{name = "helper_display_control", start_addr = 0x03ADD8, end_addr = 0x03AE84},
	{name = "frontend_core", start_addr = 0x039F80, end_addr = 0x03AD3B},
	{name = "title_init_block", start_addr = 0x03B098, end_addr = 0x03C483},
	{name = "helper_frontend_timers", start_addr = 0x03EEFA, end_addr = 0x03EFBC},
	{name = "helper_3f084_reg_write", start_addr = 0x03F084, end_addr = 0x03F09B},
	{name = "helper_55ca2_dispatch", start_addr = 0x055CA2, end_addr = 0x055DDB},
	{name = "helper_5b512_rts", start_addr = 0x05B512, end_addr = 0x05B519},
}

local EXEC_RANGES = {}
local exec_hits = {}
local window_hits = {}
local symbol_watches = {}
local arcade_workram_base = nil
local exception_handlers = {}
local last_exception_pc = nil
local last_exception_frame = -999999
local unmapped_address_set = {}
local unmapped_address_list = {}

local WINDOW_WATCHES = {
	{name = "wram_ff0000", start_addr = 0xFF0000, end_addr = 0xFFFFFF, stride = 0x80},
	{name = "io_a10000", start_addr = 0xA10000, end_addr = 0xA1001F, stride = 0x02},
	{name = "vdp_ports", start_addr = 0xC00000, end_addr = 0xC0001F, stride = 0x02},
	{name = "z80_ctrl", start_addr = 0xA11100, end_addr = 0xA11201, stride = 0x02},
}

local EXCEPTION_HANDLER_SYMBOLS = {
	"_Bus_Error",
	"_Address_Error",
	"_Illegal_Instruction",
	"_Zero_Divide",
	"_CHK_Instruction",
	"_TRAPV_Instruction",
	"_Privilege_Violation",
	"_Trace",
	"_Line_1010_Emulation",
	"_Line_1111_Emulation",
}

local FALLBACK_EXCEPTION_UI_START = 0x214000
local FALLBACK_EXCEPTION_UI_END = 0x216FFF

local WRITE_TAP_WINDOWS = {
	{name = "vdp_ports_live", start_addr = 0xC00000, end_addr = 0xC0001F},
	{name = "reg_c50000_live", start_addr = 0xC50000, end_addr = 0xC50001},
}

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

local function record_unmapped_address(addr)
	if not addr then
		return
	end
	local key = string.format("0x%08X", addr & 0xFFFFFFFF)
	if unmapped_address_set[key] then
		return
	end
	unmapped_address_set[key] = true
	table.insert(unmapped_address_list, key)
end

local function normalize_24(addr)
	return addr & 0xFFFFFF
end

local function find_repo_root()
	local home = manager.machine.options.entries.homepath:value():match("([^;]+)")
	local env_root = os.getenv("GENESISTAN_ROOT")
	if env_root and #env_root > 0 then
		return env_root, home
	end

	if home then
		local root = home:gsub("/build/mame/home$", "")
		if root ~= home then
			return root, home
		end
	end

	return ".", home
end

local function load_symbol_map(symbol_path)
	local map = {}
	local fh = io.open(symbol_path, "r")
	if not fh then
		return map
	end

	for line in fh:lines() do
		local addr_text, name = line:match("^%s*([0-9A-Fa-f]+)%s+%S+%s+(%S+)")
		if addr_text and name then
			local addr = tonumber(addr_text, 16)
			if addr then
				map[name] = normalize_24(addr)
			end
		end
	end

	fh:close()
	return map
end

local function read_state_u32(name)
	if not cpu or not cpu.state or not cpu.state[name] then
		return nil
	end
	return cpu.state[name].value & 0xFFFFFFFF
end

local function setup_exec_ranges()
	local i
	local j
	for i = 1, #EXEC_RANGE_TEMPLATES do
		for j = 1, #EXEC_BASES do
			local base = EXEC_BASES[j]
			local tpl = EXEC_RANGE_TEMPLATES[i]
			table.insert(EXEC_RANGES, {
				name = string.format("%s@%06x", tpl.name, base),
				start_addr = tpl.start_addr + base,
				end_addr = tpl.end_addr + base,
			})
		end
	end
end

local function add_symbol_watch(name, addr, width)
	if not addr then
		return
	end
	table.insert(symbol_watches, {
		name = name,
		addr = addr,
		width = width or 16,
		last = nil,
		change_count = 0,
		first_change_frame = nil,
		last_change_frame = nil,
	})
end

local function add_project_symbol_watches(symbol_map)
	arcade_workram_base = symbol_map["genesistan_arcade_workram_words"]

	add_symbol_watch("startup_result_code", symbol_map["genesistan_startup_result_code"], 16)
	add_symbol_watch("dip1", symbol_map["genesistan_shadow_dip1"], 8)
	add_symbol_watch("dip2", symbol_map["genesistan_shadow_dip2"], 8)
	add_symbol_watch("in_390001", symbol_map["genesistan_shadow_input_390001"], 8)
	add_symbol_watch("in_390003", symbol_map["genesistan_shadow_input_390003"], 8)
	add_symbol_watch("in_390005", symbol_map["genesistan_shadow_input_390005"], 8)
	add_symbol_watch("in_390007", symbol_map["genesistan_shadow_input_390007"], 8)
	add_symbol_watch("reg_3e0001", symbol_map["genesistan_shadow_reg_3e0001"], 8)
	add_symbol_watch("reg_3e0003", symbol_map["genesistan_shadow_reg_3e0003"], 8)
	add_symbol_watch("reg_3c0000", symbol_map["genesistan_shadow_reg_3c0000"], 16)
	add_symbol_watch("reg_c50000", symbol_map["genesistan_shadow_reg_c50000"], 16)
	add_symbol_watch("reg_d01bfe", symbol_map["genesistan_shadow_reg_d01bfe"], 16)
	add_symbol_watch("reg_350008", symbol_map["genesistan_shadow_reg_350008"], 16)
	add_symbol_watch("reg_380000", symbol_map["genesistan_shadow_reg_380000"], 16)
	add_symbol_watch("c20000_0", symbol_map["genesistan_shadow_c20000_words"], 16)
	add_symbol_watch("c20000_1", symbol_map["genesistan_shadow_c20000_words"] and (symbol_map["genesistan_shadow_c20000_words"] + 2), 16)
	add_symbol_watch("c40000_0", symbol_map["genesistan_shadow_c40000_words"], 16)
	add_symbol_watch("c40000_1", symbol_map["genesistan_shadow_c40000_words"] and (symbol_map["genesistan_shadow_c40000_words"] + 2), 16)
	add_symbol_watch("workram_10c000", symbol_map["genesistan_arcade_workram_words"], 16)
	add_symbol_watch("shadow_c_window", symbol_map["genesistan_shadow_c_window_words"], 16)

	-- Probes derived from our shimmed 0x10c000 shadow base.
	if arcade_workram_base then
		add_symbol_watch("arcade_page0", arcade_workram_base + 0x0000, 16)
		add_symbol_watch("arcade_page2", arcade_workram_base + 0x0002, 16)
		add_symbol_watch("arcade_mode4", arcade_workram_base + 0x0004, 16)
		add_symbol_watch("arcade_credits", arcade_workram_base + 0x0012, 16)
		add_symbol_watch("arcade_stage", arcade_workram_base + 0x013E, 16)
		add_symbol_watch("arcade_flag_2a", arcade_workram_base + 0x002A, 16)
		add_symbol_watch("arcade_flag_34", arcade_workram_base + 0x0034, 16)
		add_symbol_watch("arcade_flag_3b", arcade_workram_base + 0x003B, 8)
		add_symbol_watch("arcade_mode_42", arcade_workram_base + 0x0042, 16)
	end
end

local function setup_exception_handlers(symbol_map)
	local i
	exception_handlers = {}
	for i = 1, #EXCEPTION_HANDLER_SYMBOLS do
		local name = EXCEPTION_HANDLER_SYMBOLS[i]
		local addr = symbol_map[name]
		if addr then
			exception_handlers[addr] = name
		end
	end
end

local function current_pc()
	if not cpu or not cpu.state or not cpu.state["PC"] then
		return nil
	end
	return normalize_24(cpu.state["PC"].value)
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

local function read_value(addr, width)
	if width == 8 then
		return prog:read_u8(addr)
	elseif width == 16 then
		return prog:read_u16(addr)
	else
		return prog:read_u32(addr)
	end
end

local function ensure_write_watch_stat(name)
	local stat = write_watch_stats[name]
	if not stat then
		stat = {
			count = 0,
			first_frame = nil,
			last_frame = nil,
			first_pc = nil,
			last_pc = nil,
			first_addr = nil,
			last_addr = nil,
			first_data = nil,
			last_data = nil,
			first_mask = nil,
			last_mask = nil,
		}
		write_watch_stats[name] = stat
	end
	return stat
end

local function log_live_write(window_name, addr, data, mem_mask)
	local pc = current_pc() or 0
	local stat = ensure_write_watch_stat(window_name)
	local is_first = (stat.count == 0)

	stat.count = stat.count + 1
	if is_first then
		stat.first_frame = frame_count
		stat.first_pc = pc
		stat.first_addr = addr
		stat.first_data = data
		stat.first_mask = mem_mask
	end
	stat.last_frame = frame_count
	stat.last_pc = pc
	stat.last_addr = addr
	stat.last_data = data
	stat.last_mask = mem_mask

	if is_first or addr == 0xC00008 or addr == 0xC50000 then
		append_log(string.format(
			"[frame %06d] live_write %s pc=%06x addr=%06x data=%04x mask=%04x count=%d",
			frame_count,
			window_name,
			pc,
			addr & 0xFFFFFF,
			data or 0,
			mem_mask or 0,
			stat.count
		))
	end
end

local function install_write_taps()
	local i

	tap_refs = {}
	for i = 1, #WRITE_TAP_WINDOWS do
		local window = WRITE_TAP_WINDOWS[i]
		local ok, tap = pcall(function()
			return prog:install_write_tap(
				window.start_addr,
				window.end_addr,
				"genesistrace_" .. window.name .. "_w",
				function(offset, data, mem_mask)
					log_live_write(window.name, offset, data, mem_mask)
				end
			)
		end)

		if ok and tap then
			tap_refs[#tap_refs + 1] = tap
		else
			append_log(string.format(
				"[frame %06d] install_write_tap_failed window=%s start=%06x end=%06x err=%s",
				frame_count,
				window.name,
				window.start_addr,
				window.end_addr,
				tostring(tap)
			))
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

local function sample_window(window)
	local addr = window.start_addr
	local sig = 0
	local words = 0
	local state = window_hits[window.name]

	while addr <= window.end_addr do
		local value = prog:read_u16(addr)
		sig = ((sig * 131) + value) % 0x100000000
		words = words + 1
		addr = addr + window.stride
	end

	if not state then
		state = {
			last_sig = sig,
			change_count = 0,
			first_change_frame = nil,
			last_change_frame = nil,
		}
		window_hits[window.name] = state
	elseif state.last_sig ~= sig then
		state.change_count = state.change_count + 1
		state.last_sig = sig
		if not state.first_change_frame then
			state.first_change_frame = frame_count
			append_log(string.format("[frame %06d] first_window_change %s", frame_count, window.name))
		else
			append_log(string.format("[frame %06d] window_change %s", frame_count, window.name))
		end
		state.last_change_frame = frame_count
	end
end

local function sample_symbols()
	local i
	for i = 1, #symbol_watches do
		local w = symbol_watches[i]
		local value = read_value(w.addr, w.width)
		if w.last == nil then
			w.last = value
		elseif w.last ~= value then
			w.change_count = w.change_count + 1
			if not w.first_change_frame then
				w.first_change_frame = frame_count
				append_log(string.format("[frame %06d] first_symbol_change %s addr=%06x %s->%s",
					frame_count, w.name, w.addr, string.format("%X", w.last), string.format("%X", value)))
			else
				append_log(string.format("[frame %06d] symbol_change %s addr=%06x %s->%s",
					frame_count, w.name, w.addr, string.format("%X", w.last), string.format("%X", value)))
			end
			w.last_change_frame = frame_count
			w.last = value
		end
	end
end

local function is_reset_helper_pc(pc)
	return pc == RESET_HELPER_PC_0 or pc == RESET_HELPER_PC_1
end

local function read_arcade_word(offset)
	local addr
	if arcade_workram_base then
		addr = arcade_workram_base + offset
	else
		addr = 0x10C000 + offset
	end
	return prog:read_u16(addr)
end

local function log_reset_helper_hit(pc)
	local page0 = read_arcade_word(0x0000)
	local page2 = read_arcade_word(0x0002)
	local mode4 = read_arcade_word(0x0004)
	local credits = read_arcade_word(0x0012)
	local stage = read_arcade_word(0x013E)
	local dip_a = prog:read_u8(0x390009)
	local dip_b = prog:read_u8(0x39000B)

	append_log(string.format(
		"[frame %06d] reset_helper_hit pc=%06x page0=%04x page2=%04x mode4=%04x credits=%04x stage=%04x dipA=%02x dipB=%02x",
		frame_count, pc, page0, page2, mode4, credits, stage, dip_a, dip_b))
end

local function log_exception_context(pc, name)
	local sp = read_state_u32("SP")
	local sr = read_state_u32("SR") or 0
	local usp = read_state_u32("USP") or 0
	local i

	append_log(string.format(
		"[frame %06d] exception_handler pc=%06x name=%s sr=%04x sp=%08x usp=%08x",
		frame_count, pc, name, sr, sp or 0, usp
	))

	if not sp then
		return
	end

	append_log(string.format(
		"[frame %06d] regs d0=%08x d1=%08x d2=%08x d3=%08x d4=%08x d5=%08x d6=%08x d7=%08x",
		frame_count,
		read_state_u32("D0") or 0,
		read_state_u32("D1") or 0,
		read_state_u32("D2") or 0,
		read_state_u32("D3") or 0,
		read_state_u32("D4") or 0,
		read_state_u32("D5") or 0,
		read_state_u32("D6") or 0,
		read_state_u32("D7") or 0
	))
	append_log(string.format(
		"[frame %06d] regs a0=%08x a1=%08x a2=%08x a3=%08x a4=%08x a5=%08x a6=%08x a7=%08x",
		frame_count,
		read_state_u32("A0") or 0,
		read_state_u32("A1") or 0,
		read_state_u32("A2") or 0,
		read_state_u32("A3") or 0,
		read_state_u32("A4") or 0,
		read_state_u32("A5") or 0,
		read_state_u32("A6") or 0,
		read_state_u32("A7") or 0
	))

	local w0 = prog:read_u16(sp + 0)
	local w1 = prog:read_u16(sp + 2)
	local w2 = prog:read_u16(sp + 4)
	local offset_guess = ((w1 << 16) | w2) & 0xFFFFFFFF
	record_unmapped_address(offset_guess)
	append_log(string.format(
		"[frame %06d] exception_guess fmt=%04x offset_guess=%08x",
		frame_count, w0, offset_guess
	))

	for i = 0, 15 do
		local off = i * 2
		append_log(string.format(
			"[frame %06d] stack +%02x = %04x",
			frame_count, off, prog:read_u16(sp + off)
		))
	end
end

local function append_agents_log_summary()
	local fh
	local final_pc = current_pc()
	local final_sp = read_state_u32("SP")
	local i

	if not agents_log_path then
		return
	end

	fh = io.open(agents_log_path, "a")
	if not fh then
		return
	end

	fh:write("\n")
	fh:write(string.format("### MAME Exit Summary (%s)\n", os.date("%Y-%m-%d %H:%M:%S")))
	fh:write(string.format("- Final PC: %s\n", final_pc and string.format("0x%06X", final_pc) or "unknown"))
	fh:write(string.format("- Stack Pointer (SP): %s\n", final_sp and string.format("0x%08X", final_sp) or "unknown"))
	if #unmapped_address_list == 0 then
		fh:write("- Unique Unmapped Memory Addresses: none\n")
	else
		fh:write(string.format("- Unique Unmapped Memory Addresses (%d): %s\n",
			#unmapped_address_list,
			table.concat(unmapped_address_list, ", ")))
	end
	fh:close()
end

local function is_dispatch_pc(pc)
	local i
	for i = 1, #EXEC_BASES do
		local base = EXEC_BASES[i]
		if pc == (DISPATCH_PC_0 + base) or pc == (DISPATCH_PC_1 + base) then
			return true
		end
	end
	return false
end

local function is_fallback_exception_ui_pc(pc)
	if not pc then
		return false
	end
	return pc >= FALLBACK_EXCEPTION_UI_START and pc <= FALLBACK_EXCEPTION_UI_END
end

local function log_dispatch_context(pc)
	local d0 = read_state_u32("D0") or 0
	local a0 = read_state_u32("A0") or 0
	local a5 = read_state_u32("A5") or 0
	local w0 = 0
	local w2 = 0
	local w4 = 0

	if arcade_workram_base then
		w0 = prog:read_u16(arcade_workram_base + 0x0000)
		w2 = prog:read_u16(arcade_workram_base + 0x0002)
		w4 = prog:read_u16(arcade_workram_base + 0x0004)
	end

	append_log(string.format(
		"[frame %06d] dispatch_probe pc=%06x d0=%08x a0=%08x a5=%08x wr0=%04x wr2=%04x wr4=%04x",
		frame_count, pc, d0, a0, a5, w0, w2, w4
	))
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
			fh:write(string.format("%s count=%d first_frame=%d last_frame=%d\n",
				entry.name, hit.count, hit.first_frame, hit.last_frame))
		else
			fh:write(string.format("%s count=0\n", entry.name))
		end
	end

	fh:write("\n[window_signatures]\n")
	for i = 1, #WINDOW_WATCHES do
		local window = WINDOW_WATCHES[i]
		local state = window_hits[window.name]
		if state then
			fh:write(string.format("%s changes=%d first_change=%s last_change=%s\n",
				window.name,
				state.change_count,
				state.first_change_frame or "-",
				state.last_change_frame or "-"))
		else
			fh:write(string.format("%s changes=0\n", window.name))
		end
	end

	fh:write("\n[symbol_watches]\n")
	for i = 1, #symbol_watches do
		local w = symbol_watches[i]
		fh:write(string.format(
			"%s addr=%06x width=%d changes=%d first_change=%s last_change=%s last=%s\n",
			w.name,
			w.addr,
			w.width,
			w.change_count,
			w.first_change_frame or "-",
			w.last_change_frame or "-",
			w.last and string.format("%X", w.last) or "-"
		))
	end

	fh:write("\n[live_write_watches]\n")
	for i = 1, #WRITE_TAP_WINDOWS do
		local window = WRITE_TAP_WINDOWS[i]
		local stat = write_watch_stats[window.name]
		if stat then
			fh:write(string.format(
				"%s count=%d first_frame=%s last_frame=%s first_pc=%s last_pc=%s first_addr=%s last_addr=%s first_data=%s last_data=%s first_mask=%s last_mask=%s\n",
				window.name,
				stat.count,
				stat.first_frame or "-",
				stat.last_frame or "-",
				stat.first_pc and string.format("%06X", stat.first_pc) or "-",
				stat.last_pc and string.format("%06X", stat.last_pc) or "-",
				stat.first_addr and string.format("%06X", stat.first_addr & 0xFFFFFF) or "-",
				stat.last_addr and string.format("%06X", stat.last_addr & 0xFFFFFF) or "-",
				stat.first_data and string.format("%04X", stat.first_data & 0xFFFF) or "-",
				stat.last_data and string.format("%04X", stat.last_data & 0xFFFF) or "-",
				stat.first_mask and string.format("%04X", stat.first_mask & 0xFFFF) or "-",
				stat.last_mask and string.format("%04X", stat.last_mask & 0xFFFF) or "-"
			))
		else
			fh:write(string.format("%s count=0\n", window.name))
		end
	end

	fh:close()
end

local function reset_state()
	frame_count = 0
	last_pc = nil
	last_exec_label = nil
	error_logged = false
	exec_hits = {}
	window_hits = {}
	symbol_watches = {}
	write_watch_stats = {}
	exception_handlers = {}
	last_exception_pc = nil
	last_exception_frame = -999999
	unmapped_address_set = {}
	unmapped_address_list = {}
end

local function arm_trace()
	local root
	local home
	local symbol_env
	local symbol_path
	local symbol_map

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

	root, home = find_repo_root()
	symbol_env = os.getenv("GENESISTAN_SYMBOLS")
	symbol_path = symbol_env and symbol_env or (root .. "/apps/rastan/out/symbol.txt")
	symbol_map = load_symbol_map(symbol_path)
	add_project_symbol_watches(symbol_map)
	setup_exception_handlers(symbol_map)
	install_write_taps()

	append_log(string.format("arm: genesistrace armed root=%s symbols=%s", root, symbol_path))
	append_log(string.format("arm: symbol_watches=%d", #symbol_watches))
	local pc = current_pc()
	if pc then
		append_log(string.format("arm: initial_pc=%06x", pc))
	end
end

setup_exec_ranges()

local root, home = find_repo_root()
local trace_dir = (home and (home .. "/genesistrace")) or (root .. "/build/mame/home/genesistrace")
agents_log_path = root .. "/AGENTS_LOG.md"
os.execute(string.format("mkdir -p '%s'", trace_dir))
log_path = trace_dir .. "/genesis_exec_trace.log"
summary_path = trace_dir .. "/genesis_exec_summary.txt"

do
	local fh = io.open(log_path, "w")
	if fh then
		fh:close()
	end
	local sfh = io.open(summary_path, "w")
	if sfh then
		sfh:close()
	end
end

append_log(string.format("==== genesistrace start rom=%s game=%s machine=%s ====",
	tostring(emu.romname()),
	tostring(emu.gamename()),
	tostring(manager.machine.system.name)))
emu.print_info("genesistrace script loaded")

_G.genesistrace_reset_subscription = emu.add_machine_reset_notifier(function ()
	reset_state()
	arm_trace()
end)

_G.genesistrace_stop_subscription = emu.add_machine_stop_notifier(function ()
	write_summary()
	append_agents_log_summary()
	append_log("==== genesistrace stop ====")
end)

_G.genesistrace_frame_subscription = emu.add_machine_frame_notifier(function ()
	local ok, err = pcall(function ()
		local pc
		local exec_entry
		local exec_label
		local i

		frame_count = frame_count + 1
		if not cpu or not prog then
			return
		end

		pc = current_pc()
		if pc and pc ~= last_pc and is_reset_helper_pc(pc) then
			log_reset_helper_hit(pc)
		end
		exec_entry = find_exec_range(pc)
		exec_label = exec_entry and exec_entry.name or "other"
		bump_exec_hit(exec_label, pc or 0)

		if exec_label ~= last_exec_label then
			append_log(string.format("[frame %06d] exec_enter pc=%06x range=%s", frame_count, pc or 0, exec_label))
			last_exec_label = exec_label
		end

		if pc and exception_handlers[pc] then
			if (pc ~= last_exception_pc) or ((frame_count - last_exception_frame) > 10) then
				log_exception_context(pc, exception_handlers[pc])
				last_exception_pc = pc
				last_exception_frame = frame_count
			end
		end

		if pc and is_fallback_exception_ui_pc(pc) then
			if (pc ~= last_exception_pc) or ((frame_count - last_exception_frame) > 10) then
				log_exception_context(pc, "fallback_exception_ui")
				last_exception_pc = pc
				last_exception_frame = frame_count
			end
		end

		if pc and is_dispatch_pc(pc) then
			log_dispatch_context(pc)
		end

		if (pc ~= last_pc) and ((frame_count % SAMPLE_PC_EVERY) == 0) then
			append_log(string.format("[frame %06d] pc=%06x exec=%s", frame_count, pc or 0, exec_label))
		end

		if (frame_count % SYMBOL_SAMPLE_EVERY) == 0 then
			sample_symbols()
		end

		if (frame_count % SAMPLE_WINDOW_EVERY) == 0 then
			for i = 1, #WINDOW_WATCHES do
				sample_window(WINDOW_WATCHES[i])
			end
		end

		last_pc = pc
	end)

	if not ok and not error_logged then
		error_logged = true
		append_log("error: " .. tostring(err))
		emu.print_error("genesistrace: " .. tostring(err))
	end
end)

reset_state()
arm_trace()
