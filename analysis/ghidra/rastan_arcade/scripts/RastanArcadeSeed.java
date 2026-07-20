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
