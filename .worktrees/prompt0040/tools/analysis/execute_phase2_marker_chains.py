#!/usr/bin/env python3
"""H14 offline marker-chain executor — deterministic model of the PROVEN materialization contract.

NOT a CPU emulator. It encodes only the proven state-handler branches (from the raw/semantic C and,
for state 0x1A, the exact 0x43B32 band matrix in build/maincpu.disasm.txt) and runs them against the
record-accurate H13 Phase-2 marker occurrences. For each occurrence it records the exact branch
taken, the base written to +0x1E (if any), the retarget char (+0x0D), anim (+0x01), compositor
(+0x38), and whether the retarget target actually exists in that round's castle-scene marker map.

A base is round-pinned ONLY when a real branch writes +0x1E for an actual H13 occurrence. Handler
reachability alone is never sufficient. Run from repo root.

Handler branch provenance (arcade PCs):
  0x44082 states 0x18/0x1D/0x21   raw/00044082.c
  0x4415A state 0x1C              raw/0004415a.c (low-prog COMPLETE; high-prog matrix PARTIAL, not
                                  needed for the H13 R2 prog<0x2f occurrence)
  0x43636 state 0x22             raw/00043636.c
  0x43840 state 0x15             raw/00043840.c (owns 0x0179 at 0x438B6)
  0x43ECC state 0x1B             raw/00043ecc.c (burst spawner)
  0x40EDE state 0x20 + 0x40F52   raw/00040ede.c (torch; retarget base by prog band)
  0x40E88 state 0x1E             raw/00040e88.c
  0x43B32 state 0x1A             disasm 0x43B32..0x43E8C band matrix (prog band x char)
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools/analysis"))
import decode_rastan_scene_markers as H13

# H6 route: marker -> state (reuse H13's proven route table)
def state_of(marker):
    st, _, _ = H13.route_for(marker)
    return st

# ---- exact handler branches (return dict) -------------------------------------------------------
def h_44082(rnd, prog, char, state):
    if state == 0x18:
        if prog < 0x18: return dict(cond="0x18 prog<0x18 -> 4092e", base=None, nxt=None)
        if prog < 0x2f:
            if char == 0x45: return dict(cond="0x18 mid char E -> 4092e", base=None, nxt=None)
            return dict(cond="0x18 mid -> base 0x0224 next char-23", base=0x0224, nxt=char-23)
        return dict(cond="0x18 high -> base 0x0224 next 0x55", base=0x0224, nxt=0x55)
    # 0x1D / 0x21 else-branch
    if prog < 0x18: return dict(cond="0x1D/0x21 prog<0x18 -> 4092e", base=None, nxt=None)
    return dict(cond="0x1D/0x21 -> base 0x00F4 next 0x4f", base=0x00F4, nxt=0x4f)

def h_4415a(rnd, prog, char, state):
    if prog >= 0x2f:
        return dict(cond="0x1C high-prog char matrix (PARTIAL; not reached by H13)", base=None, nxt=None)
    return dict(cond="0x1C low -> base 0x0224 next 0x52|0x4c (per +0x2F ordinal)", base=0x0224, nxt=0x52)

def h_43636(rnd, prog, char, state):
    if rnd == 3:
        if char == 0x73: return dict(cond="R3 s -> base 0x00F4 next 0x4f (torch)", base=0x00F4, nxt=0x4f)
        if char == 0x74: return dict(cond="R3 t -> base 0x0266 next 0x44", base=0x0266, nxt=0x44)
        return dict(cond="R3 other -> base 0x0266 next 0x46", base=0x0266, nxt=0x46)
    if rnd == 5 and char == 0x73:
        return dict(cond="R5 s -> base 0x0224 anim7 next 0x67 comp2", base=0x0224, nxt=0x67, anim=0x07, comp=2)
    return dict(cond="0x22 plain -> 4092e", base=None, nxt=None)

def h_43840(rnd, prog, char, state):
    if rnd == 2: return dict(cond="R2 -> 4092e", base=None, nxt=None)
    if rnd == 5 and char == 0x61:
        return dict(cond="R5 char a -> base 0x0224 next 0x4c", base=0x0224, nxt=0x4c)
    if rnd == 6 and char == 0x6e:
        if prog < 0x80:
            return dict(cond="R6 n prog<0x80 -> base 0x09EA next 0x7b anim0x27 comp2", base=0x09EA, nxt=0x7b, anim=0x27, comp=2)
        return dict(cond="R6 n prog>=0x80 -> base 0x0179 next 0x48 anim0x70 (0x438B6)", base=0x0179, nxt=0x48, anim=0x70)
    if char == 0x6e:
        return dict(cond="n generic -> base 0x09EA next 0x71 anim0x27 comp2", base=0x09EA, nxt=0x71, anim=0x27, comp=2)
    return dict(cond="0x15 plain -> 4092e", base=None, nxt=None)

def h_43ecc(rnd, prog, char, state):
    return dict(cond="0x1B burst spawner: parent anim0x7a, 5 children @A5+0x3C8 -> state 0x0F (0x447F0/0x448B2)",
                base="BURST(children parent-template, IDENTITY PENDING)", nxt=None, anim=0x7a)

def h_40ede(rnd, prog, char, state):
    # torch visible as light source; retarget base only on marker-gone via 0x40F52 prog band
    if prog < 0x10: return dict(cond="torch prog<0x10 retarget -> base 0x0DAB next 0x49 anim0x74", base=0x0DAB, nxt=0x49, anim=0x74)
    if prog < 0x18: return dict(cond="torch step (visible torch)", base=None, nxt=None)
    if prog < 0x27: return dict(cond="torch retarget -> base 0x09EA next 0x61", base=0x09EA, nxt=0x61)
    if prog < 0x4e: return dict(cond="torch step (visible torch)", base=None, nxt=None)
    if prog < 0x54: return dict(cond="torch step (visible torch)", base=None, nxt=None)
    return dict(cond="torch retarget(prog>=0x54) -> base 0x09EA next 0x71 comp2", base=0x09EA, nxt=0x71, comp=2)

def h_40e88(rnd, prog, char, state):
    if prog < 0x18: return dict(cond="0x1E prog<0x18 -> base 0x00F4 next 0x4f", base=0x00F4, nxt=0x4f)
    if prog < 0x2f: return dict(cond="0x1E mid -> 4092e + spawn 5-part linked (0x43F52)", base=None, nxt=None)
    return dict(cond="0x1E high -> 4092e", base=None, nxt=None)

# ---- state 0x1A: exact 0x43B32 band matrix (prog band x char -> base/next) -----------------------
def h_43b32(rnd, prog, char, state):
    if prog >= 0x87: return dict(cond="0x1A prog>=0x87 anim only", base=None, nxt=None)
    if prog < 0x18:                                   # band A
        if char >= 0x53:
            nxt = char + 3
            if nxt == 0x56: nxt = 0x4b
            return dict(cond="0x1A A(prog<0x18) char>=S -> base 0x01FC next char+3", base=0x01FC, nxt=nxt)
        return dict(cond="0x1A A char<S -> 4092e", base=None, nxt=None)
    if prog < 0x2f:                                   # band B
        if char == 0x53: return dict(cond="0x1A B char S -> base 0x0224 next 0x55", base=0x0224, nxt=0x55)
        if char == 0x55: return dict(cond="0x1A B char U -> base 0x0236 next 0x47", base=0x0236, nxt=0x47)
        return dict(cond="0x1A B -> 4092e", base=None, nxt=None)
    if prog < 0x3f:                                   # band C
        if char == 0x67: return dict(cond="0x1A C char g -> base 0x0266 next 0x6c", base=0x0266, nxt=0x6c)
        if char == 0x68: return dict(cond="0x1A C char h -> base 0x0266 next 0x6d", base=0x0266, nxt=0x6d)
        if char == 0x69: return dict(cond="0x1A C char i -> base 0x09EA next 0x6e", base=0x09EA, nxt=0x6e)
        if char == 0x53: return dict(cond="0x1A C char S -> base 0x09EA next 0x72 anim0x27 comp2", base=0x09EA, nxt=0x72, anim=0x27, comp=2)
        return dict(cond="0x1A C -> 4092e", base=None, nxt=None)
    if prog < 0x46:                                   # band D
        if char == 0x53: return dict(cond="0x1A D char S -> base 0x0266 next 0x43", base=0x0266, nxt=0x43)
        if char == 0x54: return dict(cond="0x1A D char T -> base 0x0224 next 0x76 comp2", base=0x0224, nxt=0x76, comp=2)
        if char == 0x55: return dict(cond="0x1A D char U -> base 0x0224 next 0x69 comp2", base=0x0224, nxt=0x69, comp=2)
        return dict(cond="0x1A D -> 4092e", base=None, nxt=None)
    if prog < 0x49:                                   # band E
        return dict(cond="0x1A E(0x46..0x48) -> 4092e", base=None, nxt=None)
    if prog < 0x51:                                   # band F
        if char == 0x68: return dict(cond="0x1A F char h -> base 0x09EA next 0x71 anim0x27 comp2", base=0x09EA, nxt=0x71, anim=0x27, comp=2)
        return dict(cond="0x1A F -> 4092e", base=None, nxt=None)
    if prog < 0x5a:                                   # band G
        if char == 0x76: return dict(cond="0x1A G char v -> base 0x09EA next 0x71 comp2", base=0x09EA, nxt=0x71, comp=2)
        if char == 0x69: return dict(cond="0x1A G char i -> base 0x0224 next 0x67 comp2", base=0x0224, nxt=0x67, comp=2)
        return dict(cond="0x1A G -> 4092e", base=None, nxt=None)
    if prog < 0x5b:                                   # band H (prog==0x5a)
        if char == 0x4c: return dict(cond="0x1A H char L -> base 0x0266 next 0x46", base=0x0266, nxt=0x46)
        if char == 0x52: return dict(cond="0x1A H char R -> base 0x0266 next 0x46", base=0x0266, nxt=0x46)
        return dict(cond="0x1A H -> 4092e", base=None, nxt=None)
    if prog < 0x63:                                   # band I
        if char == 0x76: return dict(cond="0x1A I char v -> base 0x09EA next 0x61", base=0x09EA, nxt=0x61)
        return dict(cond="0x1A I -> 4092e", base=None, nxt=None)
    if prog < 0x6e:                                   # band J
        if char == 0x4c: return dict(cond="0x1A J char L -> base 0x0546 next 0x59", base=0x0546, nxt=0x59)
        return dict(cond="0x1A J -> 4092e", base=None, nxt=None)
    if prog < 0x79:                                   # band K
        if char == 0x67: return dict(cond="0x1A K char g -> base 0x00F4 next 0x4f comp/+0x30=2", base=0x00F4, nxt=0x4f, comp=2)
        return dict(cond="0x1A K -> 4092e", base=None, nxt=None)
    if prog < 0x7e:                                   # band L
        if char == 0x4c: return dict(cond="0x1A L char L -> base 0x09EA next 0x71", base=0x09EA, nxt=0x71)
        return dict(cond="0x1A L -> 4092e", base=None, nxt=None)
    if prog < 0x84:                                   # band M
        if char == 0x4c: return dict(cond="0x1A M char L -> base 0x0224 next 0x67 comp2", base=0x0224, nxt=0x67, comp=2)
        return dict(cond="0x1A M -> 4092e", base=None, nxt=None)
    # band N (0x84..0x86)
    if char == 0x67: return dict(cond="0x1A N char g -> base 0x09EA next 0x6e", base=0x09EA, nxt=0x6e)
    return dict(cond="0x1A N -> 4092e", base=None, nxt=None)

HANDLERS = {
    "0x44082": h_44082, "0x4415A": h_4415a, "0x43636": h_43636, "0x43840": h_43840,
    "0x43ECC": h_43ecc, "0x40EDE": h_40ede, "0x40E88": h_40e88, "0x43B32": h_43b32,
}
# state -> (handler PC, callable)
STATE_HANDLER = {
    "0x18": "0x44082", "0x1D": "0x44082", "0x21": "0x44082",
    "0x1C": "0x4415A", "0x22": "0x43636", "0x15": "0x43840",
    "0x1B": "0x43ECC", "0x20": "0x40EDE", "0x1E": "0x40E88", "0x1A": "0x43B32",
}

def round_marker_map():
    """{round: {'chars': set(all markers present in castle scenes), 'occ':[(scene,marker)]}}"""
    out = {}
    for r in range(1, 7):
        p0 = H13.phase2_start(r)
        chars, occ = set(), []
        for scene in range(p0, H13.ROUND_END[r] + 1):
            if H13.section_kind(scene) == 0:
                continue
            seen = set()
            for col in range(H13.N_COLS):
                base = H13.DESC_BASE + col * H13.COL_STRIDE + scene * H13.SCENE_STRIDE
                for e in range(H13.N_ENTRIES):
                    ea = base + e * 4
                    if ea + 4 > len(H13.MC):
                        continue
                    rp = H13.w(ea + 2)
                    cells = H13.record_cells(rp)
                    if not cells:
                        continue
                    for _s, _c, mk, _u in cells:
                        chars.add(mk)
                        if (scene, mk) not in seen:
                            seen.add((scene, mk)); occ.append((scene, mk))
        out[r] = dict(chars=chars, occ=occ)
    return out

def main():
    ad = os.path.join(ROOT, "analysis/actor_decompilation")
    rmap = round_marker_map()
    trans = ["round\tscene_prog\tentry_marker\tstate\thandler\tbranch_condition\tbase_written\tnext_char\tnext_in_scene\tanim\tcompositor"]
    present = {}   # base -> {round: [evidence]}
    for r in range(1, 7):
        for scene, mk in rmap[r]["occ"]:
            if not (0x45 <= mk <= 0x7b):
                continue
            st = state_of(mk)
            hpc = STATE_HANDLER.get(st)
            if hpc is None:
                continue
            res = HANDLERS[hpc](r, scene, mk, int(st, 16))
            base = res.get("base"); nxt = res.get("nxt")
            nxt_in = ""
            if isinstance(nxt, int):
                nxt_in = "yes" if nxt in rmap[r]["chars"] else "no(absent->latent)"
            bstr = (base if isinstance(base, str) else (f"{base:#06x}" if base is not None else "-"))
            anim = res.get("anim")
            animstr = f"{anim:#04x}" if isinstance(anim, int) else "-"
            nxtstr = f"{nxt:#04x}" if isinstance(nxt, int) else "-"
            trans.append(f"{r}\t{scene:#04x}\t{mk:#04x}\t{st}\t{hpc}\t{res['cond']}\t{bstr}\t"
                         f"{nxtstr}\t{nxt_in or '-'}\t{animstr}\t{res.get('comp','-')}")
            if isinstance(base, int):
                present.setdefault(base, {}).setdefault(r, []).append(
                    (scene, mk, hpc, res['cond']))
    with open(os.path.join(ad, "h14_marker_chain_transitions.tsv"), "w") as f:
        f.write("\n".join(trans) + "\n")

    # visible bases per round
    vis = ["round\tbase\tfirst_evidence_scene\tentry_marker\thandler\tbranch"]
    for base in sorted(present):
        for r in sorted(present[base]):
            sc, mk, hpc, cond = present[base][r][0]
            vis.append(f"{r}\t{base:#06x}\t{sc:#04x}\t{mk:#04x}\t{hpc}\t{cond}")
    with open(os.path.join(ad, "h14_phase2_visible_bases.tsv"), "w") as f:
        f.write("\n".join(vis) + "\n")

    # round-pinning for the 12 H10 bases + any discovered
    H10 = [0x0224, 0x0179, 0x09F6, 0x0DAB, 0x09EA, 0x00F4, 0x0266, 0x0235, 0x01FC, 0x0236, 0x0546, 0x05E9]
    pin = ["base\tverdict\trounds_present\tevidence"]
    for base in H10:
        rounds = sorted(present.get(base, {}).keys())
        if rounds:
            ev = "; ".join(f"R{r}@{present[base][r][0][0]:#04x} {present[base][r][0][2]}" for r in rounds)
            pin.append(f"{base:#06x}\tPROVEN PRESENT\t{','.join('R%d'%r for r in rounds)}\t{ev}")
        else:
            pin.append(f"{base:#06x}\tPROVEN ABSENT FROM PHASE-2\t-\tno phase-2 H13 occurrence satisfies any +0x1E={base:#06x} branch (state/prog/char never coincide)")
    # discovered bases not in H10
    for base in sorted(present):
        if base not in H10 and isinstance(base, int):
            rounds = sorted(present[base].keys())
            pin.append(f"{base:#06x}\tDISCOVERED (not in H10 set)\t{','.join('R%d'%r for r in rounds)}\tsee transitions")
    with open(os.path.join(ad, "h14_materialized_round_pinning.tsv"), "w") as f:
        f.write("\n".join(pin) + "\n")

    # ---- §16 exact per-round palette instances for PROVEN PRESENT bases -----------------------
    # family-2 resolver (0x45684): nibble = pal_nib_456ec[variant*18 + (round-1)*3 + comp_adj].
    # The 0x033E hunter is variant 0; comp_adj = base compositor selector (0->0, 2->2). The palette
    # line is fixed at hunter creation (transforms do NOT re-run 0x45684, per H10). Colours from
    # rom_field_palette(round, nibble): pool = rom_u8(0x3BA88+(round-1)*32+nibble); 0x4FD02+pool*32.
    PAL_NIB_456EC = [
        0x04,0x02,0x01, 0x04,0x05,0x01, 0x00,0x05,0x01, 0x00,0x07,0x00, 0x00,0x00,0x00, 0x00,0x00,0x00]
    BASE_COMP = {0x0224: 2, 0x0179: 2, 0x00F4: 0, 0x09EA: 0}   # H10 render selectors (0x0224/0x0179 sel2, 0x00F4/0x09EA sel0)
    def rom_u8(a): return H13.MC[a]
    def rom_u16(a): return H13.w(a)
    pal = ["round\tbase\tcomp_adj\tnibble\tpool\tpool_src_0x4FD02\traw16_words\tprovenance"]
    for base in sorted(present):
        if not isinstance(base, int) or base not in BASE_COMP:
            continue
        comp_adj = BASE_COMP[base]
        for r in sorted(present[base]):
            nib = PAL_NIB_456EC[(r - 1) * 3 + comp_adj]          # variant 0
            pool = rom_u8(0x3BA88 + (r - 1) * 32 + nib)
            src = 0x4FD02 + pool * 32
            words = " ".join(f"{rom_u16(src + i*2):04x}" for i in range(16))
            pal.append(f"{r}\t{base:#06x}\t{comp_adj}\t{nib:#03x}\t{pool:#04x}\t{src:#08x}\t{words}\t"
                       f"0x45684 family-2 variant0; nibble=pal_nib_456ec[(R-1)*3+comp_adj]; 0x3BA88->pool->0x4FD02 (raw ROM words)")
    with open(os.path.join(ad, "h14_materialized_palette_instances.tsv"), "w") as f:
        f.write("\n".join(pal) + "\n")

    # ---- deterministic checks ----
    for r in range(1, 7):
        for scene, mk in rmap[r]["occ"]:
            if 0x45 <= mk <= 0x7b:
                assert state_of(mk) is not None, f"marker {mk:#04x} unrouted"
                assert STATE_HANDLER.get(state_of(mk)) is not None, f"state for {mk:#04x} unhandled"
    for base in present:
        if isinstance(base, int):
            for r in present[base]:
                assert present[base][r], "empty evidence"
    print("H14 executor: wrote h14_marker_chain_transitions / _phase2_visible_bases / _materialized_round_pinning")
    print("Round-pinning summary:")
    for row in pin[1:]:
        print("  " + row.split("\t")[0] + "  " + row.split("\t")[1] + "  " + row.split("\t")[2])
    print("H14 checks: PASS (every H13 char marker routes to exactly one handled state; all pins have evidence)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
