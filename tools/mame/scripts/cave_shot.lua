local frame=0
local shots={[900]=1,[1800]=1,[2700]=1,[3600]=1,[4200]=1,[4800]=1,[5400]=1,[6000]=1}
_G.cs=emu.add_machine_frame_notifier(function()
  frame=frame+1
  if shots[frame] then pcall(function() manager.machine.video:snapshot() end) end
end)
