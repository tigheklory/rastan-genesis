//Find all references to a specific address range
//@category Analysis

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;

public class FindRefs extends GhidraScript {
    @Override
    public void run() throws Exception {
        AddressFactory af = currentProgram.getAddressFactory();
        AddressSpace space = af.getDefaultAddressSpace();

        // Search for references in range C09E00 - C09EFF
        long start = 0xC09E00L;
        long end   = 0xC09EFFL;

        println("=== References to C09E00-C09EFF ===");
        for (long addr = start; addr <= end; addr++) {
            Address target = space.getAddress(addr);
            ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(target);
            while (refs.hasNext()) {
                Reference ref = refs.next();
                println(String.format("  FROM 0x%08X  TO 0x%08X  type=%s",
                    ref.getFromAddress().getOffset(),
                    ref.getToAddress().getOffset(),
                    ref.getReferenceType()));
            }
        }
        println("=== Done ===");
    }
}
