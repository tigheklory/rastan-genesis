// Set up arcade hardware memory map segments for maincpu.bin project
// Run ONCE after import to add hardware register address spaces
// Adds named overlay blocks so Ghidra can resolve hardware register references
//@category Rastan

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.mem.*;

public class SetupArcadeMemoryMap extends GhidraScript {

    @Override
    public void run() throws Exception {
        Memory mem = currentProgram.getMemory();
        AddressFactory af = currentProgram.getAddressFactory();
        AddressSpace space = af.getDefaultAddressSpace();

        println("=== Setting up Rastan arcade memory map segments ===");

        // Segment table: name, start, size, note
        long[][] segments = {
            // start       size      (size in bytes)
            {0x0C0000L, 0x020000L},  // tilemap chip registers
            {0x100000L, 0x010000L},  // work RAM
            {0x200000L, 0x010000L},  // palette RAM
            {0xC00000L, 0x060000L},  // tilemap C-windows (C00000-C5FFFF)
            {0xD00000L, 0x000800L},  // sprite chip RAM
            {0x390000L, 0x010000L},  // I/O space (Taito I/O chips)
        };

        String[] names = {
            "tilemap_regs",
            "work_ram",
            "palette_ram",
            "cwindow",
            "sprite_ram",
            "io_space",
        };

        int added = 0;
        for (int i = 0; i < segments.length; i++) {
            long start = segments[i][0];
            long size  = segments[i][1];
            String name = names[i];

            Address addr = space.getAddress(start);

            // Skip if block already exists at this address
            if (mem.getBlock(addr) != null) {
                println(String.format("  SKIP %s @ 0x%06X (block already exists)", name, start));
                continue;
            }

            try {
                // Add uninitialized block (volatile hardware space — no backing bytes)
                mem.createUninitializedBlock(name, addr, size, false);
                println(String.format("  ADDED %s @ 0x%06X size=0x%X", name, start, size));
                added++;
            } catch (Exception e) {
                println(String.format("  ERROR adding %s @ 0x%06X: %s", name, start, e.getMessage()));
            }
        }

        println(String.format("=== Done: %d segments added ===", added));
        println("Re-run auto-analysis (or re-import with -overwrite) after adding segments.");
        println("C-window range 0xC00000-0xC5FFFF is now named 'cwindow' — FindCWindowWrites.java will resolve refs correctly.");
    }
}
