// Seed original arcade Rastan World Rev 1 maincpu image for whole-game analysis.
//@category Rastan

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.symbol.*;

public class RastanArcadeSeed extends GhidraScript {
    private AddressSpace space;

    private Address addr(long off) {
        return space.getAddress(off);
    }

    private void label(long off, String name) throws Exception {
        createLabel(addr(off), name, true, SourceType.USER_DEFINED);
    }

    private void fn(long off, String name) throws Exception {
        Address a = addr(off);
        disassemble(a);
        Function f = getFunctionAt(a);
        if (f == null) {
            try {
                f = createFunction(a, name);
            } catch (Exception e) {
                println(String.format("WARN createFunction 0x%06X %s: %s", off, name, e.getMessage()));
            }
        }
        if (f != null) {
            f.setName(name, SourceType.USER_DEFINED);
        }
    }

    private void block(String name, long start, long size, boolean read, boolean write, boolean exec, boolean vol) throws Exception {
        Memory mem = currentProgram.getMemory();
        Address a = addr(start);
        if (mem.getBlock(a) != null) {
            println(String.format("SKIP block %-18s @ 0x%06X", name, start));
            return;
        }
        MemoryBlock b = mem.createUninitializedBlock(name, a, size, false);
        b.setRead(read);
        b.setWrite(write);
        b.setExecute(exec);
        b.setVolatile(vol);
        println(String.format("ADD  block %-18s @ 0x%06X size=0x%X", name, start, size));
    }

    @Override
    public void run() throws Exception {
        space = currentProgram.getAddressFactory().getDefaultAddressSpace();
        println("=== RastanArcadeSeed start ===");

        currentProgram.setName("rastan_world_rev1_maincpu_68000");

        // MAME rastan_state::main_map, labelled as arcade address spaces.
        block("arcade_WRAM",        0x10c000L, 0x004000L, true, true,  false, false);
        block("arcade_palette_RAM", 0x200000L, 0x001000L, true, true,  false, true);
        block("arcade_io",          0x350008L, 0x000002L, false,true,  false, true);
        block("arcade_sprite_ctrl", 0x380000L, 0x000002L, false,true,  false, true);
        block("arcade_inputs",      0x390000L, 0x00000cL, true, false, false, true);
        block("arcade_watchdog",    0x3c0000L, 0x000002L, false,true,  false, true);
        block("arcade_sound_comm",  0x3e0000L, 0x000004L, true, true,  false, true);
        block("PC080SN_tilemap",    0xc00000L, 0x010000L, true, true,  false, true);
        block("PC080SN_yscroll",    0xc20000L, 0x000004L, false,true,  false, true);
        block("PC080SN_xscroll",    0xc40000L, 0x000004L, false,true,  false, true);
        block("PC080SN_ctrl",       0xc50000L, 0x000004L, false,true,  false, true);
        block("PC090OJ_sprite_RAM", 0xd00000L, 0x004000L, true, true,  false, true);

        label(0x10c000L, "arcade_WRAM_base_A5");
        label(0x200000L, "CLCS_palette_RAM");
        label(0x350008L, "unknown_nopw_350008");
        label(0x380000L, "sprite_ctrl_coin_lockout_380000");
        label(0x390000L, "input_P1_390000");
        label(0x390002L, "input_P2_390002");
        label(0x390004L, "input_SPECIAL_390004");
        label(0x390006L, "input_SYSTEM_390006");
        label(0x390008L, "input_DSWA_390008");
        label(0x39000aL, "input_DSWB_39000a");
        label(0x3c0000L, "watchdog_reset_3c0000");
        label(0x3e0001L, "PC060HA_master_port_3e0001");
        label(0x3e0003L, "PC060HA_master_comm_3e0003");
        label(0xc00000L, "PC080SN_tilemap_base_c00000");
        label(0xc20000L, "PC080SN_yscroll_c20000");
        label(0xc40000L, "PC080SN_xscroll_c40000");
        label(0xc50000L, "PC080SN_ctrl_c50000");
        label(0xd00000L, "PC090OJ_sprite_RAM_d00000");

        fn(0x03a000L, "startup_common_vector_reset");
        fn(0x03a008L, "level5_vblank_handler");
        fn(0x039f80L, "warm_restart_watchdog_gate");
        fn(0x03ae86L, "startup_common_body");
        fn(0x03ab7cL, "warm_restart_gate_caller_a");
        fn(0x03b084L, "warm_restart_gate_caller_b");
        fn(0x03acaeL, "title_fg_glyph_producer_3acae");
        fn(0x03bd48L, "shared_glyph_renderer_3bd48");
        fn(0x03b930L, "pc090oj_sprite_producer_3b930");
        fn(0x03b802L, "pc090oj_sprite_producer_3b802");
        fn(0x0565a6L, "shared_pc080sn_text_writer_565a6");

        // Player/attack semantic model. These entries are reached through
        // computed dispatch or code regions that default analysis does not
        // discover from the reset vectors.
        fn(0x03a196L, "frontend_state_dispatch_3a196");
        fn(0x03a1c4L, "frontend_state0_init_3a1c4");
        fn(0x03a200L, "frontend_state1_update_3a200");
        fn(0x03a2d8L, "frontend_state2_update_3a2d8");
        fn(0x03a304L, "frontend_state3_update_3a304");
        fn(0x03a39aL, "frontend_state4_update_3a39a");
        fn(0x03a420L, "frontend_state5_update_3a420");
        fn(0x03a450L, "frontend_state6_update_3a450");
        fn(0x03a474L, "frontend_state7_update_3a474");
        fn(0x03a478L, "frontend_state8_update_3a478");
        fn(0x051090L, "player_main_update_51090");
        fn(0x051ca0L, "player_attack_initialize_51ca0");
        fn(0x051d32L, "player_attack_advance_51d32");
        fn(0x051e24L, "player_crouch_enter_51e24");
        fn(0x03c902L, "actor_four_record_expand_3c902");
        fn(0x03d054L, "actor_family0_render_3d054");
        fn(0x045342L, "paired_actor_init_45342");
        fn(0x0453a2L, "paired_actor_activate_453a2");
        fn(0x04543eL, "actor_record_loader_4543e");
        fn(0x054052L, "player_sprite_slot_init_54052");
        fn(0x0540ccL, "player_body_constructor_540cc");
        fn(0x0547c0L, "player_aux_update_547c0");
        fn(0x054810L, "player_aux_sprite_constructor_54810");
        fn(0x0446b0L, "actor_hurtbox_base_selector_446b0");
        fn(0x0446bcL, "actor_hurtbox_selector_446bc");
        fn(0x0449b4L, "player_actor_collision_scan_449b4");
        fn(0x044c5aL, "player_attack_overlap_entry_44c5a");
        fn(0x044cbaL, "signed_interval_overlap_44cba");
        fn(0x054864L, "player_collision_boxes_update_54864");
        fn(0x054982L, "player_attack_box_enable_update_54982");

        // Actor/map grounding model. The 0x041xxx family is entered through
        // actor dispatch rather than a direct reset-vector call, so default
        // analysis previously left the decisive 8-pixel row scan unresolved.
        fn(0x041064L, "actor_surface_marker_find_41064");
        fn(0x04114aL, "actor_spawn_x_bound_select_4114a");
        fn(0x041180L, "actor_spawn_ground_and_activate_41180");
        fn(0x042e38L, "actor_velocity_and_map_collision_42e38");
        fn(0x045d10L, "actor_map_collision_variant_45d10");
        fn(0x04736aL, "actor_map_collision_variant_4736a");
        fn(0x053a2eL, "collision_map_lookup_53a2e");
        fn(0x053a6eL, "player_collision_probe_family_53a6e");
        fn(0x053b34L, "player_ground_contact_probe_family_53b34");
        fn(0x05a29cL, "collision_map_surface_postprocess_5a29c");
        fn(0x05a2eeL, "collision_map_surface_mark_5a2ee");

        label(0x03a1acL, "frontend_state_dispatch_offsets_3a1ac");
        label(0x03a1ccL, "sprite_palette_control_writer_3a1cc");
        label(0x03d09eL, "actor_family0_class_offsets_3d09e");
        label(0x03d5ebL, "lizard_class17_descriptor_3d5eb");
        label(0x03d60cL, "lizard_class18_descriptor_3d60c");
        label(0x045592L, "actor_record_table_45592");
        label(0x0550a8L, "player_state_handler_table_550a8");
        label(0x05b6a0L, "player_action0_primary_phase_table_5b6a0");
        label(0x05b978L, "player_crouch_primary_phase_table_5b978");
        label(0x05ba78L, "player_action0_secondary_phase_table_5ba78");
        label(0x05b948L, "player_crouch_secondary_phase_table_5b948");
        label(0x05bae0L, "player_attack_selector0_table_5bae0");
        label(0x05bb10L, "player_attack_selector_nonzero_table_5bb10");
        label(0x05bd40L, "player_primary_piece_descriptors_5bd40");
        label(0x05c466L, "player_secondary_piece_descriptors_5c466");
        label(0x05da5eL, "player_aux_piece_table_5da5e");
        label(0x044778L, "actor_hurtbox_base_selector_table_44778");
        label(0x044ce0L, "actor_hurtbox_extent_table_44ce0");
        label(0x044fa8L, "actor_hurtbox_alt_extent_table_44fa8");
        label(0x05c90eL, "player_body_collision_extent_table_5c90e");
        label(0x05c9eaL, "stage1_player_attack_extent_table_5c9ea");
        label(0x05cac6L, "stage2_player_attack_extent_table_5cac6");
        label(0x05cba2L, "stage3_player_attack_extent_table_5cba2");
        label(0x05cc7eL, "stage4_player_attack_extent_table_5cc7e");

        // Player collision fields are A5-relative in arcade WRAM. The labels
        // document the producer/consumer contract without imposing a C struct.
        label(0x10d0e8L, "player_broad_action_A5_10e8");
        label(0x10d108L, "player_attack_active_A5_1108");
        label(0x10d10aL, "player_attack_phase_A5_110a");
        label(0x10d114L, "player_facing_A5_1114");
        label(0x10d116L, "player_attack_variant_A5_1116");
        label(0x10d244L, "player_body_frame_selector_A5_1244");
        label(0x10d248L, "player_body_collision_extents_A5_1248");
        label(0x10d254L, "player_attack_collision_extents_A5_1254");
        label(0x10d2a8L, "player_body_contact_records_A5_12a8");
        label(0x10d2c8L, "player_attack_hit_records_A5_12c8");
        label(0x10d2f8L, "player_attack_box_enabled_A5_12f8");
        label(0x10d2faL, "player_stage_scene_A5_12fa");
        label(0x10de00L, "collision_map_64x64_words_base");
        label(0x10fe00L, "collision_map_64x64_words_end");

        // Seed functions from vector table where vector values point into main ROM.
        Memory mem = currentProgram.getMemory();
        for (int i = 0; i < 0x100; i += 4) {
            long v = mem.getInt(addr(i)) & 0xffffffffL;
            if (v >= 0 && v < 0x60000L && (v & 1L) == 0L) {
                fn(v, String.format("vector_%02x_target_%06x", i / 4, v));
            }
        }
        println("=== RastanArcadeSeed done ===");
    }
}
