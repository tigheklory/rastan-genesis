# Cody JSON Spec Inventory

## Scope
- Read-only inventory.
- Excluded from scan by instruction: `.git/`, `node_modules/`, and generated JSON under `build/` and `dist/`.

## Phase 1 - Enumerate All JSON Files
- Total in-scope JSON files: **126**

| file_path | size_bytes | last_modified |
|---|---:|---|
| `.claude/settings.json` | 788 | 2026-04-20 22:25:14 -0400 |
| `.claude_bk/settings.json` | 132 | 2026-03-21 17:32:47 -0400 |
| `.vscode/settings.json` | 41 | 2026-03-17 18:13:22 -0400 |
| `audio/rastan_music_dump/conversion_attempts/01 - Credit_conversion_summary.json` | 601 | 2026-04-06 15:31:25 -0400 |
| `audio/rastan_music_dump/conversion_attempts/02 - Broken The Promises (Opening)_conversion_summary.json` | 799 | 2026-04-06 15:31:25 -0400 |
| `audio/rastan_music_dump/conversion_attempts/03 - Aggressive World (Scene 1)_conversion_summary.json` | 845 | 2026-04-06 15:31:25 -0400 |
| `audio/rastan_music_dump/conversion_attempts/04 - Bad Bible (Name Regist)_conversion_summary.json` | 790 | 2026-04-06 15:31:25 -0400 |
| `audio/rastan_music_dump/conversion_attempts/05 - Re-In-Carnation (Scene 2)_conversion_summary.json` | 815 | 2026-04-06 15:31:25 -0400 |
| `audio/rastan_music_dump/conversion_attempts/06 - The Devil Boss Carnival (Scene 3 Boss)_conversion_summary.json` | 830 | 2026-04-06 15:31:25 -0400 |
| `audio/rastan_music_dump/conversion_attempts/07 - Scene Clear_conversion_summary.json` | 772 | 2026-04-06 15:31:25 -0400 |
| `audio/rastan_music_dump/conversion_attempts/08 - Final Destroy (Scene 3 Round 6 Boss)_conversion_summary.json` | 863 | 2026-04-06 15:31:25 -0400 |
| `audio/rastan_music_dump/conversion_attempts/09 - The Man Of Saga (Ending)_conversion_summary.json` | 815 | 2026-04-06 15:31:26 -0400 |
| `audio/rastan_music_dump/conversion_attempts/direct_fur_generation_summary.json` | 9719 | 2026-04-06 16:38:31 -0400 |
| `audio/rastan_music_dump/conversion_attempts/extracted_events/01 - Credit_events.json` | 531 | 2026-04-06 16:38:31 -0400 |
| `audio/rastan_music_dump/conversion_attempts/extracted_events/02 - Broken The Promises (Opening)_events.json` | 20568 | 2026-04-06 16:38:31 -0400 |
| `audio/rastan_music_dump/conversion_attempts/extracted_events/03 - Aggressive World (Scene 1)_events.json` | 160429 | 2026-04-06 16:38:31 -0400 |
| `audio/rastan_music_dump/conversion_attempts/extracted_events/04 - Bad Bible (Name Regist)_events.json` | 9479 | 2026-04-06 16:38:31 -0400 |
| `audio/rastan_music_dump/conversion_attempts/extracted_events/05 - Re-In-Carnation (Scene 2)_events.json` | 206206 | 2026-04-06 16:38:31 -0400 |
| `audio/rastan_music_dump/conversion_attempts/extracted_events/06 - The Devil Boss Carnival (Scene 3 Boss)_events.json` | 131252 | 2026-04-06 16:38:31 -0400 |
| `audio/rastan_music_dump/conversion_attempts/extracted_events/07 - Scene Clear_events.json` | 23731 | 2026-04-06 16:38:31 -0400 |
| `audio/rastan_music_dump/conversion_attempts/extracted_events/08 - Final Destroy (Scene 3 Round 6 Boss)_events.json` | 323531 | 2026-04-06 16:38:31 -0400 |
| `audio/rastan_music_dump/conversion_attempts/extracted_events/09 - The Man Of Saga (Ending)_events.json` | 75932 | 2026-04-06 16:38:31 -0400 |
| `audio/rastan_music_dump/conversion_attempts/pipeline_summary.json` | 13881 | 2026-04-06 15:31:26 -0400 |
| `audio/rastan_music_dump/conversion_attempts/vgm2fur_conversion_results.json` | 10259 | 2026-04-06 16:19:52 -0400 |
| `audio/rastan_music_dump/conversion_attempts/vgm2fur_file_statuses.json` | 9089 | 2026-04-06 16:22:00 -0400 |
| `audio/rastan_music_dump/conversion_attempts/vgz_to_midi_run_summary.json` | 4479 | 2026-04-06 15:41:16 -0400 |
| `docs/replacement_inventory/frontend_window_replacement_inventory.json` | 77330 | 2026-03-23 20:36:33 -0400 |
| `docs/replacement_inventory/fullgame_window_replacement_inventory.json` | 297230 | 2026-03-24 23:54:58 -0400 |
| `docs/research/semantic_entry_manifest.json` | 2571 | 2026-03-25 17:40:32 -0400 |
| `specs/audio_rules.json` | 297 | 2026-03-14 21:45:16 -0400 |
| `specs/debug_bus.json` | 721 | 2026-03-14 21:45:16 -0400 |
| `specs/extraction_manifest.json` | 3931 | 2026-03-14 21:48:22 -0400 |
| `specs/fixups.json` | 1775 | 2026-03-14 21:48:58 -0400 |
| `specs/gfx_rules.json` | 1286 | 2026-03-15 18:33:54 -0400 |
| `specs/layout.json` | 445 | 2026-03-14 21:45:16 -0400 |
| `specs/objects.json` | 1047 | 2026-03-14 21:45:16 -0400 |
| `specs/rastan_direct_remap.json` | 25028 | 2026-04-20 12:12:36 -0400 |
| `specs/refactor_rules.json` | 351 | 2026-03-14 21:45:16 -0400 |
| `specs/relocations.json` | 971 | 2026-03-14 21:45:16 -0400 |
| `specs/runtime_config.json` | 836 | 2026-03-14 21:45:16 -0400 |
| `specs/startup_title_remap.json` | 55368 | 2026-04-01 10:40:54 -0400 |
| `specs/subsystem_modes.json` | 1632 | 2026-03-14 21:45:16 -0400 |
| `specs/symbols.json` | 2665 | 2026-03-14 21:45:16 -0400 |
| `specs/validation_rules.json` | 609 | 2026-03-14 21:45:16 -0400 |
| `specs/variants.json` | 4447 | 2026-03-14 21:45:16 -0400 |
| `tools/ghidra/lab313ru_latest.json` | 144 | 2026-03-22 20:18:42 -0400 |
| `tools/ghidra/lab313ru_latest_actual.json` | 3785 | 2026-03-22 20:21:24 -0400 |
| `tools/ghidra/lab313ru_releases.json` | 135 | 2026-03-22 20:18:42 -0400 |
| `tools/ghidra/lab313ru_releases_actual.json` | 52125 | 2026-03-22 20:21:24 -0400 |
| `tools/mame/cheat/output.json` | 13405 | 2026-03-30 20:19:16 -0400 |
| `tools/mame/plugins/rastanmon/plugin.json` | 198 | 2026-03-15 19:10:02 -0400 |
| `tools/sgdk/project/template/.vscode/c_cpp_properties.json` | 321 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/project/template/.vscode/extensions.json` | 146 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/project/template/.vscode/settings.json` | 371 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/advanced/sprites-sharing-tiles/.vscode/c_cpp_properties.json` | 327 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/advanced/sprites-sharing-tiles/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/advanced/sprites-sharing-tiles/.vscode/settings.json` | 417 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/advanced/tile-animation/.vscode/c_cpp_properties.json` | 327 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/advanced/tile-animation/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/advanced/tile-animation/.vscode/settings.json` | 357 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/basics/hello-world/.vscode/c_cpp_properties.json` | 327 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/basics/hello-world/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/basics/hello-world/.vscode/settings.json` | 357 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/basics/image/.vscode/c_cpp_properties.json` | 327 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/basics/image/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/basics/image/.vscode/settings.json` | 357 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/benchmark/.vscode/c_cpp_properties.json` | 321 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/benchmark/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/benchmark/.vscode/settings.json` | 357 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/bitmap/cube-3D/.vscode/c_cpp_properties.json` | 327 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/bitmap/cube-3D/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/bitmap/cube-3D/.vscode/settings.json` | 357 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/bitmap/partic/.vscode/c_cpp_properties.json` | 327 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/bitmap/partic/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/bitmap/partic/.vscode/settings.json` | 357 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/demo/bad-apple/.vscode/c_cpp_properties.json` | 327 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/demo/bad-apple/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/demo/bad-apple/.vscode/settings.json` | 357 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/demo/starfield-donut/.vscode/c_cpp_properties.json` | 327 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/demo/starfield-donut/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/demo/starfield-donut/.vscode/settings.json` | 357 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/flash-save/.vscode/c_cpp_properties.json` | 321 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/flash-save/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/flash-save/.vscode/settings.json` | 357 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/fx/h-int/scaling/.vscode/c_cpp_properties.json` | 333 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/fx/h-int/scaling/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/fx/h-int/scaling/.vscode/settings.json` | 419 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/fx/h-int/wobble/.vscode/c_cpp_properties.json` | 333 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/fx/h-int/wobble/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/fx/h-int/wobble/.vscode/settings.json` | 419 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/fx/hilight-shadow/.vscode/c_cpp_properties.json` | 327 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/fx/hilight-shadow/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/fx/hilight-shadow/.vscode/settings.json` | 357 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/fx/scroll/linescroll/.vscode/c_cpp_properties.json` | 333 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/fx/scroll/linescroll/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/fx/scroll/linescroll/.vscode/settings.json` | 419 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/fx/sprite-masking/.vscode/c_cpp_properties.json` | 327 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/fx/sprite-masking/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/fx/sprite-masking/.vscode/settings.json` | 419 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/game/platformer/.vscode/c_cpp_properties.json` | 327 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/game/platformer/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/game/platformer/.vscode/settings.json` | 419 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/game/sonic/.vscode/c_cpp_properties.json` | 327 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/game/sonic/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/game/sonic/.vscode/settings.json` | 419 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/joy-test/.vscode/c_cpp_properties.json` | 321 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/joy-test/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/joy-test/.vscode/settings.json` | 419 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/megawifi/basic/.vscode/c_cpp_properties.json` | 327 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/megawifi/basic/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/megawifi/basic/.vscode/settings.json` | 419 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/megawifi/menu/.vscode/c_cpp_properties.json` | 327 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/megawifi/menu/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/megawifi/menu/.vscode/settings.json` | 419 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/snd/sound-test/.vscode/c_cpp_properties.json` | 327 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/snd/sound-test/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/snd/sound-test/.vscode/settings.json` | 419 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/snd/xgm-player/.vscode/c_cpp_properties.json` | 327 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/snd/xgm-player/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/snd/xgm-player/.vscode/settings.json` | 419 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/sys/console/.vscode/c_cpp_properties.json` | 327 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/sys/console/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/sys/console/.vscode/settings.json` | 419 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/sys/multitasking/.vscode/c_cpp_properties.json` | 327 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/sys/multitasking/.vscode/extensions.json` | 140 | 2026-03-11 13:11:42 -0400 |
| `tools/sgdk/sample/sys/multitasking/.vscode/settings.json` | 419 | 2026-03-11 13:11:42 -0400 |

## Phase 2 - Identify Consumers and Classification
| file_path | consumers | classification |
|---|---|---|
| `.claude/settings.json` | NONE found via in-repo text reference scan (path + unique basename fallback) | **unused / unclear** |
| `.claude_bk/settings.json` | NONE found via in-repo text reference scan (path + unique basename fallback) | **unused / unclear** |
| `.vscode/settings.json` | NONE found via in-repo text reference scan (path + unique basename fallback) | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/01 - Credit_conversion_summary.json` | audio/rastan_music_dump/conversion_attempts/conversion_attempt_manifest.md:7; audio/rastan_music_dump/conversion_attempts/pipeline_summary.json:400 | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/02 - Broken The Promises (Opening)_conversion_summary.json` | audio/rastan_music_dump/conversion_attempts/conversion_attempt_manifest.md:8; audio/rastan_music_dump/conversion_attempts/pipeline_summary.json:408 | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/03 - Aggressive World (Scene 1)_conversion_summary.json` | audio/rastan_music_dump/conversion_attempts/conversion_attempt_manifest.md:9; audio/rastan_music_dump/conversion_attempts/pipeline_summary.json:416 | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/04 - Bad Bible (Name Regist)_conversion_summary.json` | audio/rastan_music_dump/conversion_attempts/conversion_attempt_manifest.md:10; audio/rastan_music_dump/conversion_attempts/pipeline_summary.json:424 | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/05 - Re-In-Carnation (Scene 2)_conversion_summary.json` | audio/rastan_music_dump/conversion_attempts/conversion_attempt_manifest.md:11; audio/rastan_music_dump/conversion_attempts/pipeline_summary.json:432 | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/06 - The Devil Boss Carnival (Scene 3 Boss)_conversion_summary.json` | audio/rastan_music_dump/conversion_attempts/conversion_attempt_manifest.md:12; audio/rastan_music_dump/conversion_attempts/pipeline_summary.json:440 | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/07 - Scene Clear_conversion_summary.json` | audio/rastan_music_dump/conversion_attempts/conversion_attempt_manifest.md:13; audio/rastan_music_dump/conversion_attempts/pipeline_summary.json:448 | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/08 - Final Destroy (Scene 3 Round 6 Boss)_conversion_summary.json` | audio/rastan_music_dump/conversion_attempts/conversion_attempt_manifest.md:14; audio/rastan_music_dump/conversion_attempts/pipeline_summary.json:456 | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/09 - The Man Of Saga (Ending)_conversion_summary.json` | audio/rastan_music_dump/conversion_attempts/conversion_attempt_manifest.md:15; audio/rastan_music_dump/conversion_attempts/pipeline_summary.json:464 | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/direct_fur_generation_summary.json` | audio/rastan_music_dump/conversion_attempts/fur_generation_inventory.md:13 | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/extracted_events/01 - Credit_events.json` | docs/design/Cody_direct_fur_generation_report.md:51; Chad_history_breifing.md:28112; audio/rastan_music_dump/conversion_attempts/direct_fur_generation_summary.json:20 | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/extracted_events/02 - Broken The Promises (Opening)_events.json` | docs/design/Cody_direct_fur_generation_report.md:52; Chad_history_breifing.md:28113; audio/rastan_music_dump/conversion_attempts/direct_fur_generation_summary.json:38 | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/extracted_events/03 - Aggressive World (Scene 1)_events.json` | docs/design/Cody_direct_fur_generation_report.md:53; Chad_history_breifing.md:28114; audio/rastan_music_dump/conversion_attempts/direct_fur_generation_summary.json:56 | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/extracted_events/04 - Bad Bible (Name Regist)_events.json` | docs/design/Cody_direct_fur_generation_report.md:54; Chad_history_breifing.md:28115; audio/rastan_music_dump/conversion_attempts/direct_fur_generation_summary.json:74 | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/extracted_events/05 - Re-In-Carnation (Scene 2)_events.json` | docs/design/Cody_direct_fur_generation_report.md:55; Chad_history_breifing.md:28116; audio/rastan_music_dump/conversion_attempts/direct_fur_generation_summary.json:92 | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/extracted_events/06 - The Devil Boss Carnival (Scene 3 Boss)_events.json` | docs/design/Cody_direct_fur_generation_report.md:56; Chad_history_breifing.md:28117; audio/rastan_music_dump/conversion_attempts/direct_fur_generation_summary.json:110 | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/extracted_events/07 - Scene Clear_events.json` | docs/design/Cody_direct_fur_generation_report.md:57; Chad_history_breifing.md:28118; audio/rastan_music_dump/conversion_attempts/direct_fur_generation_summary.json:128 | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/extracted_events/08 - Final Destroy (Scene 3 Round 6 Boss)_events.json` | docs/design/Cody_direct_fur_generation_report.md:58; Chad_history_breifing.md:28119; audio/rastan_music_dump/conversion_attempts/direct_fur_generation_summary.json:146 | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/extracted_events/09 - The Man Of Saga (Ending)_events.json` | docs/design/Cody_direct_fur_generation_report.md:59; Chad_history_breifing.md:28120; audio/rastan_music_dump/conversion_attempts/direct_fur_generation_summary.json:164 | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/pipeline_summary.json` | docs/design/Cody_rastan_music_dump_conversion_report.md:92; Chad_history_breifing.md:27865 | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/vgm2fur_conversion_results.json` | NONE found via in-repo text reference scan (path + unique basename fallback) | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/vgm2fur_file_statuses.json` | NONE found via in-repo text reference scan (path + unique basename fallback) | **unused / unclear** |
| `audio/rastan_music_dump/conversion_attempts/vgz_to_midi_run_summary.json` | docs/design/Cody_vgz_to_midi_conversion_report.md:60; Chad_history_breifing.md:27960 | **unused / unclear** |
| `docs/replacement_inventory/frontend_window_replacement_inventory.json` | AGENTS_LOG.md:14204; AGENTS_LOG.md:14211; docs/design/Cody_sgdk_era_init_archaeology.md:1877; docs/design/Cody_sgdk_era_init_archaeology.md:11100; docs/design/Cody_sgdk_era_init_archaeology.md:11101; docs/design/Cody_sgdk_era_init_archaeology.md:11102; docs/design/Cody_sgdk_era_init_archaeology.md:11103; docs/design/Cody_sgdk_era_init_archaeology.md:11104 | **unused / unclear** |
| `docs/replacement_inventory/fullgame_window_replacement_inventory.json` | AGENTS_LOG.md:14249; AGENTS_LOG.md:14614; AGENTS_LOG.md:16487; docs/design/Cody_full_playthrough_scene_state_validation.md:15; docs/design/Cody_sgdk_era_init_archaeology.md:1880; docs/design/Cody_sgdk_era_init_archaeology.md:11476; docs/design/Cody_sgdk_era_init_archaeology.md:11477; docs/design/Cody_sgdk_era_init_archaeology.md:11478 | **unused / unclear** |
| `docs/research/semantic_entry_manifest.json` | tools/check_semantic_entries.py:145; AGENTS_LOG.md:18301; AGENTS_LOG.md:18334; AGENTS_LOG.md:18358; AGENTS_LOG.md:18391; AGENTS_LOG.md:18483; docs/design/Cody_sgdk_era_init_archaeology.md:399; docs/design/Cody_sgdk_era_init_archaeology.md:12675 | **sgdk** |
| `specs/audio_rules.json` | AGENTS_LOG.md:27131; docs/design/Cody_build_pipeline_address_space_audit.md:43; Chad_history_breifing.md:54648 | **unused / unclear** |
| `specs/debug_bus.json` | AGENTS_LOG.md:27132; docs/design/Cody_build_pipeline_address_space_audit.md:44; Chad_history_breifing.md:54649 | **unused / unclear** |
| `specs/extraction_manifest.json` | AGENTS_LOG.md:27133; docs/design/Cody_build_pipeline_address_space_audit.md:45; docs/project/rom_source_reference.md:35; docs/project/variant_reference.md:43; Chad_history_breifing.md:54650 | **unused / unclear** |
| `specs/fixups.json` | AGENTS_LOG.md:27134; docs/design/Cody_build_pipeline_address_space_audit.md:46; Chad_history_breifing.md:54651 | **unused / unclear** |
| `specs/gfx_rules.json` | AGENTS_LOG.md:9791; AGENTS_LOG.md:27135; docs/design/Cody_build_pipeline_address_space_audit.md:47; docs/design/Cody_sgdk_era_init_archaeology.md:22995; docs/design/Cody_sgdk_era_init_archaeology.md:23007; docs/design/Cody_sgdk_era_init_archaeology.md:23019; docs/design/Cody_sgdk_era_init_archaeology.md:40595; docs/design/Cody_sgdk_era_init_archaeology.md:76206 | **unused / unclear** |
| `specs/layout.json` | AGENTS_LOG.md:27136; docs/design/Cody_build_pipeline_address_space_audit.md:48; docs/design/Cody_sgdk_era_init_archaeology.md:40596; docs/design/Cody_sgdk_era_init_archaeology.md:76207; Chad_history_breifing.md:54653 | **unused / unclear** |
| `specs/objects.json` | AGENTS_LOG.md:27137; docs/design/Cody_build_pipeline_address_space_audit.md:49; docs/design/Cody_sgdk_era_init_archaeology.md:40597; docs/design/Cody_sgdk_era_init_archaeology.md:76208; Chad_history_breifing.md:54654 | **unused / unclear** |
| `specs/rastan_direct_remap.json` | apps/rastan-direct/Makefile:9; AGENTS_LOG.md:26217; AGENTS_LOG.md:26247; AGENTS_LOG.md:26250; AGENTS_LOG.md:26382; AGENTS_LOG.md:26398; AGENTS_LOG.md:26400; AGENTS_LOG.md:26408 | **rastan-direct** |
| `specs/refactor_rules.json` | AGENTS_LOG.md:27139; docs/design/Cody_build_pipeline_address_space_audit.md:51; docs/design/Cody_sgdk_era_init_archaeology.md:40599; docs/design/Cody_sgdk_era_init_archaeology.md:40608; docs/design/Cody_sgdk_era_init_archaeology.md:76210; docs/design/Cody_sgdk_era_init_archaeology.md:76219; Chad_history_breifing.md:54656 | **unused / unclear** |
| `specs/relocations.json` | AGENTS_LOG.md:27140; docs/design/Cody_build_pipeline_address_space_audit.md:52; docs/design/Cody_sgdk_era_init_archaeology.md:40600; docs/design/Cody_sgdk_era_init_archaeology.md:40609; docs/design/Cody_sgdk_era_init_archaeology.md:76211; docs/design/Cody_sgdk_era_init_archaeology.md:76220; Chad_history_breifing.md:54657 | **unused / unclear** |
| `specs/runtime_config.json` | AGENTS_LOG.md:27141; docs/design/Cody_build_pipeline_address_space_audit.md:53; docs/design/Cody_sgdk_era_init_archaeology.md:40601; docs/design/Cody_sgdk_era_init_archaeology.md:40610; docs/design/Cody_sgdk_era_init_archaeology.md:76212; docs/design/Cody_sgdk_era_init_archaeology.md:76221; Chad_history_breifing.md:54658 | **unused / unclear** |
| `specs/startup_title_remap.json` | tools/check_semantic_entries.py:146; AGENTS_LOG.md:205; AGENTS_LOG.md:216; AGENTS_LOG.md:222; AGENTS_LOG.md:2524; AGENTS_LOG.md:4652; AGENTS_LOG.md:4696; AGENTS_LOG.md:6215 | **sgdk** |
| `specs/subsystem_modes.json` | AGENTS_LOG.md:27143; docs/design/Cody_build_pipeline_address_space_audit.md:55; docs/design/Cody_sgdk_era_init_archaeology.md:40612; docs/design/Cody_sgdk_era_init_archaeology.md:76223; Chad_history_breifing.md:54660 | **unused / unclear** |
| `specs/symbols.json` | AGENTS_LOG.md:27144; docs/design/Cody_build_pipeline_address_space_audit.md:56; docs/design/Cody_sgdk_era_init_archaeology.md:40613; docs/design/Cody_sgdk_era_init_archaeology.md:76224; Chad_history_breifing.md:54661 | **unused / unclear** |
| `specs/validation_rules.json` | AGENTS_LOG.md:27145; docs/design/Cody_build_pipeline_address_space_audit.md:57; docs/design/Cody_sgdk_era_init_archaeology.md:40614; docs/design/Cody_sgdk_era_init_archaeology.md:76225; Chad_history_breifing.md:54662 | **unused / unclear** |
| `specs/variants.json` | AGENTS_LOG.md:27146; docs/design/Cody_build_pipeline_address_space_audit.md:58; docs/design/Cody_sgdk_era_init_archaeology.md:40621; docs/design/Cody_sgdk_era_init_archaeology.md:76232; docs/project/variant_reference.md:42; Chad_history_breifing.md:54663 | **unused / unclear** |
| `tools/ghidra/lab313ru_latest.json` | NONE found via in-repo text reference scan (path + unique basename fallback) | **unused / unclear** |
| `tools/ghidra/lab313ru_latest_actual.json` | AGENTS_LOG.md:12780 | **unused / unclear** |
| `tools/ghidra/lab313ru_releases.json` | NONE found via in-repo text reference scan (path + unique basename fallback) | **unused / unclear** |
| `tools/ghidra/lab313ru_releases_actual.json` | AGENTS_LOG.md:12779 | **unused / unclear** |
| `tools/mame/cheat/output.json` | NONE found via in-repo text reference scan (path + unique basename fallback) | **unused / unclear** |
| `tools/mame/plugins/rastanmon/plugin.json` | NONE found via in-repo text reference scan (path + unique basename fallback) | **unused / unclear** |
| `tools/sgdk/project/template/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/project/template/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/project/template/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/advanced/sprites-sharing-tiles/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/advanced/sprites-sharing-tiles/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/advanced/sprites-sharing-tiles/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/advanced/tile-animation/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/advanced/tile-animation/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/advanced/tile-animation/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/basics/hello-world/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/basics/hello-world/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/basics/hello-world/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/basics/image/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/basics/image/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/basics/image/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/benchmark/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/benchmark/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/benchmark/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/bitmap/cube-3D/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/bitmap/cube-3D/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/bitmap/cube-3D/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/bitmap/partic/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/bitmap/partic/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/bitmap/partic/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/demo/bad-apple/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/demo/bad-apple/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/demo/bad-apple/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/demo/starfield-donut/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/demo/starfield-donut/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/demo/starfield-donut/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/flash-save/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/flash-save/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/flash-save/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/fx/h-int/scaling/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/fx/h-int/scaling/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/fx/h-int/scaling/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/fx/h-int/wobble/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/fx/h-int/wobble/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/fx/h-int/wobble/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/fx/hilight-shadow/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/fx/hilight-shadow/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/fx/hilight-shadow/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/fx/scroll/linescroll/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/fx/scroll/linescroll/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/fx/scroll/linescroll/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/fx/sprite-masking/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/fx/sprite-masking/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/fx/sprite-masking/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/game/platformer/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/game/platformer/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/game/platformer/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/game/sonic/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/game/sonic/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/game/sonic/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/joy-test/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/joy-test/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/joy-test/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/megawifi/basic/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/megawifi/basic/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/megawifi/basic/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/megawifi/menu/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/megawifi/menu/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/megawifi/menu/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/snd/sound-test/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/snd/sound-test/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/snd/sound-test/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/snd/xgm-player/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/snd/xgm-player/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/snd/xgm-player/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/sys/console/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/sys/console/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/sys/console/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/sys/multitasking/.vscode/c_cpp_properties.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/sys/multitasking/.vscode/extensions.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |
| `tools/sgdk/sample/sys/multitasking/.vscode/settings.json` | path-context evidence: tools/sgdk/* (SGDK template/sample tree) | **sgdk** |

## Phase 3 - Summary
| classification | count | files |
|---|---:|---|
| rastan-direct | 1 | `specs/rastan_direct_remap.json` |
| sgdk | 77 | `docs/research/semantic_entry_manifest.json`, `specs/startup_title_remap.json`, `tools/sgdk/project/template/.vscode/c_cpp_properties.json`, `tools/sgdk/project/template/.vscode/extensions.json`, `tools/sgdk/project/template/.vscode/settings.json`, `tools/sgdk/sample/advanced/sprites-sharing-tiles/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/advanced/sprites-sharing-tiles/.vscode/extensions.json`, `tools/sgdk/sample/advanced/sprites-sharing-tiles/.vscode/settings.json`, `tools/sgdk/sample/advanced/tile-animation/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/advanced/tile-animation/.vscode/extensions.json`, `tools/sgdk/sample/advanced/tile-animation/.vscode/settings.json`, `tools/sgdk/sample/basics/hello-world/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/basics/hello-world/.vscode/extensions.json`, `tools/sgdk/sample/basics/hello-world/.vscode/settings.json`, `tools/sgdk/sample/basics/image/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/basics/image/.vscode/extensions.json`, `tools/sgdk/sample/basics/image/.vscode/settings.json`, `tools/sgdk/sample/benchmark/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/benchmark/.vscode/extensions.json`, `tools/sgdk/sample/benchmark/.vscode/settings.json`, `tools/sgdk/sample/bitmap/cube-3D/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/bitmap/cube-3D/.vscode/extensions.json`, `tools/sgdk/sample/bitmap/cube-3D/.vscode/settings.json`, `tools/sgdk/sample/bitmap/partic/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/bitmap/partic/.vscode/extensions.json`, `tools/sgdk/sample/bitmap/partic/.vscode/settings.json`, `tools/sgdk/sample/demo/bad-apple/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/demo/bad-apple/.vscode/extensions.json`, `tools/sgdk/sample/demo/bad-apple/.vscode/settings.json`, `tools/sgdk/sample/demo/starfield-donut/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/demo/starfield-donut/.vscode/extensions.json`, `tools/sgdk/sample/demo/starfield-donut/.vscode/settings.json`, `tools/sgdk/sample/flash-save/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/flash-save/.vscode/extensions.json`, `tools/sgdk/sample/flash-save/.vscode/settings.json`, `tools/sgdk/sample/fx/h-int/scaling/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/fx/h-int/scaling/.vscode/extensions.json`, `tools/sgdk/sample/fx/h-int/scaling/.vscode/settings.json`, `tools/sgdk/sample/fx/h-int/wobble/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/fx/h-int/wobble/.vscode/extensions.json`, `tools/sgdk/sample/fx/h-int/wobble/.vscode/settings.json`, `tools/sgdk/sample/fx/hilight-shadow/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/fx/hilight-shadow/.vscode/extensions.json`, `tools/sgdk/sample/fx/hilight-shadow/.vscode/settings.json`, `tools/sgdk/sample/fx/scroll/linescroll/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/fx/scroll/linescroll/.vscode/extensions.json`, `tools/sgdk/sample/fx/scroll/linescroll/.vscode/settings.json`, `tools/sgdk/sample/fx/sprite-masking/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/fx/sprite-masking/.vscode/extensions.json`, `tools/sgdk/sample/fx/sprite-masking/.vscode/settings.json`, `tools/sgdk/sample/game/platformer/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/game/platformer/.vscode/extensions.json`, `tools/sgdk/sample/game/platformer/.vscode/settings.json`, `tools/sgdk/sample/game/sonic/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/game/sonic/.vscode/extensions.json`, `tools/sgdk/sample/game/sonic/.vscode/settings.json`, `tools/sgdk/sample/joy-test/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/joy-test/.vscode/extensions.json`, `tools/sgdk/sample/joy-test/.vscode/settings.json`, `tools/sgdk/sample/megawifi/basic/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/megawifi/basic/.vscode/extensions.json`, `tools/sgdk/sample/megawifi/basic/.vscode/settings.json`, `tools/sgdk/sample/megawifi/menu/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/megawifi/menu/.vscode/extensions.json`, `tools/sgdk/sample/megawifi/menu/.vscode/settings.json`, `tools/sgdk/sample/snd/sound-test/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/snd/sound-test/.vscode/extensions.json`, `tools/sgdk/sample/snd/sound-test/.vscode/settings.json`, `tools/sgdk/sample/snd/xgm-player/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/snd/xgm-player/.vscode/extensions.json`, `tools/sgdk/sample/snd/xgm-player/.vscode/settings.json`, `tools/sgdk/sample/sys/console/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/sys/console/.vscode/extensions.json`, `tools/sgdk/sample/sys/console/.vscode/settings.json`, `tools/sgdk/sample/sys/multitasking/.vscode/c_cpp_properties.json`, `tools/sgdk/sample/sys/multitasking/.vscode/extensions.json`, `tools/sgdk/sample/sys/multitasking/.vscode/settings.json` |
| shared | 0 | NONE |
| unused / unclear | 48 | `.claude/settings.json`, `.claude_bk/settings.json`, `.vscode/settings.json`, `audio/rastan_music_dump/conversion_attempts/01 - Credit_conversion_summary.json`, `audio/rastan_music_dump/conversion_attempts/02 - Broken The Promises (Opening)_conversion_summary.json`, `audio/rastan_music_dump/conversion_attempts/03 - Aggressive World (Scene 1)_conversion_summary.json`, `audio/rastan_music_dump/conversion_attempts/04 - Bad Bible (Name Regist)_conversion_summary.json`, `audio/rastan_music_dump/conversion_attempts/05 - Re-In-Carnation (Scene 2)_conversion_summary.json`, `audio/rastan_music_dump/conversion_attempts/06 - The Devil Boss Carnival (Scene 3 Boss)_conversion_summary.json`, `audio/rastan_music_dump/conversion_attempts/07 - Scene Clear_conversion_summary.json`, `audio/rastan_music_dump/conversion_attempts/08 - Final Destroy (Scene 3 Round 6 Boss)_conversion_summary.json`, `audio/rastan_music_dump/conversion_attempts/09 - The Man Of Saga (Ending)_conversion_summary.json`, `audio/rastan_music_dump/conversion_attempts/direct_fur_generation_summary.json`, `audio/rastan_music_dump/conversion_attempts/extracted_events/01 - Credit_events.json`, `audio/rastan_music_dump/conversion_attempts/extracted_events/02 - Broken The Promises (Opening)_events.json`, `audio/rastan_music_dump/conversion_attempts/extracted_events/03 - Aggressive World (Scene 1)_events.json`, `audio/rastan_music_dump/conversion_attempts/extracted_events/04 - Bad Bible (Name Regist)_events.json`, `audio/rastan_music_dump/conversion_attempts/extracted_events/05 - Re-In-Carnation (Scene 2)_events.json`, `audio/rastan_music_dump/conversion_attempts/extracted_events/06 - The Devil Boss Carnival (Scene 3 Boss)_events.json`, `audio/rastan_music_dump/conversion_attempts/extracted_events/07 - Scene Clear_events.json`, `audio/rastan_music_dump/conversion_attempts/extracted_events/08 - Final Destroy (Scene 3 Round 6 Boss)_events.json`, `audio/rastan_music_dump/conversion_attempts/extracted_events/09 - The Man Of Saga (Ending)_events.json`, `audio/rastan_music_dump/conversion_attempts/pipeline_summary.json`, `audio/rastan_music_dump/conversion_attempts/vgm2fur_conversion_results.json`, `audio/rastan_music_dump/conversion_attempts/vgm2fur_file_statuses.json`, `audio/rastan_music_dump/conversion_attempts/vgz_to_midi_run_summary.json`, `docs/replacement_inventory/frontend_window_replacement_inventory.json`, `docs/replacement_inventory/fullgame_window_replacement_inventory.json`, `specs/audio_rules.json`, `specs/debug_bus.json`, `specs/extraction_manifest.json`, `specs/fixups.json`, `specs/gfx_rules.json`, `specs/layout.json`, `specs/objects.json`, `specs/refactor_rules.json`, `specs/relocations.json`, `specs/runtime_config.json`, `specs/subsystem_modes.json`, `specs/symbols.json`, `specs/validation_rules.json`, `specs/variants.json`, `tools/ghidra/lab313ru_latest.json`, `tools/ghidra/lab313ru_latest_actual.json`, `tools/ghidra/lab313ru_releases.json`, `tools/ghidra/lab313ru_releases_actual.json`, `tools/mame/cheat/output.json`, `tools/mame/plugins/rastanmon/plugin.json` |

## Phase 4 - Integrity
- Repo read access: **YES**
- No files modified (except required output doc + AGENTS_LOG append): **YES**
- Total JSON files enumerated: **126**

## Notes On Evidence Source
- Consumer scan used in-repo fixed-string reference matches (full relative path, plus unique-basename fallback when needed).
- For `tools/sgdk/*` JSON files with no in-repo reader lines, classification evidence is path-context authorship in the SGDK template/sample tree.
