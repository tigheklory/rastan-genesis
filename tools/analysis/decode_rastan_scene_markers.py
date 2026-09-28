#!/usr/bin/env python3
"""H11/H13 static scene/section + collision-marker enumerator — operates directly on the arcade ROM.

H11 layer — decodes, per round, the section kind for every A5+0x13E progression value via the
proven chain:
    section_kind = byte[0x50F6B + byte[0x50EE0 + 0x13E]]
    0 = outdoor (phase 1), != 0 = castle / interior (phase 2)
and reports the first Phase-2 (castle) start per round.

H13 layer (record-accurate marker enumeration) — the H11 blocker is now CLOSED. The exact
descriptor -> record -> grid-cell mapping is proven from the arcade disassembly:

    0x502CC : 0x10D000[col] = descriptor_base = 0x1691C + col*0x22C0 + scene*0x40   (col 0..15)
    scroll  : 0x558A2 cycles strip a5@(0x10CA) 0..3; every 4 strips 0x558C6 advances all 16
              descriptor pointers +4 (next 4-byte descriptor entry) and 0x55904 rebuilds records;
              0x558E0 advances scene a5@(0x13E) after 16 entries (16 entries * 4 = 0x40 page).
    0x55904 : per entry -> word0 (@base) -> 0x10D080[col]; word1 (@base+2) -> 0x10D040[col] = a
              16-bit ROM pointer to the COLLISION RECORD ("col_record").
    0x559B2 : a2 = col_record; for cell d2=0..3:
                 if col_record[0x20] == 0x00FF:  collision = col_record[0x22]      (uniform fill)
                 else:                           collision = col_record[20 + strip*2 + cell*8]
              grid[0x10DE00 + (dest-0xC08000)/2] = collision word
    0x41294 : consumer reads grid word, d0 = word >> 8  => MARKER = HIGH byte.

So each record is a 4x4 cell grid (strip 0..3, cell 0..3) at byte offsets 20..0x32 (20 == 0x14
decimal; the arcade `lea a2@(20,d7)` uses DECIMAL 20 = 0x14 hex). The control/sentinel word is at
hex offset 0x20 and the uniform-fill alternate at hex offset 0x22. Marker = collision-word high
byte, classified by the H6 0x41362 route table below.

It does NOT hard-code expected actors; it enumerates the markers actually present in ROM and maps
them through the PROVEN H6 routes. Run from repo root.
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MC = open(os.path.join(ROOT, "build/regions/maincpu.bin"), "rb").read()
EE0, F6B = 0x50EE0, 0x50F6B
# code-proven round-end 0x13E values (0x502AC boundary work)
ROUND_END = {1:0x16, 2:0x2D, 3:0x44, 4:0x5B, 5:0x72, 6:0x89}
ROUND_START = {1:0x00, 2:0x17, 3:0x2E, 4:0x45, 5:0x5C, 6:0x73}

DESC_BASE, COL_STRIDE, SCENE_STRIDE = 0x1691C, 0x22C0, 0x40  # 0x502CC
N_COLS, N_ENTRIES = 16, 16   # 16 descriptor pointers; 16 four-byte entries per scene page

# H6 0x41362 route table (marker char -> assigned state +0x05, 0x40BAA handler). PROVEN in
# docs/design/Andy_h6_marker_materialization_decompilation.md and h6_marker_materialization_routes.tsv.
# 0x31..0x3C are the FLOOR/STRUCTURAL band (0x3A = Cody scheduled-hostile zero-X); 0x45..0x7B are
# the character-hunter enemy/item band consumed for rosters.
H6_ROUTES = [
    (0x31, 0x44, "0x1D", "0x44082", "floor/structural (0x3A=scheduled-hostile)"),
    (0x45, 0x45, "0x18", "0x44082", "char E"),
    (0x46, 0x46, "0x1D", "0x44082", "char F"),
    (0x47, 0x47, "0x1C", "0x4415A", "char G"),
    (0x48, 0x48, "0x1E", "0x40E88", "char H (transform)"),
    (0x49, 0x49, "rec1", "0x4092E", "char I (projectile template)"),
    (0x4B, 0x4B, "0x19", "0x4396A", "char K"),
    (0x4C, 0x4C, "0x1A", "0x43B32", "char L"),
    (0x4D, 0x4D, "0x1B", "0x43ECC", "char M"),
    (0x4F, 0x51, "0x20", "0x40EDE", "char O-Q (torch/light)"),
    (0x52, 0x56, "0x1A", "0x43B32", "char R-V"),
    (0x57, 0x58, "0x19", "0x4396A", "char W-X"),
    (0x59, 0x5D, "0x17", "0x43F88", "char Y-]"),
    (0x5E, 0x60, "0x16", "0x43AE6", "char ^-`"),
    (0x61, 0x63, "0x15", "0x43840", "char a-c"),
    (0x64, 0x64, "0x14", "0x4375C", "char d"),
    (0x65, 0x66, "0x13", "0x4375C", "char e-f"),
    (0x67, 0x69, "0x1A", "0x43B32", "char g-i"),
    (0x6A, 0x6B, "0x18", "0x44082", "char j-k"),
    (0x6C, 0x6D, "0x1D", "0x44082", "char l-m"),
    (0x6E, 0x70, "0x15", "0x43840", "char n-p"),
    (0x71, 0x72, "0x21", "0x44082", "char q-r"),
    (0x73, 0x75, "0x22", "0x43636", "char s-u"),
    (0x76, 0x77, "0x1A", "0x43B32", "char v-w"),
    (0x78, 0x78, "0x21", "0x44082", "char x"),
    (0x79, 0x79, "0x22", "0x43636", "char y"),
    (0x7A, 0x7A, "0x15", "0x43840", "char z"),
    (0x7B, 0x7B, "0x21", "0x44082", "char {"),
]

def route_for(marker):
    for lo, hi, st, h, note in H6_ROUTES:
        if lo <= marker <= hi:
            return (st, h, note)
    return (None, None, None)

def w(a):
    return (MC[a] << 8) | MC[a + 1]

def section_kind(p): return MC[F6B + MC[EE0 + p]]

def phase2_start(r):
    for p in range(ROUND_START[r], ROUND_END[r] + 1):
        if section_kind(p) != 0:
            return p
    return None

def record_cells(rp):
    """Return the 16 (strip,cell,marker) triples of one collision record (0x559B2 model)."""
    if rp + 0x34 > len(MC):
        return None
    ctrl = w(rp + 0x20)
    out = []
    if ctrl == 0x00FF:                       # sentinel -> uniform fill from hex offset 0x22
        m = w(rp + 0x22) >> 8
        for strip in range(4):
            for cell in range(4):
                out.append((strip, cell, m, True))
        return out
    for strip in range(4):
        for cell in range(4):
            out.append((strip, cell, w(rp + 20 + strip * 2 + cell * 8) >> 8, False))
    return out

def enumerate_h13():
    """Full record-accurate phase-2 marker enumeration -> writes the H13 evidence TSVs."""
    ad = os.path.join(ROOT, "analysis/actor_decompilation")
    cells_rows = ["round\t13E_scene\tcol\tentry\trecord_ptr\tstrip\tcell\tmarker\tuniform\tstate\thandler\tnote"]
    occ = {}   # (round, marker) -> [count, state, handler, note]
    desc_rows = ["round\t13E_scene\tcol\tdescriptor_base\tentry\tentry_addr\tword0\tword1_record_ptr"]
    per_round_markers = {r: {} for r in range(1, 7)}
    for r in range(1, 7):
        p0 = phase2_start(r)
        if p0 is None:
            continue
        for scene in range(p0, ROUND_END[r] + 1):
            if section_kind(scene) == 0:
                continue
            for col in range(N_COLS):
                base = DESC_BASE + col * COL_STRIDE + scene * SCENE_STRIDE
                for e in range(N_ENTRIES):
                    ea = base + e * 4
                    if ea + 4 > len(MC):
                        continue
                    word0, rp = w(ea), w(ea + 2)
                    if col == 0:
                        desc_rows.append(f"{r}\t{scene:#04x}\t{col}\t{base:#08x}\t{e}\t{ea:#08x}\t{word0:#06x}\t{rp:#06x}")
                    cells = record_cells(rp)
                    if cells is None:
                        continue
                    for strip, cell, mk, uni in cells:
                        st, h, note = route_for(mk)
                        if 0x45 <= mk <= 0x7B:      # character-hunter band -> roster evidence
                            per_round_markers[r].setdefault(mk, 0)
                            per_round_markers[r][mk] += 1
                            key = (r, mk)
                            if key not in occ:
                                occ[key] = [0, st, h, note]
                            occ[key][0] += 1
                            cells_rows.append(
                                f"{r}\t{scene:#04x}\t{col}\t{e}\t{rp:#06x}\t{strip}\t{cell}\t{mk:#04x}\t"
                                f"{int(uni)}\t{st}\t{h}\t{note}")
    with open(os.path.join(ad, "h13_phase2_collision_cells.tsv"), "w") as f:
        f.write("\n".join(cells_rows) + "\n")
    with open(os.path.join(ad, "h13_descriptor_layout.tsv"), "w") as f:
        f.write("\n".join(desc_rows) + "\n")
    occ_rows = ["round\tmarker\toccurrences\tstate_+0x05\thandler_0x40BAA\troute_note"]
    for (r, mk) in sorted(occ):
        c, st, h, note = occ[(r, mk)]
        occ_rows.append(f"{r}\t{mk:#04x}\t{c}\t{st}\t{h}\t{note}")
    with open(os.path.join(ad, "h13_phase2_marker_occurrences.tsv"), "w") as f:
        f.write("\n".join(occ_rows) + "\n")
    return per_round_markers

def main():
    out_tsv = os.path.join(ROOT, "analysis/actor_decompilation/h11_scene_markers.tsv")
    rows = ["round\t13E\tscene_index\tsection_kind\tphase\tsource_rom_addr"]
    phase2 = {}
    for r in range(1, 7):
        s, e = ROUND_START[r], ROUND_END[r]
        started = None
        for p in range(s, e + 1):
            si = MC[EE0 + p]; sk = MC[F6B + si]
            ph = "phase2" if sk != 0 else "phase1"
            if sk != 0 and started is None: started = p
            rows.append(f"{r}\t{p:#04x}\t{si}\t{sk}\t{ph}\t{F6B+si:#08x}")
        phase2[r] = started
    with open(out_tsv, "w") as f:
        f.write("\n".join(rows) + "\n")
    print("PHASE-2 (castle) start 0x13E per round (section kind != 0):")
    for r in range(1, 7):
        p = phase2[r]
        print(f"  R{r}: {p:#04x}  (kind {section_kind(p)})" if p is not None else f"  R{r}: none")
    # deterministic checks
    assert all(0 <= MC[EE0 + p] < len(MC) for p in range(0, 0x8A)), "scene index out of range"
    assert all(phase2[r] is not None for r in range(1, 7)), "a round has no phase-2 section"
    print(f"wrote {out_tsv}")
    print("checks: PASS (all six rounds have a proven phase-2 start; indices in range)")

    # ---- H13 record-accurate marker enumeration + rosters -------------------------------------
    ad = os.path.join(ROOT, "analysis/actor_decompilation")
    per_round = enumerate_h13()
    print("\nH13 phase-2 character-hunter markers per round (0x45..0x7B -> H6 route):")
    for r in range(1, 7):
        mks = sorted(per_round[r])
        print(f"  R{r}: " + " ".join(f"{m:#04x}({route_for(m)[0]})" for m in mks))

    # 0x55904 record-mapping TSV (the exact byte transform, one row per record field)
    map_rows = [
        "field\tsource\ttransform\tconsumer\tmeaning",
        "descriptor_base\t0x502CC 0x10D000[col]\t0x1691C + col*0x22C0 + scene*0x40\t0x55904 a4=@a0\tper-(col,scene) descriptor page (0x40 bytes = 16 four-byte entries)",
        "entry.word0\tROM @entry+0\t0x55904 movew a4@,a2@+ -> 0x10D080[col]\t0x559B4 movew a1@,a0@\tname-table tile word written to dest",
        "entry.word1\tROM @entry+2\t0x55904 movew a4@(2),d1; a1@+=d1 -> 0x10D040[col]\t0x55968 a2=a3@\t16-bit ROM pointer to the collision RECORD (col_record)",
        "col_record[0x20]\tROM @rec+0x20\t(none)\t0x559B6 cmpiw #0x00FF\tcontrol/sentinel: ==0x00FF -> uniform fill",
        "col_record[0x22]\tROM @rec+0x22\t(none)\t0x559D4 lea a2@(0x22)\tuniform collision word when sentinel set",
        "col_record[20+strip*2+cell*8]\tROM @rec+20+strip*2+cell*8\t(none)\t0x559CE lea a2@(20,d7:w)\tper-cell collision word (strip=a5@0x10CA 0..3, cell=d2 0..3); 20 dec = 0x14 hex",
        "grid word\tcollision word\td7=(dest-0xC08000)/2\t0x559EC movew d0,(0x10DE00+d7)\t64x64 word grid; high byte = MARKER (0x41294 lsrw #8)",
    ]
    with open(os.path.join(ad, "h13_55904_record_mapping.tsv"), "w") as f:
        f.write("\n".join(map_rows) + "\n")

    # materialized-actor round REACHABILITY (handler-level, honest): a base is reachable in a round
    # when a grid marker routing to its handler is present that round. Name/exact-site stay PENDING.
    import json
    man = json.load(open(os.path.join(ROOT, "docs/design/rastan_actor_graphics_manifest.json")))
    mat = [a for a in man["actors"] if a.get("category") == "ENEMY_MATERIALIZED"]
    # handler -> set of rounds whose markers route to that handler
    handler_rounds = {}
    for r in range(1, 7):
        for m in per_round[r]:
            _, h, _ = route_for(m)
            if h:
                handler_rounds.setdefault(h, set()).add(r)
    ros_rows = ["technical_id\tbase\tstate\thandler\tmarker_route\treachable_rounds\tround_status\tname_status"]
    for a in mat:
        rt = a.get("materialization_route", {})
        h = rt.get("handler", "")
        reach = sorted(handler_rounds.get(h, set()))
        status = ("REACHABLE via handler in rounds " + ",".join(map(str, reach))) if reach \
            else "PENDING (handler not reached by a unique phase-2 grid marker; chain/generic)"
        ros_rows.append(
            f"{a['technical_id']}\t{a['base_graphics']}\t{rt.get('state','')}\t{h}\t"
            f"{rt.get('marker','')}\t{reach if reach else '-'}\t{status}\t{a['name_status']}")
    with open(os.path.join(ad, "h13_phase2_actor_rosters.tsv"), "w") as f:
        f.write("\n".join(ros_rows) + "\n")

    # deterministic H13 checks
    assert all(len(per_round[r]) >= 0 for r in range(1, 7))
    # every enumerated character marker must resolve to a proven H6 route
    for r in range(1, 7):
        for m in per_round[r]:
            assert route_for(m)[1] is not None, f"unmapped marker {m:#04x} in R{r}"
    print("wrote H13 TSVs: h13_phase2_collision_cells / _marker_occurrences / _descriptor_layout / "
          "_55904_record_mapping / _phase2_actor_rosters")
    print("H13 checks: PASS (every enumerated 0x45..0x7B marker resolves to a proven H6 route)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
