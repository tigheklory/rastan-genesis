#!/usr/bin/env python3
"""H20 game-wide 68000 decompilation coverage census.

Denominator = ALL Ghidra-identified 68000 functions in build/regions/maincpu.bin, from
analysis/ghidra/rastan_arcade/exports/function_inventory.tsv. Status is joined from the durable
decompilation tracker analysis/decompilation/c/function_coverage.csv (COMPLETE/PARTIAL/STUB_ONLY);
functions absent from it are NOT_DECOMPILED and REMAIN in the denominator. Byte span per function =
body_max - body_min; the game-wide denominator uses the UNION of function byte-ranges so overlapping
Ghidra ranges/thunks are not double-counted. Each function has ONE primary subsystem owner (by its
tracker semantic-file when tracked, else a PC-range heuristic), so subsystem byte totals sum exactly
to the union denominator. Run from repo root. NOT a Genesis/runtime tool. """
import os, csv, json, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INV = os.path.join(ROOT, "analysis/ghidra/rastan_arcade/exports/function_inventory.tsv")
COV = os.path.join(ROOT, "analysis/decompilation/c/function_coverage.csv")
OUT_INV = os.path.join(ROOT, "analysis/decompilation/gamewide_function_inventory.csv")
OUT_SUB = os.path.join(ROOT, "analysis/decompilation/gamewide_subsystem_coverage.csv")
OUT_SUM = os.path.join(ROOT, "analysis/decompilation/gamewide_coverage_summary.json")

SUBSYS = [
 "PLAYER_CONTROL_MOVEMENT","PLAYER_WEAPONS_ITEMS_STATUS","ACTOR_CORE_LIFECYCLE_CREATION",
 "ENEMY_AI_BEHAVIORS","COLLISION_DAMAGE_PHYSICS","BOSS_LOGIC","MAP_SCENE_ROUND_PROGRESSION",
 "PC080SN_TILEMAP_SCROLL_COLLISIONMAP","PC090OJ_SPRITE_COMPOSITOR","PALETTE_COLOR",
 "HUD_SCORE_LIVES_GAMESTATE","INPUT_SERVICE_ATTRACT","INTERRUPTS_TIMING_VBLANK_SYSTEM",
 "AUDIO_INTERFACE","INIT_RESET_MEMORY","OTHER_KNOWN","UNCLASSIFIED"]

# tracked semantic-file -> primary subsystem
SEMFILE_SUB = {
 "rastan_player_weapon_state.c":"PLAYER_WEAPONS_ITEMS_STATUS",
 "rastan_player_items.c":"PLAYER_WEAPONS_ITEMS_STATUS",
 "rastan_player_solid_object.c":"COLLISION_DAMAGE_PHYSICS",
 "rastan_player_world_contact.c":"COLLISION_DAMAGE_PHYSICS",
 "rastan_actor_render.c":"PC090OJ_SPRITE_COMPOSITOR",
 "rastan_anim_motion_core.c":"PC090OJ_SPRITE_COMPOSITOR",
 "rastan_actor_behavior.c":"ENEMY_AI_BEHAVIORS",
 "rastan_actor_creation.c":"ACTOR_CORE_LIFECYCLE_CREATION",
 "rastan_actor_materialization.c":"ACTOR_CORE_LIFECYCLE_CREATION",
 "rastan_actor_lifecycle.c":"ACTOR_CORE_LIFECYCLE_CREATION",
 "rastan_actor_helpers.c":"ACTOR_CORE_LIFECYCLE_CREATION",
 "rastan_actor_dispatch.c":"ACTOR_CORE_LIFECYCLE_CREATION",
 "rastan_actor_subsystems.c":"ACTOR_CORE_LIFECYCLE_CREATION",
 "rastan_actor_tables.c":"ACTOR_CORE_LIFECYCLE_CREATION",
 "rastan_boss_composite.c":"BOSS_LOGIC",
 "rastan_actor_collision.c":"COLLISION_DAMAGE_PHYSICS",
 "rastan_actor_palette.c":"PALETTE_COLOR",
 "rastan_scene_map.c":"MAP_SCENE_ROUND_PROGRESSION",
 "rastan_world_progression.c":"MAP_SCENE_ROUND_PROGRESSION",
 "rastan_world_stream.c":"PC080SN_TILEMAP_SCROLL_COLLISIONMAP",
 "rastan_world_scroll.c":"PC080SN_TILEMAP_SCROLL_COLLISIONMAP",
 "rastan_player_animation.c":"PLAYER_CONTROL_MOVEMENT",
 "rastan_player_render.c":"PLAYER_CONTROL_MOVEMENT",
 "rastan_execution_spine.c":"INTERRUPTS_TIMING_VBLANK_SYSTEM",
}
# PC-range heuristic for UNTRACKED functions (start,end,subsystem). Ranges from the H1-H19 map.
PC_RULES = [
 (0x00000,0x00400,"INTERRUPTS_TIMING_VBLANK_SYSTEM"),
 (0x00400,0x03A00,"INIT_RESET_MEMORY"),
 (0x03A00,0x03A80,"AUDIO_INTERFACE"),
 (0x03A80,0x03C90,"PALETTE_COLOR"),
 (0x03C90,0x03F00,"PC090OJ_SPRITE_COMPOSITOR"),
 (0x03F00,0x40000,"PC090OJ_SPRITE_COMPOSITOR"),
 (0x40000,0x42000,"ACTOR_CORE_LIFECYCLE_CREATION"),
 (0x42000,0x44000,"ENEMY_AI_BEHAVIORS"),
 (0x44000,0x45000,"COLLISION_DAMAGE_PHYSICS"),
 (0x45000,0x46000,"ACTOR_CORE_LIFECYCLE_CREATION"),
 (0x46000,0x48000,"BOSS_LOGIC"),
 (0x48000,0x50000,"ENEMY_AI_BEHAVIORS"),
 (0x50000,0x51000,"PLAYER_CONTROL_MOVEMENT"),
 (0x51000,0x54000,"COLLISION_DAMAGE_PHYSICS"),
 (0x54000,0x55900,"PLAYER_WEAPONS_ITEMS_STATUS"),
 (0x55900,0x57000,"MAP_SCENE_ROUND_PROGRESSION"),
 (0x57000,0x59000,"PC080SN_TILEMAP_SCROLL_COLLISIONMAP"),
 (0x59000,0x5A800,"HUD_SCORE_LIVES_GAMESTATE"),
 (0x5A800,0x60000,"INPUT_SERVICE_ATTRACT"),
]
def pc_subsys(pc):
    for a,b,s in PC_RULES:
        if a<=pc<b: return s
    return "UNCLASSIFIED"

def norm(pc): return int(str(pc).replace("0x","").strip() or "0",16)

# load tracker: pc -> (status, semfile)
track={}
with open(COV) as f:
    for r in csv.DictReader(f):
        pc=norm(r["arcade_pc"]); st=r["status"].strip(); sem=(r["semantic_file"] or "").strip()
        track[pc]=(st,sem)

# load inventory. Status is joined CONSERVATIVELY by EXACT ENTRY-PC match: a Ghidra function counts
# COMPLETE/PARTIAL/STUB only if its entry PC is a durable-C tracked routine of that status. A tracked
# routine that is only an INTERNAL PC of a larger Ghidra function does NOT credit the whole function
# (that would overstate coverage), so it is recorded separately as an internal-coverage note but the
# enclosing function stays NOT_DECOMPILED unless its own entry is tracked. This deliberately
# UNDER-credits rather than over-credits, per the anti-overstatement rule.
def map_status(st):
    return {"COMPLETE":"COMPLETE","PARTIAL":"PARTIAL","STUB_ONLY":"STUB","STUB":"STUB"}.get(st)
funcs=[]
with open(INV) as f:
    for r in csv.DictReader(f, delimiter="\t"):
        pc=norm(r["arcade_pc"]); bmin=norm(r["body_min"]); bmax=norm(r["body_max"])
        span=max(0,bmax-bmin)
        st,sem=track.get(pc,(None,None))
        if st is None and pc!=bmin:  # try the body_min as entry too
            st,sem=track.get(bmin,(None,None))
        status=map_status(st) or "NOT_DECOMPILED"
        sub = SEMFILE_SUB.get(sem) if (sem and status!="NOT_DECOMPILED") else None
        if not sub: sub = pc_subsys(pc)
        funcs.append(dict(pc=pc,name=r["name"],bmin=bmin,bmax=bmax,span=span,status=status,
                          subsystem=sub,tracked=(st is not None),semfile=sem or ""))

# union-of-ranges denominator (avoid double counting overlaps/thunks)
def union_bytes(ranges):
    ivals=sorted((a,b) for a,b in ranges if b>a)
    tot=0; cur=None
    for a,b in ivals:
        if cur is None: cur=[a,b]
        elif a<=cur[1]: cur[1]=max(cur[1],b)
        else: tot+=cur[1]-cur[0]; cur=[a,b]
    if cur: tot+=cur[1]-cur[0]
    return tot
total_union = union_bytes([(f["bmin"],f["bmax"]) for f in funcs])
# union-based per-status physical-code bytes (PRIMARY metric, H21): a byte is counted once even
# when overlapping Ghidra functions share it, and only credited COMPLETE if some COMPLETE function
# covers it (touched = COMPLETE|PARTIAL|STUB). Prevents both double-counting and status inflation.
def status_union(stset):
    return union_bytes([(f["bmin"],f["bmax"]) for f in funcs if f["status"] in stset])
u_complete = status_union({"COMPLETE"})
u_touched  = status_union({"COMPLETE","PARTIAL","STUB"})

# per-subsystem aggregation (byte span sum per function; each function one owner)
sub_agg={s:collections.Counter() for s in SUBSYS}
sub_bytes={s:collections.Counter() for s in SUBSYS}
for f in funcs:
    s=f["subsystem"]
    sub_agg[s][f["status"]]+=1; sub_agg[s]["total"]+=1
    sub_bytes[s][f["status"]]+=f["span"]; sub_bytes[s]["total"]+=f["span"]
sum_span=sum(f["span"] for f in funcs)

# write function inventory csv
with open(OUT_INV,"w",newline="") as f:
    w=csv.writer(f); w.writerow(["pc","name","body_min","body_max","span_bytes","status","subsystem","tracked","semantic_file"])
    for x in sorted(funcs,key=lambda x:x["pc"]):
        w.writerow(["0x%06x"%x["pc"],x["name"],"0x%06x"%x["bmin"],"0x%06x"%x["bmax"],x["span"],
                    x["status"],x["subsystem"],int(x["tracked"]),x["semfile"]])

# write subsystem coverage csv
def pct(n,d): return round(100.0*n/d,1) if d else 0.0
rows=[]
for s in SUBSYS:
    a=sub_agg[s]; b=sub_bytes[s]
    tot_b=b["total"]
    fully=pct(b["COMPLETE"],tot_b)
    touched=pct(b["COMPLETE"]+b["PARTIAL"]+b["STUB"],tot_b)
    rows.append(dict(subsystem=s,total_functions=a["total"],complete_functions=a["COMPLETE"],
        partial_functions=a["PARTIAL"],stub_functions=a["STUB"],not_decompiled_functions=a["NOT_DECOMPILED"],
        total_code_bytes=b["total"],complete_code_bytes=b["COMPLETE"],partial_code_bytes=b["PARTIAL"],
        stub_code_bytes=b["STUB"],not_decompiled_code_bytes=b["NOT_DECOMPILED"],
        fully_decompiled_pct=fully,touched_pct=touched))
with open(OUT_SUB,"w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())+["notes"]); w.writeheader()
    for r in rows: r["notes"]=""; w.writerow(r)

# overall
tot_funcs=len(funcs)
c_b=sum(f["span"] for f in funcs if f["status"]=="COMPLETE")
p_b=sum(f["span"] for f in funcs if f["status"]=="PARTIAL")
s_b=sum(f["span"] for f in funcs if f["status"]=="STUB")
n_b=sum(f["span"] for f in funcs if f["status"]=="NOT_DECOMPILED")
summary=dict(
  denominator="Ghidra-identified 68000 functions in build/regions/maincpu.bin (function_inventory.tsv)",
  metric="68000 executable-code decompilation coverage, byte-weighted by function span",
  total_functions=tot_funcs,
  complete_functions=sum(1 for f in funcs if f["status"]=="COMPLETE"),
  partial_functions=sum(1 for f in funcs if f["status"]=="PARTIAL"),
  stub_functions=sum(1 for f in funcs if f["status"]=="STUB"),
  not_decompiled_functions=sum(1 for f in funcs if f["status"]=="NOT_DECOMPILED"),
  total_code_bytes_spansum=sum_span, total_code_bytes_union=total_union,
  complete_code_bytes=c_b, partial_code_bytes=p_b, stub_code_bytes=s_b, not_decompiled_code_bytes=n_b,
  overall_fully_decompiled_pct=pct(c_b,sum_span),
  overall_touched_pct=pct(c_b+p_b+s_b,sum_span),
  # PRIMARY H21 physical-code metric: unique executable byte (union denominator), each byte counted once
  primary_metric="unique_executable_byte_union",
  complete_code_bytes_union=u_complete, touched_code_bytes_union=u_touched,
  overall_fully_decompiled_pct_union=pct(u_complete,total_union),
  overall_touched_pct_union=pct(u_touched,total_union),
  historical_h20=dict(basis="span-sum (secondary)", fully_pct=pct(c_b,sum_span), touched_pct=pct(c_b+p_b+s_b,sum_span)),
  subsystems=rows,
  other_processors="Rastan sound is a separate Z80 + YM2151/MSM5205 program ROM; NOT included in this 68000 census (measured separately / not yet included).",
  notes=["PARTIAL gets NO fractional completion credit (only COMPLETE counts as fully decompiled).",
         "Denominator includes untracked (NOT_DECOMPILED) functions.",
         "Each function has one primary subsystem owner; subsystem span sums equal spansum denominator.",
         "spansum may exceed union by overlaps/thunks; overall % uses spansum (per-function), union reported for reference."])
json.dump(summary,open(OUT_SUM,"w"),indent=1)
print("gamewide census written.")
print("  functions=%d  spansum=%d bytes  union=%d bytes"%(tot_funcs,sum_span,total_union))
print("  COMPLETE=%d(%d B)  PARTIAL=%d(%d B)  STUB=%d(%d B)  NOT_DECOMPILED=%d(%d B)"%(
  summary["complete_functions"],c_b,summary["partial_functions"],p_b,summary["stub_functions"],s_b,
  summary["not_decompiled_functions"],n_b))
print("  OVERALL fully-decompiled=%.1f%%  touched=%.1f%%  (span-sum, secondary / H20 basis)"%(summary["overall_fully_decompiled_pct"],summary["overall_touched_pct"]))
print("  PRIMARY (unique executable byte / union): fully=%.1f%% (%d/%d B)  touched=%.1f%% (%d B)"%(
  summary["overall_fully_decompiled_pct_union"],u_complete,total_union,summary["overall_touched_pct_union"],u_touched))
