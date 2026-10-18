#!/usr/bin/env python3
"""Verify shared native HUD assets and consumer ownership contracts."""
import argparse, importlib.util, json
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
    result = generator.build(args.maincpu.read_bytes(), args.pc090oj.read_bytes())
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
    title = args.title_source.read_text()
    if "genesistan_hud_activate_frontend" not in title:
        raise SystemExit("title does not activate shared FRONTEND_FULL HUD")
    print("NATIVE_HUD_VERIFY_PASS records=30 links=0->1..28->29,29->0 modes=FRONTEND_FULL,GAMEPLAY_REDUCED_P1")

if __name__ == "__main__":
    main()
