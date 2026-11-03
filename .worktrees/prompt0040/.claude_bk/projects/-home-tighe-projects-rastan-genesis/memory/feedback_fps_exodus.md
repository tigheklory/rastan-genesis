---
name: FPS in Exodus screenshots is manual throttle
description: When user provides Exodus screenshots with varying/low FPS numbers, this is from manual CPU throttle to capture frames — not a real performance issue
type: feedback
---

Do not interpret varying or low FPS values in Exodus emulator screenshots as evidence of performance degradation. The user manually throttles the CPU in Exodus to capture specific frames. Only diagnose performance issues if the user explicitly reports slowdown during normal gameplay.

**Why:** Incorrectly attributed FPS drop (123→7) to VBlank overrun in Build 320 analysis, when it was just the user's capture technique.

**How to apply:** When analyzing emulator screenshots, ignore FPS counter values unless the user specifically calls out a performance problem.
