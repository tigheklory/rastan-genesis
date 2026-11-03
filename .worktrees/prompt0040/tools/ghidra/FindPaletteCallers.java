// Find all callers of 0x59AD4 (palette conversion routine) and their callers (2-level call tree)
// Run against maincpu.bin project (68000:BE:32:default)
//@category Rastan

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;

import java.util.*;

public class FindPaletteCallers extends GhidraScript {

    private static final long PALETTE_ROUTINE = 0x59AD4L;

    @Override
    public void run() throws Exception {
        AddressFactory af = currentProgram.getAddressFactory();
        AddressSpace space = af.getDefaultAddressSpace();
        ReferenceManager refMgr = currentProgram.getReferenceManager();
        FunctionManager funcMgr = currentProgram.getFunctionManager();

        Address palAddr = space.getAddress(PALETTE_ROUTINE);

        println("=== PALETTE ROUTINE CALL TREE ===");
        println(String.format("Target: 0x%06X (palette conversion routine)", PALETTE_ROUTINE));
        println("");

        // Level 1: direct callers of 0x59AD4
        ReferenceIterator refs = refMgr.getReferencesTo(palAddr);
        List<Address> level1 = new ArrayList<>();
        while (refs.hasNext()) {
            Reference ref = refs.next();
            RefType rt = ref.getReferenceType();
            if (rt.isCall() || rt == RefType.UNCONDITIONAL_JUMP || rt == RefType.COMPUTED_CALL) {
                level1.add(ref.getFromAddress());
            }
        }

        if (level1.isEmpty()) {
            println("No direct callers found via reference manager.");
            println("Falling back to raw reference scan...");
            // Try all reference types (Ghidra may not mark jumps as calls in flat binary)
            refs = refMgr.getReferencesTo(palAddr);
            while (refs.hasNext()) {
                Reference ref = refs.next();
                println(String.format("  Ref from 0x%06X type=%s",
                    ref.getFromAddress().getOffset(), ref.getReferenceType()));
                level1.add(ref.getFromAddress());
            }
        }

        println(String.format("LEVEL 1 CALLERS of 0x%06X: %d found", PALETTE_ROUTINE, level1.size()));
        println("");

        for (Address caller1 : level1) {
            long pc1 = caller1.getOffset();
            Function f1 = funcMgr.getFunctionContaining(caller1);
            String f1name = (f1 != null) ? f1.getName() : "<no function>";
            Address f1Entry = (f1 != null) ? f1.getEntryPoint() : caller1;

            println(String.format("  CALLER: 0x%06X  [in function: %s @ 0x%06X]",
                pc1, f1name, f1Entry.getOffset()));

            // Level 2: who calls the containing function
            if (f1 != null) {
                ReferenceIterator refs2 = refMgr.getReferencesTo(f1Entry);
                List<Address> level2 = new ArrayList<>();
                while (refs2.hasNext()) {
                    Reference ref2 = refs2.next();
                    RefType rt2 = ref2.getReferenceType();
                    if (rt2.isCall() || rt2 == RefType.UNCONDITIONAL_JUMP || rt2 == RefType.COMPUTED_CALL) {
                        level2.add(ref2.getFromAddress());
                    }
                }
                // Also try all ref types if nothing found
                if (level2.isEmpty()) {
                    refs2 = refMgr.getReferencesTo(f1Entry);
                    while (refs2.hasNext()) {
                        Reference ref2 = refs2.next();
                        level2.add(ref2.getFromAddress());
                    }
                }
                if (level2.isEmpty()) {
                    println(String.format("    No callers of function 0x%06X found.", f1Entry.getOffset()));
                }
                for (Address caller2 : level2) {
                    long pc2 = caller2.getOffset();
                    Function f2 = funcMgr.getFunctionContaining(caller2);
                    String f2name = (f2 != null) ? f2.getName() : "<no function>";
                    Address f2Entry = (f2 != null) ? f2.getEntryPoint() : caller2;
                    println(String.format("    CALLER2: 0x%06X  [in function: %s @ 0x%06X]",
                        pc2, f2name, f2Entry.getOffset()));
                }
            } else {
                // No function container — search for all references to the call site itself
                println("    (Call site is not in a recognized function — checking refs to call site)");
                ReferenceIterator refs2 = refMgr.getReferencesTo(caller1);
                while (refs2.hasNext()) {
                    Reference ref2 = refs2.next();
                    println(String.format("    REF to call site from 0x%06X type=%s",
                        ref2.getFromAddress().getOffset(), ref2.getReferenceType()));
                }
            }
            println("");
        }

        println("=== END PALETTE CALL TREE ===");
    }
}
