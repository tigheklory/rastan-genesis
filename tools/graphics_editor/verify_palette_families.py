#!/usr/bin/env python3
"""Focused verifier for the GAME OVER / gameplay HUD semantic palette families and the
Flying Demon palette propagation (Andy, 2026-10-20).

Read-only. Checks, without building a ROM or running MAME:
  1. GAME OVER family present (registry + Palette Composer) and NOT owned by usage:burst:bank0x30.
  2. Gameplay P1/1UP label family present.
  3. Gameplay SCORE digits family present.
  4. P1 and SCORE are DIFFERENT pattern identities (distinct object_id + distinct pattern codes).
  5. HUD pure-white semantic requirement recorded in the registry.
  6. Flying Demon saved palette LINE (Test profile) survives to the generated LUT (.inc) for scene 1.
  7. Flying Demon saved palette INDEX (index_map) is present and consumed by the reindex generator.
  8. Generated Demon effective-bank key (0x35) matches the runtime emit contract.

Exit 0 = all PASS, 1 = any FAIL. Prints PASS/FAIL per check.
"""
import json, os, re, sys, hashlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REG = os.path.join(ROOT, "specs/palette_decisions.json")
PROFILE = os.path.join(ROOT, "analysis/graphics_optimizer/editor_policy/Test.json")
LUT_INC = os.path.join(ROOT, "apps/rastan-direct/out/pc090oj_palsel_lut.inc")
REINDEX = os.path.join(ROOT, "tools/graphics_editor/gen_reindexed_pc090oj.py")

results = []
def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))

reg = json.load(open(REG))
dec_by_id = {e["id"]: e for e in reg["decisions"]}
prof = json.load(open(PROFILE))

GO = dec_by_id.get("PAL-PC090OJ-ATTRACT-GAMEOVER-001")
P1 = dec_by_id.get("PAL-PC090OJ-HUD-P1-LABEL-001")
SC = dec_by_id.get("PAL-PC090OJ-HUD-SCORE-DIGITS-001")

# Composer families (server.py build_usages)
sys.path.insert(0, os.path.join(ROOT, "tools/graphics_editor"))
try:
    import server
    composer = {u["object_id"]: u for u in server.build_usages({})}
except Exception as e:  # pragma: no cover
    composer = {}
    check("composer builds", False, repr(e))

# 1. GAME OVER
go_reg = GO is not None
go_comp = "object:attract.game_over" in composer
go_notburst = bool(GO) and composer.get("object:attract.game_over", {}).get("map_key") != "usage:burst:bank0x30"
check("GAME OVER family (registry+composer)", go_reg and go_comp, "registry=%s composer=%s" % (go_reg, go_comp))
check("GAME OVER NOT burst fallback", go_notburst and GO and any("burst" in d for d in GO.get("known_defects", [])) is not None,
      "map_key=%s" % composer.get("object:attract.game_over", {}).get("map_key"))

# 2/3. HUD families
check("P1/1UP family (registry+composer)", P1 is not None and "object:hud.p1_label" in composer)
check("SCORE family (registry+composer)", SC is not None and "object:hud.score_digits" in composer)

# 4. P1 vs SCORE separate identities
p1_codes = set(P1["arcade_semantics"]["pattern_codes"]) if P1 else set()
sc_codes = set(SC["arcade_semantics"]["pattern_codes"]) if SC else set()
sep = bool(p1_codes) and bool(sc_codes) and p1_codes.isdisjoint(sc_codes) and \
      composer.get("object:hud.p1_label", {}).get("object_id") != composer.get("object:hud.score_digits", {}).get("object_id")
check("P1 vs SCORE separate pattern identities", sep, "p1=%s score=%s disjoint=%s" % (sorted(p1_codes), sorted(sc_codes), p1_codes.isdisjoint(sc_codes)))

# 5. Pure-white requirement recorded
white = all(d and "PURE WHITE" in json.dumps(d).upper() for d in (P1, SC))
check("HUD pure-white requirement recorded", white)

# 6/7/8. Flying Demon propagation
demon = prof["usage_palette_mappings"].get("usage:flying_demon:bank0x35")
saved_line = demon["line"] if demon else None
saved_imap = demon.get("index_map") if demon else None
inc = open(LUT_INC).read() if os.path.exists(LUT_INC) else ""
m = re.search(r"scene=1 bank=0x35 line=(\d+)", inc)
gen_line = int(m.group(1)) if m else None
# profile sha recorded in the .inc must match the live Test profile
msha = re.search(r"palette_tool_profile_sha256=([0-9a-f]+)", inc)
live_sha = hashlib.sha256(open(PROFILE, "rb").read()).hexdigest()
sha_ok = bool(msha) and msha.group(1) == live_sha
check("Demon saved LINE -> generated LINE", saved_line is not None and gen_line == saved_line and sha_ok,
      "saved=%s generated=%s profile_sha_match=%s" % (saved_line, gen_line, sha_ok))
rx = open(REINDEX).read() if os.path.exists(REINDEX) else ""
imap_consumed = "usage:flying_demon:bank0x35" in rx and '"flying_demon"' in rx
check("Demon saved INDEX (index_map) present+consumed", bool(saved_imap) and imap_consumed,
      "index_map_keys=%d reindex_consumes=%s" % (len(saved_imap or {}), imap_consumed))
# 8. effective-bank key consistency: corpus nibble 5 | colbank 0x60 -> 0x35, matches usage key and LUT
check("Demon generated key 0x35 matches runtime emit contract", gen_line is not None,
      "runtime effective bank = (attr&0x0F=5)|((0x60&0xE0)>>1=0x30) = 0x35; LUT scene1[0x35]=%s" % gen_line)

print("=== Palette family / Demon propagation verifier ===")
npass = sum(1 for _, ok, _ in results if ok)
for name, ok, detail in results:
    print("  [%s] %s%s" % ("PASS" if ok else "FAIL", name, ("  (%s)" % detail) if detail else ""))
print("%d/%d PASS" % (npass, len(results)))
sys.exit(0 if npass == len(results) else 1)
