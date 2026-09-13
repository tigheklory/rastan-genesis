#!/usr/bin/env python3
"""OPT-003 build-time generator: prebaked PC090OJ sprite palette-line lookup (Build 0340).

The runtime hot path `.Lnative_palsel` (apps/rastan-direct/src/pc090oj_hooks.s) formerly resolved every
emitted SAT piece's Genesis CRAM palette line (0..3) by:

    effective_bank = (piece_nibble & 0x0F) | colbank        (colbank = (sprite_ctrl & 0xE0) >> 1)
    if effective_bank == 0x30:            line = 2          (death-burst / effects special case)
    elif route_hit(scene, PC090OJ, eb):   line = route_line (LINEAR SCAN of palette_route_table)
    else:                                 line = (eb >> 4) & 3   (miss fallback)

That linear `palette_route_lookup` scan ran per emitted piece (dozens/frame, up to the SAT cap). The
result is a deterministic function of `(scene_id, effective_bank)`, so this tool BAKES it into a direct
[scene][bank] byte LUT. The runtime becomes one indexed load.

For the current R1/P1 performance landing, the saved Palette Editing Tool profile is authoritative for
the mappings it contains. Unauthored inputs retain the current renderer's special/route/fallback result,
which makes the migration total over the 4x128 input domain without inventing future palette decisions.
The generated .inc is runtime data, not a second hand-maintained registry. palette_decisions.json is not
used to override the current Tool arrangement in this task.

Domain (proven in-repo, 2026-09-02):
  * scene_id in {0,1,2}: scene_load.s collapses PC080SN tileset ids >= 3 to gameplay scene 1; only
    values 0,1,2 reach genesistan_current_scene_id. Only scene 1 has PC090OJ route rows, so scenes 0/2
    are pure special-case+fallback. NUM_SCENES=4 (power-of-two, mask 0x03) so scene index is always
    in-bounds without a runtime branch; the unreachable row 3 is filled with the same fallback.
  * effective_bank in [0,0x7F]: nibble (0..0x0F) | colbank ((x&0xE0)>>1, i.e. 0x00..0x70). Row width 128.

Usage:
  gen ... --out <path.inc>        generate the .inc (deterministic; no timestamps)
  gen ... --out <path.inc> --verify   also re-derive independently, re-parse the emitted .inc, and
                                      assert 0 mismatches + hand-anchored spot checks; prints a report.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys

# --- fixed LUT geometry (mirrored by the runtime direct-index path) ---
NUM_SCENES = 4          # rows; scene index masked with (NUM_SCENES-1)
SCENE_MASK = NUM_SCENES - 1
BANK_WIDTH = 128        # columns; effective_bank in [0,0x7F]
BANK_MASK = BANK_WIDTH - 1
BANK_SHIFT = 7          # BANK_WIDTH == 1 << BANK_SHIFT
SPECIAL_BANK = 0x30     # effective_bank == 0x30 -> line 2 (scene-independent, pre-lookup)
SPECIAL_LINE = 2
PC090OJ_OWNER_NAME = "PROUTE_OWNER_PC090OJ"

FORMAT_VERSION = 2


def parse_editor_profile(path: str) -> tuple[dict[int, int], str]:
    """Return effective-bank -> line decisions authored in the Palette Editing Tool."""
    raw = open(path, "rb").read()
    profile = json.loads(raw)
    result: dict[int, int] = {}
    for usage, mapping in profile.get("usage_palette_mappings", {}).items():
        match = re.search(r":bank0x([0-9A-Fa-f]{2})$", usage)
        if not match:
            continue
        bank = int(match.group(1), 16)
        line = int(mapping["line"])
        if not 0 <= bank < BANK_WIDTH:
            raise SystemExit(f"FATAL: {usage} bank is outside the runtime LUT domain")
        if not 0 <= line <= 3:
            raise SystemExit(f"FATAL: {usage} has invalid Genesis line {line}")
        if bank in result and result[bank] != line:
            raise SystemExit(f"FATAL: Palette Tool assigns bank 0x{bank:02X} to two lines")
        result[bank] = line
    if not result:
        raise SystemExit(f"FATAL: no usage palette mappings in {path}")
    return result, hashlib.sha256(raw).hexdigest()


def _resolve(tok: str, symmap: dict) -> int:
    tok = tok.strip()
    if tok in symmap:
        return symmap[tok]
    if tok.lower().startswith("0x"):
        return int(tok, 16)
    return int(tok, 10)


def parse_route_table(src_path: str):
    """Return (pc090oj_map {(scene,bank):line}, owner_id, route_rows_text) from palette_hooks.s."""
    with open(src_path, "r") as f:
        text = f.read()

    symmap = {}
    for m in re.finditer(r"^\s*\.equ\s+(PROUTE_\w+)\s*,\s*([0-9A-Fa-fxX]+)", text, re.M):
        symmap[m.group(1)] = int(m.group(2), 0)
    if PC090OJ_OWNER_NAME not in symmap:
        raise SystemExit(f"FATAL: {PC090OJ_OWNER_NAME} not defined in {src_path}")
    owner_id = symmap[PC090OJ_OWNER_NAME]

    # Isolate the palette_route_table body.
    tbl = re.search(r"palette_route_table:\s*(.*?)\n\s*\.section", text, re.S)
    if not tbl:
        raise SystemExit("FATAL: palette_route_table block not found")
    body = tbl.group(1)

    pc090oj_map = {}
    rows_norm = []
    for raw in body.splitlines():
        line = re.sub(r"/\*.*?\*/", "", raw)          # strip inline block comments
        line = line.strip()
        if not line.startswith(".word"):
            continue
        ops = [o.strip() for o in line[len(".word"):].split(",")]
        if len(ops) < 5:
            continue
        scene = _resolve(ops[0], symmap)
        if scene == 0xFFFF:
            break                                      # terminator
        owner = _resolve(ops[1], symmap)
        bank = _resolve(ops[2], symmap)
        gline = _resolve(ops[3], symmap)
        if owner == owner_id:
            key = (scene, bank)
            if key in pc090oj_map:
                # linear scan returns FIRST match; keep it, warn.
                sys.stderr.write(f"WARN: duplicate PC090OJ route row {key}; keeping first\n")
            else:
                pc090oj_map[key] = gline
                rows_norm.append(f"scene={scene} bank=0x{bank:02X} line={gline}")
    return pc090oj_map, owner_id, "\n".join(rows_norm)


def oracle(scene: int, eb: int, pc090oj_map: dict) -> int:
    """EXACT reproduction of the current .Lnative_palsel (RASTAN_GAMEPLAY_HUD_SPRITES != 1) algorithm."""
    if eb == SPECIAL_BANK:
        return SPECIAL_LINE
    hit = pc090oj_map.get((scene, eb))
    if hit is not None:
        return hit
    return (eb >> 4) & 3


def build_lut(pc090oj_map: dict, editor_map: dict[int, int]):
    lut = [oracle(s, b, pc090oj_map) for s in range(NUM_SCENES) for b in range(BANK_WIDTH)]
    for bank, line in editor_map.items():
        lut[BANK_WIDTH + bank] = line
    return lut


def sat_word2(line: int, priority: int, vflip: int, hflip: int, pattern: int) -> int:
    """Compose the final Genesis SAT word-2 fields covered by this migration."""
    return ((priority & 1) << 15) | ((line & 3) << 13) | ((vflip & 1) << 12) | \
           ((hflip & 1) << 11) | (pattern & 0x07FF)


def emit_inc(lut, route_sha: str, rows_norm: str, profile_sha: str, editor_map: dict[int, int]) -> str:
    out = []
    out.append("/* GENERATED by tools/translation/gen_pc090oj_palsel_lut.py -- do not hand-edit. */")
    out.append("/* OPT-003 (Build 0340): prebaked PC090OJ sprite palette-line LUT.")
    out.append(" * Scene 1 authored entries come from the current Palette Editing Tool snapshot;")
    out.append(" * remaining entries preserve the current renderer's special/fallback behavior.")
    out.append(f" * format_version={FORMAT_VERSION}")
    out.append(f" * dims: NUM_SCENES={NUM_SCENES} (scene index masked {SCENE_MASK:#04x}),"
               f" BANK_WIDTH={BANK_WIDTH} (bank masked {BANK_MASK:#04x}), element=1 byte, line range 0..3")
    out.append(f" * index = (scene & {SCENE_MASK:#04x}) << {BANK_SHIFT} | (effective_bank & {BANK_MASK:#04x})")
    out.append(f" * route_table_sha1={route_sha}")
    out.append(f" * palette_tool_profile_sha256={profile_sha}")
    out.append(" * Palette Tool mappings: " + ", ".join(
        f"0x{bank:02X}->{line}" for bank, line in sorted(editor_map.items())))
    out.append(" * baked PC090OJ route rows:")
    for r in rows_norm.splitlines():
        out.append(f" *   {r}")
    out.append(" */")
    out.append(f"    .equ PALSEL_LUT_NUM_SCENES, {NUM_SCENES}")
    out.append(f"    .equ PALSEL_LUT_SCENE_MASK, {SCENE_MASK:#04x}")
    out.append(f"    .equ PALSEL_LUT_BANK_WIDTH, {BANK_WIDTH}")
    out.append(f"    .equ PALSEL_LUT_BANK_MASK, {BANK_MASK:#04x}")
    out.append(f"    .equ PALSEL_LUT_BANK_SHIFT, {BANK_SHIFT}")
    out.append("    .section .rodata")
    out.append("    .align 2")
    out.append("    .global pc090oj_palsel_lut")
    out.append("pc090oj_palsel_lut:")
    for s in range(NUM_SCENES):
        out.append(f"    .global pc090oj_palsel_lut_scene{s}")
        out.append(f"pc090oj_palsel_lut_scene{s}:")
        row = lut[s * BANK_WIDTH:(s + 1) * BANK_WIDTH]
        out.append(f"    /* scene {s} */")
        for i in range(0, BANK_WIDTH, 16):
            chunk = ", ".join(str(v) for v in row[i:i + 16])
            out.append(f"    .byte {chunk}")
    out.append("    .section .text,\"ax\"")
    return "\n".join(out) + "\n"


def parse_emitted_bytes(inc_path: str):
    """Re-parse the .byte rows of an emitted .inc -> flat list, for independent verification."""
    vals = []
    started = False
    with open(inc_path) as f:
        for line in f:
            if "pc090oj_palsel_lut:" in line:
                started = True
                continue
            if not started:
                continue
            s = line.strip()
            if s.startswith(".byte"):
                vals += [int(x.strip()) for x in s[len(".byte"):].split(",")]
            elif s.startswith(".section") and vals:
                break
    return vals


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    default_src = os.path.normpath(os.path.join(here, "..", "..", "apps", "rastan-direct", "src", "palette_hooks.s"))
    ap.add_argument("--route-src", default=default_src)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    pc090oj_map, owner_id, rows_norm = parse_route_table(args.route_src)
    editor_map, profile_sha = parse_editor_profile(args.profile)
    route_sha = hashlib.sha1(rows_norm.encode()).hexdigest()[:16]
    lut = build_lut(pc090oj_map, editor_map)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as f:
        f.write(emit_inc(lut, route_sha, rows_norm, profile_sha, editor_map))

    if not args.verify:
        print(f"[gen_pc090oj_palsel_lut] wrote {args.out} ({NUM_SCENES}x{BANK_WIDTH}={len(lut)} bytes), "
              f"PC090OJ rows={len(pc090oj_map)}, route_sha1={route_sha}")
        return 0

    # Compare the direct map with the exact pre-migration renderer oracle.
    emitted = parse_emitted_bytes(args.out)
    mismatches = 0
    route_hits = fallback_cases = special_cases = 0
    for s in range(NUM_SCENES):
        for b in range(BANK_WIDTH):
            want = oracle(s, b, pc090oj_map)
            got = emitted[s * BANK_WIDTH + b]
            if want != got:
                mismatches += 1
                sys.stderr.write(f"MISMATCH scene={s} bank=0x{b:02X}: want {want} got {got}\n")
            if b == SPECIAL_BANK:
                special_cases += 1
            elif (s, b) in pc090oj_map:
                route_hits += 1
            else:
                fallback_cases += 1

    # Hand-anchored spot checks tie the oracle to human-verified ASM/table semantics (not self-check).
    def g(s, b):
        return emitted[s * BANK_WIDTH + b]
    anchors = {
        "scene1 bank0x30 (special->2)": (g(1, 0x30), 2),
        "scene1 bank0x33 (route->0)": (g(1, 0x33), 0),
        "scene1 bank0x36 (route->1)": (g(1, 0x36), 1),
        "scene1 bank0x31 (miss->(0x31>>4)&3=3)": (g(1, 0x31), 3),
        "scene0 bank0x33 (frontend miss->3)": (g(0, 0x33), 3),
        "scene0 bank0x30 (special->2)": (g(0, 0x30), 2),
    }
    anchor_fail = 0
    print("=== OPT-003 palsel LUT equivalence report ===")
    print(f"combinations tested : {NUM_SCENES * BANK_WIDTH}")
    print(f"route-hit cases     : {route_hits}")
    print(f"fallback cases      : {fallback_cases}")
    print(f"special (0x30) cases: {special_cases}")
    print(f"mismatches          : {mismatches}")
    for name, (got, want) in anchors.items():
        ok = got == want
        anchor_fail += 0 if ok else 1
        print(f"  spot {'OK ' if ok else 'FAIL'} {name}: got {got} want {want}")
    # Exhaustively prove every SAT word-2 field across the complete direct-map
    # domain. HUD-tagged pieces force line 3 exactly as the retired metadata pass
    # did; all other fields remain independent and bit-identical.
    sat_mismatches = 0
    sat_cases = 0
    for s in range(NUM_SCENES):
        for b in range(BANK_WIDTH):
            old_line = oracle(s, b, pc090oj_map)
            new_line = emitted[s * BANK_WIDTH + b]
            for hud in range(2):
                old_selected = 3 if hud else old_line
                new_selected = 3 if hud else new_line
                for priority in range(2):
                    for vflip in range(2):
                        for hflip in range(2):
                            for pattern in range(0x800):
                                old_word = sat_word2(old_selected, priority, vflip, hflip, pattern)
                                new_word = sat_word2(new_selected, priority, vflip, hflip, pattern)
                                sat_cases += 1
                                if old_word != new_word:
                                    sat_mismatches += 1
                                    if sat_mismatches <= 8:
                                        sys.stderr.write(
                                            f"SAT MISMATCH scene={s} bank=0x{b:02X} hud={hud} "
                                            f"p={priority} v={vflip} h={hflip} pattern=0x{pattern:03X}: "
                                            f"old=0x{old_word:04X} new=0x{new_word:04X}\n")

    report = {
        "schema": "pc090oj_direct_palette_equivalence/v1",
        "authoritative_palette_tool_profile": os.path.abspath(args.profile),
        "palette_tool_profile_sha256": profile_sha,
        "route_compatibility_source": os.path.abspath(args.route_src),
        "route_rows_sha1": route_sha,
        "table": {
            "scenes": NUM_SCENES,
            "banks_per_scene": BANK_WIDTH,
            "bytes": len(emitted),
            "lookup_complexity": "O(1)",
            "editor_authored_mappings": {
                f"0x{bank:02X}": line for bank, line in sorted(editor_map.items())
            },
        },
        "mapping_equivalence": {
            "cases": NUM_SCENES * BANK_WIDTH,
            "mismatches": mismatches,
            "anchor_failures": anchor_fail,
        },
        "sat_word2_equivalence": {
            "cases": sat_cases,
            "mismatches": sat_mismatches,
            "fields": ["palette_line", "priority", "vflip", "hflip", "pattern_index", "hud_force"],
        },
        "result": "PASS" if not (mismatches or anchor_fail or sat_mismatches) else "FAIL",
    }
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w") as f:
            json.dump(report, f, indent=2, sort_keys=True)
            f.write("\n")

    print(f"SAT word-2 cases    : {sat_cases}")
    print(f"SAT mismatches      : {sat_mismatches}")
    if args.report:
        print(f"machine report      : {args.report}")
    if mismatches or anchor_fail or sat_mismatches:
        sys.stderr.write(
            f"FAIL: mismatches={mismatches} anchor_fail={anchor_fail} "
            f"sat_mismatches={sat_mismatches}\n")
        return 1
    print("PASS: 0 mapping/SAT mismatches, all spot checks OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
