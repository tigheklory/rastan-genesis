local frame_count = 0
local cpu = nil
local prog = nil
local profile_path = nil
local hook_refs = {}
local tap_refs = {}
local error_logged = false

_G.rastantrace_reset_subscription = nil
_G.rastantrace_stop_subscription = nil
_G.rastantrace_frame_subscription = nil

local C_WINDOW_BASE = 0xC00000
local C_WINDOW_END = 0xC0FFFF
local PAGE_SIZE_BYTES = 0x4000
local WORD_SIZE_BYTES = 2
local WORDS_PER_PAGE = PAGE_SIZE_BYTES / WORD_SIZE_BYTES
local PAGE_COUNT = 4
local DEAD_ZONE_MIN_BYTES = 0x100
local DEAD_ZONE_MIN_WORDS = DEAD_ZONE_MIN_BYTES / WORD_SIZE_BYTES

local PAGE_DEFS = {
	{ id = 0, start_addr = 0xC00000, end_addr = 0xC03FFF },
	{ id = 1, start_addr = 0xC04000, end_addr = 0xC07FFF },
	{ id = 2, start_addr = 0xC08000, end_addr = 0xC0BFFF },
	{ id = 3, start_addr = 0xC0C000, end_addr = 0xC0FFFF },
}

local page_profiles = {}
local hook_backend = "uninitialized"
local exec_detection_mode = "uninitialized"

local function is_rastan_set(name)
	return string.match(name or "", "^rastan") ~= nil
end

local function to_hex(value, width)
	return string.format("0x%0" .. tostring(width) .. "X", value or 0)
end

local function current_pc()
	if not cpu or not cpu.state or not cpu.state["PC"] then
		return nil
	end
	return cpu.state["PC"].value & 0xFFFFFF
end

local function new_page_profile(def)
	return {
		id = def.id,
		start_addr = def.start_addr,
		end_addr = def.end_addr,
		read_bits = {},
		write_bits = {},
		any_bits = {},
		exec_bits = {},
		read_unique_words = 0,
		write_unique_words = 0,
		unique_words_touched = 0,
		min_offset_touched = nil,
		max_offset_touched = nil,
		possible_execute = false,
		heuristic_exec = false,
	}
end

local function reset_profile_state()
	local i
	frame_count = 0
	error_logged = false
	page_profiles = {}
	for i = 1, #PAGE_DEFS do
		page_profiles[i] = new_page_profile(PAGE_DEFS[i])
	end
end

local function mark_offset_span(page, word_index)
	local offset = word_index * WORD_SIZE_BYTES
	if not page.min_offset_touched or offset < page.min_offset_touched then
		page.min_offset_touched = offset
	end
	if not page.max_offset_touched or offset > page.max_offset_touched then
		page.max_offset_touched = offset
	end
end

local function resolve_page_access(addr)
	local rel
	local page_index
	local page
	local page_rel
	local word_index
	if not addr then
		return nil
	end
	addr = addr & 0xFFFFFF
	if addr < C_WINDOW_BASE or addr > C_WINDOW_END then
		return nil
	end
	rel = addr - C_WINDOW_BASE
	page_index = math.floor(rel / PAGE_SIZE_BYTES) + 1
	page = page_profiles[page_index]
	if not page then
		return nil
	end
	page_rel = rel - ((page_index - 1) * PAGE_SIZE_BYTES)
	word_index = math.floor(page_rel / WORD_SIZE_BYTES)
	if word_index < 0 then
		word_index = 0
	elseif word_index >= WORDS_PER_PAGE then
		word_index = WORDS_PER_PAGE - 1
	end
	return page, word_index
end

local function normalize_hook_addr(raw)
	if type(raw) ~= "number" then
		return nil
	end
	raw = raw & 0xFFFFFF
	if raw >= C_WINDOW_BASE and raw <= C_WINDOW_END then
		return raw
	end
	if raw <= (C_WINDOW_END - C_WINDOW_BASE) then
		return (C_WINDOW_BASE + raw) & 0xFFFFFF
	end
	return nil
end

local function mark_possible_execute_heuristic(page, word_index)
	if exec_detection_mode ~= "heuristic_exec" then
		return
	end
	local pc = current_pc()
	if pc and pc >= page.start_addr and pc <= page.end_addr then
		page.possible_execute = true
		page.heuristic_exec = true
		page.exec_bits[word_index] = true
	end
end

local function mark_read(addr)
	local page, word_index = resolve_page_access(normalize_hook_addr(addr))
	if not page then
		return
	end
	if not page.read_bits[word_index] then
		page.read_bits[word_index] = true
		page.read_unique_words = page.read_unique_words + 1
	end
	if not page.any_bits[word_index] then
		page.any_bits[word_index] = true
		page.unique_words_touched = page.unique_words_touched + 1
		mark_offset_span(page, word_index)
	end
	mark_possible_execute_heuristic(page, word_index)
end

local function mark_write(addr)
	local page, word_index = resolve_page_access(normalize_hook_addr(addr))
	if not page then
		return
	end
	if not page.write_bits[word_index] then
		page.write_bits[word_index] = true
		page.write_unique_words = page.write_unique_words + 1
	end
	if not page.any_bits[word_index] then
		page.any_bits[word_index] = true
		page.unique_words_touched = page.unique_words_touched + 1
		mark_offset_span(page, word_index)
	end
	mark_possible_execute_heuristic(page, word_index)
end

local function mark_execute(addr)
	local page, word_index = resolve_page_access(normalize_hook_addr(addr))
	if not page then
		return
	end
	page.possible_execute = true
	page.exec_bits[word_index] = true
end

local function extract_addr_from_args(...)
	local i
	local argc = select("#", ...)
	local best_relative = nil
	for i = 1, argc do
		local v = select(i, ...)
		if type(v) == "number" then
			local n = v & 0xFFFFFF
			if n >= C_WINDOW_BASE and n <= C_WINDOW_END then
				return n
			end
			if not best_relative and n <= (C_WINDOW_END - C_WINDOW_BASE) then
				best_relative = (C_WINDOW_BASE + n) & 0xFFFFFF
			end
		end
	end
	return best_relative
end

local function try_add_memory_hook_with_signature(signature_fn)
	local ok, result = pcall(signature_fn)
	if ok and result ~= nil then
		hook_refs[#hook_refs + 1] = result
		return true
	end
	return false
end

local function install_emu_memory_hooks()
	local read_callback
	local write_callback
	local fetch_callback
	local installed_read = false
	local installed_write = false
	local installed_fetch = false
	local i
	local read_attempts = {}
	local write_attempts = {}
	local fetch_attempts = {}

	if type(emu.add_memory_hook) ~= "function" then
		return false, false, false
	end

	read_callback = function(...)
		local addr = extract_addr_from_args(...)
		if addr then
			mark_read(addr)
		end
	end
	write_callback = function(...)
		local addr = extract_addr_from_args(...)
		if addr then
			mark_write(addr)
		end
	end
	fetch_callback = function(...)
		local addr = extract_addr_from_args(...)
		if addr then
			mark_execute(addr)
		end
	end

	read_attempts = {
		function() return emu.add_memory_hook("read", C_WINDOW_BASE, C_WINDOW_END, read_callback) end,
		function() return emu.add_memory_hook("program", "read", C_WINDOW_BASE, C_WINDOW_END, read_callback) end,
		function() return emu.add_memory_hook(":maincpu", "program", "read", C_WINDOW_BASE, C_WINDOW_END, read_callback) end,
	}
	write_attempts = {
		function() return emu.add_memory_hook("write", C_WINDOW_BASE, C_WINDOW_END, write_callback) end,
		function() return emu.add_memory_hook("program", "write", C_WINDOW_BASE, C_WINDOW_END, write_callback) end,
		function() return emu.add_memory_hook(":maincpu", "program", "write", C_WINDOW_BASE, C_WINDOW_END, write_callback) end,
	}
	fetch_attempts = {
		function() return emu.add_memory_hook("fetch", C_WINDOW_BASE, C_WINDOW_END, fetch_callback) end,
		function() return emu.add_memory_hook("opcode", C_WINDOW_BASE, C_WINDOW_END, fetch_callback) end,
		function() return emu.add_memory_hook("execute", C_WINDOW_BASE, C_WINDOW_END, fetch_callback) end,
		function() return emu.add_memory_hook("program", "fetch", C_WINDOW_BASE, C_WINDOW_END, fetch_callback) end,
		function() return emu.add_memory_hook(":maincpu", "program", "fetch", C_WINDOW_BASE, C_WINDOW_END, fetch_callback) end,
	}

	for i = 1, #read_attempts do
		if try_add_memory_hook_with_signature(read_attempts[i]) then
			installed_read = true
			break
		end
	end
	for i = 1, #write_attempts do
		if try_add_memory_hook_with_signature(write_attempts[i]) then
			installed_write = true
			break
		end
	end
	for i = 1, #fetch_attempts do
		if try_add_memory_hook_with_signature(fetch_attempts[i]) then
			installed_fetch = true
			break
		end
	end

	return installed_read, installed_write, installed_fetch
end

local function install_tap_hooks()
	local ok_read, read_tap
	local ok_write, write_tap

	if not prog then
		return false, false
	end

	ok_read, read_tap = pcall(function()
		return prog:install_read_tap(
			C_WINDOW_BASE,
			C_WINDOW_END,
			"rastantrace_ramcov_read",
			function(offset, data, mem_mask)
				mark_read(offset)
				return data
			end
		)
	end)

	ok_write, write_tap = pcall(function()
		return prog:install_write_tap(
			C_WINDOW_BASE,
			C_WINDOW_END,
			"rastantrace_ramcov_write",
			function(offset, data, mem_mask)
				mark_write(offset)
				return data
			end
		)
	end)

	if ok_read and read_tap then
		tap_refs[#tap_refs + 1] = read_tap
	end
	if ok_write and write_tap then
		tap_refs[#tap_refs + 1] = write_tap
	end

	return ok_read and read_tap ~= nil, ok_write and write_tap ~= nil
end

local function close_range(ranges, run_start, run_end)
	local start_offset = run_start * WORD_SIZE_BYTES
	local end_offset = (run_end * WORD_SIZE_BYTES) + (WORD_SIZE_BYTES - 1)
	local length_words = run_end - run_start + 1
	local length_bytes = length_words * WORD_SIZE_BYTES
	ranges[#ranges + 1] = {
		start_offset = start_offset,
		end_offset = end_offset,
		length_words = length_words,
		length_bytes = length_bytes,
	}
end

local function bitmap_to_ranges(bitmap, want_set)
	local wi
	local ranges = {}
	local run_start = nil

	for wi = 0, WORDS_PER_PAGE - 1 do
		local is_set = bitmap[wi] == true
		local include = (want_set and is_set) or ((not want_set) and (not is_set))
		if include and not run_start then
			run_start = wi
		elseif (not include) and run_start then
			close_range(ranges, run_start, wi - 1)
			run_start = nil
		end
	end

	if run_start then
		close_range(ranges, run_start, WORDS_PER_PAGE - 1)
	end
	return ranges
end

local function filtered_dead_zones(any_bitmap)
	local i
	local all_untouched = bitmap_to_ranges(any_bitmap, false)
	local filtered = {}
	for i = 1, #all_untouched do
		local r = all_untouched[i]
		if r.length_words >= DEAD_ZONE_MIN_WORDS then
			filtered[#filtered + 1] = r
		end
	end
	return filtered
end

local function json_escape(s)
	return (s:gsub("\\", "\\\\"):gsub("\"", "\\\""):gsub("\n", "\\n"):gsub("\r", "\\r"):gsub("\t", "\\t"))
end

local function write_json_range_array(fh, key, ranges, indent, trailing_comma)
	local i
	fh:write(string.rep(" ", indent))
	fh:write("\"")
	fh:write(key)
	fh:write("\": [\n")
	for i = 1, #ranges do
		local r = ranges[i]
		fh:write(string.rep(" ", indent + 2))
		fh:write("{")
		fh:write(string.format("\"start_offset\":\"%s\",", to_hex(r.start_offset, 4)))
		fh:write(string.format("\"end_offset\":\"%s\",", to_hex(r.end_offset, 4)))
		fh:write(string.format("\"length_words\":%d,", r.length_words))
		fh:write(string.format("\"length_bytes\":%d", r.length_bytes))
		fh:write("}")
		if i < #ranges then
			fh:write(",")
		end
		fh:write("\n")
	end
	fh:write(string.rep(" ", indent))
	fh:write("]")
	if trailing_comma then
		fh:write(",")
	end
	fh:write("\n")
end

local function write_profile_json()
	local fh
	local i
	local now_utc = os.date("!%Y-%m-%dT%H:%M:%SZ")

	if not profile_path then
		return
	end

	fh = io.open(profile_path, "w")
	if not fh then
		return
	end

	fh:write("{\n")
	fh:write("  \"metadata\": {\n")
	fh:write(string.format("    \"generated_utc\": \"%s\",\n", json_escape(now_utc)))
	fh:write(string.format("    \"rom_name\": \"%s\",\n", json_escape(tostring(emu.romname() or ""))))
	fh:write(string.format("    \"game_name\": \"%s\",\n", json_escape(tostring(emu.gamename() or ""))))
	fh:write(string.format("    \"frames_profiled\": %d,\n", frame_count))
	fh:write(string.format("    \"range\": \"%s-%s\",\n", to_hex(C_WINDOW_BASE, 6), to_hex(C_WINDOW_END, 6)))
	fh:write("    \"granularity\": \"word16\",\n")
	fh:write(string.format("    \"hook_backend\": \"%s\",\n", json_escape(hook_backend)))
	fh:write(string.format("    \"execution_detection\": \"%s\",\n", json_escape(exec_detection_mode)))
	fh:write("    \"warning\": \"Coverage reflects only the traced scenario and is evidence for reduction candidates, not proof of universal safety.\"\n")
	fh:write("  },\n")
	fh:write("  \"pages\": {\n")

	for i = 1, #page_profiles do
		local page = page_profiles[i]
		local read_ranges = bitmap_to_ranges(page.read_bits, true)
		local write_ranges = bitmap_to_ranges(page.write_bits, true)
		local untouched_ranges = filtered_dead_zones(page.any_bits)
		local key = string.format("page%d", page.id)

		fh:write(string.format("    \"%s\": {\n", key))
		fh:write(string.format("      \"arcade_start\": \"%s\",\n", to_hex(page.start_addr, 6)))
		fh:write(string.format("      \"arcade_end\": \"%s\",\n", to_hex(page.end_addr, 6)))
		if page.min_offset_touched then
			fh:write(string.format("      \"min_offset_touched\": \"%s\",\n", to_hex(page.min_offset_touched, 4)))
			fh:write(string.format("      \"max_offset_touched\": \"%s\",\n", to_hex(page.max_offset_touched, 4)))
		else
			fh:write("      \"min_offset_touched\": null,\n")
			fh:write("      \"max_offset_touched\": null,\n")
		end
		fh:write(string.format("      \"unique_words_touched\": %d,\n", page.unique_words_touched))
		fh:write(string.format("      \"read_unique_words\": %d,\n", page.read_unique_words))
		fh:write(string.format("      \"write_unique_words\": %d,\n", page.write_unique_words))
		fh:write(string.format("      \"possible_execute\": %s,\n", page.possible_execute and "true" or "false"))
		fh:write(string.format("      \"heuristic_exec\": %s,\n", page.heuristic_exec and "true" or "false"))
		write_json_range_array(fh, "read_ranges", read_ranges, 6, true)
		write_json_range_array(fh, "write_ranges", write_ranges, 6, true)
		write_json_range_array(fh, "untouched_ranges", untouched_ranges, 6, false)
		fh:write("    }")
		if i < #page_profiles then
			fh:write(",")
		end
		fh:write("\n")
	end

	fh:write("  }\n")
	fh:write("}\n")
	fh:close()
end

local function arm_profiler()
	local has_add_hook_read, has_add_hook_write, has_add_hook_fetch
	local has_tap_read, has_tap_write

	cpu = manager.machine.devices[":maincpu"]
	if not cpu then
		emu.print_error("rastantrace: maincpu not found")
		return
	end
	prog = cpu.spaces["program"]
	if not prog then
		emu.print_error("rastantrace: maincpu program space not found")
		return
	end

	hook_refs = {}
	tap_refs = {}

	has_add_hook_read, has_add_hook_write, has_add_hook_fetch = install_emu_memory_hooks()
	has_tap_read, has_tap_write = install_tap_hooks()

	if has_add_hook_read or has_add_hook_write then
		if has_tap_read or has_tap_write then
			hook_backend = "emu.add_memory_hook+address_space_taps"
		else
			hook_backend = "emu.add_memory_hook"
		end
	else
		hook_backend = "address_space_taps"
	end

	if has_add_hook_fetch then
		exec_detection_mode = "opcode_fetch_hook"
	else
		exec_detection_mode = "heuristic_exec"
	end
end

if not is_rastan_set(emu.romname()) then
	emu.print_info("rastantrace: skipped for rom " .. tostring(emu.romname()))
	return
end

do
	local home = manager.machine.options.entries.homepath:value():match("([^;]+)")
	local trace_dir = home .. "/rastantrace"
	os.execute(string.format("mkdir -p '%s'", trace_dir))
	profile_path = trace_dir .. "/ram_usage_profile.json"
end

emu.print_info("rastantrace RAM coverage profiler loaded")

_G.rastantrace_reset_subscription = emu.add_machine_reset_notifier(function ()
	reset_profile_state()
	arm_profiler()
end)

_G.rastantrace_stop_subscription = emu.add_machine_stop_notifier(function ()
	write_profile_json()
end)

_G.rastantrace_frame_subscription = emu.add_machine_frame_notifier(function ()
	local ok, err = pcall(function ()
		frame_count = frame_count + 1
	end)

	if not ok and not error_logged then
		error_logged = true
		emu.print_error("rastantrace profiler: " .. tostring(err))
	end
end)

reset_profile_state()
arm_profiler()
