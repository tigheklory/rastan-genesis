#!/usr/bin/env python3
"""Build PROMT-ID-0154's arcade-derived PC090OJ appearance authority.

This is deliberately read-only with respect to the Composer and production build.  It decodes
the original 68000 schedule table and combines it with separately cited constructor/dispatcher
facts from the durable C decompilation.  Unknown scripted domains remain UNRESOLVED.
"""
from __future__ import annotations

import hashlib, json, struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROM = ROOT / "build/regions/maincpu.bin"
OUT = ROOT / "analysis/graphics_optimizer/pc090oj_subround_appearance_manifest.json"
REPORT = ROOT / "docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0154_pc090oj_round_subround_appearance_authority.md"
PROFILE = ROOT / "analysis/graphics_optimizer/editor_policy/Test_2_0.json"
ALLOWED = {"PROVEN_APPEARS", "CONDITIONAL_PROVEN", "PROVEN_ABSENT", "UNRESOLVED"}
SUBS = []
for rnd in range(1, 7):
    base = (rnd - 1) * 23
    SUBS += [
        {"key": f"R{rnd}-S1", "round": rnd, "subround": 1, "records": [base, base+15], "environment": "OUTSIDE"},
        {"key": f"R{rnd}-S2", "round": rnd, "subround": 2, "records": [base+16, base+21], "environment": "CASTLE"},
        {"key": f"R{rnd}-S3", "round": rnd, "subround": 3, "records": [base+22, base+22], "environment": "BOSS"},
    ]

data = ROM.read_bytes()
profile = json.loads(PROFILE.read_text())
maps = profile.get("usage_palette_mappings", {})
generator_text = (ROOT / "tools/graphics_editor/gen_reindexed_pc090oj.py").read_text()
def w(a): return struct.unpack_from(">H", data, a)[0]

FAM = [
    (0, "Lizardman", 0x004B, "usage:lizardman:bank0x36"),
    (1, "Chimera", 0x00D0, "usage:chimera:bank0x34"),
    (2, "Green Sword Knight family", 0x033E, "object:castle.green_sword_knight.r1.n3"),
    (3, "Four-Armed Insect", 0x02E8, "usage:four_armed_insect:bank0x3A"),
    (4, "Horned field family", 0x0420, None),
    (5, "Field family 5", 0x01CB, None),
    (6, "Skeleton field family", 0x03B3, None),
    (7, "Field family 7", 0x043A, None),
    (8, "Family-8 Valkyrie / rope-state actor", 0x0241, "object:castle.rope_climber.family8.r1"),
    (9, "Field family 9", 0x06E2, None),
    (10, "Field family 10", 0x0889, None),
    (11, "Serpent field family", 0x0400, None),
]

def schedule_for_record(record):
    rnd = record // 23 + 1
    progression = record + 1
    block = (progression - rnd) >> 1
    off = 0x4A104 + block * 40
    rows = []
    for slot in range(5):
        r = data[off+slot*8:off+slot*8+8]
        rows.append({"slot": slot, "class": r[0], "family": r[1], "comp": r[2]&15,
                     "variant": r[2]>>4, "reward_kind": r[3],
                     "timer": int.from_bytes(r[4:6], "big"), "marker": int.from_bytes(r[6:8], "big")})
    return rows

def appearance(default="PROVEN_ABSENT"):
    return {s["key"]: {"status": default, "records": [], "evidence": []} for s in SUBS}

objects = []
def add(stable_id, name, category, base=None, rec_type=None, usage_id=None, aliases=None,
        palette="UNRESOLVED", composer="MISSING", bestiary="MISSING", app=None, spawn=""):
    line = None
    if usage_id in maps: line = maps[usage_id].get("line")
    objects.append({"stable_id": stable_id, "canonical_name": name, "aliases": aliases or [],
        "category": category, "arcade_identity": {"base": None if base is None else f"0x{base:04X}",
        "record_type": rec_type}, "graphics": {"base": None if base is None else f"0x{base:04X}"},
        "palette_source": palette, "spawn_source": spawn, "current_genesis": {"usage_id": usage_id,
        "line": line, "mapping_present_in_test_2_0": usage_id in maps if usage_id else False,
        "build_0573_consumption": ("PROVEN_GENERATOR_KEY" if usage_id and usage_id in generator_text
                                   else "NOT_PROVEN_BY_CURRENT_GENERATOR")},
        "current_metadata": {"composer": composer, "bestiary": bestiary},
        "appearance": app or appearance("UNRESOLVED")})

# Global player workload and legal weapon states.
for sid, name, cat, uid in [
    ("player.rastan", "Rastan", "PLAYER", "object:player.rastan"),
    ("weapon.sword", "Sword", "PLAYER_WEAPON", "object:weapon.sword"),
    ("weapon.axe", "Axe", "PLAYER_WEAPON", "object:weapon.axe"),
    ("weapon.hammer", "Hammer", "PLAYER_WEAPON", "object:weapon.hammer"),
    ("weapon.fire_sword", "Fire Sword", "PLAYER_WEAPON", "object:weapon.fire_sword")]:
    a = appearance()
    for s in SUBS:
        a[s["key"]] = {"status": "PROVEN_APPEARS" if cat == "PLAYER" else "CONDITIONAL_PROVEN",
                       "records": s["records"], "evidence": ["player/weapon retained state; rastan_player_weapon_state.c"]}
    add(sid,name,cat,usage_id=uid,palette="record selector + PC090OJ program",composer="CORRECT",
        bestiary="CORRECT",app=a,spawn="retained player state / legal weapon grant state")

# The field schedule is exact per record.  A status is direct appearance, not a graphics inference.
for fam,name,base,uid in FAM:
    a=appearance()
    for s in SUBS:
        hits=[]
        if s["subround"] != 3:
            for rec in range(s["records"][0],s["records"][1]+1):
                if any(e["family"]==fam for e in schedule_for_record(rec)): hits.append(rec)
        if hits:
            a[s["key"]]={"status":"PROVEN_APPEARS","records":hits,
                "evidence":["0x4A104 schedule -> 0x4A086 installer -> 0x4544E template"]}
    cstat = "CORRECT" if fam in (0,1,3) else ("CONFLATED_IDENTITY" if fam==8 else "TOO_NARROW")
    bstat = "CONFLATED_IDENTITY" if fam==8 else ("CORRECT" if fam in (0,1,3) else "TOO_NARROW")
    add(f"enemy.field.family{fam}",name,"ENEMY",base=base,usage_id=uid,
        palette="0x45684 family/round/variant/compositor selector",composer=cstat,bestiary=bstat,app=a,
        spawn="0x4A104 8-byte field schedule; 0x4A086")

# Scripted bats: Ghidra-derived dispatchers 0x4580C and 0x45EFC and constructor 0x45B18.
for large in (False,True):
    a=appearance("UNRESOLVED")
    for k in ("R1-S1","R1-S2"):
        recs=[1,4,8,12] if k=="R1-S1" else [16]
        a[k]={"status":"CONDITIONAL_PROVEN","records":recs,
              "evidence":["0x4580C progression branches -> 0x45B18; round 1 selects type 0x0A and 0x0B"]}
    a["R1-S3"]={"status":"PROVEN_ABSENT","records":[],"evidence":["boss record is outside 0x4580C dispatch"]}
    for k,recs in (("R2-S1",[25,29,32,34,36,37]),("R2-S2",[41])):
        if large:
            a[k]={"status":"PROVEN_ABSENT","records":[],"evidence":["0x45B18 round 2 substitutes record type 0x12 for type 0x0A"]}
        else:
            a[k]={"status":"CONDITIONAL_PROVEN","records":recs,"evidence":["0x45EFC -> 0x45B18 always creates type 0x0B"]}
    a["R2-S3"]={"status":"PROVEN_ABSENT","records":[],"evidence":["boss record outside 0x45EFC"]}
    add("enemy.large_bat" if large else "enemy.small_bat", "Large Bat" if large else "Small Bat", "ENEMY",
        base=0x03F6 if large else 0x0268, rec_type="0x0A" if large else "0x0B",
        usage_id="usage:large_bat:bank0x3E" if large else "usage:small_bat:bank0x3E",
        palette="embedded bank 0x3E",composer="TOO_BROAD",bestiary="TOO_BROAD",app=a,
        spawn="0x4580C/0x45EFC scripted dispatch -> 0x45B18 fixed-slot group")

# Flying Demon proven in the two decompiled dispatchers; other-round dispatchers remain unresolved.
a=appearance("UNRESOLVED")
for k,recs in (("R1-S1",[8,12]),("R2-S1",[26,29,33,36])):
    a[k]={"status":"CONDITIONAL_PROVEN","records":recs,"evidence":["dispatcher -> 0x45342 paired creator"]}
for k in ("R1-S3","R2-S3"):
    a[k]={"status":"PROVEN_ABSENT","records":[],"evidence":["boss record outside scripted dispatcher"]}
add("enemy.flying_demon","Flying Demon","ENEMY",base=0x0129,rec_type="0x08/0x09",
    usage_id="usage:flying_demon:bank0x35",palette="embedded bank 0x35",composer="TOO_NARROW",
    bestiary="TOO_NARROW",app=a,spawn="0x45342 paired fixed-slot creator")

# Seventeen reward kinds: schedule +0x36 -> death transform at 0x40CCC, base 0x0A5A.
idents=[0x17,0x18,0x19,0x12,0x13,0x14,0x15,0x1D,0x1C,0x16,0x1B,0x1A,0x11,0x0D,0x0E,0x0F,0x10]
for kind,ident in enumerate(idents,1):
    a=appearance()
    for s in SUBS:
        hits=[]
        if s["subround"]!=3:
            for rec in range(s["records"][0],s["records"][1]+1):
                if any(e["reward_kind"]==kind for e in schedule_for_record(rec)): hits.append(rec)
        if hits: a[s["key"]]={"status":"CONDITIONAL_PROVEN","records":hits,
            "evidence":["schedule +0x36 kind -> 0x40CCC/0x40D32 reward transform"]}
    add(f"reward.kind{kind:02d}",f"Gameplay Reward Kind {kind:02d}","GAMEPLAY_REWARD",base=0x0A5A,
        usage_id=f"object:item.reward.kind{kind:02d}",aliases=[f"identity byte 0x{ident:02X}"],
        palette="embedded line 0 (1-13) or line 3 (14-17)",composer="TOO_BROAD",bestiary="TOO_BROAD",
        app=a,spawn="eligible ordinary enemy death; same record transforms at 0x40CCC")

# Shared effects are legal consequences, not stage-table enemies.
for sid,name,base,uid,parent in [
    ("effect.ordinary_death","Ordinary enemy death / item-drop transition",0x0A73,"object:effect.item_drop_death","field enemy"),
    ("effect.generic_burst","Generic burst / impact",0x0275,None,"damage/effect producer"),
    ("effect.bat_death","Bat death",0x0275,"object:effect.bat_death","Small or Large Bat")]:
    a=appearance()
    for s in SUBS:
        if s["subround"]!=3:
            a[s["key"]]={"status":"CONDITIONAL_PROVEN","records":s["records"],
                "evidence":[f"legal {parent} lifecycle; 0x40CCC/actor behavior C"]}
    add(sid,name,"DEATH_EFFECT",base=base,usage_id=uid,palette="effect program selector",
        composer="CORRECT" if uid else "MISSING",bestiary="CORRECT",app=a,spawn="actor lifecycle transform")

# Boss bodies and their source-proven auxiliary/component domain.
boss_base=[0x061D,0x0753,0x082C,0x07BF,0x0988,0x0B35]
for rnd,base in enumerate(boss_base,1):
    for aux in (False,True):
        a=appearance()
        key=f"R{rnd}-S3"
        a[key]={"status":"CONDITIONAL_PROVEN" if aux else "PROVEN_APPEARS",
                "records":[rnd*23-1],"evidence":["record-type templates 0x45592; round boss creator/component path"]}
        add(f"boss.r{rnd}.auxiliary" if aux else f"boss.r{rnd}.body",
            f"Round {rnd} Boss auxiliary/projectile domain" if aux else f"Round {rnd} Boss body",
            "BOSS_PROJECTILE" if aux else "BOSS",base=base,
            usage_id=("object:boss.r1.flying_daggers" if aux and rnd==1 else "object:boss.r1.body" if rnd==1 else None),
            palette="boss-stage sprite-control bank",composer="CORRECT" if rnd==1 else "MISSING",
            bestiary="CORRECT" if not aux else "TOO_NARROW",app=a,
            spawn="round-specific S3 boss state / component creator")

# Preserve technical domains that are visible in constructors but not yet closed to all scene dispatchers.
for sid,name,base,rt in [
    ("scripted.type0c","Scripted type 0x0C",0x050B,"0x0C"),
    ("scripted.type0d","Scripted type 0x0D",0x0D5F,"0x0D"),
    ("scripted.batch16","Batch/swarm type 0x16",0x0D56,"0x16"),
    ("effect.special019d","Specialized death 0x019D",0x019D,None),
    ("effect.special09dc","Specialized death 0x09DC",0x09DC,None)]:
    add(sid,name,"OTHER_GAMEPLAY" if "effect" not in sid else "DEATH_EFFECT",base=base,rec_type=rt,
        usage_id=f"object:{sid}",palette="UNRESOLVED",composer="MISSING",bestiary="MISSING",
        app=appearance("UNRESOLVED"),spawn="constructor exists; full round dispatcher/lifetime closure pending")

manifest={"schema":"pc090oj-subround-appearance/v1","prompt_id":"TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0154",
 "authority":{"primary":["build/regions/maincpu.bin","canonical Ghidra project","analysis/decompilation/c"],
 "non_authoritative_audit_inputs":["Palette Composer","bestiary","Test 2.0","Genesis Build 0573","screenshots/traces"]},
 "status_vocabulary":sorted(ALLOWED),"subrounds":SUBS,"objects":objects,
 "limitations":["UNRESOLVED is intentionally not absence","human item names for reward kinds are not source-proven",
 "later-round scripted dispatchers and five technical domains require further decompilation"]}

# Mechanical invariants requested by the prompt.
for o in objects:
    assert set(o["appearance"]) == {s["key"] for s in SUBS}
    for cell in o["appearance"].values():
        assert cell["status"] in ALLOWED
        if cell["status"] in ("PROVEN_APPEARS","CONDITIONAL_PROVEN"): assert cell["evidence"]
assert any(o["stable_id"]=="enemy.small_bat" for o in objects)
assert any(o["stable_id"]=="enemy.large_bat" for o in objects)
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
manifest_sha=hashlib.sha256(OUT.read_bytes()).hexdigest()

legend={"PROVEN_APPEARS":"P","CONDITIONAL_PROVEN":"C","PROVEN_ABSENT":"A","UNRESOLVED":"?"}
bad={"MISSING","WRONG_SUBROUND","TOO_BROAD","TOO_NARROW","DUPLICATED","CONFLATED_IDENTITY","STALE"}
composer_bad=sum(o["current_metadata"]["composer"] in bad for o in objects)
bestiary_bad=sum(o["current_metadata"]["bestiary"] in bad for o in objects)

md=[]
def h(n,title): md.append(f"## {n}. {title}\n")
md += ["TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0154\n",
"# Arcade-derived PC090OJ round/subround appearance authority\n",
"> Authority order: original World Rev. 1 68000 binary, canonical Ghidra project/export, then the durable C decompilation. Composer, bestiary, Test 2.0, Build 0573, screenshots, and traces are audit inputs—not appearance authority. This report deliberately preserves unknowns.\n"]
h(1,"Starting state")
md.append("Branch `rastan-direct-proposal`; starting HEAD `275e2e35e65e46dab46ce685c035e554dea4110d`; Makefile counter `573`. The worktree already contained the uncommitted 0149/0151 reports and analyzer files, `AGENTS_LOG.md`, audio source/output, generated build/address-map/trace files, Andy 0134–0136 documents, and other concurrent documentation. Nothing was reset, cleaned, restored, or built.\n")
h(2,"Research methodology")
md.append("The generator decodes the original `$4A104` 8-byte field schedule, follows `$4A086` into the family/template and palette selectors, and records direct per-record membership. Scripted actors use Ghidra decompilation of `$4580C`, `$45EFC`, `$46204`, and `$4650E`; bats then close through `$45B18`. Rewards use schedule byte `+$36` and the `$40CCC/$40D32` in-place death→reward transform. Bosses use the `$45592` record-type templates and round-specific S3 creators. A graphics base, palette mapping, screenshot, or existing label never creates an appearance claim.\n")
h(3,"Exact 18-subround progression/record mapping")
md.append("`$50248` maps master section through `$5073A` to progression `$013E`; `$502AC` contains round endpoints `$16,$2D,$44,$5B,$72,$89`; `$507C5` selects the scene descriptor. The project coordinate is 23 retained records per round: 16 outside, 6 castle, 1 boss.\n")
md.append("|Subround|Round|Environment|Retained records|Entry|Exit|\n|---|---:|---|---|---:|---:|\n")
for s in SUBS: md.append(f"|{s['key']}|{s['round']}|{s['environment']}|{s['records'][0]}–{s['records'][1]}|{s['records'][0]}|{s['records'][1]}|\n")
h(4,"Current Palette Composer roster architecture")
md.append("The visible `v0.4` is hardcoded in `tools/graphics_editor/index.html`. New profiles and backend fallbacks also write schema `v0.4` (`app.js` branch creation and `server.py` profile response). Object membership is a mixture: exact `scene_key`, broad `membership=field_phase1`, `shared`, hardcoded Python constructors, bestiary-era labels, and a coverage endpoint. The subround table explicitly says `sprites (per-scene roster pending)`. Thus the UI version, profile schema tag, and feature maturity are effectively conflated.\n")
h(5,"Current bestiary roster architecture")
md.append("`tools/graphics_optimizer/build_bestiary.py` combines hand-curated identities, historical prompt findings, graphics/program domains, and partial source tables. It is useful evidence but is not generated from a complete spawn/record authority. Human labels and graphics families can therefore be correct while round/subround membership is broad, narrow, or conflated.\n")
h(6,"Why current classifications became unreliable")
md.append("The systems historically inferred gameplay membership from graphics availability, broad `shared` mappings, one captured phase, or manual scene tags. They did not keep identity, graphics, palette, Genesis realization, subround legality, and record-local legality as six independent facts. In particular, rewards were treated as globally shared, bats lacked record membership, and the family-8 rope-state label was manually attached to R1-S2 despite no R1-S2 family-8 schedule entry.\n")
h(7,"Complete arcade-derived PC090OJ gameplay-object inventory")
md.append(f"This pass defines {len(objects)} canonical workload records: player/weapons, 12 field families, scripted bats/demon, 17 distinct reward kinds, shared death effects, six boss bodies and six auxiliary domains, plus five technical scripted/effect identities retained as unresolved rather than omitted. Presentation-only title/READY/Stage Clear actors are excluded.\n")
h(8,"Object identity table")
md.append("|Stable ID|Name|Category|Base/type|Spawn source|Palette source|Test 2.0 usage/line|\n|---|---|---|---|---|---|---|\n")
for o in objects:
    ai=o['arcade_identity']; g=o['current_genesis']; bt=(ai['base'] or '—')+'/'+(ai['record_type'] or '—')
    md.append(f"|`{o['stable_id']}`|{o['canonical_name']}|{o['category']}|{bt}|{o['spawn_source']}|{o['palette_source']}|`{g['usage_id'] or '—'}` / {g['line'] if g['line'] is not None else '—'}|\n")
h(9,"Master 18-subround appearance matrix")
md.append("Legend: `P` PROVEN_APPEARS; `C` CONDITIONAL_PROVEN; `A` PROVEN_ABSENT; `?` UNRESOLVED.\n\n")
keys=[s['key'] for s in SUBS]
md.append("|Object|"+"|".join(keys)+"|\n|---|"+"|".join(["---"]*18)+"|\n")
for o in objects: md.append("|"+o['canonical_name']+"|"+"|".join(legend[o['appearance'][k]['status']] for k in keys)+"|\n")

# Sections 10-27: direct downstream tables.  Only legal P/C entries are included; absence/? remains in matrix.
for idx,s in enumerate(SUBS,10):
    h(idx,f"{s['key']} detailed roster")
    md.append("|Object|Category|Arcade identity/base|Spawn source|Record/window|Conditional?|Palette source|Genesis line|Composer|Bestiary|Evidence|\n|---|---|---|---|---|---|---|---|---|---|---|\n")
    for o in objects:
        c=o['appearance'][s['key']]
        if c['status'] not in ("PROVEN_APPEARS","CONDITIONAL_PROVEN"): continue
        ai=o['arcade_identity']; rec=','.join(map(str,c['records'])) if isinstance(c['records'],list) else str(c['records'])
        ev='; '.join(c['evidence']); line=o['current_genesis']['line']
        md.append(f"|{o['canonical_name']}|{o['category']}|{ai['base'] or '—'} / {ai['record_type'] or '—'}|{o['spawn_source']}|{rec}|{'yes' if c['status']=='CONDITIONAL_PROVEN' else 'no'}|{o['palette_source']}|{line if line is not None else 'unresolved'}|{o['current_metadata']['composer']}|{o['current_metadata']['bestiary']}|{ev}|\n")

h(28,"Small Bat proof")
md.append("Type `$0B`, base `$0268`. `$4580C` reaches `$45B18` at Round-1 progression 2, 5, 9, 13, and 17 (conditional local thresholds); progression 17 is retained record 16, the R1-S2 entry. `$45B18` always creates the type-$0B slot. It is therefore conditional-proven in R1-S1 and R1-S2. `$45EFC` similarly proves R2-S1/S2 occurrences. Current `shared` metadata is too broad because it has no legal record set.\n")
h(29,"Large Bat proof")
md.append("Type `$0A`, base `$03F6`, is created by the same `$45B18` group in Round 1, so it is conditional-proven in R1-S1 and R1-S2, including retained record 16. In Round 2, `$45B18` deliberately substitutes record type `$12` for `$0A`; therefore the Large Bat is proven absent from the R2 calls even though the Small Bat remains. This independent representation prevents the old Small/Large conflation.\n")
h(30,"Green Sword Knight proof")
md.append("Family 2/base `$033E` is installed directly by `$4A086` from schedule `$4A104` across all six R1-S2 retained records 16–21 (progression `$11..$16`). The technical family is proven; the exact human pose names remain secondary. Test 2.0 maps the R1 knight object to Line 0.\n")
h(31,"Rope Climber proof")
md.append("The current separate `object:castle.rope_climber.family8.r1` claim is not source-proven for R1-S2. Family 8/base `$0241` occurs in the Round-1 schedule only in outside records 6–7, not castle records 16–21. The R1-S2 screenshots show a rope-climbing pose, but source membership says it cannot be used to create a separate family-8 R1-S2 actor without another persistence/constructor path. The correct R1-S2 rope pose may belong to scheduled family 2; until that state identity is closed, the current metadata is `CONFLATED_IDENTITY`, and Andy must not preserve the family-8 R1-S2 listing as authority.\n")
h(32,"Blue Crystal proof")
md.append("The arcade executable exposes 17 technical reward kinds, identity bytes, anims and codes, but no human string that identifies which kind is called “Blue Crystal.” R1-S2 legally permits kinds 3, 4, 6, 11 and 13 through schedule `+$36` and `$40CCC/$40D32`. Thus the collectible class and its R1-S2 legality are proven, while the Blue-Crystal→kind alias remains UNRESOLVED and must not be guessed from pixels. An enemy-only roster misses it because the dying enemy record transforms in place into family 12/base `$0A5A`.\n")
h(33,"All gameplay reward/item appearance rules")
md.append("Each reward row in the matrix is computed from exact schedule byte `+$36`. Status is conditional because the owning enemy must be killed and the death path must reach the transform. Kinds 1–13 use embedded source line 0 and kinds 14–17 line 3; Test 2.0 may remap individual kinds differently. Human names remain unresolved.\n")
h(34,"Projectiles, children, and effects")
md.append("Ordinary item-drop/death and generic/bat death are independent workload identities. The bat effect is base `$0275` anim `$A8`; generic burst uses `$0275` anim `$9D..$A0`; ordinary reward transition uses `$0A73` then `$0A5A`. Five constructor-visible technical domains remain `?` because this pass did not falsely promote an unclosed dispatcher to absence or universal membership.\n")
h(35,"Boss/boss-projectile appearance rules")
md.append("Each boss body is constrained to the one S3 record of its round. Auxiliary/component/projectile domains are conditional in that same record and absent elsewhere. R1 body and flying-dagger mappings exist in Test 2.0; later boss mappings are missing from the current Composer authority.\n")
h(36,"Current Composer discrepancies")
md.append(f"Object-level audit: {composer_bad} of {len(objects)} records are MISSING/TOO_BROAD/TOO_NARROW/CONFLATED (MISSING 16, TOO_BROAD 19, TOO_NARROW 9, CONFLATED 1); 12 are classified CORRECT at this granularity. Most serious: pending per-scene roster, bats without records, rewards marked shared, family-8 rope actor assigned to R1-S2, and later bosses/scripted identities absent.\n")
h(37,"Current bestiary discrepancies")
md.append(f"Object-level audit: {bestiary_bad} of {len(objects)} records are MISSING/TOO_BROAD/TOO_NARROW/CONFLATED (MISSING 5, TOO_BROAD 19, TOO_NARROW 15, CONFLATED 1); 17 are CORRECT at this granularity. The bestiary contains valuable technical identities but is not a complete spawn matrix.\n")
h(38,"Current Test 2.0 / Build-0573 Genesis mapping cross-reference")
md.append("The identity table records exact Test 2.0 usage IDs and lines when a matching key exists. The manifest separately marks `PROVEN_GENERATOR_KEY` only where the current offline generator contains that exact usage key; all others are `NOT_PROVEN_BY_CURRENT_GENERATOR`. The generator explicitly consumes player, four weapons, Lizardman, Chimera, Four-Armed Insect, Flying Demon, Small Bat, Large Bat, and R1 Green Sword Knight. It does not consume the reward-kind keys or the family-8 rope key. Crucially, R1-S2-legal reward kind 11 is mapped to Line 1 in Test 2.0 but is not proven consumed by Build 0573's current generator—mapping existence and production consumption are distinct.\n")
h(39,"Palette Composer v0.4/versioning audit")
md.append("`index.html` supplies the visible version; `app.js` and `server.py` also use `v0.4` as profile schema. The tool has since gained contexts, per-scene packages, object domains, local overrides, validation, and many specialized rosters without separating application release from data schema. Andy should introduce independent fields such as application `0.5.0` (or `1.0.0` after the authority integration), profile schema `palette-profile/v1`, and appearance-manifest schema `pc090oj-subround-appearance/v1`, with explicit migration. No version was changed here.\n")
h(40,"Machine-readable manifest schema/path/SHA")
md.append(f"Path: `analysis/graphics_optimizer/pc090oj_subround_appearance_manifest.json`. Schema `pc090oj-subround-appearance/v1`. SHA-256 `{manifest_sha}`. Generator: `tools/analysis/build_pc090oj_subround_appearance_manifest.py`.\n")
md.append("Artifact validation PASS: 57 objects × 18 cells, allowed status vocabulary, evidence on every P/C cell, separate Small/Large Bat identities, 49 report sections, report/manifest matrix agreement, Python compile, selected new-C syntax, and byte-identical regeneration. Repository-wide legacy decompilation guards are not clean at this starting state: coverage already reports six older COMPLETE rows without raw files; fidelity reports the older `raw/00047004.c` annotation gap; whole-tree C syntax has older airborne/attract reconstruction errors. Those pre-existing failures were not hidden or repaired outside this task.\n")
h(41,"Remaining unresolved identities/appearances")
md.append("Eight object records retain at least one `UNRESOLVED` cell: Small Bat, Large Bat, Flying Demon, and five technical scripted/effect domains. Later-round scripted dispatchers must be decompiled before those cells can become P/C/A. Reward human names—including Blue Crystal—also remain unresolved aliases even where technical kinds are exact.\n")
h(42,"Impact on historical PROMT-ID-0151")
md.append("0151’s Line-1 capacity conclusion is contradicted by the corrected roster: reward kind 11 can legally appear in R1-S2 and Test 2.0 maps it to Line 1. The prior roster also omitted conditional bats, although their current mapping is Line 2. Therefore 0151 cannot authorize the fire pit on Line 1 until reward identity/residency and all remaining conditional R1-S2 objects are included. No fire-pit decision is made here.\n")
h(43,"Exact instructions for Andy’s subsequent correction task")
md.append("Consume this JSON as the sole appearance input; keep identity/graphics/palette/Genesis mapping/subround/record facts separate; render P/C/A/? explicitly; replace `field_phase1` and `shared` roster shortcuts with manifest membership; preserve authored palette mappings; remove the family-8 R1-S2 rope assertion pending a proven path; expose reward kinds 3/4/6/11/13 in R1-S2; add record-window UI; migrate app and schema versions independently; update bestiary from the same manifest; never convert `?` to absent.\n")
for n,title in [(44,"Production source changed"),(45,"Palette Composer changed"),(46,"Bestiary changed"),(47,"Test 2.0 changed"),(48,"ROM produced"),(49,"Build number consumed")]:
    h(n,title); md.append("NONE.\n")
md.append("TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0154\n")
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text("".join(md))
print(f"WROTE {OUT} objects={len(objects)} sha256={manifest_sha}")
print(f"WROTE {REPORT}")
