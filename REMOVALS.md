Active contaminations that are clearly still present
1. FG buffer sentinel write

What it does:

Forces pc080sn_fg_buffer[0] to 0xFFFF every VBlank before the tick, so Plane A is never “natural” at cell (0,0). Andy calls this a direct contamination of FG content; Cody also lists it as active item A01.

Cross-reference:

Cody: A01, active, immediate cleanup candidate.
Andy: Item 1, active, high-risk.

Verdict:

Remove unless you are actively running the original sentinel proof again.
2. FG before/after capture (fg_debug_before, fg_debug_after)

What it does:

Captures FG buffer word 0 before and after the tick every frame. Andy treats this as lower-risk instrumentation; Cody keeps it in the active list.

Cross-reference:

Cody: A01/A03 neighborhood, active diagnostic instrumentation.
Andy: Item 2, active instrumentation.

Verdict:

Remove soon. It is not the worst contaminant, but it is still proof scaffolding.
3. Plane A debug telemetry overlay (genesistan_debug_fg_proof)

What it does:

Writes B:, A:, P:, M:, I:, K: text directly into FG buffer every frame, overwriting multiple rows and columns of Plane A. Andy explicitly says this permanently clobbers those cells and makes attract/text analysis invalid there; Cody lists it as active A03.

Cross-reference:

Cody: A03, active, high contamination, cleanup candidate.
Andy: Item 3, active, high-risk.

Verdict:

Remove immediately once you are done reading those values.
4. VDP commit counters and 3-frame history

What it does:

Tracks per-frame counts for plane, palette, and scroll commits. Cody lists this as A04; Andy lists the frame-history and per-function increments separately as active instrumentation.

Cross-reference:

Cody: A04, active, instrumentation, “soon.”
Andy: Items 4 and 5, active instrumentation.

Verdict:

Remove soon. Useful proof already served its purpose.
5. Tick-phase preload suppression (genesistan_bulk_preload_check immediate return)

What it does:

Disables the tick-path scene preload call entirely. Cody flags this as A05 and high-risk because it changes tile visibility/content timing. Andy’s summary also notes that tick-phase tile DMA no longer runs.

Cross-reference:

Cody: A05, active, immediate cleanup candidate, high-risk.
Andy: Included in his “no screenshot reflects intended rendering behavior” summary.

Verdict:

Remove immediately unless you deliberately want preload disabled for a controlled proof build.
6. Post-reset forced test palette (apply_post_reset_test_palette)

What it does:

Injects a fixed 64-entry CRAM palette after reset/handoff. Cody lists it as A06 and high-risk because it forces visibility from outside the normal runtime palette path.

Cross-reference:

Cody: A06, active, immediate cleanup candidate, high-risk.
Andy’s audit snippet and earlier history support it as part of the current contamination state.

Verdict:

Remove immediately.
7. C sprite SAT DMA publish suppression in genesistan_render_sprites_vdp

What it does:

Keeps sprite prep running but comments out VDP_updateSprites(..., DMA) and VDP_waitDMACompletion(). Cody lists this as A07 and high-risk; Andy identifies sprite SAT DMA suppression as one of the most serious active contaminants.

Cross-reference:

Cody: A07, active, immediate cleanup candidate, high-risk.
Andy: one of the explicitly named high-risk items.

Verdict:

Remove or replace with the intended architecture immediately. This is one of the biggest current distortions.
8. ASM sprite renderer early rts

What it does:

genesistan_render_sprites_vdp_asm exits immediately, making the entire assembly sprite path unreachable. Cody lists it as A08; Andy calls it a high-risk suppressor.

Cross-reference:

Cody: A08, active, immediate cleanup candidate, high-risk.
Andy: explicitly high-risk.

Verdict:

Remove immediately unless you are intentionally keeping the ASM sprite path disabled while a clean replacement exists.
9. Temporary palette commit algorithm in genesistan_palette_commit_asm

What it does:

Uses the temporary mirrored-block palette strategy from the visibility proof era. Cody marks this as A09 and high-risk/verify-first.

Cross-reference:

Cody: A09, active, verify-first, high-risk.
Not highlighted as strongly by Andy in the visible snippet, but still part of Cody’s active debt list.

Verdict:

Verify first, then remove/replace. This one may be intertwined with current visibility, so don’t rip it blindly without noting its intended replacement.
10. Row visibility filter disabled in text_writer_ptr_to_xy

What it does:

The original row-bias visibility filter is commented out, so rows that should be filtered can now pass through. Andy calls this active Item 6; Cody lists it as A10.

Cross-reference:

Cody: A10, active, “soon.”
Andy: Item 6, active suppression/change.

Verdict:

Remove soon. It directly alters what text gets written and where.
11. sanitize_arcade_workram() pointer/memory mutation

What it does:

Scans work RAM and zeroes values in the 0xC00000–0xC0FFFF range after each tick. Cody explicitly says this mutates work RAM every frame and is high-risk.

Cross-reference:

Cody: A11, active, verify-first, high-risk.
Andy’s shorter visible audit does not foreground it as much, but Cody absolutely does.

Verdict:

High priority verify-first, probably remove once you have a safer alternative. This is one of the most dangerous contaminants because it changes game state, not just display.
12. Startup remap JSON bypasses: boot probe/text-fill NOPs

What it does:

NOP/RTS startup boot text-fill writes and related startup bypasses. Cody marks these as A12 and high-risk.

Verdict:

Immediate review candidate. These are not harmless.
13. Startup remap JSON C-window pointer/store/read bypass cluster

What it does:

Replaces many C-window pointer/store/read instructions with bypass forms. Cody marks this as A13 and high-risk.

Verdict:

Immediate review candidate. This can fundamentally distort memory semantics.
14. Startup remap JSON text-writer silencing cluster

What it does:

Silences legacy direct C-window text/status writes while hooks are used instead. Cody marks this as A14 and high-risk.

Verdict:

Immediate review candidate.
15. Startup remap JSON transition/helper bypass cluster

What it does:

RTS/NOP/BRA bypasses in unstable helper/transition paths. Cody marks this as A15 and high-risk.

Verdict:

Immediate review candidate.
16. Test-mode preview / debug routing

What it does:

Cody lists this as A16, active, verify-first. The snippet does not show the full description, but it is on his cleanup candidates list.

Verdict:

Verify-first. Needs explicit review in code before removal.
17. Palette fallback / debug table retention

What it does:

Cody lists this as A17, active, later priority. Again, the snippet is partial, but it is a live cleanup candidate.

Verdict:

Later, after the higher-risk items are resolved.
Historical/reverted diagnostic debt you should still track

Cody’s cleanup candidates include reverted/historical items that affected reasoning and may still be referenced in AGENTS history:

H01: blunt hook top-return suppression from Build 338, reverted.
H02: forced zero-scroll commit from Build 322, reverted.
H03 and other historical/offline proof items also appear in Cody’s cleanup list and should stay in the master debt document even if not active.
Cross-referenced “remove first” list

If your goal is “remove anything that shouldn’t be there” before resuming real debugging, this is the first-pass list:

FG sentinel write
FG before/after capture
Plane A debug overlay
VDP commit counters/history
Tick preload suppression
Post-reset forced palette
Sprite SAT DMA suppression in C path
ASM sprite renderer early rts
Row visibility filter disable

These are either directly marked active/high-risk by one or both audits, or they clearly alter runtime/visible behavior in ways that poison conclusions.

Cross-referenced “verify before removing” list

These are dangerous enough that they need a documented replacement plan, but you still should not leave them untracked:

Temporary palette commit algorithm
sanitize_arcade_workram()
Test-mode preview/debug routing
Palette fallback/debug table retention
The remap JSON bypass clusters (boot probe/text-fill, C-window pointer/store/read, text-writer silencing, transition/helper bypasses)

Cody’s audit makes clear these are still active and architecturally significant.

Bottom line

The most important cross-referenced conclusion is this:

No screenshot from the current ROM reflects intended rendering behavior while these active contaminants remain in place. Andy says that directly for the current build state, and Cody’s audit backs it up with the active/high-risk inventory.

The clean next move is to turn this into a master cleanup checklist with three columns:

active now
safe to remove immediately
verify-first before removal

If you want, I’ll build that master cleanup checklist next in a format you can hand directly to Cody and Andy.


