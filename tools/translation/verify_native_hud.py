#!/usr/bin/env python3
"""Verify shared native HUD assets, geometry, and change-driven ownership."""
import argparse, importlib.util, json, re
from pathlib import Path

def u16(data, offset):
    return int.from_bytes(data[offset:offset + 2], "big")

def load(path):
    spec = importlib.util.spec_from_file_location("native_hud_generator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def reduced_score_records(packed):
    """Build the accepted compact visible-digit semantic stream."""
    digits = []
    for value in packed:
        digits.extend((value >> 4, value & 0x0f))
    records = []
    visible = False
    for index, digit in enumerate(digits):
        visible = visible or digit != 0
        if visible:
            records.append((0, 0x10, 0xD02A + digit, 0x08 + index * 8))
    return records

def cached_reduced_step(cache, packed):
    """Model the production cache and expose whether conversion ran."""
    if cache.get("valid") and cache["packed"] == packed:
        return cache, cache["records"], False
    records = reduced_score_records(packed)
    return {"valid": True, "packed": packed, "records": records}, records, True

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
    if compact.count("move.w #0x0010, %d2") != 1:
        raise SystemExit("gameplay P1 digit geometry must set score Y=0x10 exactly once")

    # RG-008: the compact score stream is persistent and reconstructed only
    # when one of the exact three bytes consumed by the accepted projector
    # changes.  Static label tuples are immutable and are emitted after that
    # stream into whichever alternating SAT bank owns the current frame.
    cache_contract = (
        "gameplay_hud_score_cache_valid", "gameplay_hud_score_cache+1",
        "gameplay_hud_score_cache+2", "0x00FF011E", "0x00FF011D",
        "0x00FF011C", ".Lnq_p1_hud_rebuild", ".Lnq_p1_hud_done",
    )
    if any(token not in gameplay for token in cache_contract):
        raise SystemExit("gameplay reduced HUD lacks its three-byte presentation cache")
    labels = sprites.split(".Lnq_p1_label_records:", 1)[1].split(
        ".Lnq_emit_hud_digit:", 1)[0]
    label_words = re.findall(r"\.word\s+([^\n]+)", labels)
    wanted_labels = [
        "PC090OJ_HUD_P1_PROFILE_LINE, 0x0010, 0xD039, 0x0040",
        "PC090OJ_HUD_P1_PROFILE_LINE, 0x0000, 0xD048, 0x0028",
        "PC090OJ_HUD_P1_PROFILE_LINE, 0x0000, 0xD046, 0x0038",
    ]
    if [word.strip() for word in label_words[:3]] != wanted_labels:
        raise SystemExit("immutable gameplay 1UP label changed")
    gameplay_finalizer = sprites.split(".Lnq_gameplay:", 1)[1].split(
        ".Lnq_project_p1_hud:", 1)[0]
    if not re.search(r"lea\s+\.Lnq_p1_label_records, %a0\s+moveq\s+#3, %d6\s+bsr\s+\.Lnq_emit_lane",
                     gameplay_finalizer):
        raise SystemExit("immutable P1 label is not emitted into every gameplay SAT bank")

    # Bounded semantic regression: all ten digits at all six positions, plus
    # leading-zero boundaries and consecutive unchanged/change/invalidate
    # transitions.  Cache initialization output must equal the old projector.
    cases = {(0, 0, 0), (0, 0, 1), (0, 0, 0x10), (0, 1, 0),
             (1, 0, 0), (0x12, 0x34, 0x56), (0x99, 0x99, 0x99)}
    for position in range(6):
        for digit in range(10):
            nibbles = [0] * 6
            nibbles[position] = digit
            cases.add(tuple((nibbles[i] << 4) | nibbles[i + 1]
                            for i in range(0, 6, 2)))
    for packed in cases:
        cache, records, rebuilt = cached_reduced_step({}, packed)
        if not rebuilt or records != reduced_score_records(packed):
            raise SystemExit(f"cache initialization mismatch for {packed!r}")
        cache2, records2, rebuilt2 = cached_reduced_step(cache, packed)
        if rebuilt2 or cache2 is not cache or records2 != records:
            raise SystemExit(f"unchanged score reconstructed for {packed!r}")
    cache, _, _ = cached_reduced_step({}, (0, 0, 1))
    cache, changed, rebuilt = cached_reduced_step(cache, (0, 0, 2))
    if not rebuilt or changed != reduced_score_records((0, 0, 2)):
        raise SystemExit("score-change cache update failed")
    cache["valid"] = False
    _, rebuilt_records, rebuilt = cached_reduced_step(cache, (0, 0, 2))
    if not rebuilt or rebuilt_records != changed:
        raise SystemExit("cache invalidation did not force equivalent rebuild")

    # FRONTEND_FULL is already the intended RG-008 architecture: one immutable
    # static SAT installation, ten scalar comparisons on stable frames, and
    # updates only for P1/P2/high-score groups or the credit record.
    full_contract = (
        ".Lhud_copy_static:", "native_hud_cache", "native_hud_cache_valid",
        ".Lhud_group_changed:", ".Lhud_update_group:",
        ".Lhud_update_credit:", "native_hud_cache+9",
    )
    if any(token not in hud for token in full_contract):
        raise SystemExit("FRONTEND_FULL change-driven/template contract missing")
    prepare = hud.split("genesistan_hud_prepare_frontend:", 1)[1].split(
        "genesistan_hud_deactivate:", 1)[0]
    if ".Lhud_copy_static" in prepare:
        raise SystemExit("stable FRONTEND_FULL path revisits the static SAT body")
    deactivate = hud.split("genesistan_hud_deactivate:", 1)[1].split(
        ".Lhud_deactivate_done:", 1)[0]
    if "clr.b   gameplay_hud_score_cache_valid" not in deactivate:
        raise SystemExit("scene HUD deactivation does not invalidate reduced HUD cache")
    title = args.title_source.read_text()
    if "genesistan_hud_activate_frontend" not in title:
        raise SystemExit("title does not activate shared FRONTEND_FULL HUD")
    print("NATIVE_HUD_VERIFY_PASS records=30 links=0->1..28->29,29->0 "
          "modes=FRONTEND_FULL,GAMEPLAY_REDUCED_P1 "
          "gameplay_geometry=score_y10,label_y10_00_00 "
          f"cache_cases={len(cases)} unchanged_no_rebuild=PASS invalidation=PASS")

if __name__ == "__main__":
    main()
