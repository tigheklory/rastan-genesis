#!/usr/bin/env python3
"""Verify shared native HUD assets, geometry, and consumer ownership contracts."""
import argparse, importlib.util, json, re
from pathlib import Path

def u16(data, offset):
    return int.from_bytes(data[offset:offset + 2], "big")

def load(path):
    spec = importlib.util.spec_from_file_location("native_hud_generator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    parser = argparse.ArgumentParser()
    for name in ("generator", "maincpu", "pc090oj", "patterns", "static-sat",
                 "dynamic-records", "report", "hud-source", "sprite-source", "title-source"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    generator = load(args.generator)
    maincpu = args.maincpu.read_bytes()
    result = generator.build(maincpu, args.pc090oj.read_bytes())
    expected = {args.patterns: result["patterns"], args.static_sat: result["static_sat"],
                args.dynamic_records: result["dynamic_records"]}
    for path, wanted in expected.items():
        if path.read_bytes() != wanted:
            raise SystemExit(f"shared HUD output mismatch: {path}")
    sat = args.static_sat.read_bytes()
    for index in range(30):
        link = u16(sat, index * 8 + 2) & 0x7f
        wanted = index + 1 if index < 29 else 0
        if link != wanted:
            raise SystemExit(f"HUD SAT link {index} is {link}, expected {wanted}")
    if len(args.dynamic_records.read_bytes()) != 19 * 11 * 8:
        raise SystemExit("shared HUD dynamic table is not 19 positions x 11 variants")

    # Original arcade geometry is authoritative.  Mode 0 at 0x03B87E owns the
    # six P1 score digits; the setup table at 0x03B9B0 owns the fixed 1UP label.
    score = maincpu[0x3B87E:0x3B888]
    score_contract = (score[0], score[1], int.from_bytes(score[2:6], "big"),
                      int.from_bytes(score[6:10], "big"))
    if score_contract != (6, 0x10, 0x00D00108, 0x0010C11E):
        raise SystemExit(f"arcade P1 score geometry changed: {score_contract!r}")
    p1 = generator.template(maincpu, 0x3B9B0, 9)
    if p1[6:9] != [(0x10, 0x0040, 0x39),
                    (0x00, 0x0028, 0x48),
                    (0x00, 0x0038, 0x46)]:
        raise SystemExit(f"arcade 1UP label geometry changed: {p1[6:9]!r}")
    report = json.loads(args.report.read_text())
    if report.get("format") != "rastan-shared-native-hud-v1":
        raise SystemExit("wrong shared HUD report format")
    if set(report["modes"]) != {"FRONTEND_FULL", "GAMEPLAY_REDUCED_P1", "GAMEPLAY_FULL_future_supported"}:
        raise SystemExit("shared HUD mode contract incomplete")
    hud = args.hud_source.read_text()
    required = ("HUD_MODE_FRONTEND_FULL", "native_hud_patterns", "native_hud_static_sat",
                "native_hud_dynamic_records", "0x00FF009E", "0x00FF00DE",
                "0x00FF011E", "0x00FF0142", "0x00FF0117")
    if any(token not in hud for token in required):
        raise SystemExit("shared HUD runtime lacks generated asset or semantic input")
    sprites = args.sprite_source.read_text()
    if "native_title_static_sat" in sprites:
        raise SystemExit("duplicate generic/title-private frontend HUD owner remains")
    legacy = sprites.find("native_frontend_hud_emit:")
    guard = sprites.rfind(".if 0", 0, legacy)
    end_guard = sprites.find(".endif", legacy)
    if legacy >= 0 and not (guard >= 0 and end_guard > legacy):
        raise SystemExit("compiled legacy frontend HUD owner remains")
    if "genesistan_hud_prepare_frontend" not in sprites or ".Lnq_project_p1_hud" not in sprites:
        raise SystemExit("frontend full or gameplay reduced HUD consumer is missing")
    gameplay = sprites.split(".Lnq_project_p1_hud:", 1)[1].split(".Lnq_emit_hud_digit:", 1)[0]
    compact = re.sub(r"\s+", " ", gameplay)
    score_geometry = re.compile(
        r"movea\.l #0x00FF011E, %a0 clr\.w %d5 .*? move\.w #0x0010, %d2 .*? "
        r"move\.b \(%a0\), %d1",
    )
    if not score_geometry.search(compact):
        raise SystemExit("gameplay P1 digits do not explicitly use arcade Y=0x10")
    if compact.count("move.w #0x0010, %d2") != 2:
        raise SystemExit("gameplay P1 geometry must set Y=0x10 for score and code 0x39 only")
    label_contract = re.compile(
        r"move\.w #0xD039, %d3 .*? bsr native_sprite_emit_fast .*? clr\.w %d2 .*? "
        r"move\.w #0xD048, %d3 .*? bsr native_sprite_emit_fast .*? "
        r"move\.w #0xD046, %d3",
    )
    if not label_contract.search(compact):
        raise SystemExit("gameplay 1UP label does not preserve arcade Y split 0x10/0x00/0x00")
    title = args.title_source.read_text()
    if "genesistan_hud_activate_frontend" not in title:
        raise SystemExit("title does not activate shared FRONTEND_FULL HUD")
    print("NATIVE_HUD_VERIFY_PASS records=30 links=0->1..28->29,29->0 "
          "modes=FRONTEND_FULL,GAMEPLAY_REDUCED_P1 "
          "gameplay_geometry=score_y10,label_y10_00_00")

if __name__ == "__main__":
    main()
