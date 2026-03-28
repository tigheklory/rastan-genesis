# Title Logo Decode Breakpoint

## Scope
- Mode: research only.
- Path traced only: `0x202B80 -> 0x2005C4` (pre-coin title window).
- Artifact context: `dist/Rastan_271.bin` plus existing trace artifacts.

## Section 1 - Full Consumer Trace
Trace source: `/tmp/build271_logo_consumer_bridgecall.txt` + disassembly from `dist/Rastan_271.bin`.

1. `PC=0x202B80` `moveml %d0-%fp,%sp@-`
- Effect: bridge saves caller register set.
- Data state: `descA(FF11FE..)=0000...`, `descB(FF01BC..)=0000...`, `code0=0000`, `tile0=0000`.

2. `PC=0x202B84` `jsr 0x2005C4`
- Effect: enters real logo consumer.

3. `PC=0x2005FE` `pea 0x2000`
4. `PC=0x200604` `jsr 0x2088B8`
- Effect: clears tile decode buffer at `0xE0FF791C` (`memset` path).

5. `PC=0x200624` `moveal %sp@(64),%a0`
6. `PC=0x200628` `moveq #0,%d0`
7. `PC=0x20062A` `movew %a0@,%d0`
8. `PC=0x20062C` `moveal %d0,%a3`
9. `PC=0x20062E` `addal #0xE0FF004C,%a3`
- Effect: resolves descriptor base pointer.
- First block resolves to `A3=0xE0FF11FE`.

10. `PC=0x200634` `movew %a0@(2),%d0`
11. `PC=0x200638` `beqw 0x20087E`
- Branch: not taken (`D0=0x0012`, block count non-zero).

12. `PC=0x20064C` `moveb %a3@,%d5`
13. `PC=0x200670` `movew %d3,%d1`
14. `PC=0x200686` `movew %d0,%sp@(50)`
- Effect: first descriptor tuple read is all zero (from `0xE0FF11FE..`).
- Observed state at these PCs remains `descA=0000...`, `descB=0000...`, `code0=0000`, `tile0=0000`.

15. `PC=0x200690` `tstw %d7`
16. `PC=0x200692` `beqw 0x200B44`
- Branch: taken on first iteration (`D7=0`).

17. `PC=0x200B44` `moveq #0,%d6`
18. `PC=0x200B54` `addqw #1,%d7`
19. `PC=0x2006B4` `tstw %d2`
20. `PC=0x2006B6` `beqs 0x2006D4`
- Branch: taken first time (`D2=0`).

21. `PC=0x2006D4` `moveq #0,%d0`
22. `PC=0x2006E6` `movew %d1,%a0@(0,%a1:l)`
- Effect: writes zero decode code (`D1=0`) into decode staging family.

23. `PC=0x200712` loop (`jsr %a4@`) then `PC=0x200742` loop
- Effect: decode-copy loops execute, but sampled tile buffer head remains zero.

24. Loop continuation for remaining entries (same call):
- Repeated hits at `0x20064C/0x200670/0x200686` with zero-derived values.
- For subsequent entries (`D2>0`), decode remains non-productive:
  - `0x2006B6 beq 0x2006D4`: not taken (`D2 != 0`)
  - compare path at `0x2006C0/0x2006C2` reuses zero-code path (`D1=0` against zero-initialized cache), so flow returns through the non-productive side path instead of new non-zero decode staging.
- After first decode slot, flow repeatedly returns without producing non-zero sprite code/tile staging in this call.

25. Second descriptor block (`A3=0xE0FF01BC`) entered:
- `PC=0x200634` (offset `0x0170`), `PC=0x20063C` (`count=0x0004`), then same zero-data read path (`0x20064C...`).

26. End of consumer call:
- `PC=0x2009F8` DMA call setup path
- `PC=0x200A30` restore
- `PC=0x200A38` `rts`
- Return occurs with `code0=0000` and no SAT-visible payload proven.

## Section 2 - First Non-Productive Opcode
=== FIRST_LOGO_DECODE_BREAKPOINT ===
- PC: `0x20064C`
- instruction: `moveb %a3@,%d5`
- expected effect: first logo descriptor byte load should carry non-zero logo tuple content into decode state.
- actual effect: loads `0x00` from `A3=0xE0FF11FE` (descriptor window is zero at call time).
- why it prevents tile/sprite staging: this zero read propagates to zero decode fields (`D5/D4/D3/D1`), so the call builds/uses blank decode state (`code0` remains `0000`, tile buffer stays zero-leading), and no SAT-visible logo output is produced.

## Section 3 - Direct Opcode Replacement Target
=== NEXT_DIRECT_OPCODE_TARGET ===
- PC: `0x202B84`
- current bytes: `4E B9 00 20 05 C4`
- current semantic meaning: unconditional bridge call into logo consumer at the current timeline point.
- required semantic change: invoke the same consumer only when producer-populated descriptor windows are live for this frame (keep consumer semantics; fix handoff timing/ordering at opcode level).
- why this is the first correct direct replacement target: `0x20064C` is the first data-consumption breakpoint, and `0x202B84` is the nearest direct callsite controlling when that read happens without changing descriptor format or injecting fake sprite data.

## Section 4 - State / Data Proof
1. Descriptor values entering consumer are zero in traced bridge call:
- `bridge_entry` / `bridge_jsr_consumer` lines show
  - `descA=0000000000000000`
  - `descB=0000000000000000`
- Source: `/tmp/build271_logo_consumer_bridgecall.txt`.

2. First point `sprite_code0` remains zero:
- Already zero at `bridge_entry` and remains zero at first descriptor read site (`0x20064C`) and later decode setup sites.
- Source: `/tmp/build271_logo_consumer_bridgecall.txt` (`code0=0000` throughout traced call).

3. First point tile buffer remains empty:
- During decode loop hits (`0x200712`/`0x200742`), sampled tile buffer head remains zero.
- Source: `/tmp/build271_logo_consumer_bridgecall.txt` (`tile0_8=...0000`) and artifact summary (`tilebuf_nonzero=0/2048`).

4. First point SAT path is not reached productively:
- Build artifact reports `sat_writes=0`, `sat_nonzero=0` in pre-coin window.
- Source: `docs/research/artifacts/build271_logo_proof.txt`.

5. Producer output present but decode/output not:
- Later frame snapshot shows non-zero renderer-owned descriptor windows (`FF11FE/FF01BC`), while `sprite_code0` stays zero.
- Source: `docs/research/artifacts/build271_logo_proof.txt`.
