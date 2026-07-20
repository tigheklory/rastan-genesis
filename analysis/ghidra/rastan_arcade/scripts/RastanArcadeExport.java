// Export whole-game static-analysis artifacts for original arcade Rastan maincpu.
//@category Rastan

import ghidra.app.decompiler.*;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.block.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.scalar.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.pcode.*;
import ghidra.program.model.data.*;

import java.io.*;
import java.util.*;

public class RastanArcadeExport extends GhidraScript {
    private File outDir;
    private AddressSpace space;
    private Listing listing;
    private FunctionManager fm;
    private ReferenceManager refs;
    private Memory mem;

    private Address addr(long off) { return space.getAddress(off); }
    private String hex(long v, int w) { return String.format("0x%0" + w + "X", v); }
    private PrintWriter writer(String name) throws Exception { return new PrintWriter(new BufferedWriter(new FileWriter(new File(outDir, name)))); }

    private boolean inRom(long v) { return v >= 0 && v < 0x60000L; }
    private boolean inHw(long v) {
        return (v >= 0x10c000L && v <= 0x10ffffL) || (v >= 0x200000L && v <= 0x200fffL) ||
               (v >= 0x350008L && v <= 0x350009L) || (v >= 0x380000L && v <= 0x380001L) ||
               (v >= 0x390000L && v <= 0x39000bL) || (v >= 0x3c0000L && v <= 0x3c0001L) ||
               (v >= 0x3e0000L && v <= 0x3e0003L) || (v >= 0xc00000L && v <= 0xc0ffffL) ||
               (v >= 0xc20000L && v <= 0xc20003L) || (v >= 0xc40000L && v <= 0xc40003L) ||
               (v >= 0xc50000L && v <= 0xc50003L) || (v >= 0xd00000L && v <= 0xd03fffL);
    }
    private String spaceName(long v) {
        if (v >= 0x10c000L && v <= 0x10ffffL) return "arcade_WRAM";
        if (v >= 0x200000L && v <= 0x200fffL) return "arcade_palette_RAM";
        if (v >= 0x350008L && v <= 0x350009L) return "arcade_unknown_350008";
        if (v >= 0x380000L && v <= 0x380001L) return "arcade_sprite_ctrl";
        if (v >= 0x390000L && v <= 0x39000bL) return "arcade_inputs";
        if (v >= 0x3c0000L && v <= 0x3c0001L) return "arcade_watchdog";
        if (v >= 0x3e0000L && v <= 0x3e0003L) return "arcade_sound_comm";
        if (v >= 0xc00000L && v <= 0xc0ffffL) return "PC080SN_tilemap";
        if (v >= 0xc20000L && v <= 0xc20003L) return "PC080SN_yscroll";
        if (v >= 0xc40000L && v <= 0xc40003L) return "PC080SN_xscroll";
        if (v >= 0xc50000L && v <= 0xc50003L) return "PC080SN_ctrl";
        if (v >= 0xd00000L && v <= 0xd03fffL) return "PC090OJ_sprite_RAM";
        if (inRom(v)) return "arcade_ROM";
        return "other";
    }

    private String bytesFor(Instruction ins) {
        try {
            byte[] bs = ins.getBytes();
            StringBuilder sb = new StringBuilder();
            for (byte b: bs) sb.append(String.format("%02X", b & 0xff));
            return sb.toString();
        } catch(Exception e) { return ""; }
    }

    private String refsFrom(Address a) {
        StringBuilder sb = new StringBuilder();
        Reference[] rr = refs.getReferencesFrom(a);
        for (Reference r: rr) {
            if (sb.length() > 0) sb.append(";");
            sb.append(r.getReferenceType()).append(":").append(r.getToAddress());
        }
        return sb.toString();
    }

    private void exportListing() throws Exception {
        PrintWriter pw = writer("full_listing.tsv");
        pw.println("arcade_pc\tbytes\tmnemonic\toperands\tfunction\trefs_from");
        InstructionIterator it = listing.getInstructions(addr(0), true);
        while (it.hasNext() && !monitor.isCancelled()) {
            Instruction ins = it.next();
            long off = ins.getAddress().getOffset();
            if (!inRom(off)) continue;
            Function f = fm.getFunctionContaining(ins.getAddress());
            StringBuilder ops = new StringBuilder();
            for (int i=0; i<ins.getNumOperands(); i++) {
                if (i > 0) ops.append(", ");
                ops.append(ins.getDefaultOperandRepresentation(i));
            }
            pw.printf("0x%06X\t%s\t%s\t%s\t%s\t%s\n", off, bytesFor(ins), ins.getMnemonicString(), ops.toString(), f == null ? "" : f.getName(), refsFrom(ins.getAddress()));
        }
        pw.close();
    }

    private void exportFunctions() throws Exception {
        PrintWriter inv = writer("function_inventory.tsv");
        PrintWriter cg = writer("call_graph_edges.tsv");
        PrintWriter dot = writer("call_graph.dot");
        inv.println("arcade_pc\tname\tentry\tbody_min\tbody_max\tinstruction_count\tcallers\tcallees");
        cg.println("caller_pc\tcaller_name\tcallee_pc\tcallee_name\tcallsite\ttype");
        dot.println("digraph rastan_arcade_call_graph {");
        int fc = 0;
        FunctionIterator fit = fm.getFunctions(true);
        while (fit.hasNext() && !monitor.isCancelled()) {
            Function f = fit.next();
            long entry = f.getEntryPoint().getOffset();
            if (!inRom(entry)) continue;
            fc++;
            long min = Long.MAX_VALUE, max = 0; int ic = 0;
            InstructionIterator ii = listing.getInstructions(f.getBody(), true);
            while (ii.hasNext()) { Instruction ins = ii.next(); ic++; long o=ins.getAddress().getOffset(); min=Math.min(min,o); max=Math.max(max,o); }
            ArrayList<String> callers = new ArrayList<String>();
            for (Function c : f.getCallingFunctions(monitor)) callers.add(String.format("0x%06X:%s", c.getEntryPoint().getOffset(), c.getName()));
            ArrayList<String> callees = new ArrayList<String>();
            for (Function c : f.getCalledFunctions(monitor)) {
                callees.add(String.format("0x%06X:%s", c.getEntryPoint().getOffset(), c.getName()));
                cg.printf("0x%06X\t%s\t0x%06X\t%s\t\tFUNCTION_CALL\n", entry, f.getName(), c.getEntryPoint().getOffset(), c.getName());
                dot.printf("  \"%06X %s\" -> \"%06X %s\";\n", entry, f.getName().replace("\"", ""), c.getEntryPoint().getOffset(), c.getName().replace("\"", ""));
            }
            inv.printf("0x%06X\t%s\t0x%06X\t0x%06X\t0x%06X\t%d\t%s\t%s\n", entry, f.getName(), entry, min == Long.MAX_VALUE ? entry : min, max, ic, String.join(",", callers), String.join(",", callees));
        }
        dot.println("}");
        inv.close(); cg.close(); dot.close();
    }

    private void exportXrefsAndHw() throws Exception {
        PrintWriter xr = writer("xrefs.tsv");
        PrintWriter hw = writer("hw_refs.tsv");
        PrintWriter consts = writer("scalar_constants.tsv");
        xr.println("from_arcade_pc\tto\ttype\toperand_index\tfrom_function\tto_space");
        hw.println("arcade_pc\tinstruction\tref_or_scalar\ttarget\ttarget_space\taccess_guess\tfunction");
        consts.println("arcade_pc\tinstruction\toperand_index\tscalar\tscalar_space\tfunction");
        InstructionIterator it = listing.getInstructions(addr(0), true);
        while (it.hasNext() && !monitor.isCancelled()) {
            Instruction ins = it.next();
            long pc = ins.getAddress().getOffset();
            if (!inRom(pc)) continue;
            Function f = fm.getFunctionContaining(ins.getAddress());
            String fn = f == null ? "" : f.getName();
            for (Reference r : refs.getReferencesFrom(ins.getAddress())) {
                long to = r.getToAddress().getOffset();
                xr.printf("0x%06X\t%s\t%s\t%d\t%s\t%s\n", pc, r.getToAddress().toString(), r.getReferenceType().toString(), r.getOperandIndex(), fn, spaceName(to));
                if (inHw(to)) {
                    String acc = r.getReferenceType().isWrite() ? "write" : (r.getReferenceType().isRead() ? "read" : "unknown");
                    hw.printf("0x%06X\t%s\tref\t0x%06X\t%s\t%s\t%s\n", pc, ins.toString().replace('\t',' '), to, spaceName(to), acc, fn);
                }
            }
            for (int op=0; op<ins.getNumOperands(); op++) {
                Object[] objs = ins.getOpObjects(op);
                for (Object o: objs) {
                    Long val = null;
                    if (o instanceof Scalar) val = Long.valueOf(((Scalar)o).getUnsignedValue());
                    else if (o instanceof Address) val = Long.valueOf(((Address)o).getOffset());
                    if (val != null) {
                        long v = val.longValue();
                        if (inHw(v) || inRom(v)) {
                            consts.printf("0x%06X\t%s\t%d\t0x%06X\t%s\t%s\n", pc, ins.toString().replace('\t',' '), op, v, spaceName(v), fn);
                            if (inHw(v)) {
                                hw.printf("0x%06X\t%s\tscalar\t0x%06X\t%s\tunknown\t%s\n", pc, ins.toString().replace('\t',' '), v, spaceName(v), fn);
                            }
                        }
                    }
                }
            }
        }
        xr.close(); hw.close(); consts.close();
    }

    private void exportMemoryMap() throws Exception {
        PrintWriter pw = writer("memory_map.md");
        pw.println("# Rastan Arcade Main CPU Memory Map");
        pw.println();
        pw.println("Source: `docs/reference/mame/rastan/src/mame/taito/rastan.cpp`, `rastan_state::main_map`.");
        pw.println();
        pw.println("| address range | label | access | note |");
        pw.println("|---|---|---|---|");
        pw.println("| `arcade_pc 0x000000-0x05FFFF` | maincpu ROM | R/X | World Rev 1 MAME `maincpu`, 6x64 KiB LOAD16_BYTE interleave |");
        pw.println("| `arcade_WRAM 0x10C000-0x10FFFF` | work RAM | R/W | A5 base commonly `0x10C000` |");
        pw.println("| `arcade_HW_ADDRESS 0x200000-0x200FFF` | CLCS palette RAM | R/W | xBGR-555 palette RAM, 2048 words |");
        pw.println("| `arcade_HW_ADDRESS 0x350008-0x350009` | unknown/nop write | W | MAME nopw |");
        pw.println("| `arcade_HW_ADDRESS 0x380000-0x380001` | sprite control | W | sprite palette bank / coin / lockout |");
        pw.println("| `arcade_HW_ADDRESS 0x390000-0x39000B` | inputs / DIP | R | P1/P2/SPECIAL/SYSTEM/DSWA/DSWB |");
        pw.println("| `arcade_HW_ADDRESS 0x3C0000-0x3C0001` | watchdog | W | watchdog reset |");
        pw.println("| `arcade_HW_ADDRESS 0x3E0000-0x3E0003` | PC060HA sound comm | R/W | master port / comm |");
        pw.println("| `arcade_HW_ADDRESS 0xC00000-0xC0FFFF` | PC080SN tilemap | R/W | BG/FG tilemap C-window |");
        pw.println("| `arcade_HW_ADDRESS 0xC20000-0xC20003` | PC080SN Y scroll | W | yscroll_word_w |");
        pw.println("| `arcade_HW_ADDRESS 0xC40000-0xC40003` | PC080SN X scroll | W | xscroll_word_w |");
        pw.println("| `arcade_HW_ADDRESS 0xC50000-0xC50003` | PC080SN control | W | ctrl_word_w |");
        pw.println("| `arcade_HW_ADDRESS 0xD00000-0xD03FFF` | PC090OJ sprite RAM | R/W | object/sprite RAM |");
        pw.println();
        pw.println("## Ghidra Blocks");
        pw.println();
        pw.println("| block | start | end | R | W | X | volatile |");
        pw.println("|---|---:|---:|---|---|---|---|");
        for (MemoryBlock b : mem.getBlocks()) {
            pw.printf("| `%s` | `%s` | `%s` | %s | %s | %s | %s |\n", b.getName(), b.getStart(), b.getEnd(), b.isRead(), b.isWrite(), b.isExecute(), b.isVolatile());
        }
        pw.close();
    }

    private void exportJumpTables() throws Exception {
        PrintWriter pw = writer("jump_tables_and_indirects.tsv");
        pw.println("arcade_pc\tinstruction\tfunction\treferences_from\tnote");
        InstructionIterator it = listing.getInstructions(addr(0), true);
        while (it.hasNext()) {
            Instruction ins = it.next();
            long pc = ins.getAddress().getOffset();
            if (!inRom(pc)) continue;
            String m = ins.getMnemonicString().toLowerCase();
            String s = ins.toString().toLowerCase();
            boolean suspect = m.startsWith("jmp") || m.startsWith("jsr") || s.contains("pc,") || s.contains("@(") || s.contains("@[") || s.contains("switch") || s.contains("a0") || s.contains("a1") || s.contains("a2") || s.contains("a3") || s.contains("a4") || s.contains("a5");
            if (suspect && (m.startsWith("jmp") || m.startsWith("jsr") || s.contains("pc"))) {
                Function f = fm.getFunctionContaining(ins.getAddress());
                pw.printf("0x%06X\t%s\t%s\t%s\tmanual review for dynamic dispatch/table\n", pc, ins.toString().replace('\t',' '), f == null ? "" : f.getName(), refsFrom(ins.getAddress()));
            }
        }
        pw.close();
    }

    private void exportDecompiler() throws Exception {
        PrintWriter pw = writer("decompiler_export.c");
        DecompInterface ifc = new DecompInterface();
        DecompileOptions opts = new DecompileOptions();
        ifc.setOptions(opts);
        ifc.openProgram(currentProgram);
        int count = 0;
        FunctionIterator fit = fm.getFunctions(true);
        while (fit.hasNext() && !monitor.isCancelled()) {
            Function f = fit.next();
            if (!inRom(f.getEntryPoint().getOffset())) continue;
            DecompileResults res = ifc.decompileFunction(f, 20, monitor);
            pw.printf("\n/* ===== arcade_pc 0x%06X %s ===== */\n", f.getEntryPoint().getOffset(), f.getName());
            if (res != null && res.decompileCompleted() && res.getDecompiledFunction() != null) {
                pw.println(res.getDecompiledFunction().getC());
            } else {
                pw.printf("/* DECOMPILER_FAILED: %s */\n", res == null ? "null result" : res.getErrorMessage());
            }
            count++;
        }
        ifc.dispose();
        pw.close();
        println("Decompiler functions exported: " + count);
    }

    private void exportCoverage() throws Exception {
        boolean[] code = new boolean[0x60000];
        int instrCount = 0, codeBytes = 0;
        InstructionIterator it = listing.getInstructions(addr(0), true);
        while (it.hasNext()) {
            Instruction ins = it.next(); long pc = ins.getAddress().getOffset(); if (!inRom(pc)) continue;
            instrCount++;
            int len = ins.getLength();
            for (int i=0;i<len && pc+i<code.length;i++) if (!code[(int)pc+i]) { code[(int)pc+i]=true; codeBytes++; }
        }
        int funcs = 0;
        FunctionIterator fit = fm.getFunctions(true);
        while (fit.hasNext()) if (inRom(fit.next().getEntryPoint().getOffset())) funcs++;
        PrintWriter unr = writer("unresolved_regions.tsv");
        unr.println("start\tend\tsize\tnote");
        int regions=0, largest=0; int i=0;
        while (i<code.length) {
            if (code[i]) { i++; continue; }
            int st=i; while(i<code.length && !code[i]) i++; int en=i-1; int sz=i-st; regions++; largest=Math.max(largest,sz);
            String note = sz < 16 ? "small gap/data/alignment" : "unclassified data or unanalyzed code";
            unr.printf("0x%06X\t0x%06X\t0x%X\t%s\n", st,en,sz,note);
        }
        unr.close();
        PrintWriter cov = writer("coverage_report.md");
        cov.println("# Ghidra Coverage Report"); cov.println();
        cov.printf("- ROM bytes: `0x60000` (%d)\n", code.length);
        cov.printf("- Instruction count: `%d`\n", instrCount);
        cov.printf("- Code bytes classified by Ghidra: `0x%X` (%d)\n", codeBytes, codeBytes);
        cov.printf("- Code coverage by byte: `%.2f%%`\n", 100.0 * codeBytes / code.length);
        cov.printf("- Function count: `%d`\n", funcs);
        cov.printf("- Unresolved/data gap count: `%d`\n", regions);
        cov.printf("- Largest unresolved/data gap: `0x%X` bytes\n", largest);
        cov.println("- Note: unresolved gaps include intentional data tables, graphics/text descriptors, jump tables, constants, and any code Ghidra did not discover statically.");
        cov.close();
    }

    private void exportSubsystemMap() throws Exception {
        String[][] subs = {
            {"startup/reset", "0x03A000,0x03AE86,0x039F80", "reset vector/startup body/warm restart watchdog gate"},
            {"VBlank/lifecycle", "0x03A008", "arcade Level-5 VBlank handler and state dispatch"},
            {"title/attract text", "0x03ACAE,0x03BD48,0x0565A6", "known title glyph producer, glyph renderer, shared PC080SN text writer"},
            {"PC080SN tilemaps", "HW 0xC00000-0xC0FFFF", "BG/FG tilemap C-window references in hw_refs.tsv"},
            {"PC080SN scroll", "HW 0xC20000/0xC40000", "Y/X scroll hardware references in hw_refs.tsv"},
            {"PC090OJ sprites", "0x03B930,0x03B802,HW 0xD00000-0xD03FFF", "sprite producers and object RAM references"},
            {"palette", "HW 0x200000-0x200FFF,0x380000", "CLCS palette RAM and sprite palette-control refs"},
            {"input/sound/watchdog", "HW 0x390000,0x3E0000,0x3C0000", "input ports, PC060HA sound comm, watchdog"}
        };
        PrintWriter pw = writer("subsystem_map.md");
        pw.println("# Rastan Arcade Subsystem Map"); pw.println();
        pw.println("| subsystem | anchor addresses | notes |"); pw.println("|---|---|---|");
        for (String[] s: subs) pw.printf("| %s | `%s` | %s |\n", s[0], s[1], s[2]);
        pw.println(); pw.println("Detailed static references are in `hw_refs.tsv`, `function_inventory.tsv`, and `call_graph_edges.tsv`.");
        pw.close();
    }

    private void exportCorrelationSkeleton() throws Exception {
        PrintWriter pw = writer("address_correlation_report.json");
        pw.println("{");
        pw.println("  \"rule\": \"Arcade-to-Genesis correlation must use build/rastan-direct/address_map.json. This export does not derive Genesis addresses by arithmetic.\",");
        pw.println("  \"arcade_image\": \"analysis/ghidra/rastan_arcade/input/rastan_world_rev1_maincpu_68000.bin\",");
        pw.println("  \"arcade_space\": {\"load_base\": \"0x000000\", \"size\": \"0x60000\"},");
        pw.println("  \"genesis_mapping_source\": \"build/rastan-direct/address_map.json\",");
        pw.println("  \"status\": \"machine-readable exact mapping should be performed with project scripts against address_map.json; no +0x200/-0x200 proof is encoded here\"");
        pw.println("}");
        pw.close();
    }

    @Override
    public void run() throws Exception {
        String arg = getScriptArgs().length > 0 ? getScriptArgs()[0] : "analysis/ghidra/rastan_arcade/exports";
        outDir = new File(arg); outDir.mkdirs();
        space = currentProgram.getAddressFactory().getDefaultAddressSpace();
        listing = currentProgram.getListing(); fm = currentProgram.getFunctionManager(); refs = currentProgram.getReferenceManager(); mem = currentProgram.getMemory();
        println("=== RastanArcadeExport -> " + outDir.getAbsolutePath() + " ===");
        exportListing();
        exportFunctions();
        exportXrefsAndHw();
        exportMemoryMap();
        exportJumpTables();
        exportCoverage();
        exportSubsystemMap();
        exportCorrelationSkeleton();
        exportDecompiler();
        println("=== RastanArcadeExport done ===");
    }
}
