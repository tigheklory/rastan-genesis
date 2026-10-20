#!/usr/bin/env python3
"""Static verifier for the H25 enemy death / effect families and the gameplay item/weapon-pickup
semantics exposed in the Bestiary + Palette Composer + palette registry (Andy, 2026-10-20).

Read-only; no ROM / MAME / build. Separate from the production-coupled verify_palette_families.py
(Cody's Build 0459-0462 semantic-object integration) so it does not depend on build artifacts.

Checks:
  1  item-drop death is a distinct semantic family (registry + composer), distinct from the collectible
  2  item-drop death distinct from generic burst
  3  bat death family present; one frame; shared by Small+Large bat
  4  bat death is a distinct PATTERN identity from the generic burst (not merged)
  5  generic burst / Demon / boss death family present and intact (object:effect.burst preserved)
  6  held Rastan weapon (object:weapon.*) is NOT treated as a pickup/effect family
  7  no semantic duplicate object_ids created in the composer
  8  Bestiary exposes the death-families section + links to the composer families
  9  h25 taxonomy TSV present and internally consistent
 10  scrolling item-screen decisions untouched (no PC080SN item-screen family added/altered here)
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "specs/palette_decisions.json"
H25 = ROOT / "analysis/actor_decompilation/h25_death_and_effect_families.tsv"
BESTIARY = ROOT / "docs/design/rastan_actor_bestiary.html"

results = []
def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))

reg = {e["id"]: e for e in json.loads(REGISTRY.read_text())["decisions"]}

sys.path.insert(0, str(ROOT / "tools/graphics_editor"))
try:
    import server
    comp = {u["object_id"]: u for u in server.build_usages({})}
except Exception as exc:  # pragma: no cover
    comp = {}
    check("composer builds", False, repr(exc))

# 1/2 item-drop death
idd_reg = "PAL-PC090OJ-ENEMY-ITEM-DROP-DEATH-001" in reg
idd_comp = "object:effect.item_drop_death" in comp
idd = reg.get("PAL-PC090OJ-ENEMY-ITEM-DROP-DEATH-001", {})
distinct_text = json.dumps(idd).lower()
check("item-drop death distinct family (registry+composer)", idd_reg and idd_comp,
      "registry=%s composer=%s" % (idd_reg, idd_comp))
# Corrected finding: the item-drop death reward presentation (0x0A5A) IS the visible collectible
# (same mechanism), so it is distinct from the generic burst (0x0275) and ordinary death (0x0A73),
# NOT from a separate collectible sprite (which does not exist).
check("item-drop death distinct from burst + ordinary death (base 0x0A5A)", idd_reg and
      idd.get("arcade_semantics", {}).get("base") == "0x0A5A" and
      "0x0275" not in idd.get("arcade_semantics", {}).get("base", "") and
      "rec_type-12 pickup actor" in distinct_text,
      "base=%s" % idd.get("arcade_semantics", {}).get("base"))

# 3/4 bat death
bat_reg = reg.get("PAL-PC090OJ-BAT-DEATH-001")
bat_comp = comp.get("object:effect.bat_death")
one_frame = bool(bat_comp) and bat_comp["n_pieces"] == 1
shared = bool(bat_reg) and "0x0268" in json.dumps(bat_reg) and "0x03F6" in json.dumps(bat_reg)
check("bat death family present; one frame; shared Small+Large", bool(bat_reg) and one_frame and shared,
      "n_pieces=%s shared=%s" % (bat_comp["n_pieces"] if bat_comp else None, shared))
burst_comp = comp.get("object:effect.burst")
distinct_pattern = bool(bat_comp) and bool(burst_comp) and \
    bat_comp["object_id"] != burst_comp["map_key"] and bat_comp["object_id"] != "usage:burst:bank0x30"
check("bat death distinct PATTERN identity from burst", distinct_pattern,
      "bat object_id=%s burst map_key=%s" % (bat_comp and bat_comp["object_id"], burst_comp and burst_comp["map_key"]))

# 5 generic burst / demon / boss
burst_reg = "PAL-PC090OJ-ENEMY-DEATH-BURST-001" in reg
check("generic burst/Demon/boss death family present + composer burst preserved", burst_reg and bool(burst_comp),
      "registry=%s composer=%s" % (burst_reg, bool(burst_comp)))

# 6 held weapon not a pickup/effect
held = [oid for oid in comp if oid.startswith("object:weapon.")]
held_clean = all(not comp[oid].get("map_key", "").startswith(("object:effect", "object:hud", "object:attract"))
                 for oid in held)
check("held Rastan weapon NOT treated as pickup/effect", held_clean,
      "held weapon objects=%d" % len(held))

# 7 no duplicate object_ids (burst has 3 frames sharing one id, which is expected)
from collections import Counter
ids = Counter(u["object_id"] for u in (comp.values() if comp else []))
unexpected = {k: v for k, v in ids.items() if v > 1 and k != "object:effect.burst"}
check("no unexpected duplicate composer object_ids", not unexpected, "dups=%s" % unexpected)

# 8 bestiary
bhtml = BESTIARY.read_text() if BESTIARY.exists() else ""
best_ok = "Enemy Death / Effect" in bhtml and "object:effect.bat_death" in bhtml and \
          "object:effect.item_drop_death" in bhtml and "object:item.gameplay_reward_b31" in bhtml
check("Bestiary exposes death-families section + composer links", best_ok)

# 9 h25 TSV
rows = list(csv.DictReader(open(H25), delimiter="\t")) if H25.exists() else []
fam = {r["death_family"]: r for r in rows}
h25_ok = all(k in fam for k in ("ordinary_enemy_death", "item_drop_death", "generic_burst", "bat_death")) and \
         fam.get("bat_death", {}).get("base") == "0x0275" and \
         fam.get("bat_death", {}).get("anim_codes") == "0xA8" and \
         fam.get("item_drop_death", {}).get("base") == "0x0A5A"
check("h25 taxonomy present + internally consistent", h25_ok, "families=%d" % len(rows))

# 10 item screen untouched: these PC090OJ families must not claim the PC080SN scrolling item screen,
# and no new item-screen family/decision is introduced here.
no_itemscreen = all("item-description" not in json.dumps(reg[d]).lower() and
                    "0xC00828" not in json.dumps(reg[d]) for d in
                    ("PAL-PC090OJ-ENEMY-ITEM-DROP-DEATH-001", "PAL-PC090OJ-BAT-DEATH-001")
                    if d in reg)
check("scrolling item-screen decisions untouched", no_itemscreen)

# 11 item-drop reward now PROVEN (real bank, not preview backdrop) + bank groups exposed
idd_comp = comp.get("object:effect.item_drop_death")
reward_b31 = comp.get("object:item.gameplay_reward_b31")
reward_b37 = comp.get("object:item.gameplay_reward_b37")
reward_ok = (idd_comp and idd_comp["sprite_bank"] == "0x30" and
             reward_b31 and reward_b31["sprite_bank"] == "0x31" and
             reward_b37 and reward_b37["sprite_bank"] == "0x37")
check("item-drop reward exposed across real banks 0x30/0x31/0x37 (no backdrop)", reward_ok,
      "idd=%s b31=%s b37=%s" % (idd_comp and idd_comp["sprite_bank"], reward_b31 and reward_b31["sprite_bank"],
                                reward_b37 and reward_b37["sprite_bank"]))
idd_decided = idd.get("status") == "decided" and "0x37" in json.dumps(idd.get("arcade_semantics", {}))
check("item-drop death palette PINNED (decided, banks/kinds)", idd_decided)

# 12 specialized deaths exposed with real banks
sp019d = comp.get("object:effect.specialized_death_019d")
sp09dc = comp.get("object:effect.specialized_death_09dc")
sp_ok = (sp019d and sp019d["sprite_bank"] == "0x34" and "PAL-PC090OJ-SPECIALIZED-DEATH-019D-001" in reg and
         sp09dc and sp09dc["sprite_bank"] == "0x33" and "PAL-PC090OJ-SPECIALIZED-DEATH-09DC-001" in reg)
check("specialized deaths 0x019D (0x34) + 0x09DC (0x33) exposed (composer+registry)", sp_ok,
      "019d=%s 09dc=%s" % (sp019d and sp019d["sprite_bank"], sp09dc and sp09dc["sprite_bank"]))

# 13 transient_alt classified non-death (no composer family)
talt = fam.get("transient_alt_effect", {})
talt_ok = "NOT a standard enemy death" in talt.get("semantic_name", "") and \
          (talt.get("composer_key", "").startswith("(none") or not talt.get("composer_key", "").startswith("object:"))
check("transient_alt classified non-death (no death palette family)", talt_ok,
      "composer_key=%s" % talt.get("composer_key"))

print("=== H25 death / item family verifier ===")
npass = sum(1 for _, ok, _ in results if ok)
for name, ok, detail in results:
    print("  [%s] %s%s" % ("PASS" if ok else "FAIL", name, ("  (%s)" % detail) if detail else ""))
print("%d/%d PASS" % (npass, len(results)))
sys.exit(0 if npass == len(results) else 1)
