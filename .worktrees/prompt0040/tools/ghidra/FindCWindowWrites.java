// Find all instructions that write to C-window address range (0xC00000–0xCFFFFF)
// Outputs arcade address, mnemonic, raw bytes, byte count, and ready-to-paste opcode_replace JSON
// Run against maincpu.bin project (68000:BE:32:default)
//@category Rastan

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.symbol.*;

import java.util.*;

public class FindCWindowWrites extends GhidraScript {

    private static final long CWINDOW_START = 0xC00000L;
    private static final long CWINDOW_END   = 0xD00000L; // exclusive

    @Override
    public void run() throws Exception {
        AddressFactory af = currentProgram.getAddressFactory();
        AddressSpace space = af.getDefaultAddressSpace();
        Listing listing = currentProgram.getListing();
        Memory memory = currentProgram.getMemory();
        ReferenceManager refMgr = currentProgram.getReferenceManager();

        Address cwStart = space.getAddress(CWINDOW_START);
        Address cwEnd   = space.getAddress(CWINDOW_END - 1);
        AddressRange cwRange = new AddressRangeImpl(cwStart, cwEnd);

        println("=== C-WINDOW WRITE SCAN (0xC00000-0xCFFFFF) ===");
        println("Format: ARCADE_PC | MNEMONIC | BYTES_HEX | BYTE_COUNT | JSON_ENTRY");
        println("");

        List<Instruction> hits = new ArrayList<>();

        // Walk all instructions in the program
        InstructionIterator iter = listing.getInstructions(true);
        while (iter.hasNext()) {
            Instruction instr = iter.next();
            Reference[] refs = instr.getReferencesFrom();
            for (Reference ref : refs) {
                RefType rt = ref.getReferenceType();
                if (!rt.isWrite() && !rt.isData()) continue;
                Address to = ref.getToAddress();
                long offset = to.getOffset();
                if (offset >= CWINDOW_START && offset < CWINDOW_END) {
                    hits.add(instr);
                    break;
                }
            }
        }

        // Also scan for CLR instructions that hit C-window (CLR is RMW — Ghidra may mark as READ)
        InstructionIterator iter2 = listing.getInstructions(true);
        while (iter2.hasNext()) {
            Instruction instr = iter2.next();
            String mnem = instr.getMnemonicString().toLowerCase();
            if (!mnem.startsWith("clr")) continue;
            Reference[] refs = instr.getReferencesFrom();
            for (Reference ref : refs) {
                Address to = ref.getToAddress();
                long offset = to.getOffset();
                if (offset >= CWINDOW_START && offset < CWINDOW_END) {
                    if (!hits.contains(instr)) hits.add(instr);
                    break;
                }
            }
        }

        // Sort by address
        hits.sort(Comparator.comparingLong(i -> i.getAddress().getOffset()));

        // Deduplicate
        Set<Long> seen = new LinkedHashSet<>();
        List<Instruction> unique = new ArrayList<>();
        for (Instruction i : hits) {
            long pc = i.getAddress().getOffset();
            if (seen.add(pc)) unique.add(i);
        }

        int count = 0;
        for (Instruction instr : unique) {
            long pc = instr.getAddress().getOffset();
            String mnem = instr.getMnemonicString();
            StringBuilder opStr = new StringBuilder();
            for (int i = 0; i < instr.getNumOperands(); i++) {
                if (i > 0) opStr.append(",");
                opStr.append(instr.getDefaultOperandRepresentation(i));
            }

            byte[] rawBytes;
            try {
                rawBytes = instr.getBytes();
            } catch (Exception e) {
                rawBytes = new byte[0];
            }

            StringBuilder hexBytes = new StringBuilder();
            for (byte b : rawBytes) hexBytes.append(String.format("%02x", b));

            // Build NOP replacement (4e71 repeated for same length)
            StringBuilder nopBytes = new StringBuilder();
            for (int i = 0; i < rawBytes.length; i += 2) nopBytes.append("4e71");

            String arcadePc = String.format("0x%06X", pc);
            String json = String.format(
                "{\"arcade_pc\":\"%s\",\"original_bytes\":\"%s\",\"replacement_bytes\":\"%s\",\"note\":\"NOP %s %s\"}",
                arcadePc, hexBytes, nopBytes, mnem, opStr
            );

            println(String.format("0x%06X | %s %s | %s | %d bytes",
                pc, mnem, opStr, hexBytes, rawBytes.length));
            println("  -> " + json);
            count++;
        }

        println("");
        println(String.format("=== TOTAL: %d write instructions found ===", count));

        // Coverage check against existing NOPs (reads existing JSON if accessible)
        println("");
        println("NOTE: Indirect writes (via register, e.g. movew d0,(a1)+) are NOT captured here.");
        println("Those require call-chain tracing from the caller (see FindCWindowIndirectWriters.java).");
    }
}
