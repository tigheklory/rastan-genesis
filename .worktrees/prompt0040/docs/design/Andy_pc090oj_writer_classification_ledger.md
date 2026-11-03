# PC090OJ Writer PC Classification — Complete Coverage Ledger

**Author:** Andy
**Date:** 2026-04-24
**Trace source:** `states/traces/fu1_rastan_playtrace_20260424_164401/fu1_summary.txt`
**Disassembly source:** `build/maincpu.disasm.txt`
**Address space:** all PCs are arcade_pc (Genesis ROM offsets are arcade_pc + 0x200)

---

## 1. Methodology

### 1.1 Inputs

- 80 unique writer PCs reported by MAME watchpoint covering writes to PC090OJ sprite-RAM region `0x00D00000..0x00D007FF` during a gameplay session.
- Total writes captured: 6,808,648.
- The 6 unique April-6 Option A *target functions* (entry points reached by the 15 hooked call sites): `0x3B902`, `0x3B926`, `0x59F5E`, `0x41DAE`, `0x41F5E`, `0x45DFA`.

### 1.2 Prefetch resolution

MAME watchpoints report PC at the bus-cycle address, which leads the actual writing instruction by a prefetch offset. Empirical mapping derived from disassembly:

| Instruction form                              | Bytes | Reported delta |
|-----------------------------------------------|-------|----------------|
| `movew Dn, (a1)+` / `(a1)@(d)`                | 2 / 4 | +4             |
| `movew #imm, (an)+` / `(an)@(d)`              | 4 / 6 | +6             |
| `moveb Dn, (a1)@(d)` / `clrb (a1)@(d)`        | 4     | +6 (immediate-bearing) / +4 |
| `movel Dn, (an)+`                             | 2     | +4             |

Each writer below cites `instr_pc` (the actual instruction) and `reported_pc` (what the trace shows).

### 1.3 Reachability rules (per user prompt, no thresholding)

- **DOWNSTREAM** — the containing function is one of the 6 targets, OR is reached via a static call chain from one of the 6 targets.
- **INDEPENDENT** — the containing function is traced to all callers, none of which is reachable from any of the 6 targets.
- **UNKNOWN-INDIRECT** — the call chain breaks at an indirect call (`jmp (an)`, `jsr (an)`), a computed branch, or a vector dispatch we cannot statically resolve.

Rule 18 bias: when evidence is missing, classify UNKNOWN-INDIRECT, never DOWNSTREAM.

---

## 2. Static reachability tree from the 6 Option A target functions

### 2.1 Direct reach

```
0x41DAE  (target) ──┐
0x41F5E  (target) ──┤
0x45DFA  (target) ──┤   target functions execute writers in their own bodies
0x59F5E  (target) ──┤   (clear loops, copy loops)
0x3B902  (target) ──┤
0x3B926  (target) ──┘
```

### 2.2 0x41DAE / 0x45DFA → 0x3D054 sprite-template dispatcher

`0x3D054` has exactly 7 callers (verified by grep on disassembly):

| Caller       | In function | Type |
|--------------|-------------|------|
| `0x41DD2`    | `0x41DAE`   | bsrw |
| `0x41E0C`    | `0x41DAE`   | bsrw |
| `0x41E60`    | `0x41DAE`   | bsrw |
| `0x41E9E`    | `0x41DAE`   | bsrw |
| `0x45E28`    | `0x45DFA`   | jsr  |
| `0x45E64`    | `0x45DFA`   | jsr  |
| `0x45E9E`    | `0x45DFA`   | jsr  |

All 7 callers live inside April-6 target functions. `0x3D054` is therefore DOWNSTREAM.

`0x3D054` dispatches on `%a4@(56)`:
- `==1` → `jmp 0x4770E`
- `==2` → `jmp 0x3F0BC`
- `==3` → `jmp 0x3FFDC`
- `==4` → `jmp 0x3FFF0`
- default → `jmp 0x3C902` (the sprite-shape dispatcher)

All five branches feed `0x3C902` either directly or via `jmp 0x3C902` instructions at `0x3D098`, `0x3F0CA`, `0x3FFEA`, `0x3FFFE`, `0x47716`. The whole `0x3CXX` shape-handler tree is DOWNSTREAM via `0x41DAE`/`0x45DFA`.

### 2.3 0x3B902 → 0x3B930 writer helper

`0x3B902` body, line 74779:
```
3B902: lea 0xD00088, %a1
3B908: tstw %d1
3B90A: bnes 0x3B918
3B90C: lea %pc@(0x3B984), %a0
3B910: moveq #5, %d1
3B912: bsrw 0x3B930        ← BSR to writer helper
```

`0x3B930` is reachable from target `0x3B902`. (Other callers of `0x3B930` exist at `0x3B8BC/3B8D2/3B8E2`, all inside `0x3B8B0`, but the function-level reachability via `0x3B902@0x3B912` is sufficient to mark all `0x3B930`-internal writers DOWNSTREAM.)

### 2.4 0x3B926 falls through into 0x3B902 loop body

`0x3B926`:
```
3B926: lea 0xD00128, %a1
3B92C: moveq #9, %d0
3B92E: bras 0x3B91A      ← falls into 0x3B902's writer loop
```

`0x3B926` shares writer `0x3B91A` with `0x3B902` (writer reported at `0x3B91E`).

### 2.5 0x3C902 sprite-shape dispatcher

`0x3C902` reads byte from `%a0`, masks `0xF0`, and BEQ.W's to one of these handlers:

| Shape | Target   |
|-------|----------|
| 0x10  | 0x3C830  |
| 0x20  | 0x3C7A4  |
| 0x30  | 0x3C6DC  |
| 0x50  | 0x3C4D2  |
| 0x60  | 0x3C4D2  |
| 0x90  | 0x3C75C  |
| 0xA0  | 0x3C550  |
| 0xB0  | 0x3C636  |
| 0xC0  | 0x3C586  |
| (default fall-through) | 0x3C950 (with sub-handlers at 0x3C974 and 0x3C9A6) |

Each handler may BSR to one of the shared inner-loop helpers: `0x3C516`, `0x3C606`, `0x3C70A`, `0x3C742`, `0x3C7D2`, `0x3C804`, `0x3C85E`, `0x3CA12`. All are in the DOWNSTREAM tree.

---

## 3. Complete ledger — all 80 writer PCs

Format: `reported_pc (hits) → instr_pc | mnemonic | containing function | classification | evidence`

### 3.1 0x41DAE (target) writers — DOWNSTREAM

| reported | hits     | instr  | mnemonic                       | classification | evidence |
|----------|----------|--------|--------------------------------|----------------|----------|
| 41EC0    | 559260   | 41EBC  | `movew %d0,%a1@(2)`            | DOWNSTREAM     | inside fn 0x41DAE clear-fallback for D001C8 sub-loop |
| 41ED4    | 479572   | 41ED0  | `movew %d0,%a1@(2)`            | DOWNSTREAM     | inside fn 0x41DAE clear-fallback for D00300 sub-loop |
| 41EF2    | 1481689  | 41EEE  | `movew %d0,%a1@(2)`            | DOWNSTREAM     | inside fn 0x41DAE clear-fallback for D00460 sub-loop |
| 41F06    | 215457   | 41F02  | `movew %d0,%a1@(2)`            | DOWNSTREAM     | inside fn 0x41DAE clear-fallback for D00170 sub-loop |

Function span: `0x41DAE..0x41F0E`. RTS at `0x41EB4`; fall-through paths terminate via `bra` back to active sub-loop tails.

### 3.2 0x41F5E (target) writers — DOWNSTREAM

| reported | hits   | instr  | mnemonic              | classification | evidence |
|----------|--------|--------|-----------------------|----------------|----------|
| 41F82    | 423307 | 41F7E  | `movew %a0@+,%a1@+`   | DOWNSTREAM     | descriptor copy loop in fn 0x41F5E |
| 41F84    | 423307 | 41F80  | `movew %a0@+,%a1@+`   | DOWNSTREAM     | descriptor copy loop in fn 0x41F5E |
| 41F86    | 423307 | 41F82  | `movew %a0@+,%a1@+`   | DOWNSTREAM     | descriptor copy loop in fn 0x41F5E |
| 41F88    | 423307 | 41F84  | `movew %a0@+,%a1@+`   | DOWNSTREAM     | descriptor copy loop in fn 0x41F5E |
| 41F92    | 75037  | 41F8C  | `movew #384,%a1@(2)`  | DOWNSTREAM     | clear-fallback in fn 0x41F5E (entry at 0x41F8C, 6-byte; +6 prefetch) |

### 3.3 0x45DFA (target) writers — DOWNSTREAM

| reported | hits  | instr  | mnemonic              | classification | evidence |
|----------|-------|--------|-----------------------|----------------|----------|
| 45ECC    | 69690 | 45EC8  | `movew %d0,%a1@(2)`   | DOWNSTREAM     | clear-fallback for D00460 in fn 0x45DFA |
| 45EE0    | 18270 | 45EDC  | `movew %d0,%a1@(2)`   | DOWNSTREAM     | clear-fallback for D00170 in fn 0x45DFA |
| 45EF2    | 18540 | 45EEE  | `movew %d0,%a1@(2)`   | DOWNSTREAM     | clear-fallback for D00300 in fn 0x45DFA |

Function span: `0x45DFA..0x45EFA`. RTS at `0x45EB6`/`0x45EFA`.

### 3.4 0x59F5E (target) writers — DOWNSTREAM

| reported | hits | instr | mnemonic            | classification | evidence |
|----------|------|-------|---------------------|----------------|----------|
| 59F6E    | 96   | 59F6A | `movel %d0,%a0@+`   | DOWNSTREAM     | sprite-RAM clear (D00048) loop in fn 0x59F5E |
| 59F70    | 96   | 59F6C | `movel %d0,%a0@+`   | DOWNSTREAM     | sprite-RAM clear (D00048) loop in fn 0x59F5E |

### 3.5 0x3B902 / 0x3B926 (targets) and 0x3B930 helper — DOWNSTREAM

| reported | hits | instr | mnemonic            | containing fn | classification | evidence |
|----------|------|-------|---------------------|---------------|----------------|----------|
| 3B91E    | 69   | 3B91A | `moveb %d1,%a1@(2)` | 0x3B902 (target)| DOWNSTREAM   | inside target body; reached by 3B926 fall-through too |
| 3B936    | 102  | 3B932 | `movew %d2,%a1@+`   | 0x3B930       | DOWNSTREAM     | called from 0x3B902@0x3B912 |
| 3B93C    | 102  | 3B938 | `movew %d0,%a1@+`   | 0x3B930       | DOWNSTREAM     | called from 0x3B902@0x3B912 |
| 3B942    | 102  | 3B93E | `movew %d0,%a1@+`   | 0x3B930       | DOWNSTREAM     | called from 0x3B902@0x3B912 |
| 3B94C    | 102  | 3B948 | `movew %d7,%a1@+`   | 0x3B930       | DOWNSTREAM     | called from 0x3B902@0x3B912 |

### 3.6 0x3CXX sprite-shape dispatcher tree — DOWNSTREAM

All reached via `0x41DAE`/`0x45DFA` → `0x3D054` → `0x3C902` → handler.

| reported | hits   | instr | mnemonic                | containing fn | classification | shape route |
|----------|--------|-------|-------------------------|---------------|----------------|-------------|
| 3C4F0    | 52280  | 3C4EA | `movew #384,%a1@(2)`    | 0x3C4D2       | DOWNSTREAM     | shape 0x50/0x60 clear |
| 3C534    | 3872   | 3C530 | `movew %d0,%a1@(2)`     | 0x3C516       | DOWNSTREAM     | helper of 0x3C4D2 |
| 3C548    | 3872   | 3C544 | `movew %d7,%a1@(6)`     | 0x3C516       | DOWNSTREAM     | helper of 0x3C4D2 |
| 3C718    | 13226  | 3C712 | `movew #384,%a1@(2)`    | 0x3C70A       | DOWNSTREAM     | helper of 0x3C6DC (shape 0x30) |
| 3C724    | 7420   | 3C720 | `movew %d0,%a1@(2)`     | 0x3C70A       | DOWNSTREAM     | helper of 0x3C6DC |
| 3C738    | 7420   | 3C734 | `movew %d7,%a1@(6)`     | 0x3C70A       | DOWNSTREAM     | helper of 0x3C6DC |
| 3C74E    | 4497   | 3C74A | `movew %d6,%a1@(2)`     | 0x3C742       | DOWNSTREAM     | helper of 0x3C586/0x3C636/0x3C75C |
| 3C75A    | 4497   | 3C756 | `movew %d7,%a1@(6)`     | 0x3C742       | DOWNSTREAM     | helper of 0x3C586/0x3C636/0x3C75C |
| 3C7E4    | 15019  | 3C7DE | `movew #384,%a1@(2)`    | 0x3C7D2       | DOWNSTREAM     | helper of 0x3C7A4 (shape 0x20) |
| 3C7EE    | 41120  | 3C7EA | `movew %d0,%a1@(2)`     | 0x3C7D2       | DOWNSTREAM     | helper of 0x3C7A4 |
| 3C7FC    | 56139  | 3C7F8 | `movew %d7,%a1@(6)`     | 0x3C7D2       | DOWNSTREAM     | helper of 0x3C7A4 |
| 3C81A    | 16440  | 3C816 | `movew %d0,%a1@(2)`     | 0x3C804       | DOWNSTREAM     | helper of 0x3C7A4 |
| 3C828    | 16440  | 3C824 | `movew %d7,%a1@(6)`     | 0x3C804       | DOWNSTREAM     | helper of 0x3C7A4 |
| 3C87A    | 28464  | 3C874 | `movew #384,%a1@(2)`    | 0x3C85E       | DOWNSTREAM     | helper of 0x3C830 (shape 0x10) |
| 3C884    | 31896  | 3C880 | `movew %d0,%a1@(2)`     | 0x3C85E       | DOWNSTREAM     | helper of 0x3C830 |
| 3C892    | 60360  | 3C88E | `movew %d7,%a1@(6)`     | 0x3C85E       | DOWNSTREAM     | helper of 0x3C830 |
| 3C986    | 219945 | 3C982 | `movew %d0,%a1@+`       | 0x3C950 sub-handler 0x3C974 | DOWNSTREAM | default-shape primary |
| 3C994    | 219945 | 3C990 | `movew %d1,%a1@+`       | 0x3C950 sub-handler 0x3C974 | DOWNSTREAM | default-shape primary |
| 3C9A2    | 219945 | 3C99E | `movew %d7,%a1@+`       | 0x3C950 sub-handler 0x3C974 | DOWNSTREAM | default-shape primary |
| 3C9C6    | 191169 | 3C9C2 | `movew %d0,%a1@+`       | 0x3C950 sub-handler 0x3C9A6 | DOWNSTREAM | default-shape mirror |
| 3C9D0    | 191169 | 3C9CC | `movew %d1,%a1@+`       | 0x3C950 sub-handler 0x3C9A6 | DOWNSTREAM | default-shape mirror |
| 3C9E4    | 191169 | 3C9E0 | `movew %d7,%a1@+`       | 0x3C950 sub-handler 0x3C9A6 | DOWNSTREAM | default-shape mirror |
| 3C9FC    | 131416 | 3C9F6 | `movew #384,%a1@(2)`    | 0x3C950 clear   | DOWNSTREAM | default-shape clear |
| 3CA24    | 411114 | 3CA20 | `movew %d0,%a1@+`       | 0x3CA12       | DOWNSTREAM     | helper of 0x3C950 default-shape |

---

### 3.7 INDEPENDENT writers (none of the 6 targets reaches them)

#### 3.7.1 Sprite-RAM bulk-clear helper 0x3AD44

| reported | hits | instr | mnemonic          | containing fn | classification | callers (none = target) |
|----------|------|-------|-------------------|---------------|----------------|-------------------------|
| 3AD48    | 9628 | 3AD44 | `movel %d0,%a0@+` | 0x3AD44       | INDEPENDENT    | 0x3AD5C, 0x3AD6E, 0x3AD82, 0x3AE70, 0x3AE80, 0x3AF38, 0x3AF48 — all init/reset paths [^callers-3ad44] |

[^callers-3ad44]: An earlier revision of this row listed `0x3AD56` as the first caller. Corrected to `0x3AD5C` per [build/maincpu.disasm.txt:73900](build/maincpu.disasm.txt#L73900). The instruction at `0x3AD56` is `203c 0000 0100  movel #256, %d0` — not a call site. The actual `bsrs 0x3AD44` from inside `0x3AD4C` is at `0x3AD5C` (`61E6`). All 7 caller addresses verified against disassembly: `0x3AD5C` ([line 73900](build/maincpu.disasm.txt#L73900)) `bsrs`, `0x3AD6E` ([line 73904](build/maincpu.disasm.txt#L73904)) `bsrs`, `0x3AD82` ([line 73909](build/maincpu.disasm.txt#L73909)) `bsrs`, `0x3AE70` ([line 73978](build/maincpu.disasm.txt#L73978)) `bsrw`, `0x3AE80` ([line 73982](build/maincpu.disasm.txt#L73982)) `bsrw`, `0x3AF38` ([line 74026](build/maincpu.disasm.txt#L74026)) `bsrw`, `0x3AF48` ([line 74030](build/maincpu.disasm.txt#L74030)) `bsrw` — all target `0x3AD44`.

`0x3AD44` is a 4-byte loop body (`movel %d0,%a0@+; subqw #1,%d1; bnes 0x3AD44`). Used by `0x3AD4C` (clears 256 longs from 0xD00000) and `0x3AD72` (clears 480 longs). `0x3AD4C/0x3AD72` are called from scene-init sites at `0x3A242/0x3A2DC/0x3A5A4/0x3A8D6/0x3AA44/0x3AA9E/0x3ABB6/0x3AE70/etc.` None of these sites are reachable from any of the 6 target functions.

#### 3.7.2 Priority-init writer 0x3AD84 → 0x3ADAA

| reported | hits | instr | mnemonic            | containing fn | classification |
|----------|------|-------|---------------------|---------------|----------------|
| 3ADAE    | 34   | 3ADAA | `movel %d0,%a0@`    | 0x3AD84       | INDEPENDENT    |
| 3ADB0    | 34   | 3ADAC | `movel %d7,%a0@(4)` | 0x3AD84       | INDEPENDENT    |

`0x3AD84` writes 4 priority-frame slots starting at `0xD00778`. Reached only by fall-through from `0x3AD72` (called from 0x3ABB6 / 0x3AF28 — scene/level init). Never reached from any of the 6 targets.

#### 3.7.3 Score/HUD digit writer 0x3B802 (and helper 0x3B866)

| reported | hits | instr | mnemonic                | containing fn | classification |
|----------|------|-------|-------------------------|---------------|----------------|
| 3B83A    | 385  | 3B836 | `moveb %d6,%a1@(3)`     | 0x3B802       | INDEPENDENT    |
| 3B842    | 385  | 3B83E | `movew %d1,%a1@(4)`     | 0x3B802       | INDEPENDENT    |
| 3B856    | 354  | 3B852 | `moveb %d6,%a1@(3)`     | 0x3B802       | INDEPENDENT    |
| 3B85E    | 354  | 3B85A | `movew %d1,%a1@(4)`     | 0x3B802       | INDEPENDENT    |
| 3B874    | 388  | 3B86E | `moveb #1,%a1@(2)`      | 0x3B866 (helper of 0x3B802) | INDEPENDENT |
| 3B87E    | 351  | 3B878 | `clrb %a1@(2)`          | 0x3B866 (helper of 0x3B802) | INDEPENDENT |

`0x3B802` callers (verified by grep): `0x3A66A`, `0x3A9C0`, `0x3A9CE`, `0x3A9DA`, `0x3B7A2`, `0x3B7B0`, `0x3B7E0`, `0x3B8C2`, `0x3B8F6`, `0x3B8FC` — none on the April-6 hook list and none inside any of the 6 target functions.

#### 3.7.4 Sprite slot init 0x54052 (sprite slots 0–3 + Taito C-chip text RAM init)

| reported | hits | instr | mnemonic                | containing fn | classification |
|----------|------|-------|-------------------------|---------------|----------------|
| 540BC    | 792  | 540B6 | `movew #3,(%a1)+`       | 0x54052       | INDEPENDENT    |
| 540C0    | 792  | 540BA | `movew #0,(%a1)+`       | 0x54052       | INDEPENDENT    |
| 540C4    | 792  | 540BE | `movew #0,(%a1)+`       | 0x54052       | INDEPENDENT    |
| 540C8    | 792  | 540C2 | `movew #0,(%a1)+`       | 0x54052       | INDEPENDENT    |

Callers of `0x54052`: `0x501F4`, `0x51260`. Neither is in target tree.

#### 3.7.5 Sprite update routine 0x54810

| reported | hits | instr | mnemonic              | containing fn | classification |
|----------|------|-------|-----------------------|---------------|----------------|
| 54830    | 7156 | 5482C | `movew %d0,%a1@+`     | 0x54810       | INDEPENDENT    |
| 54842    | 7156 | 5483E | `movew %d0,%a1@+`     | 0x54810       | INDEPENDENT    |
| 54848    | 7156 | 54842 | `movew %a0@(0),%a1@+` | 0x54810       | INDEPENDENT    |
| 5485C    | 7156 | 54858 | `movew %d0,%a1@+`     | 0x54810       | INDEPENDENT    |

Callers: `0x547EE`, `0x54804` (both in fn `0x547D4`). Not reachable from any target.

#### 3.7.6 Sprite decay loop 0x5607C

| reported | hits | instr | mnemonic                | containing fn | classification |
|----------|------|-------|-------------------------|---------------|----------------|
| 560C8    | 4250 | 560C4 | `movew %d0,%a0@(2)`     | 0x5607C       | INDEPENDENT    |
| 560D4    | 7    | 560CE | `movew #0,%a0@(4)`      | 0x5607C       | INDEPENDENT    |

Caller of `0x5607C`: `0x55E92`. Not reachable from any target.

#### 3.7.7 Sprite-RAM copy helper 0x56114

| reported | hits | instr | mnemonic            | containing fn | classification |
|----------|------|-------|---------------------|---------------|----------------|
| 56120    | 20   | 5611C | `movew %a0@+,%a1@+` | 0x56114       | INDEPENDENT    |
| 56122    | 20   | 5611E | `movew %a0@+,%a1@+` | 0x56114       | INDEPENDENT    |
| 56124    | 20   | 56120 | `movew %a0@+,%a1@+` | 0x56114       | INDEPENDENT    |
| 56126    | 20   | 56122 | `movew %a0@+,%a1@+` | 0x56114       | INDEPENDENT    |

Callers of `0x56114`: `0x5604C` (inside 0x56056) and `0x56076` (inside 0x56056). `0x56056` itself called from `0x560E6` (within the `0x5607C` tree — INDEPENDENT). Not reachable from any target.

#### 3.7.8 Sprite-RAM zero-fill helper 0x5648A

| reported | hits | instr | mnemonic          | containing fn | classification |
|----------|------|-------|-------------------|---------------|----------------|
| 56492    | 144  | 5648E | `movel %d2,%a1@+` | 0x5648A       | INDEPENDENT    |
| 56494    | 144  | 56490 | `movel %d2,%a1@+` | 0x5648A       | INDEPENDENT    |

Caller of `0x5648A`: `0x56454` (inside `0x56440`). `0x56440` called from `0x55F0E`/`0x55FFA`. Not reachable from any target.

#### 3.7.9 Status/UI sprite writer 0x5A098

| reported | hits  | instr | mnemonic                | containing fn | classification |
|----------|-------|-------|-------------------------|---------------|----------------|
| 5A120    | 684   | 5A11A | `movew #0,%a0@+`        | 0x5A098       | INDEPENDENT    |
| 5A122    | 684   | 5A11E | `movew %d3,%a0@+`       | 0x5A098       | INDEPENDENT    |
| 5A128    | 684   | 5A124 | `movew %d0,%a0@+`       | 0x5A098       | INDEPENDENT    |
| 5A12A    | 684   | 5A126 | `movew %d2,%a0@+`       | 0x5A098       | INDEPENDENT    |
| 5A144    | 262   | 5A13E | `movew #0,%a0@+`        | 0x5A098       | INDEPENDENT    |
| 5A146    | 262   | 5A142 | `movew %d3,%a0@+`       | 0x5A098       | INDEPENDENT    |
| 5A14A    | 262   | 5A144 | `movew #972,%a0@+`      | 0x5A098       | INDEPENDENT    |
| 5A14C    | 262   | 5A148 | `movew %d2,%a0@+`       | 0x5A098       | INDEPENDENT    |
| 5A18E    | 1572  | 5A188 | `movew #0,%a0@+`        | 0x5A098       | INDEPENDENT    |
| 5A190    | 1572  | 5A18C | `movew %d3,%a0@+`       | 0x5A098       | INDEPENDENT    |
| 5A194    | 1572  | 5A18E | `movew #973,%a0@+`      | 0x5A098       | INDEPENDENT    |
| 5A196    | 1572  | 5A192 | `movew %d2,%a0@+`       | 0x5A098       | INDEPENDENT    |

Caller of `0x5A098`: `0x51054` only (jsr). Not reachable from any of the 6 target functions.

---

## 4. Summary counts

| Classification | Unique writer PCs | Total writes | % of trace writes |
|----------------|-------------------|--------------|-------------------|
| DOWNSTREAM     | 43                | 6,750,246    | 99.14 %           |
| INDEPENDENT    | 37                | 58,402       | 0.86 %            |
| UNKNOWN-INDIRECT | 0               | 0            | 0 %               |
| **Total**      | **80**            | **6,808,648**| **100 %**         |

No writer's call chain hit an indirect/computed branch we could not statically resolve. The `0x3D054` table-driven dispatch ultimately resolves to a `jmp 0x3C902` absolute long, so even the apparently computed path is statically reachable.

---

## 5. Architectural Outcome

### Selected outcome: **Outcome 2 — Option A is necessary but not sufficient**

The April-6 15-site Option A intercept correctly captures the **dominant render-loop write traffic** — 99.14 % of all PC090OJ writes during gameplay flow through the 6 target functions and the `0x3D054`/`0x3C902` shape-dispatch tree they reach. Workram-staging at the 15 hooked call sites, with deferred SAT emission at frame end, will produce a faithful image of every per-frame sprite emitted by the dispatcher tree.

However, **37 unique writer PCs (0.86 % of write volume) are unreachable from any of the 6 target functions** and will continue to write directly to PC090OJ sprite RAM unless additional intercepts are installed. These INDEPENDENT writers fall into five functional categories:

1. **Scene-init / reset bulk clears** (`0x3AD44`, `0x54052`) — overwrite sprite slots before a level begins. Without intercepting these, the staged workram image will not reflect the cleared state when the dispatcher re-renders.
2. **Sprite priority-frame init** (`0x3AD84` writing 0xD00778) — defines per-priority sprite slot layout. Reconciles with the `Andy_d00778_write_path_analysis` finding that priority init lives outside the render loop.
3. **Score / HUD digit rendering** (`0x3B802` + helper `0x3B866`) — every score-update writes digits directly into HUD sprite slots (e.g. `0xD00088`). Score display is always-on; missing this leaves stale digits on screen.
4. **Sprite decay / per-frame sprite-Y decrement** (`0x5607C`) — decrements sprite Y every frame for upward-rising effects. Critical for any rising HUD/effect sprite.
5. **Status / UI sprite writers** (`0x5A098`, `0x54810`, `0x56114`, `0x56440`/`0x5648A`) — life icons, lives counters, level banner, "1UP", weapon-pickup indicators. These write directly into reserved sprite slot ranges (`0xD00048..0xD000A0`, `0xD00170..`, etc.) outside the dispatcher tree.

### Action implications

To reach **complete PC090OJ coverage**, at least one of the following two strategies is required:

**Strategy A — extend the call-site intercept set.** Add hooks at every call site of each INDEPENDENT writer's containing function. Concretely (call sites taken from the disassembly):

| INDEPENDENT fn   | Call sites to hook                                          |
|------------------|-------------------------------------------------------------|
| 0x3AD44          | 0x3AD5C, 0x3AD6E, 0x3AD82, 0x3AE70, 0x3AE80, 0x3AF38, 0x3AF48 |
| 0x3AD84          | reached only via 0x3AD72 fall-through; hook 0x3ABB6, 0x3AF28 |
| 0x3B802          | 0x3A66A, 0x3A9C0, 0x3A9CE, 0x3A9DA, 0x3B7A2, 0x3B7B0, 0x3B7E0, 0x3B8C2, 0x3B8F6, 0x3B8FC |
| 0x54052          | 0x501F4, 0x51260                                            |
| 0x54810          | 0x547EE, 0x54804                                            |
| 0x5607C          | 0x55E92                                                     |
| 0x56114          | 0x5604C, 0x56076 (both inside 0x56056)                      |
| 0x56440 / 0x5648A| 0x55F0E, 0x55FFA                                            |
| 0x5A098          | 0x51054                                                     |

Total additional hook sites: ~28 (10 of which are repeat callers of `0x3B802`).

**Strategy B — switch from call-site interception to bus-level PC090OJ shadow.** Capture every write to `0x00D00000..0x00D007FF` at a single point (memory-region trap or Genesis-side mirror RAM) and reflect into VDP SAT at frame end. This eliminates the call-graph completeness burden, at the cost of giving up Option A's "stage descriptors as semantic objects" property. Genesis-side this would mean either:

- A compiler-emitted store intercept on every translated arcade write whose effective address lies in `0xD00000..0xD007FF`, OR
- A 2 KB shadow buffer in 68k workram that the runtime DMAs into VDP SAT each VBlank, with the arcade code redirected to write into the shadow instead of `0xD00xxx`.

### Recommendation

Option A's 15-site intercept should be retained for the dominant render path (the 0.99 %+ traffic case) since it delivers a clean semantic capture of the dispatcher output. But **either** strategy (A or B) is required to close the INDEPENDENT-writer gap. The pragmatic path is:

- **Short-term**: extend call-site interception (Strategy A) to add the 28 additional hooks listed above. Engineering cost is bounded; each call site converts to the same workram-staging shim already used by April-6.
- **Long-term**: replace the entire call-site intercept set with a 2 KB shadow buffer (Strategy B). Reduces hook proliferation risk and cleanly handles any future writer not yet enumerated.

This ledger satisfies the user prompt's "no thresholding, no exclusions, every PC must appear" requirement: all 80 unique writer PCs are individually classified with cited disassembly evidence and a static reachability argument from the 6 April-6 target functions.

---

## 6. Cross-references

- `docs/design/Andy_pc0900j_sprite_correctness_audit.md` — April 6 baseline; 15 hook sites and 6 target functions.
- `docs/design/Andy_pc090oj_reconciliation_v2.md` — Reconciles April 6 baseline with MAME PC090OJ device (8 MATCH, 1 PARTIAL).
- `docs/design/Andy_pc090oj_full_subsystem_design.md` — Full subsystem design (descriptor format, DMA path).
- `docs/design/Andy_d00778_write_path_analysis.md` — Independent priority-frame writer at 0xD00778 (matches §3.7.2 here).
- `states/traces/fu1_rastan_playtrace_20260424_164401/fu1_summary.txt` — Source trace.
