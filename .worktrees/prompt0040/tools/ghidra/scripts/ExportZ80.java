// Headless Z80 export for AUDIO-001. Exports disassembly, decompiled C, function map, IO xrefs.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.lang.OperandType;
import java.io.*;
import java.util.*;

public class ExportZ80 extends GhidraScript {
  public void run() throws Exception {
    String out = getScriptArgs().length>0 ? getScriptArgs()[0] : "build/audio";
    new File(out).mkdirs();
    Listing listing = currentProgram.getListing();

    // 1) disassembly listing
    PrintWriter dis = new PrintWriter(new FileWriter(out+"/audiocpu.disasm.txt"));
    InstructionIterator it = listing.getInstructions(true);
    while (it.hasNext()) { Instruction i = it.next();
      dis.printf("%s:\t%s%n", i.getAddress(), i.toString()); }
    dis.close();

    // 2) function map + decompiled C
    PrintWriter fmap = new PrintWriter(new FileWriter(out+"/z80_functions.tsv"));
    fmap.println("entry_addr\tname\tsize_bytes\tcalled_by\tcalls");
    PrintWriter cout = new PrintWriter(new FileWriter(out+"/z80_decomp.c"));
    cout.println("/* GENERATED Ghidra Z80 decompilation of audiocpu.bin (b04-19.49). Reference only. */");
    DecompInterface dec = new DecompInterface();
    dec.openProgram(currentProgram);
    FunctionManager fm = currentProgram.getFunctionManager();
    int nfun=0;
    for (Function f : fm.getFunctions(true)) {
      nfun++;
      Set<Function> callers = f.getCallingFunctions(monitor);
      Set<Function> callees = f.getCalledFunctions(monitor);
      StringBuilder cb=new StringBuilder(), ce=new StringBuilder();
      for (Function c: callers){ cb.append(c.getEntryPoint()); cb.append(","); }
      for (Function c: callees){ ce.append(c.getEntryPoint()); ce.append(","); }
      fmap.printf("%s\t%s\t%d\t%s\t%s%n", f.getEntryPoint(), f.getName(),
        f.getBody().getNumAddresses(), cb.toString(), ce.toString());
      DecompileResults r = dec.decompileFunction(f, 60, monitor);
      cout.printf("%n/* ==== %s @ Z80 0x%s  (callers=%d callees=%d) ==== */%n",
        f.getName(), f.getEntryPoint(), callers.size(), callees.size());
      if (r!=null && r.decompileCompleted() && r.getDecompiledFunction()!=null)
        cout.println(r.getDecompiledFunction().getC());
      else cout.println("/* decompile FAILED; see disasm */");
    }
    fmap.close(); cout.close();

    // 3) IO port references (immediate operands hitting chip ports)
    PrintWriter io = new PrintWriter(new FileWriter(out+"/z80_io_refs.tsv"));
    io.println("addr\tinstr\tport");
    long[] ports = {0x9000,0x9001,0xA000,0xB000,0x8000,0x9800,0xA800};
    InstructionIterator it2 = listing.getInstructions(true);
    while (it2.hasNext()) { Instruction i = it2.next();
      for (int op=0; op<i.getNumOperands(); op++){
        Object[] rep = i.getOpObjects(op);
        for (Object o: rep){ if (o instanceof Scalar){ long v=((Scalar)o).getUnsignedValue();
          for (long p: ports) if (v==p){ io.printf("%s\t%s\t0x%04X%n", i.getAddress(), i.toString(), p); } } }
      } }
    io.close();
    println("ExportZ80 done: functions="+nfun);
  }
}
