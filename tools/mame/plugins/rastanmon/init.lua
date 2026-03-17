-- license:BSD-3-Clause
local exports = {
	name = "rastanmon",
	version = "0.2.0",
	description = "Rastan mode and palette monitor",
	license = "BSD-3-Clause",
	author = { name = "OpenAI Codex" }
}

local rastanmon = exports

local frame_subscription
local reset_subscription
local stop_subscription
local prestart_registered = false

local frame_count = 0
local log_path = nil
local last_mode_key = nil
local palette_snapshot = {}
local error_logged = false

local MODE_BASE = 0x10c000
local PAL_BASE = 0x200000
local PAL_BLOCK_SIZE = 0x20
local PAL_BLOCK_COUNT = 72

local function is_rastan_set(name)
	return string.match(name, "^rastan") ~= nil
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

local function mode_key(state)
	return string.format(
		"%04x:%04x:%04x:%04x:%04x:%04x:%04x:%04x:%04x:%04x",
		state.page0,
		state.page2,
		state.mode4,
		state.credits,
		state.stage,
		state.player_sel,
		state.ctrl_13aa,
		state.ctrl_13ac,
		state.ctrl_13ae,
		state.ctrl_13b0
	)
end

local function log_mode_change(state)
	append_log(string.format(
		"[frame %06d] mode page0=%04x page2=%04x mode4=%04x(%s) credits=%04x stage=%04x sel118=%04x 13aa=%04x(%s) 13ac=%04x 13ae=%04x 13b0=%04x",
		frame_count,
		state.page0,
		state.page2,
		state.mode4,
		mode4_label(state.mode4),
		state.credits,
		state.stage,
		state.player_sel,
		state.ctrl_13aa,
		ctrl13aa_label(state.ctrl_13aa),
		state.ctrl_13ac,
		state.ctrl_13ae,
		state.ctrl_13b0
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

local function scan_palette(space)
	for block = 0, PAL_BLOCK_COUNT - 1 do
		local words = read_palette_block(space, block)
		if block_changed(palette_snapshot[block], words) then
			if (not palette_snapshot[block]) and block_is_all_zero(words) then
				palette_snapshot[block] = words
			else
				local base = PAL_BASE + (block * PAL_BLOCK_SIZE)
				append_log(string.format(
					"[frame %06d] palblk %02x @%06x %s",
					frame_count,
					block,
					base,
					block_words_text(words)
				))
				palette_snapshot[block] = words
			end
		end
	end
end

local function reset_state()
	frame_count = 0
	last_mode_key = nil
	palette_snapshot = {}
	append_log("---- reset ----")
end

function rastanmon.startplugin()
	local romname = emu.romname()
	if not is_rastan_set(romname) then
		return
	end
	emu.print_info("rastanmon plugin loaded")
	if prestart_registered then
		return
	end
	prestart_registered = true
	emu.register_prestart(function ()
		local ok, err = pcall(function ()
			local home = manager.machine.options.entries.homepath:value():match("([^;]+)")
			if not home or home == "" then
				home = "."
			end
			log_path = home .. "/rastanmon/rastan_monitor.log"
			append_log(string.format("==== rastanmon start rom=%s game=%s ====", emu.romname(), emu.gamename()))

			reset_subscription = emu.add_machine_reset_notifier(function ()
				reset_state()
			end)

			stop_subscription = emu.add_machine_stop_notifier(function ()
				append_log("==== rastanmon stop ====")
			end)

			frame_subscription = emu.add_machine_frame_notifier(function ()
				local frame_ok, frame_err = pcall(function ()
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
					if key ~= last_mode_key then
						last_mode_key = key
						log_mode_change(state)
					end

					scan_palette(space)
				end)
				if (not frame_ok) and (not error_logged) then
					error_logged = true
					append_log("ERROR " .. tostring(frame_err))
					emu.print_error("rastanmon: " .. tostring(frame_err))
				end
			end)
		end)
		if not ok then
			emu.print_error("rastanmon prestart: " .. tostring(err))
		end
	end)
end

return exports
