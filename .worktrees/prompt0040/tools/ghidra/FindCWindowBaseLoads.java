// Find instructions that load/compose C-window base addresses (0xC00000–0xCFFFFF)
// Captures immediate/base loads used for computed indirect accesses:
//  - MOVEA.L #0xC0xxxx,An
//  - ADDA.L  #0xC0xxxx,An
//  - ADDI.L  #0xC0xxxx,An
//  - LEA     0xC0xxxx,An
//  - MOVE.L  #0xC0xxxx,Dn
//
// Output includes arcade PC, mnemonic + operands, raw bytes/length, and
// ready-to-paste opcode_replace JSON with same-length NOP replacement.
//@category Rastan

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.scalar.Scalar;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class FindCWindowBaseLoads extends GhidraScript {

    private static final long CWINDOW_START = 0xC00000L;
    private static final long CWINDOW_END   = 0xD00000L; // exclusive

    private static boolean inCWindow(long value) {
        return value >= CWINDOW_START && value < CWINDOW_END;
    }

    private static String buildOperandString(Instruction instr) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < instr.getNumOperands(); i++) {
            if (i > 0) sb.append(",");
            sb.append(instr.getDefaultOperandRepresentation(i));
        }
        return sb.toString();
    }

    private static String bytesToHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) sb.append(String.format("%02x", b));
        return sb.toString();
    }

    private static String nopForLength(int byteLen) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < byteLen; i += 2) sb.append("4e71");
        return sb.toString();
    }

    private static byte[] readBytes(Memory memory, Address addr, int len) throws Exception {
        byte[] out = new byte[len];
        for (int i = 0; i < len; i++) {
            out[i] = memory.getByte(addr.add(i));
        }
        return out;
    }

    private static boolean hasCWindowImmediate(Instruction instr) {
        for (int op = 0; op < instr.getNumOperands(); op++) {
            Object[] objs = instr.getOpObjects(op);
            for (Object obj : objs) {
                if (obj instanceof Scalar) {
                    Scalar s = (Scalar) obj;
                    long unsignedVal = s.getUnsignedValue();
                    if (inCWindow(unsignedVal)) {
                        return true;
                    }
                }
            }
        }
        return false;
    }

    private static boolean isTargetMnemonic(String mnemonic) {
        String m = mnemonic.toLowerCase();
        return m.startsWith("movea")
            || m.startsWith("adda")
            || m.startsWith("addi")
            || m.startsWith("lea")
            || m.equals("move");
    }

    private static String inferredMnemonic(int op) {
        switch (op) {
            case 0x207c: case 0x227c: case 0x247c: case 0x267c:
            case 0x287c: case 0x2a7c: case 0x2c7c: case 0x2e7c:
                return "movea.l";
            case 0xd1fc: case 0xd3fc: case 0xd5fc: case 0xd7fc:
            case 0xd9fc: case 0xdbfc: case 0xddfc: case 0xdffc:
                return "adda.l";
            case 0x41f9: case 0x43f9: case 0x45f9: case 0x47f9:
            case 0x49f9: case 0x4bf9: case 0x4df9: case 0x4ff9:
                return "lea";
            case 0x203c: case 0x223c: case 0x243c: case 0x263c:
            case 0x283c: case 0x2a3c: case 0x2c3c: case 0x2e3c:
                return "move.l";
            default:
                return "unknown";
        }
    }

    private static boolean isPatternOpcode(int op) {
        switch (op) {
            case 0x207c: case 0x227c: case 0x247c: case 0x267c:
            case 0x287c: case 0x2a7c: case 0x2c7c: case 0x2e7c:
            case 0xd1fc: case 0xd3fc: case 0xd5fc: case 0xd7fc:
            case 0xd9fc: case 0xdbfc: case 0xddfc: case 0xdffc:
            case 0x41f9: case 0x43f9: case 0x45f9: case 0x47f9:
            case 0x49f9: case 0x4bf9: case 0x4df9: case 0x4ff9:
            case 0x203c: case 0x223c: case 0x243c: case 0x263c:
            case 0x283c: case 0x2a3c: case 0x2c3c: case 0x2e3c:
                return true;
            default:
                return false;
        }
    }

    @Override
    public void run() throws Exception {
        Listing listing = currentProgram.getListing();
        Memory memory = currentProgram.getMemory();
        List<Instruction> hits = new ArrayList<>();

        InstructionIterator iter = listing.getInstructions(true);
        while (iter.hasNext()) {
            Instruction instr = iter.next();
            String mnemonic = instr.getMnemonicString();
            if (!isTargetMnemonic(mnemonic)) continue;
            if (!hasCWindowImmediate(instr)) continue;
            hits.add(instr);
        }

        Set<Long> seen = new HashSet<>();
        List<Long> pcs = new ArrayList<>();

        println("=== C-WINDOW BASE LOAD SCAN (0xC00000-0xCFFFFF immediates) ===");
        println("Format: ARCADE_PC | MNEMONIC OPERANDS | BYTES_HEX | BYTE_COUNT | JSON_ENTRY");
        println("");

        for (Instruction instr : hits) {
            long pc = instr.getAddress().getOffset();
            if (seen.add(pc)) pcs.add(pc);
        }

        // Fallback pattern sweep to catch valid immediate-load opcodes in regions
        // Ghidra has not yet disassembled.
        for (MemoryBlock block : memory.getBlocks()) {
            if (!block.isInitialized()) continue;
            Address start = block.getStart();
            Address end = block.getEnd();
            long s = start.getOffset();
            long e = end.getOffset();
            if (e - s + 1 < 6) continue;

            for (long off = s; off <= (e - 5); off += 2) {
                Address addr = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(off);
                Instruction at = listing.getInstructionAt(addr);
                if (at != null) continue;

                int op = memory.getShort(addr) & 0xFFFF;
                if (!isPatternOpcode(op)) continue;

                long imm = memory.getInt(addr.add(2)) & 0xFFFFFFFFL;
                if (!inCWindow(imm)) continue;
                if (seen.add(off)) pcs.add(off);
            }
        }

        pcs.sort(Comparator.naturalOrder());

        int count = 0;
        for (Long pcObj : pcs) {
            long pc = pcObj.longValue();
            Address addr = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(pc);
            Instruction instr = listing.getInstructionAt(addr);
            String mnemonic;
            String operands;
            byte[] raw;

            if (instr != null) {
                mnemonic = instr.getMnemonicString();
                operands = buildOperandString(instr);
                raw = instr.getBytes();
            } else {
                int op = memory.getShort(addr) & 0xFFFF;
                long imm = memory.getInt(addr.add(2)) & 0xFFFFFFFFL;
                mnemonic = inferredMnemonic(op);
                operands = String.format("#0x%06X,<ea>", imm);
                raw = readBytes(memory, addr, 6);
            }

            String hex = bytesToHex(raw);
            String repl = nopForLength(raw.length);
            String arcadePc = String.format("0x%06X", pc);

            println(String.format("0x%06X | %s %s | %s | %d bytes",
                    pc, mnemonic, operands, hex, raw.length));

            String json = String.format(
                "{\"arcade_pc\":\"%s\",\"original_bytes\":\"%s\",\"replacement_bytes\":\"%s\",\"note\":\"NOP %s %s (C-window base load)\"}",
                arcadePc, hex, repl, mnemonic, operands);
            println("  -> " + json);

            count++;
        }

        println("");
        println(String.format("=== TOTAL: %d base-load instructions found ===", count));
    }
}
