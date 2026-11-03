# Cody — KNOWN_FINDINGS Curation Candidates (Task 1: Inventory + Extraction)

## Scope and Bootstrap Acknowledgment
- Task mode: **inventory + extraction only** (no synthesis, no deduplication, no KF numbering).
- `KNOWN_FINDINGS.md` bootstrap state at task start: **rulebook preamble + KF-001 only**.
- This document is a candidate list for Tighe/Chad review before Task 2 writes any new KF entries.

## Phase 1 — Inventory

### Inventory Summary
- Total in-scope files inventoried: **403**
- `FINDINGS_SUBSTANTIAL`: **23**
- `FINDINGS_PARTIAL`: **6**
- `NO_FINDINGS`: **369**
- `INFRASTRUCTURE_ONLY`: **5**

### Full Inventory (all in-scope files)
| File path | Classification | Estimated candidates | Notes |
|---|---|---:|---|
| `AGENTS_LOG.md` | FINDINGS_SUBSTANTIAL | 2 | High-noise source; runtime/system observations only per admissibility restriction. |
| `AGENTS.md` | FINDINGS_SUBSTANTIAL | 3 | Contains durable architecture/hardware mapping decisions mixed with workflow guidance. |
| `AGENT_GUIDE.md` | INFRASTRUCTURE_ONLY | 0 | Rules/template/architecture policy content; not candidate source for durable behavior entries in this task. |
| `ARCHITECTURE.md` | INFRASTRUCTURE_ONLY | 0 | Rules/template/architecture policy content; not candidate source for durable behavior entries in this task. |
| `Chad_history_breifing.md` | FINDINGS_PARTIAL | 0 | Read and screened; no additional durable candidate survived extraction filter in this pass. |
| `CLOSED_ISSUES.md` | FINDINGS_SUBSTANTIAL | 3 | Closure metadata excluded; only durable behavior statements considered. |
| `CURRENT_STATE.md` | FINDINGS_PARTIAL | 0 | Read and screened; no additional durable candidate survived extraction filter in this pass. |
| `GRAPHICS_STATUS.md` | FINDINGS_PARTIAL | 0 | Read and screened; no additional durable candidate survived extraction filter in this pass. |
| `KNOWN_FINDINGS.md` | INFRASTRUCTURE_ONLY | 0 | Destination file; read for bootstrap-state awareness only (KF-001 present). |
| `Master Diagnostic Debt.md` | FINDINGS_SUBSTANTIAL | 3 | Meta-findings about evidence contamination and diagnostic limitations. |
| `OPEN_ISSUES.md` | FINDINGS_SUBSTANTIAL | 4 | Issue bookkeeping excluded; only system-behavior statements in issue bodies considered. |
| `PROMPT_TEMPLATE.md` | INFRASTRUCTURE_ONLY | 0 | Rules/template/architecture policy content; not candidate source for durable behavior entries in this task. |
| `README.md` | FINDINGS_PARTIAL | 0 | Read and screened; no additional durable candidate survived extraction filter in this pass. |
| `REMOVALS.md` | FINDINGS_PARTIAL | 0 | Read and screened; no additional durable candidate survived extraction filter in this pass. |
| `RULES.md` | INFRASTRUCTURE_ONLY | 0 | Rules/template/architecture policy content; not candidate source for durable behavior entries in this task. |
| `TODO.md` | FINDINGS_PARTIAL | 0 | Read and screened; no additional durable candidate survived extraction filter in this pass. |
| `docs/design/0x5a4de_hook_crash_fix_report.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_3BB60_to_3ABD0_control_flow.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_3c516_caller_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_BM002_runtime_failure_investigation.md` | FINDINGS_SUBSTANTIAL | 3 | Primary source for coordinate-space mismatch behavior findings. |
| `docs/design/Andy_OPEN011_verification_report.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_OPEN012_bookmark_coordinate_model_design.md` | FINDINGS_SUBSTANTIAL | 4 | Primary source for coordinate model replacement semantics. |
| `docs/design/Andy_a5_initialization_analysis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_active_entry_classifications.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_address_lookup_tool_design.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_address_map_artifact_design.md` | FINDINGS_SUBSTANTIAL | 2 | Address map lookup behavior and non-ROM classification semantics. |
| `docs/design/Andy_arcade_execution_reachability_vs_static_checkerboard.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_arcade_hw_io_stub_strategy.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_arcade_state_producer_nonprogression_diagnosis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_arcade_vs_genesis_profiling_correction.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_arcade_workram_relocation_analysis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_audit_cody_scene_and_sprite_analysis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_audit_of_cody_rastan_direct_video_backbone.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_bg_blockcopy_hook_warm_restart_analysis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_bg_fill_hook_no_visible_output_diagnosis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_bg_fill_hook_post_rts_no_change_diagnosis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_bg_hook_no_visible_change_diagnosis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_boot_s_160_deletion_viability.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_bootstrap_symbol_visibility.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_build337_full_per_frame_vdp_write_census.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_build53_d0_origin_root_cause.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_build53_update_inputs_root_cause.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_build54_hvc_writer_root_cause.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_build54_palette_root_cause.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_build55_active_palette_writer_classification.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_build55_palette_045dae_redesign.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_build55_palette_translation_design.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_build_0027_runtime_diagnosis_scroll_plan.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_build_0028_fg_hook_failure_analysis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_build_33_diagnostic.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_build_34_exodus_rendering_failure.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_build_36_exodus_rendering_analysis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_build_36_multiframe_analysis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_build_pipeline_determinism_gate_design.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_coverage_invariant_analysis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_crash_handler_spec.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_cwindow_clear_hook_spec.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_d00778_write_path_analysis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_d_register_base_pointer_trace.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_default_path_3c950_hook_spec.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_descriptor_model_validation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_dffffe_exact_write_pc_diagnosis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_dffffe_hardware_identification.md` | FINDINGS_SUBSTANTIAL | 2 | Unmapped open-bus determination for 0xDFFFFE writes. |
| `docs/design/Andy_diagnostic_bookmark_helper_design.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_diagnostic_bookmark_postpatch_invariant_design.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_diagnostic_debt_audit.md` | FINDINGS_SUBSTANTIAL | 2 | Diagnostic contamination classes and high-risk masking behavior. |
| `docs/design/Andy_direct_execution_entry_symbol_design.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_dispatcher_map_analysis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_early_control_flow_loop_diagnosis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_early_title_control_flow_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_fg_regression_after_commit_removal.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_final_architecture_transition_plan_no_scaffolding.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_final_pc080sn_hook_strategy.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_first_arcade_driven_bg_hook_plan.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_genesis_bss_relocation_and_wram_map_design.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_graphics_pipeline_break_diagnosis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_img02_display_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_img02_display_audit_corrected.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_init_staging_state_split_design.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_interrupt_enable_timing.md` | FINDINGS_SUBSTANTIAL | 2 | Interrupt-enable ordering and ownership behavior. |
| `docs/design/Andy_load_scene_tiles_sr_analysis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_mode_based_pc080sn_tile_residency_system.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_nametable_composition_path_classification.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_number_renderer_3c2e2_hook_spec.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_p1_p2_hook_closure_design.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_p1_p2_prerequisite_verification.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_palette_diagnosis_after_recent_fixes.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_pc080sn_data_collection_spec.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_pc080sn_readback_interception_strategy.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_pc080sn_tile_preload_system_design.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_pc080sn_wram_write_path_diagnosis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_pc0900j_sprite_correctness_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_pc090oj_full_subsystem_design.md` | FINDINGS_SUBSTANTIAL | 2 | Sprite subsystem static limits and unresolved runtime-surface facts. |
| `docs/design/Andy_pc090oj_implementation_spec.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_pc090oj_reconciliation_v2.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_pc090oj_writer_classification_ledger.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_per_mode_vram_working_set_profiling_plan.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_polling_loop_investigation.md` | FINDINGS_SUBSTANTIAL | 4 | Primary watchdog mechanism and kick-site behavior evidence. |
| `docs/design/Andy_post_d2_fix_no_visible_change_diagnosis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_post_plane_b_fix_palette_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_rainbow_islands_comparative_translation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_rastan_arcade_scrolling_and_genesis_translation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_rastan_arcade_sound_and_rainbow_bridge.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_rastan_credit_start_flow_diagnosis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_rastan_dip_defaults_and_flip_behavior.md` | FINDINGS_SUBSTANTIAL | 2 | DIP/flip active-low mapping behavior facts. |
| `docs/design/Andy_rastan_direct_display_tightening_against_rainbow.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_rastan_direct_runtime_decomposition.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_rastan_direct_video_bringup_plan.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_rastan_sound_command_execution_verified.md` | FINDINGS_SUBSTANTIAL | 2 | Sound command format and dispatch-path behavior. |
| `docs/design/Andy_reconcile_pc080sn_ground_truth.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_reset_path_root_cause.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_scene_mode_transition_trigger_spec.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_scene_transition_readiness.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_scene_trigger_runtime_diagnosis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_sgdk_vs_rastan_direct_address_mapping_diagnosis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_slot_reservation_removal_classification.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_ssp_corruption_source_exposed_by_step4.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_stride8_sibling_hook_spec.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_stripe_root_cause_build0046.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_tc0040ioc_and_arcade_execution_plan.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_test_pattern_execution_verification.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_text_writer_3c3fe_hook_spec.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_text_writer_3c4d2_hook_spec.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_tile_index_alignment_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_tile_mapping_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_tile_reference_correctness_under_mode_residency.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_tilemap_correctness_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_title_hook_failure_analysis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_title_screen_zero_input_diagnosis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_vblank_commit_audit_corrected_spec.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_vblank_efficiency_audit_and_transition_plan.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_vblank_interrupt_block_diagnosis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_verify_fg_top_band_artifact.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_verify_load_scene_tiles_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Andy_vram_tile_offset_analysis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_BM001_insert.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_BM001_revert_BM002_insert.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_BM002_revert.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_BM003_insert.md` | FINDINGS_SUBSTANTIAL | 3 | Real-runtime positive-control evidence for bookmark instrument behavior. |
| `docs/design/Cody_BM003_revert.md` | FINDINGS_SUBSTANTIAL | 2 | Revert lifecycle behavior evidence (byte-identity/state-file deletion). |
| `docs/design/Cody_OPEN012_OPEN013_implementation.md` | FINDINGS_SUBSTANTIAL | 3 | Implementation evidence for schema and invariant behavior under bookmarks_v2. |
| `docs/design/Cody_a5_2c_seed_check.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_a5_init_before_first_arcade_tick.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_a5_init_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_a5_lifecycle_trace.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_a5_wram_base_redirect.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_address_map_artifact_implementation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_andy_corrections_build_0026.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_arcade_tilemap_ram_dump.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_arcade_workram_relocation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_bg_blockcopy_hook_implementation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_bg_descriptor_column_advance_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_bg_descriptor_row_reset_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_bg_fg_dirty_flag_implementation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_bg_fg_dirty_guard_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_bg_fill_hook_implementation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_bg_row_dirty_strip_commit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_boot_comparison_trace.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_boot_s_160_deletion_implementation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_bootstrap_symbol_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_bss_vma_wram_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build0049_first_exception_trace.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build337_full_per_frame_vdp_write_census.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build53_emit_slot_caller_trace.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build53_rts_caller_chain.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build53_wildpc_evidence.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build54_cram_white_palette_evidence.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build54_hvc_actual_writer_trace.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build54_hvc_writer_search.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build54_nop_provenance_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build54_palette_payload_evidence_gap.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build55_03bc84_origin_archaeology.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build55_active_palette_producer_discovery.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build55_mame_palette_format_evidence.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build55_mame_palette_runtime_trace.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build55_palette_bank_mapping_evidence.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build55_palette_fix_shape_evidence.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build55_palette_implementation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build55_palette_phase_a_block.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build55_palette_pipeline_runtime_localization.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build55_video_30fps_debug_windows.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build55b_palette_implementation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build55b_video_30fps_debug_windows.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build56_sprite_palette_bank_mapping_todo.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build58_offset_graphics_evidence.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build58b_nametable_dump_evidence.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build58c_visible_state_acquisition.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build59_runtime_state_comparison.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build59_video_30fps_debug_windows.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build60_regression_fix_and_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build60_regression_forensics.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build_0026_hw_write_nop_patch_report.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build_0027_clrw_nop_patch_report.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build_0028_scroll_redirect_and_fg_hook_report.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build_0029_cwindow_clear_hook.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build_0029_fg_cwindow_trace_report.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build_0029_scroll_rewrite_and_cwindow_hook.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build_0029_scroll_rewrite_and_cwindow_hook_report.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build_32_screenshot_extraction.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build_pipeline_address_space_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build_pipeline_determinism_gate_implementation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build_pipeline_disasm_and_trace.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_build_pipeline_investigation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_coin_pulse_and_start_bit_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_coverage_invariant_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_crash_handler_implementation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_d00778_vs_delay_loop_ordering_trace.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_decomposition_implementation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_delay_loop_entry_trace.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_diagnostic_bookmark_postpatch_invariant_implementation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_diagnostic_debt_audit.md` | FINDINGS_SUBSTANTIAL | 1 | Corroborative diagnostic contamination evidence. |
| `docs/design/Cody_diagnostic_palette_replacement.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_direct_execution_spec_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_direct_fur_generation_report.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_exchange_summary_2026-04-08.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_exodus_frame_extraction.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_exodus_frame_extraction_build_53_2.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_exodus_frame_extraction_build_54_11_16.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_fg_hook_and_scroll_redirect.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_fg_row0_bringup_stripe_removal.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_first_arcade_execution_bringup.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_fix_arcade_tick_jsr_rte_mismatch.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_fix_bg_fill_patch_rts_tail.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_fu1_arcade_trace_510EA_510F4.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_fu1_playtrace_script.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_full_arcade_scene_state_taxonomy.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_full_playthrough_scene_state_validation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_genesis_bss_relocation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_genesis_bss_relocation_impl_report.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_genesis_staged_buffer_dump.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_ghidra_arcade_function_index.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_ghidra_arcade_reference.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_hook_closure_implementation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_independent_vram_budget_verification.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_json_spec_inventory.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_legacy_vdp_writer_removal.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_load_scene_tiles_boot_preload_implementation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_load_scene_tiles_register_clobber_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_mame_pc080sn_extract.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_move_tile_commit_to_top_level_vblank.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_no_c_direct_execution_proposal.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_no_sgdk_direct_execution_proposal.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_palette_deletion_context_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_palette_source_conversion_evidence_review.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_path_a_countdown_reset_confirmation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_pc080sn_bg_hook_implementation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_pc080sn_dest_trace.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_pc080sn_readback_bypass.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_pc080sn_writer_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_pc080sn_writer_audit_report.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_pc090oj_implementation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_phase_a_count_guard_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_phase_a_nop_coverage.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_plane_a_init_clear.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_plane_b_base_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_postpatch_invariant_inspection.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_rainbow_islands_sound_translation_analysis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_rainbow_islands_vdp_template_analysis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_rastan_direct_final_rom_boot_byte_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_rastan_direct_forced_z80_tone_debug.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_rastan_direct_patcher_reuse_and_extension.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_rastan_direct_permanent_rom_layout_and_numbered_builds.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_rastan_direct_stale_bin_pipeline_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_rastan_direct_video_backbone_bringup.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_rastan_music_dump_conversion_report.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_rastan_vs_rainbow_tilemap_mismatch.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_registers_video_extraction.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_remove_fg_dirty_infrastructure.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_remove_fg_full_plane_commit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_remove_hook_plane_a_hits.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_reset_path_runtime_trace.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_scene_load_sr_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_scene_preload_restore.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_scene_trigger_implementation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_scene_trigger_slow_path_register_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_seed_clear_ordering_trace.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_sgdk_era_init_archaeology.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_slot_reservation_removal_implementation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_stale_symbol_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_startup_test_pattern_removal.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_strip_index_destination_offset_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_tc0040ioc_verification_and_full_implementation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_vdp_ground_truth_build36.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_vdp_ground_truth_build36_early.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_vdp_ground_truth_build38.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_verify_bg_hook_patch_and_title_write_site.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_vgm2fur_rastan_conversion_report.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_vgz_to_midi_conversion_report.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_video_exchange_summary_2026-04-08.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/Cody_warm_restart_gate_trace.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/TC0040IOC_specifications.md` | FINDINGS_SUBSTANTIAL | 2 | Arcade I/O register behavior and access-pattern facts. |
| `docs/design/WRAM_memory_map.md` | FINDINGS_SUBSTANTIAL | 2 | Durable address ownership and mirrored field mapping facts. |
| `docs/design/absolute_call_target_fix_plan.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/arcade_init_vs_launcher_fake_init_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/arcade_owned_graphics_replacement_design.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/blockA_producer_reconstruction_plan.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build296_attract_progression_and_text_position_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build297_pc080sn_bg_vdp_mapping_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build299_theory_vs_reality_reconciliation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build305_vblank_ownership_and_version_fix_report.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build306_shift_adjusted_init_report.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build308_arcade_owned_graphics_phase1.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build309_vint_arcade_handoff_completion.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build310_complete_arcade_execution_model.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build310_vdp_and_input_timing_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build311_reentrant_vblank_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build312_display_disable_bracketing.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build313_pc080sn_wram_staging.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build314_vertical_crop_row_bias_experiment.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build315_title_attract_tilemap_producer_hook.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build316_vram_handoff_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build316_vs_rainbow_islands_genesis_vblank_noninterrupt_vdp_report.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build317_scroll_wram_staging_and_single_commit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build318_palette_regression_and_offline_runtime_conversion_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build318_title_text_contradiction_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build318_vdp_plane_base_nametable_correlation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build319_hscroll_command_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build319_tile_mapping_vs_palette_analysis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build320_palette_bank_mirror_visibility_proof_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build320_vertical_text_and_screen_instability_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build321_title_attract_scroll_freeze_proof_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build322_fg_text_coordinate_transpose_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build322_unconditional_zero_scroll_proof_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build323_empty_plane_a_fg_write_path_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build323_full_vblank_dispatch_sgdk_influence_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build323_text_writer_ptr_row_major_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build325_fg_buffer_sentinel_proof_test.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build327_attract_mode_vs_visible_plane_a_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build327_exact_c7121a_fault_site_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build327_runtime_contradiction_and_blastem_crash_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build327_runtime_contradiction_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build328_exact_dereference_instrumentation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build329_force_plane_a_only_display_proof.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build330_early_vdp_reset_missing_palette_until_scrolling_phase_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build330_plane_a_mode_and_input_debug_overlay.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build331_input_refresh_path_stale_shadow_input_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build331_post_reset_test_palette_proof.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build332_arcade_vblank_joystick_cache_refresh_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build332_vblank_vdp_control_flow_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build333_staged_per_frame_scroll_commit_fix.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build334_vdp_write_ownership_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build335_disable_tick_dma_vdp_writer.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build336_vdp_commit_execution_count.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build337_full_per_frame_vdp_write_census.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build338_disable_sprite_sat_dma_hook.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build339_disable_only_sprite_sat_dma_commit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/build340_sprite_sat_hook_side_effect_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/canonical_blocka_attr_decode_results.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/complete_interrupt_handoff_analysis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/credit_tilt_provenance_report.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/current_c_owned_vblank_graphics_analysis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/direct_pc080sn_bulk_tilemap_translation_design.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/direct_pc080sn_bulk_tilemap_validation_gate.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/final_block_write_and_scene_scoped_tile_loading_architecture.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/final_block_write_and_scene_scoped_tile_loading_architecture_amendment.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/final_patched_rom_verification_0x5a4de.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/first_non_c_graphics_migration_slice.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/first_real_graphics_replacement_slice.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/full_graphics_system_completion_plan.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/full_prototype_sprite_execution_path.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/full_prototype_sprite_execution_results.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/handler_translation_coverage.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/live_decode_buffer_wiring_fix_results.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/live_gameplay_input_ownership_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/minimal_post_launch_crash_handling_plan.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/multi_pass_operand_relocation_design.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/next_major_graphics_phase_python_first.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/next_sprite_content_selection_object_composition.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/next_sprite_system_slice_size_grouping.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/non_c_sprite_commit_results.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/opcode_change_audit_keep_rework_revert.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/opcode_vblank_sprite_migration_plan.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/pc080sn_only_vdp_isolation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/pc080sn_semantic_mismatch_analysis_build293.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/pc080sn_semantic_mismatch_analysis_build294.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/pc080sn_semantic_mismatch_analysis_build295.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/pc080sn_tilemap_architecture.md` | FINDINGS_SUBSTANTIAL | 2 | Tilemap LUT/attribute and staged commit strategy facts. |
| `docs/design/phase1_execution_results.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/phase1_per_vblank_sprite_commit_results.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/phase1_revert_and_order_fix_patch_plan.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/phase1_runtime_ordering_proof.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/phase1_sprite_pipeline_results.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/phase2_blockA_builder_implementation_results.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/phase2_renderer_hide_guard_fix_results.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/proposal_no_sgdk_direct_execution_branch.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/rainbow_islands_vs_rastan_vdp_vram_buffering_comparative_trace.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/rastan_68000_opcode_patch_templates.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/rastan_graphics_translation_layer.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/rastan_opcode_to_vdp_translation.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/rastan_vblank_and_vdp_buffer_architecture.md` | FINDINGS_SUBSTANTIAL | 3 | Arcade VBlank sequence and producer-within-VBlank behavior. |
| `docs/design/real_attract_state_progression_and_coin_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/rom_absolute_call_relocation_vs_shift_proof.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/sat_publish_failure_diagnosis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/sprite_interpretation_failure_diagnosis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/sprite_interpretation_fix_results.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/system_wide_sprite_visibility_bringup_plan.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/system_wide_tile_visibility_results.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/title_screen_composition_audit.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/title_screen_state_analysis.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/vblank_graphics_architecture_plan.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/vblank_handoff_implementation_results.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/vblank_phase1_sprite_pipeline.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |
| `docs/design/zero_code_filter_results.md` | NO_FINDINGS | 0 | Read and screened; build-era/implementation-specific content did not survive durability filter for this pass. |

## Phase 2 — Extracted Candidate Findings (No Synthesis)

### BOOT_PATH

[BOOT-01] — Repeated bootstrap re-entry chain is observed in runtime loops
Source: `OPEN_ISSUES.md` (OPEN-004, lines 176-183)
Category: `BOOT_PATH`
Survival-outside-source check: PASS — runtime control-flow re-entry behavior is durable evidence for future boot-path investigations.
Proposed finding statement: Runtime repeatedly re-enters the bootstrap/startup path (`0x0202 -> 0x022C -> 0x024A`) at roughly 15 cycles per 64 seconds in the observed build window.
Proposed confidence: `STRONG` — issue ledger records explicit observed chain and cadence; still tracked as open investigation.
Proposed applicability: `BUILD_SPECIFIC` — cited on OPEN-004 as observed in Builds 55a/55b.
Rediscovery hazard hint: `HIGH` — bootstrap-loop framing has been repeatedly rediscovered historically.
Addresses (if applicable): runtime Genesis PC `0x00000202`, `0x0000022C`, `0x0000024A`
Related issues (if applicable): `OPEN-004`, `OPEN-001`
Cody notes: Observation is behavior-only; trigger cause remains unresolved in this source.

[BOOT-02] — Delay-loop expiry path restores vectors and jumps to bootstrap
Source: `docs/design/Andy_polling_loop_investigation.md` (§1.1, lines 45-47; §1.2 lines 55-66)
Category: `BOOT_PATH`
Survival-outside-source check: PASS — vector-based jump path is a durable boot/reset mechanism fact.
Proposed finding statement: On watchdog expiry path, code loads SP from `0x00000000`, loads PC target from `0x00000004`, and jumps to `0x00000202` (`_bootstrap`).
Proposed confidence: `CONFIRMED` — direct hex/disassembly citation in canonical Build 0077.
Proposed applicability: `GLOBAL` — mechanism reported as canonical Build 0077 behavior and tied to preserved vectors.
Rediscovery hazard hint: `HIGH` — this reset chain has been repeatedly reframed.
Addresses (if applicable): runtime Genesis PC `0x0003A19E`, `0x0003A1A2`, `0x0003A1A6`, `0x00000202`; vectors `0x00000000`, `0x00000004`
Related issues (if applicable): `OPEN-004`
Cody notes: Semantically overlaps KF-001; kept per-source for Task 2 dedup review.

### WATCHDOG

[WATCHDOG-01] — Watchdog gate uses A5+0x2C countdown with decrement-and-return fast path
Source: `docs/design/Andy_polling_loop_investigation.md` (§1.2, lines 60-64; §2.2 lines 125-130)
Category: `WATCHDOG`
Survival-outside-source check: PASS — counter-gated watchdog semantics are durable runtime behavior.
Proposed finding statement: The watchdog routine tests `%a5@(44)` (`0x00FF002C`), decrements and returns when positive, and enters delay/reset path when zero.
Proposed confidence: `CONFIRMED` — instruction-level routine body is cited from canonical disassembly.
Proposed applicability: `GLOBAL` — mechanism is in canonical runtime path.
Rediscovery hazard hint: `HIGH` — core watchdog semantics have repeatedly required re-clarification.
Addresses (if applicable): runtime Genesis PC `0x0003A180`, `0x0003A186`, `0x00FF002C`
Related issues (if applicable): `OPEN-004`, `OPEN-001`
Cody notes: Directly supports existing KF-001, included here as separate source candidate.

[WATCHDOG-02] — Delay-loop body is countdown-based, not external polling
Source: `docs/design/Andy_polling_loop_investigation.md` (§2.1, lines 111-122)
Category: `WATCHDOG`
Survival-outside-source check: PASS — this distinguishes mechanism behavior from misclassified "polling wait" interpretations.
Proposed finding statement: The loop at `0x0003A192..0x0003A19C` exits only via `D1` countdown (`SUBI.L` + `BNE.S`); `MOVE.L $0.W,D0` reads a constant ROM value and does not provide a dynamic exit condition.
Proposed confidence: `CONFIRMED` — instruction sequence and value source are explicitly cited.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `HIGH` — polling-vs-countdown misinterpretation has recurred.
Addresses (if applicable): runtime Genesis PC `0x0003A192`, `0x0003A196`, `0x0003A19C`; memory `0x00000000`
Related issues (if applicable): `OPEN-004`
Cody notes: Behavior statement intentionally excludes root-cause attribution.

[WATCHDOG-03] — Kick-site and force-expire write classes are distinct
Source: `docs/design/Andy_polling_loop_investigation.md` (§3.1, lines 150-174)
Category: `WATCHDOG`
Survival-outside-source check: PASS — writer-class inventory is durable and operationally important.
Proposed finding statement: The write inventory for `%a5@(44)` includes 11 positive-value kick sites, 5 decrement sites, and one explicit clear (`CLRW`) force-expire site at `0x0003AE76`.
Proposed confidence: `STRONG` — inventory is explicit, but deep `0x0009Axxx` kick interpretation is acknowledged as classification-level rather than single-path runtime proof.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `HIGH`
Addresses (if applicable): runtime Genesis PC `0x0003A5D4`, `0x0003A63E`, `0x0003AC88`, `0x0003ACF2`, `0x0003AD22`, `0x0003AD5E`, `0x0003ADD0`, `0x0003AE76`, `0x0009A3B0`, `0x0009A3D0`, `0x0009A4B0`, `0x0009A4D0`
Related issues (if applicable): `OPEN-004`
Cody notes: Confidence kept conservative due mixed static/runtime evidence depths.

[WATCHDOG-04] — Observed excursion regions omit known watchdog-kick region
Source: `docs/design/Andy_polling_loop_investigation.md` (§4.1-§4.2, lines 189-210)
Category: `WATCHDOG`
Survival-outside-source check: PASS — negative reachability of kick-region during sampled runtime is durable investigative context.
Proposed finding statement: In the analyzed observation window, sampled execution includes interrupt/helper excursion regions but does not include the known watchdog kick-site region.
Proposed confidence: `STRONG` — explicitly cited as reachability analysis in source.
Proposed applicability: `BUILD_SPECIFIC` — tied to the analyzed Build 0077 observation context.
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): missing region (kick sites) around `0x0003A5D4..0x0003ADD0`; observed excursion regions listed in source §4.
Related issues (if applicable): `OPEN-004`, `OPEN-001`
Cody notes: This candidate is reachability evidence, not a causality claim.

### COORDINATE_MODEL

[COORD-01] — Runtime Genesis PC equals cartridge ROM file offset
Source: `docs/design/Andy_BM002_runtime_failure_investigation.md` (§1.2, lines 54-59)
Category: `COORDINATE_MODEL`
Survival-outside-source check: PASS — this mapping is foundational for trace-to-ROM interpretation.
Proposed finding statement: In this port context, CPU fetch at runtime Genesis PC `N` reads bytes at cartridge ROM file offset `N`.
Proposed confidence: `CONFIRMED` — explicitly stated and used in decisive evidence path.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `HIGH`
Addresses (if applicable): runtime Genesis PC `0x03A19C` vs file offset `0x03A19C`
Related issues (if applicable): `CLOSED-010`, `CLOSED-011`
Cody notes: This is a core prior for all bookmark and trace interpretation.

[COORD-02] — BM-002 failure was target-space mismatch (`arcade_pc` vs runtime PC)
Source: `docs/design/Andy_BM002_runtime_failure_investigation.md` (§5.1, lines 199-207)
Category: `COORDINATE_MODEL`
Survival-outside-source check: PASS — durable fault-class finding from retired cycle analysis.
Proposed finding statement: BM-002 placed activator at translated offset for `arcade_pc 0x03A19C` (`0x03A39C`), while trace-observed execution occurred at runtime PC/file offset `0x03A19C`.
Proposed confidence: `CONFIRMED` — direct offset and trace-hit evidence cited.
Proposed applicability: `CONTAMINATED_CONTEXT` — specific to retired BM-002 cycle evidence.
Rediscovery hazard hint: `HIGH`
Addresses (if applicable): arcade_pc `0x03A19C`; runtime Genesis PC/file offsets `0x03A39C` and `0x03A19C`
Related issues (if applicable): `CLOSED-010`
Cody notes: Contaminated-context applicability avoids over-generalization.

[COORD-03] — `identity_offset` is constant `0x200` across current `arcade_copy` segments
Source: `docs/design/Andy_OPEN012_bookmark_coordinate_model_design.md` (§1.1, lines 44-55)
Category: `COORDINATE_MODEL`
Survival-outside-source check: PASS — durable translation-constant fact for current configuration.
Proposed finding statement: In current `address_map.json`, all `arcade_copy` segments use `identity_offset = 0x200` and no alternate `identity_offset` value appears.
Proposed confidence: `CONFIRMED` — explicit query result in source.
Proposed applicability: `ERA_SPECIFIC` — scoped to current build configuration documented in source.
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): translation constant `0x200`
Related issues (if applicable): `CLOSED-010`
Cody notes: Marked ERA_SPECIFIC because source explicitly warns future configurations could differ.

[COORD-04] — `bookmarks_v2` workflow writes activators using trace PC verbatim
Source: `docs/design/Andy_OPEN012_bookmark_coordinate_model_design.md` (§2.4, lines 128-136; §3.1 lines 155-162)
Category: `COORDINATE_MODEL`
Survival-outside-source check: PASS — durable operational behavior of validated bookmark model.
Proposed finding statement: Under `bookmarks_v2`, target selection uses trace `pc` value verbatim as `runtime_genesis_pc`, and activator bytes are written at ROM file offset `runtime_genesis_pc` without bookmark-side arithmetic.
Proposed confidence: `CONFIRMED` — documented workflow and stage behavior.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `HIGH`
Addresses (if applicable): runtime Genesis PC == ROM file offset (bookmark target)
Related issues (if applicable): `CLOSED-010`, `CLOSED-011`
Cody notes: This is model behavior, not implementation history.

[COORD-05] — BM-001 had the same coordinate mismatch class as BM-002
Source: `docs/design/Andy_BM002_runtime_failure_investigation.md` (§6.1, lines 228-240)
Category: `COORDINATE_MODEL`
Survival-outside-source check: PASS — durable interpretation rule for retired BM-001 evidence.
Proposed finding statement: BM-001 patched ROM offset `0x055B48` from `arcade_pc 0x055948`, while trace observation `pc=055948` corresponded to execution at file offset `0x055948` (different code path).
Proposed confidence: `STRONG` — explicit offset comparison and disassembly references are cited.
Proposed applicability: `CONTAMINATED_CONTEXT` — specific to retired BM-001 cycle evidence.
Rediscovery hazard hint: `HIGH`
Addresses (if applicable): arcade_pc `0x055948`; runtime Genesis PC/file offsets `0x055948` and `0x055B48`
Related issues (if applicable): `CLOSED-010`
Cody notes: Source states BM-001 Outcome B was not trustworthy for original question.

### MEMORY_MAP

[MEMORY-01] — WRAM ownership split between arcade workram and Genesis BSS
Source: `docs/design/WRAM_memory_map.md` (Address Space Overview, lines 7-11)
Category: `MEMORY_MAP`
Survival-outside-source check: PASS — stable ownership map is core prior for runtime-state interpretation.
Proposed finding statement: WRAM range `0xFF0000..0xFF3FFF` is arcade workram (A5-base domain), while `0xFF4000..` is Genesis BSS ownership in this layout.
Proposed confidence: `STRONG` — mapping table is explicit; scoped to documented build era.
Proposed applicability: `ERA_SPECIFIC` — source is build-era memory map (`Build: 0025` metadata).
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): `0xFF0000..0xFF3FFF`, `0xFF4000..0xFF60CB`
Related issues (if applicable): `(none)`
Cody notes: Candidate retained despite age because map is repeatedly used by later analyses.

[MEMORY-02] — Workram field `0xFF002C` is watchdog/warm-restart countdown location
Source: `docs/design/WRAM_memory_map.md` (Arcade Workram Fields, lines 32-33)
Category: `MEMORY_MAP`
Survival-outside-source check: PASS — exact field location is durable and repeatedly required.
Proposed finding statement: Workram offset `A5+0x2C` (address `0xFF002C`) is the warm-restart/watchdog countdown field in the documented map.
Proposed confidence: `STRONG` — explicit field table entry.
Proposed applicability: `ERA_SPECIFIC` — from documented build-era map.
Rediscovery hazard hint: `HIGH`
Addresses (if applicable): `0xFF002C` (`A5+0x2C`)
Related issues (if applicable): `OPEN-004`
Cody notes: Complements WATCHDOG candidates from independent source.

[MEMORY-03] — Diagnostic bookmark helper location and bytes are stable
Source: `docs/design/Cody_BM003_insert.md` (lines 76-78) and `docs/design/Cody_BM003_revert.md` (lines 45-47)
Category: `MEMORY_MAP`
Survival-outside-source check: PASS — helper address/byte identity is durable infrastructure behavior.
Proposed finding statement: The diagnostic helper is at `0x00071C78`, with bytes `60 FE`, and matches canonical helper SHA in BM-003 Insert/Revert validation records.
Proposed confidence: `CONFIRMED` — independently restated in Insert and Revert docs.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): runtime Genesis PC `0x00071C78`
Related issues (if applicable): `OPEN-014`
Cody notes: Source pair used to avoid single-document drift.

[MEMORY-04] — Address-map reverse lookup distinguishes non-ROM hardware address targets
Source: `docs/design/Andy_address_map_artifact_design.md` (§7.3, lines 357-380; §8 example 5, lines 442-447)
Category: `MEMORY_MAP`
Survival-outside-source check: PASS — behavior-level distinction between ROM offsets and hardware-space addresses is reusable.
Proposed finding statement: Reverse lookup/classification in `address_map` treats hardware-space runtime addresses (example `0xC09EA0`) as non-ROM/unmapped-to-arcade, rather than as translated arcade code addresses.
Proposed confidence: `STRONG` — source gives worked classification examples.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): runtime Genesis address `0xC09EA0`
Related issues (if applicable): `(none)`
Cody notes: Operationally relevant when interpreting trace PCs outside ROM range.

### VDP_BEHAVIOR

[VDP-01] — Populated VDP internals can coexist with blank composed game output
Source: `OPEN_ISSUES.md` (OPEN-001 summary, lines 21-22)
Category: `VDP_BEHAVIOR`
Survival-outside-source check: PASS — this observed divergence is a durable investigative prior.
Proposed finding statement: In the cited observation state, CRAM and tile/pattern internals are populated, yet composed game output remains effectively blank in both MAME and Exodus.
Proposed confidence: `STRONG` — directly reported by issue body with cross-emulator observation.
Proposed applicability: `BUILD_SPECIFIC` — tied to Build-59-era evidence chain in OPEN-001.
Rediscovery hazard hint: `HIGH`
Addresses (if applicable): Plane bases cited in source: VRAM `0xC000` / `0xE000`
Related issues (if applicable): `OPEN-001`, `OPEN-003`, `OPEN-004`
Cody notes: Finding statement avoids root-cause interpretation from same issue text.

[VDP-02] — Captured Plane A/B nametable ranges were all zero in OPEN-001 evidence run
Source: `OPEN_ISSUES.md` (OPEN-001 Build 58b evidence, lines 33-43)
Category: `VDP_BEHAVIOR`
Survival-outside-source check: PASS — explicit captured-state fact useful for future comparative capture runs.
Proposed finding statement: In the referenced read-only dump runs, Plane B (`0xC000..0xCFFF`) and Plane A (`0xE000..0xEFFF`) decoded as all `0x0000` cells.
Proposed confidence: `STRONG` — repeated dump results are listed in issue body.
Proposed applicability: `BUILD_SPECIFIC` — tied to build58b capture artifacts.
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): VRAM `0xC000..0xCFFF`, `0xE000..0xEFFF`
Related issues (if applicable): `OPEN-001`
Cody notes: This is capture-state evidence, not generalized renderer behavior.

[VDP-03] — Palette conversion is precomputed offline and copied to CRAM at runtime
Source: `AGENTS.md` (Palette Architecture, lines 257-263 and 281-283)
Category: `VDP_BEHAVIOR`
Survival-outside-source check: PASS — palette data-path behavior is a durable port architecture fact used repeatedly.
Proposed finding statement: Palette RAM entries are pre-converted to Genesis format during patching and stored in ROM; runtime palette load is a direct DMA copy to CRAM without per-entry runtime conversion.
Proposed confidence: `STRONG` — stated as settled architecture in AGENTS.md.
Proposed applicability: `ERA_SPECIFIC` — tagged to Build-112-era architecture note in source.
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): CRAM destination (no singular address in source statement)
Related issues (if applicable): `(none)`
Cody notes: Survives source-loss test because it defines expected palette data path.

[VDP-04] — Plane mapping in direct model is BG->Plane B, FG->Plane A
Source: `AGENTS.md` (VDP Layer Mapping, lines 319-329)
Category: `VDP_BEHAVIOR`
Survival-outside-source check: PASS — plane-role mapping is durable reference context for visual/output debugging.
Proposed finding statement: Arcade BG layer 0 maps to Genesis Plane B (`0xC000`) and arcade FG layer 1 maps to Genesis Plane A (`0xE000`) in the documented layer mapping.
Proposed confidence: `STRONG` — stated as confirmed mapping in source.
Proposed applicability: `ERA_SPECIFIC` — Build-112-era confirmed mapping note.
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): VRAM Plane B `0xC000`, Plane A `0xE000`
Related issues (if applicable): `OPEN-001`
Cody notes: Kept as mapping fact, not implementation prescription.

### INTERRUPT_BEHAVIOR

[INTR-01] — Frame ownership is arcade Level-5 VBlank, Genesis VBlank is servicing-only
Source: `ARCHITECTURE.md` (Frame Ownership / VBlank Behavior, lines 45-62)
Category: `INTERRUPT_BEHAVIOR`
Survival-outside-source check: PASS — foundational runtime ownership model needed by all future investigations.
Proposed finding statement: Frame progression is owned by arcade Level-5 VBlank; Genesis VBlank is constrained to staged commit/DMA servicing and must not run gameplay logic.
Proposed confidence: `STRONG` — architecture-level declared behavior model.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `HIGH`
Addresses (if applicable): Level-5 VBlank ownership model (no singular address in source section)
Related issues (if applicable): `(none)`
Cody notes: This is a behavior model prior, not a task-history statement.

[INTR-02] — First IMASK lowering on cold boot occurs in Genesis bootstrap before arcade startup
Source: `docs/design/Andy_interrupt_enable_timing.md` (Phase 3, lines 94-103; Summary lines 200-203)
Category: `INTERRUPT_BEHAVIOR`
Survival-outside-source check: PASS — interrupt-enable ordering is durable and affects early-runtime interpretation.
Proposed finding statement: On the analyzed cold-boot path, the first IMASK-lowering instruction is `move.w #0x2000, %sr` in Genesis-side `boot.s` before control reaches arcade startup_common.
Proposed confidence: `CONFIRMED` — source ties this to enumerated boot-path walk.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): `apps/rastan-direct/src/boot/boot.s:160` (runtime ordering context)
Related issues (if applicable): `(none)`
Cody notes: Includes ownership and sequencing only.

[INTR-03] — Arcade-intended enable site is `0x03B07A`, yielding observed ENABLE-then-CLEAR ordering on Genesis
Source: `docs/design/Andy_interrupt_enable_timing.md` (lines 122-127; 170-177; 210-213)
Category: `INTERRUPT_BEHAVIOR`
Survival-outside-source check: PASS — explicit ordering fact is reusable debugging prior.
Proposed finding statement: Arcade startup contains SR-clearing enable at `arcade_pc 0x03B07A` (`andi.w #0xF0FF,%sr`), but reported observed ordering on Genesis is ENABLE-then-CLEAR due earlier Genesis-side enable.
Proposed confidence: `STRONG` — static path proof plus ordering summary in source.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): arcade_pc `0x03B07A`, startup clear site `0x03AEFC`
Related issues (if applicable): `(none)`
Cody notes: Behavior statement preserves source's "fact, not fix-direction" boundary.

### GRAPHICS_PIPELINE

[GFXPIPE-01] — Text producer dispatch executes inside VBlank handler
Source: `docs/design/rastan_vblank_and_vdp_buffer_architecture.md` (Key Finding section, lines 119-127)
Category: `GRAPHICS_PIPELINE`
Survival-outside-source check: PASS — producer timing relative to VBlank is durable pipeline behavior.
Proposed finding statement: The primary text dispatch entry (`0x3BB48`) is called from inside the VBlank interrupt handler for title/text selectors.
Proposed confidence: `STRONG` — explicit disassembly-backed statement in source.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): runtime Genesis PC `0x0003BB48`; VBlank handler region around `0x0003A008`
Related issues (if applicable): `OPEN-001`
Cody notes: Statement avoids design prescriptions.

[GFXPIPE-02] — PC080SN tile LUT guarantees O(1) lookup for strip-table tile codes
Source: `docs/design/pc080sn_tilemap_architecture.md` (§2a, lines 84-96)
Category: `GRAPHICS_PIPELINE`
Survival-outside-source check: PASS — LUT guarantee is durable expected behavior for tile commit path.
Proposed finding statement: The tile-LUT generation path assigns VRAM slots to all tile codes reachable from strip tables and uses direct LUT lookup at runtime (no per-hit DMA lookup work).
Proposed confidence: `STRONG` — source states algorithm and guarantee explicitly.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): LUT domain tile codes `0x0000..0x3FFF`
Related issues (if applicable): `(none)`
Cody notes: Behavior-level statement only; no claims about correctness of every scene.

[GFXPIPE-03] — Scroll model is full-plane with +8 vertical bias and no per-line scroll
Source: `docs/design/pc080sn_tilemap_architecture.md` (Scroll System, lines 228-240)
Category: `GRAPHICS_PIPELINE`
Survival-outside-source check: PASS — durable scroll behavior assumptions for renderer debugging.
Proposed finding statement: Documented scroll commit uses full-plane BG/FG scroll values from WRAM offsets with +8 vertical bias; per-scanline scroll mode is not used.
Proposed confidence: `STRONG` — explicit mapping and mode statement in source.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): A5 offsets `0x10EC`, `0x10EE`, `0x10AE`, `0x10B0`
Related issues (if applicable): `(none)`
Cody notes: Treated as behavior contract in architecture doc.

[GFXPIPE-04] — Title-state VBlank path clears sprite RAM to off-screen marker value
Source: `docs/design/rastan_vblank_and_vdp_buffer_architecture.md` (Sprite RAM Clear, lines 135-142)
Category: `GRAPHICS_PIPELINE`
Survival-outside-source check: PASS — this clear pattern is a concrete producer behavior fact.
Proposed finding statement: The title-state VBlank sequence includes sprite RAM fill writes at `0xD00000` region with `0x00000100` (off-screen Y marker) across clear loops.
Proposed confidence: `STRONG` — direct disassembly sequence cited.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): runtime Genesis PC `0x0003AD4C`; arcade sprite RAM region `0x00D00000`
Related issues (if applicable): `(none)`
Cody notes: Kept as observed routine behavior, not outcome interpretation.

### TRANSLATION_MODEL

[TRANSLATE-01] — Under `bookmarks_v2`, opcode_replace invariants remain strict canonical values in all modes
Source: `docs/design/Cody_OPEN012_OPEN013_implementation.md` (A3 lines 37-41; A5 lines 54-58)
Category: `TRANSLATION_MODEL`
Survival-outside-source check: PASS — invariant behavior is durable for build-validation interpretation.
Proposed finding statement: In the `bookmarks_v2` model, opcode_replace invariant checks remain strict at 94 sites and `0x17CAEC` covered bytes, including diagnostic-mode runs.
Proposed confidence: `CONFIRMED` — implementation and validation sections both report this behavior.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): N/A
Related issues (if applicable): `CLOSED-011`
Cody notes: Source reports behavior post-old-path removal.

[TRANSLATE-02] — Legacy bookmark schema inputs are fail-closed rejected
Source: `docs/design/Cody_OPEN012_OPEN013_implementation.md` (A2 lines 20-22, 26-33; A5 lines 59-61)
Category: `TRANSLATION_MODEL`
Survival-outside-source check: PASS — reject behavior is durable gate/postpatch contract.
Proposed finding statement: Legacy `diagnostic_bookmarks` and legacy `opcode_replace.bookmark_cycle` bookmark schema forms are rejected fail-closed in the postpatch/gate path.
Proposed confidence: `CONFIRMED` — implementation and phase-A validation logs are cited in source.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): N/A
Related issues (if applicable): `CLOSED-011`
Cody notes: Statement is schema-behavior only.

[TRANSLATE-03] — Failure ID namespace was split to restore single-meaning semantics
Source: `docs/design/Cody_OPEN012_OPEN013_implementation.md` (Failure-ID table lines 102-111)
Category: `TRANSLATION_MODEL`
Survival-outside-source check: PASS — durable diagnostic classification behavior for gate failures.
Proposed finding statement: Legacy-schema rejection and `bookmarks_v2` schema-validation failures are now emitted under distinct IDs (`GATE_FAIL_LEGACY_BOOKMARK_SCHEMA` and `GATE_FAIL_2_5_BOOKMARK_SCHEMA_VALIDATION`).
Proposed confidence: `CONFIRMED` — source records post-hygiene split table.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): N/A
Related issues (if applicable): `CLOSED-011`
Cody notes: Behavior-level diagnostic semantics only.

### DIAGNOSTIC_LIMITATION

[DIAG-01] — Parked-helper outcome signal is not reliably sampled in primary MAME trace path
Source: `OPEN_ISSUES.md` (OPEN-014, lines 254-257)
Category: `DIAGNOSTIC_LIMITATION`
Survival-outside-source check: PASS — instrumentation limitation affects future evidence interpretation.
Proposed finding statement: In BM-003, helper park at `0x00071C78` was confirmed by Exodus + MAME exit summary, while sampled MAME trace lines did not directly capture parked-helper PCs.
Proposed confidence: `CONFIRMED` — issue body gives direct evidence and impact statement.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `HIGH`
Addresses (if applicable): helper `0x00071C78`; observed final PC `0x071C7A`
Related issues (if applicable): `OPEN-014`
Cody notes: This is limitation-of-evidence-path, not mechanism failure.

[DIAG-02] — BM-003 log records sampled-trace gap despite Outcome-A confirmation
Source: `AGENTS_LOG.md` (lines 35128-35131; 35165-35168)
Category: `DIAGNOSTIC_LIMITATION`
Survival-outside-source check: PASS — direct runtime-observation record needed for future trace interpretation.
Proposed finding statement: BM-003 logs explicitly record no sampled `pc=071c78/071c7a` lines in `mame_run_log.txt` while separately recording Outcome-A confirmation via MAME exit summary and Exodus observation.
Proposed confidence: `CONFIRMED` — same log section provides both facts.
Proposed applicability: `BUILD_SPECIFIC` — BM-003 run context.
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): `0x071C78`, `0x071C7A`
Related issues (if applicable): `OPEN-014`
Cody notes: Included under AGENTS_LOG admissibility restriction (runtime/system observation only).

[DIAG-03] — FG sentinel/overlay contamination invalidates Plane-A/text-path evidence quality
Source: `Master Diagnostic Debt.md` (§2.1, lines 24-31)
Category: `DIAGNOSTIC_LIMITATION`
Survival-outside-source check: PASS — contamination caveat is durable evidence-integrity context.
Proposed finding statement: Active FG sentinel and overlay diagnostics can make Plane A data and text-pipeline conclusions non-trustworthy in contaminated runs.
Proposed confidence: `STRONG` — explicitly stated as impact in debt audit.
Proposed applicability: `CONTAMINATED_CONTEXT`
Rediscovery hazard hint: `HIGH`
Addresses (if applicable): N/A
Related issues (if applicable): `(none)`
Cody notes: Meta-finding intentionally scoped to contaminated contexts.

[DIAG-04] — Combined sprite suppression controls can mask sprite output regardless of upstream behavior
Source: `docs/design/Andy_diagnostic_debt_audit.md` (High-Risk Contaminants table, lines 191-194)
Category: `DIAGNOSTIC_LIMITATION`
Survival-outside-source check: PASS — durable warning for interpreting historical screenshots/traces from contaminated runs.
Proposed finding statement: Simultaneous sprite-renderer early return and SAT DMA suppression can fully suppress visible sprites, making sprite-layer conclusions from those runs non-diagnostic.
Proposed confidence: `STRONG` — source classifies this as high-risk contamination.
Proposed applicability: `CONTAMINATED_CONTEXT`
Rediscovery hazard hint: `HIGH`
Addresses (if applicable): N/A
Related issues (if applicable): `(none)`
Cody notes: Candidate is evidence-quality guardrail, not runtime mechanism claim.

[DIAG-05] — MAME vs Exodus runtime-state disagreement remains unresolved in OPEN-003
Source: `OPEN_ISSUES.md` (OPEN-003 summary/evidence, lines 138-139 and 176-183 context from OPEN-004/OPEN-001 linkage)
Category: `DIAGNOSTIC_LIMITATION`
Survival-outside-source check: PASS — unresolved emulator divergence directly affects confidence in tool-specific observations.
Proposed finding statement: OPEN-003 tracks unresolved disagreement between MAME-captured runtime evidence and Exodus-observed runtime behavior for the same investigation areas.
Proposed confidence: `STRONG` — issue remains open with explicit evidence conflict narrative.
Proposed applicability: `ERA_SPECIFIC` — tied to Build 55x/59 evidence chain.
Rediscovery hazard hint: `HIGH`
Addresses (if applicable): N/A
Related issues (if applicable): `OPEN-003`, `OPEN-001`, `OPEN-004`
Cody notes: Statement intentionally avoids selecting one emulator as canonical truth.

### HARDWARE_MAPPING

[HWMAP-01] — TC0040IOC input registers are active-low bytes
Source: `docs/design/TC0040IOC_specifications.md` (Register map and convention, lines 15-25)
Category: `HARDWARE_MAPPING`
Survival-outside-source check: PASS — input polarity is a durable hardware-interface fact.
Proposed finding statement: TC0040IOC input reads (`0x390001..0x39000B`) are active-low byte semantics; open/unpressed reads as `1`, pressed/on reads as `0`.
Proposed confidence: `CONFIRMED` — source states convention explicitly.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): `0x390001`, `0x390003`, `0x390005`, `0x390007`, `0x390009`, `0x39000B`
Related issues (if applicable): `(none)`
Cody notes: Useful prior for input/bitmask debugging.

[HWMAP-02] — TC0040IOC control writes at `0x380000` carry lockout/flip semantics
Source: `docs/design/TC0040IOC_specifications.md` (§3.5, lines 89-100)
Category: `HARDWARE_MAPPING`
Survival-outside-source check: PASS — control-register semantics are durable hardware mapping context.
Proposed finding statement: Writes to `0x380000` are used for control behaviors including coin lockout and flip-screen related state in the documented map.
Proposed confidence: `STRONG` — explicit write-site and semantic description in source.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): `0x380000`
Related issues (if applicable): `(none)`
Cody notes: Semantics described at map level; bit-level mode behavior is separately documented.

[HWMAP-03] — Documented non-flipped upright DIP defaults map to specific active-high values
Source: `docs/design/Andy_rastan_dip_defaults_and_flip_behavior.md` (§5.3 lines 201-208; §9 lines 368-392)
Category: `HARDWARE_MAPPING`
Survival-outside-source check: PASS — DIP default mapping is durable configuration behavior context.
Proposed finding statement: The documented normal upright/non-flipped DIP configuration maps to active-high work values of `DIP1=0x01` and `DIP2=0x00` after inversion.
Proposed confidence: `STRONG` — source provides explicit derivation and final values.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): DIP ports `0x390009`, `0x39000B`
Related issues (if applicable): `(none)`
Cody notes: Source frames this as final implementation target values.

[HWMAP-04] — `0xDFFFFE` is classified as unmapped open-bus target (not watchdog/control)
Source: `docs/design/Andy_dffffe_hardware_identification.md` (§5, lines 123-136)
Category: `HARDWARE_MAPPING`
Survival-outside-source check: PASS — hardware-target classification is durable for write-site analysis.
Proposed finding statement: The `0xDFFFFE` target is classified as unmapped/open-bus in the analyzed mapping context, and is explicitly distinguished from watchdog/control register paths.
Proposed confidence: `STRONG` — source states determination with ruled-out alternatives.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): `0xDFFFFE`, watchdog `0x3C0000`
Related issues (if applicable): `(none)`
Cody notes: Candidate avoids prescribing remediation strategy.

### OTHER_REQUIRES_REVIEW

[OTHER-01] — PC090OJ runtime write surface is not fully statically enumerable
Source: `docs/design/Andy_pc090oj_full_subsystem_design.md` (§1.3 lines 54-70; §3/§9 lines 170-207)
Category: `OTHER_REQUIRES_REVIEW` (suggested: `SPRITE_ENGINE`)
Survival-outside-source check: PASS — unresolved sprite write-surface characterization is a durable limitation/fact for sprite investigations.
Proposed finding statement: Static analysis alone does not fully enumerate all PC090OJ write surfaces because pointer-indexed runtime addressing contributes write destinations that require trace evidence.
Proposed confidence: `STRONG` — source marks this as explicit STOP boundary for static-only design.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): example pointer-based path around runtime PCs `0x41BF8..0x41C1C`
Related issues (if applicable): `OPEN-006`
Cody notes: Category suggestion included because canonical taxonomy has no sprite-engine-specific bucket.

[OTHER-02] — Sound queue can silently drop commands on full buffer
Source: `docs/design/Andy_rastan_sound_command_execution_verified.md` (Queue behavior, lines 161-164; Edge case lines 202-204)
Category: `OTHER_REQUIRES_REVIEW` (suggested: `SOUND_SUBSYSTEM`)
Survival-outside-source check: PASS — queue-drop behavior is durable subsystem behavior relevant to audio debugging.
Proposed finding statement: The documented 6-slot sound queue drops new command bytes silently when all slots are occupied (no overflow flag).
Proposed confidence: `STRONG` — behavior is explicitly described in queue and edge-case sections.
Proposed applicability: `GLOBAL`
Rediscovery hazard hint: `NORMAL`
Addresses (if applicable): WRAM queue range `a5+0x292..0x297` (source line 161)
Related issues (if applicable): `(none)`
Cody notes: Survives filter; category is outside canonical taxonomy and surfaced for review.

## Phase 3 — Judgment Calls (surfaced, not resolved)

[WATCHDOG-04] — Reachability-negative interpretation boundary
Source(s): `docs/design/Andy_polling_loop_investigation.md` (§4.1-§4.2, lines 189-210)
Category proposal: `WATCHDOG`
Proposed finding statement: Sampled excursion regions omit known kick-site region during analyzed window.
Confidence question: Could be `STRONG` or `WORKING_HYPOTHESIS` depending on how strictly reviewers require runtime sampling breadth.
Applicability question: `BUILD_SPECIFIC` is likely, but reviewers may prefer `ERA_SPECIFIC` if similar traces corroborate.
Conflicts: None explicit.
Cody's recommendation: Keep as `STRONG`, `BUILD_SPECIFIC` until additional trace windows broaden coverage.
Why surfaced: §A.4 confidence ambiguity + applicability ambiguity.

[VDP-01] — Blank composed output despite populated internals
Source(s): `OPEN_ISSUES.md` OPEN-001 lines 21-29
Category proposal: `VDP_BEHAVIOR`
Proposed finding statement: Populated CRAM/pattern internals can coexist with effectively blank composed output.
Confidence question: Strong evidence exists, but some linked artifacts are build-era-specific and partially contradictory across tooling contexts.
Applicability question: `BUILD_SPECIFIC` vs broader `ERA_SPECIFIC`.
Conflicts: OPEN-003 describes emulator evidence disagreement in same era.
Cody's recommendation: Keep `STRONG`, scope as `BUILD_SPECIFIC` for now.
Why surfaced: §A.4 source conflict + applicability ambiguity.

[VDP-03] — AGENTS.md palette architecture as behavior candidate
Source(s): `AGENTS.md` lines 255-283
Category proposal: `VDP_BEHAVIOR`
Proposed finding statement: Palette conversion is precomputed in ROM and runtime loads by DMA copy.
Confidence question: Source is project guide (policy/architecture), not direct runtime trace artifact.
Applicability question: `ERA_SPECIFIC` appears appropriate due explicit Build-112 wording.
Conflicts: None explicit.
Cody's recommendation: Retain candidate but keep conservative `STRONG` and `ERA_SPECIFIC` until independently reconfirmed by runtime artifact citation in Task 2.
Why surfaced: §A.4 borderline qualification (system behavior vs infrastructure statement).

[DIAG-03/DIAG-04] — Diagnostic debt findings as durable memory entries
Source(s): `Master Diagnostic Debt.md` lines 22-31, 35-43, 51-64; `docs/design/Andy_diagnostic_debt_audit.md` lines 191-196
Category proposal: `DIAGNOSTIC_LIMITATION`
Proposed finding statement: Specific contamination modes can invalidate evidence interpretation.
Confidence question: Should these be preserved as durable behavior priors or treated as historical contamination notes only?
Applicability question: likely `CONTAMINATED_CONTEXT`, but boundary of contamination eras may need explicit dating.
Conflicts: None explicit.
Cody's recommendation: Keep candidates with strict `CONTAMINATED_CONTEXT`; Task 2 can decide whether to promote as permanent KF entries or maintain as contingent cautions.
Why surfaced: §A.4 meta-finding representation question.

[OTHER-01] — Sprite-system static-limit finding category fit
Source(s): `docs/design/Andy_pc090oj_full_subsystem_design.md` lines 54-70, 170-207
Category proposal: `OTHER_REQUIRES_REVIEW` (suggested: `SPRITE_ENGINE`)
Proposed finding statement: PC090OJ runtime write surface is not fully statically enumerable.
Confidence question: Confidence is clear (`STRONG`), but taxonomy fit is unclear.
Applicability question: likely `GLOBAL` until disproven.
Conflicts: None explicit.
Cody's recommendation: Introduce `SPRITE_ENGINE` category in Task 2 if multiple sprite-specific findings are accepted.
Why surfaced: §A.4 OTHER category trigger.

[OTHER-02] — Sound queue-overflow behavior category fit
Source(s): `docs/design/Andy_rastan_sound_command_execution_verified.md` lines 161-164, 202-204
Category proposal: `OTHER_REQUIRES_REVIEW` (suggested: `SOUND_SUBSYSTEM`)
Proposed finding statement: 6-slot sound queue silently drops new commands when full.
Confidence question: confidence itself is clear (`STRONG`).
Applicability question: likely `GLOBAL`.
Conflicts: None explicit.
Cody's recommendation: Introduce `SOUND_SUBSYSTEM` category only if additional non-overlapping sound-behavior findings are accepted in Task 2.
Why surfaced: §A.4 OTHER category trigger.

## Phase 4 — Taxonomy Diagnostic

| Category | Candidate count | Notes |
|---|---:|---|
| BOOT_PATH | 2 | Bootstrap-loop and vector-jump behavior candidates |
| WATCHDOG | 4 | Core mechanism + writer classes + reachability context |
| COORDINATE_MODEL | 5 | BM-001/BM-002 fault class + bookmarks_v2 replacement model |
| MEMORY_MAP | 4 | WRAM ownership/fields + helper location + non-ROM classification |
| VDP_BEHAVIOR | 4 | Composed-output mismatch + nametable-state evidence + palette/layer behavior |
| INTERRUPT_BEHAVIOR | 3 | Ownership + enable-site ordering |
| GRAPHICS_PIPELINE | 4 | VBlank producer timing + LUT/scroll/sprite-clear behavior |
| TRANSLATION_MODEL | 3 | Invariants + legacy rejection + failure-ID split semantics |
| DIAGNOSTIC_LIMITATION | 5 | Trace sampling and contamination/evidence-integrity limitations |
| HARDWARE_MAPPING | 4 | TC0040IOC, DIP polarity/defaults, open-bus mapping |
| OTHER_REQUIRES_REVIEW | 2 | `SPRITE_ENGINE`:1, `SOUND_SUBSYSTEM`:1 |
| **TOTAL** | **40** | Within thresholds (no soft/hard count trigger) |

Diagnostic interpretation: **TAXONOMY_FITS** (OTHER count = 2, within 0-3 band).

Candidate-threshold check:
- Total candidates = 40 (`<=50`): no soft warning.
- Total candidates = 40 (`<=75`): no hard STOP.
- OTHER count = 2 (`<=15`): no taxonomy STOP.

