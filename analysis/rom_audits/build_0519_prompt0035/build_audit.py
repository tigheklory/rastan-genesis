#!/usr/bin/env python3
from pathlib import Path
from collections import Counter, defaultdict
import csv, hashlib, json, os

PROJECT_ROOT = Path(__file__).resolve().parents[3]
# Set RASTAN_AUDIT_SOURCE_ROOT to an exact Build 0519 checkout when regenerating;
# the committed result files beside this script remain the durable audit evidence.
ROOT = Path(os.environ.get('RASTAN_AUDIT_SOURCE_ROOT', PROJECT_ROOT))
OUT = Path(__file__).resolve().parent
ROM = PROJECT_ROOT/'dist/rastan-direct/rastan_direct_video_test_build_0519.bin'
LIMIT = 4 * 1024 * 1024

def sha(b): return hashlib.sha256(b).hexdigest()

rows=[]
def add(name,start,size,category,owner,refs='',kind='measured',source='Build 0519 link map / ELF'):
    rows.append(dict(asset=name,rom_start=f'0x{start:06X}',rom_end=f'0x{start+size:06X}',bytes=size,
                     category=category,physical_owner=owner,logical_references=refs,measurement=kind,source=source))

# Exact non-overlapping physical ownership from the SHA-identical map-only relink.
add('Genesis header/bootstrap',0x000000,0x372,'code','shared frontend/runtime')
add('preserved-low zero fill',0x000372,0x117e-0x372,'padding','linker/postpatch')
add('retained relocated arcade maincpu',0x00117e,0x60058-0x117e,'retained_arcade','all rounds','R1-S1..R6-S3')
add('low-ROM gap',0x60058,0x70000-0x60058,'padding','linker')
add('native wrapper executable',0x70000,0x75ec0-0x70000,'code','shared native hardware services','all scenes/front-end')

cur=0x75ec0
for a,n,c,o,r in [
 ('best-5 number descriptors',104,'maps','front-end','high-score'),('best-5 name descriptors',48,'maps','front-end','high-score'),
 ('Plane-A scene-fill maps',49336,'maps','R1/R2 scenes','R1-S1..R2-S3'),
 ('Plane-A deduplicated row maps',218920,'maps','R1/R2 records','R1-S1..R2-S3'),
 ('Plane-B scene-fill maps',24760,'maps','R1/R2 scenes','R1-S1..R2-S3'),
 ('Plane-A pan-row maps',32952,'maps','R1/R2 vertical records','R1-S2,R2-S2'),
 ('authored descriptor visuals',340096,'maps','authored R1 contexts','R1-S1,R1-S2'),
 ('Plane-A boundary packages',86312,'maps','R1/R2 residency','R1-S1..R2-S3')]:
 add(a,cur,n,c,o,r);cur+=n
add('palette route + authored CRAM assets',cur,574,'palettes','authored R1/front-end','R1-S1,R1-S2');cur+=574
for a,n,c,o,r in [('title Plane-B map',4096,'frontend','title','title'),('title Plane-A map',4096,'frontend','title','title'),('title invincible Plane-A map',4096,'frontend','title variant','title'),('title palette',32,'palettes','title','title'),('title patterns',7346,'graphics','title','title')]: add(a,cur,n,c,o,r);cur+=n
for a,n,c,o,r in [('HUD patterns',2722,'graphics','shared HUD','all gameplay/front-end'),('HUD static SAT',640,'frontend','shared HUD','all gameplay/front-end'),('HUD dynamic records',1672,'frontend','shared HUD','all gameplay/front-end')]: add(a,cur,n,c,o,r);cur+=n
for a,n,c,o,r in [('item logical map',8192,'frontend','item attract','item attract'),('item initial rows',4096,'frontend','item attract','item attract'),('item Plane patterns',920,'graphics','item attract','item attract'),('item icon patterns',2722,'graphics','item attract','item attract'),('item icon records',160,'frontend','item attract','item attract')]: add(a,cur,n,c,o,r);cur+=n
for a,n,c,o,r in [('PC090OJ palette-line LUT',512,'palettes','shared sprites','all sprite scenes'),('PC090OJ variant group table',8192,'sprite_metadata','shared sprites','all sprite scenes'),('PC090OJ variant bank table',128,'sprite_metadata','shared sprites','all sprite scenes'),('PC090OJ variant source table',246,'sprite_metadata','shared sprites','all sprite scenes')]: add(a,cur,n,c,o,r);cur+=n
for a,n,c,o,r in [
 ('PC090OJ base pattern corpus',524288,'graphics','shared sprites','R1-S1..R6-S3'),('PC090OJ appended palette variants',15744,'graphics','authored sprite variants','R1 actors/effects'),
 ('PC090OJ frame table',148060,'sprite_metadata','shared sprites','R1-S1..R6-S3'),('player piece table',19428,'sprite_metadata','player','R1-S1..R6-S3'),
 ('player frame index',14400,'sprite_metadata','player','R1-S1..R6-S3'),('secondary frame index',4992,'sprite_metadata','player/weapon','R1-S1..R6-S3'),
 ('generic frame index',304,'sprite_metadata','actors','R1-S1..R6-S3'),('generic piece table',1422,'sprite_metadata','actors','R1-S1..R6-S3'),
 ('universal frame index',15360,'sprite_metadata','actors','R1-S1..R6-S3'),('special frame index',4092,'sprite_metadata','actors','R1-S1..R6-S3'),
 ('death frame index',480,'sprite_metadata','actors/effects','R1-S1..R6-S3'),('death piece table',1074,'sprite_metadata','actors/effects','R1-S1..R6-S3'),
 ('generic base LUT',4096,'sprite_metadata','actors','R1-S1..R6-S3'),('generic usage table',50,'sprite_metadata','actors','R1-S1..R6-S3'),
 ('frame residency metadata',23332,'sprite_metadata','shared sprites','R1-S1..R6-S3'),('semantic glyph profile patterns',3968,'graphics','HUD/GAME OVER','front-end/gameplay'),
 ('sprite slot LUT',256,'sprite_metadata','shared sprites','all sprite scenes'),('blank-code bitset',512,'sprite_metadata','shared sprites','all sprite scenes'),
 ('opaque bounding boxes',65536,'sprite_metadata','shared sprites','all sprite scenes')]: add(a,cur,n,c,o,r);cur+=n
add('alignment before scene-load rodata',cur,4,'padding','linker');cur+=4
for a,n,c,o,r in [
 ('PC080SN tile-to-VRAM LUT',32768,'maps','shared planes','R1/R2 native'),('front-end base palette',128,'palettes','front-end','front-end'),('PC080SN attr LUT',64,'maps','shared planes','all planes'),
 ('native metatile dense index',392702,'maps','all-round arcade descriptors','all rounds'),('native metatile records',302912,'maps','all-round arcade descriptors','all rounds'),
 ('Plane-B visual records',2802,'maps','all-round arcade descriptors','all rounds'),('pattern alignment',16,'padding','linker','all rounds'),
 ('PC080SN native pattern corpus',524288,'graphics','shared planes','R1-S1..R6-S3'),
 ('title preload list',3382,'maps','title','title'),('gameplay preload list',4010,'maps','R1 gameplay','R1'),('gameplay cave preload list',2434,'maps','R1-S1','R1-S1'),
 ('stage1 cave-S4 preload',4494,'maps','R1-S1','R1-S1'),('stage1 cave-S5 preload',4010,'maps','R1-S1','R1-S1'),('stage1 cave-S6 preload',4614,'maps','R1-S1','R1-S1'),
 ('stage1 segment-1 preload',4154,'maps','R1-S1','R1-S1'),('stage1 segment-2 preload',4602,'maps','R1-S1','R1-S1'),('end-round preload',4270,'maps','boss/end-round','R1-S3'),
 ('scene A0 ranges',24,'maps','shared scene loader','all rounds')]: add(a,cur,n,c,o,r);cur+=n
add('Z80 sound driver',cur,564,'audio','shared audio','all game');cur+=564
add('audio catalog/dispatch',cur,256,'audio','shared audio','all game');cur+=256
add('wrapper terminal alignment',cur,2,'padding','linker');cur+=2
assert cur==0x344650,hex(cur)
add('pre-audio 0x8000 alignment',cur,0x348000-cur,'padding','linker')
add('nine native audio streams',0x348000,0x94dca,'audio','shared complete soundtrack','all rounds/front-end')
add('pre-crash 0x1000 alignment',0x3dcdca,0x3dd000-0x3dcdca,'padding','linker')
add('crash/diagnostic executable',0x3dd000,0xeb8,'code','shared diagnostics','all builds')

assert sum(r['bytes'] for r in rows)==ROM.stat().st_size, (sum(r['bytes'] for r in rows),ROM.stat().st_size)
with (OUT/'rom_assets.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)

# Pattern stores and verified exact duplicates.
pc080=(ROOT/'build/pc080sn_boundary/native_pattern_region.bin').read_bytes()
pc090=(ROOT/'build/regions/pc090oj_editor.bin').read_bytes()
def units(data,n): return [data[i:i+n] for i in range(0,len(data),n)]
def stat(blobs,unit):
    c=Counter(map(sha,blobs)); z=sha(bytes(unit));
    return {'stored_units':len(blobs),'unique_units':len(c),'stored_bytes':len(blobs)*unit,
            'unique_bytes':len(c)*unit,'raw_duplicate_bytes':(len(blobs)-len(c))*unit,
            'zero_units':c.get(z,0),'zero_excess_bytes':max(0,c.get(z,0)-1)*unit}
dup={
 'pc080_tiles_32':stat(units(pc080,32),32),
 'pc090_cells_128':stat(units(pc090,128),128),
 'pc090_subtiles_32':stat(units(pc090,32),32),
}

# Slot+pattern record formats: 2-byte slot + 32-byte tile, terminated by FFFF.
record_files=['native_title_patterns.bin','native_hud_patterns.bin','native_item_plane_patterns.bin','native_item_icon_patterns.bin']
aux=[]
for fn in record_files:
    b=(ROOT/'build/rastan-direct'/fn).read_bytes(); assert b[-2:]==b'\xff\xff'
    pats=[b[i+2:i+34] for i in range(0,len(b)-2,34)]; aux += [(fn,p) for p in pats]
pc080set=set(units(pc080,32)); pc090set=set(units(pc090,32))
cross=Counter()
cross_aux_unique_bytes=0
for fn,p in aux:
    in80=p in pc080set; in90=p in pc090set
    if in80: cross[(fn,'PC080 corpus')]+=32
    if in90: cross[(fn,'PC090 corpus')]+=32
    if in80 or in90: cross_aux_unique_bytes+=32
semantic=(ROOT/'build/pc090oj_semantic_profile_genesis.bin').read_bytes()
semantic_cells=units(semantic,128); pc090cells=set(units(pc090,128))
cross[('semantic glyph profile','PC090 corpus')]=sum(128 for x in semantic_cells if x in pc090cells)

# Map rows: 184-byte record tables followed by 128-byte rows.
map_names=['scene_fill_maps.bin','plane_b_scene_fill_maps.bin','pan_row_maps.bin']
map_rows=[]
for fn in map_names:
    b=(ROOT/'build/pc080sn_boundary'/fn).read_bytes(); tail=b[184:]; assert len(tail)%128==0
    map_rows += [(fn,x) for x in units(tail,128)]
allrow=Counter(sha(x) for _,x in map_rows)
map_stored=len(map_rows)*128; map_unique=len(allrow)*128; map_index=len(map_rows)*2
dup['map_rows_128']={'stored_units':len(map_rows),'unique_units':len(allrow),'stored_bytes':map_stored,
                     'unique_bytes':map_unique,'raw_duplicate_bytes':map_stored-map_unique,
                     'u16_index_bytes':map_index,'net_saving_with_index':map_stored-map_unique-map_index}

# Authored descriptor structure.
adb=(ROOT/'build/pc080sn_boundary/authored_descriptor_visuals.bin').read_bytes(); idxbytes=284672; n=35584
ctx=[]
for c in range(2):
    vals=[int.from_bytes(adb[(c*n+i)*4:(c*n+i+1)*4],'big') for i in range(n)]
    q=Counter(vals);ctx.append({'entries':n,'unique_records':len(q),'repeated_pointer_bytes':(n-len(q))*4,'top_pointer_repeat':q.most_common(1)[0][1]})
descriptor={'span_entries_per_context':n,'contexts':2,'dense_index_bytes':idxbytes,'payload_bytes':55424,'unique_payload_records':866,
            'r1s1_live_entries':4096,'r1s2_live_entries':1536,'live_entries_total':5632,
            'compact_u32_band_index_bytes':5632*4,'compact_u16_record_id_bytes':5632*2,
            'saving_u32_band_index':idxbytes-5632*4,'saving_u16_record_ids':idxbytes-5632*2,
            'contexts_detail':ctx}

# Confirmed and opportunity savings; do not combine incompatible alternatives.
cross_total=cross_aux_unique_bytes+cross[('semantic glyph profile','PC090 corpus')]
confirmed={'cross_library_exact_pattern_copies':cross_total,
           'map_row_dedup_net':dup['map_rows_128']['net_saving_with_index'],
           'descriptor_dense_to_u32_band_index':descriptor['saving_u32_band_index'],
           'descriptor_dense_to_u16_record_ids':descriptor['saving_u16_record_ids']}
json.dump({'pattern_stats':dup,'cross_library':[{ 'asset':k[0],'duplicates_with':k[1],'bytes':v} for k,v in sorted(cross.items())],
           'authored_descriptor':descriptor,'savings':confirmed},(OUT/'duplication_analysis.json').open('w'),indent=2)

# Logical 18-subround inventory and projection. Plane patterns and complete sprite corpora are already shared in ROM.
scene_counts={1:(16,6,1),2:(16,6,1),3:(16,6,1),4:(16,6,1),5:(16,6,1),6:(16,6,1)}
rosters={
1:'Lizardman, Chimera, Four-Armed Insect, Valkyrie; special Demon/bats/effects where map-triggered; R1 boss',
2:'R1 common field set + families base 0x0420,0x0400; map-triggered specials unresolved by subround; R2 boss',
3:'R2 field set + base 0x03B3; map-triggered specials unresolved by subround; R3 boss',
4:'bases 0x004B,0x00D0,0x02E8,0x03B3,0x06E2,0x0889,0x0400; map-triggered specials unresolved; R4 boss',
5:'bases 0x004B,0x00D0,0x02E8,0x0420,0x03B3,0x043A,0x0889,0x0400; map-triggered specials unresolved; R5 boss',
6:'bases 0x004B,0x00D0,0x02E8,0x0420,0x01CB,0x03B3,0x0889,0x0400; map-triggered specials unresolved; R6 boss'}
inv=[]
for rnd in range(1,7):
  for sub,count in enumerate(scene_counts[rnd],1):
    implemented = rnd<=2
    palette = ('authored CRAM/index context' if (rnd,sub) in [(1,1),(1,2)] else 'missing scene-specific authored palette')
    exclusive=12288 if implemented else 0 # one A 8K + one B 4K fill map
    if (rnd,sub) in [(1,1),(1,2)]: exclusive += 142336+96
    missing=0
    if not implemented:
      # current-design central: scene maps + proportional row/package data + one dense authored context.
      missing=12288 + round(218920/46*count) + round(86312/46*count) + 170048
    elif palette.startswith('missing'):
      missing=170048
    inv.append({'subround':f'R{rnd}-S{sub}','round':rnd,'records':count,'native_scene_status':'native_converted' if implemented else 'native_not_converted',
      'existing_shared_pattern_bytes':524288+540032,'existing_allocated_bytes_proxy':exclusive,'estimated_missing_bytes_current_design':missing,
      'plane_patterns':'complete 512 KiB all-code corpus already linked','sprite_patterns':'complete 4,096-cell base corpus + 123 variants already linked; gamewide native frame tables present',
      'maps_descriptors':'R1/R2 native maps present' if implemented else 'native scene/row/package maps absent',
      'palette':palette,'actors':rosters[rnd] if sub<3 else f'round {rnd} boss base 0x033E, round-specific variant/palette; shared player/HUD/effects',
      'actor_gap':'special/map-triggered actor split by S1 versus S2 is UNKNOWN; no fabricated allocation',
      'vram':'scene-scoped residency required; entire ROM library is not simultaneous'})
with (OUT/'subround_inventory.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=inv[0].keys());w.writeheader();w.writerows(inv)

# Three projection scenarios with explicit uncertainty.
current_add=sum(x['estimated_missing_bytes_current_design'] for x in inv)
# Add later-round preload lists, sprite palette variants, and bounded code growth.
current_low=ROM.stat().st_size+current_add+60000
current_central=ROM.stat().st_size+current_add+140000
current_high=ROM.stat().st_size+current_add+300000
current=(current_low,current_central,current_high)
# Across all 18 contexts, each dense 35,584-entry u32 index (142,336 bytes)
# can be reduced only to that subround's live record band, not by the current
# two-context aggregate saving.  Six rounds each have 4,096/1,536/256 live entries.
all_context_dense_index=18*142336
all_context_u32_band_index=6*(4096+1536+256)*4
all_context_u32_saving=all_context_dense_index-all_context_u32_band_index
conservative=tuple(x-all_context_u32_saving-dup['map_rows_128']['net_saving_with_index']-cross_total for x in current)
# Shared library: no per-scene dense authored indexes; compact maps, palettes/load lists only; compact exact pattern stores.
pattern_cell_saving=dup['pc080_tiles_32']['raw_duplicate_bytes']+dup['pc090_cells_128']['raw_duplicate_bytes']
shared_low=ROM.stat().st_size-descriptor['saving_u16_record_ids']-dup['map_rows_128']['net_saving_with_index']-cross_total-pattern_cell_saving+280000
shared_central=shared_low+220000
shared_high=shared_central+350000
shared=(shared_low,shared_central,shared_high)
projection={'current_design':current,'conservative_dedup':conservative,'shared_library':shared,
            'current_missing_scene_sum':current_add,'pattern_cell_saving_used_in_shared':pattern_cell_saving,
            'all_18_context_dense_index_bytes':all_context_dense_index,
            'all_18_context_u32_band_index_bytes':all_context_u32_band_index,
            'all_18_context_u32_band_saving':all_context_u32_saving,
            'notes':['ranges include unresolved later-round package/preload/variant demand','audio and base PC080/PC090 corpora are already complete and are not multiplied']}
json.dump(projection,(OUT/'projection.json').open('w'),indent=2)

with (OUT/'duplication_opportunities.csv').open('w',newline='') as f:
    fields=['opportunity','measured_bytes','classification','can_add_with_others','requirements']
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows([
      {'opportunity':'exact cross-library pattern copies','measured_bytes':cross_total,'classification':'exact duplicate','can_add_with_others':'yes, after validating consumers','requirements':'reuse canonical pattern slots'},
      {'opportunity':'combined repeated map rows, net of u16 index','measured_bytes':dup['map_rows_128']['net_saving_with_index'],'classification':'exact duplicate','can_add_with_others':'yes','requirements':'shared row dictionary + per-row IDs'},
      {'opportunity':'current authored descriptor dense index to u32 live bands','measured_bytes':descriptor['saving_u32_band_index'],'classification':'proven structural','can_add_with_others':'alternative to u16 row below','requirements':'native lookup shape change'},
      {'opportunity':'current authored descriptor dense index to u16 record IDs','measured_bytes':descriptor['saving_u16_record_ids'],'classification':'proven structural','can_add_with_others':'alternative to u32 row above','requirements':'native lookup + payload-base resolution'},
      {'opportunity':'PC080 exact 32-byte tile identities','measured_bytes':dup['pc080_tiles_32']['raw_duplicate_bytes'],'classification':'theoretical identity-remap ceiling','can_add_with_others':'scenario only','requirements':'tile-code indirection/remap; not direct deletion'},
      {'opportunity':'PC090 exact 128-byte cell identities','measured_bytes':dup['pc090_cells_128']['raw_duplicate_bytes'],'classification':'theoretical identity-remap ceiling','can_add_with_others':'scenario only','requirements':'sprite-code indirection/remap; not direct deletion'},
    ])
with (OUT/'projection_scenarios.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['scenario','low_bytes','central_bytes','high_bytes','central_vs_4MiB_bytes'])
    for name,rng in [('current_design',current),('conservative_dedup',conservative),('shared_library',shared)]:
        w.writerow([name,*rng,rng[1]-LIMIT])

# Charts
os.environ.setdefault('MPLCONFIGDIR',str(OUT/'.mplconfig'))
import matplotlib.pyplot as plt
plt.rcParams.update({'figure.dpi':150,'font.size':9})
cats=Counter();
for r in rows: cats[r['category']]+=r['bytes']
order=['retained_arcade','code','graphics','maps','sprite_metadata','frontend','audio','palettes','padding']
colors=['#6b7280','#2563eb','#16a34a','#f59e0b','#7c3aed','#0ea5e9','#dc2626','#ec4899','#cbd5e1']
fig,ax=plt.subplots(figsize=(12,3.4));left=0
for k,col in zip(order,colors): ax.barh(['Build 0519'],[cats[k]],left=left,label=f'{k}: {cats[k]:,}',color=col);left+=cats[k]
ax.axvline(LIMIT,color='black',ls='--',lw=2,label='4 MiB limit');ax.set_xlabel('ROM bytes');ax.set_title('Chart A — Build 0519 exact ROM ownership');ax.legend(ncol=3,fontsize=7,loc='upper center',bbox_to_anchor=(.5,-.25));fig.tight_layout();fig.savefig(OUT/'chart_A_rom_usage.png',bbox_inches='tight');plt.close(fig)

labels=[x['subround'] for x in inv]; exc=[x['existing_allocated_bytes_proxy'] for x in inv]; sharedv=[x['existing_shared_pattern_bytes'] for x in inv]; miss=[x['estimated_missing_bytes_current_design'] for x in inv]
fig,ax=plt.subplots(figsize=(14,6));xx=range(18);ax.bar(xx,exc,label='existing allocation proxy',color='#2563eb');ax.bar(xx,sharedv,bottom=exc,label='shared dependency (reference only)',color='#94a3b8',alpha=.45);ax.bar(xx,miss,bottom=[a+b for a,b in zip(exc,sharedv)],label='estimated missing',color='#f59e0b',hatch='//');ax.set_xticks(list(xx),labels,rotation=45);ax.set_ylabel('bytes (shared bars are not additive ROM ownership)');ax.set_title('Chart B — Graphics/maps by Round and Subround');ax.legend();fig.tight_layout();fig.savefig(OUT/'chart_B_subrounds.png');plt.close(fig)

dup_labels=['Exact cross-library\npatterns','Repeated map rows\n(net)','Dense descriptor\nindex (u32 bands)','PC080 exact tile\nrepeats (theoretical)','PC090 exact cell\nrepeats (theoretical)']
dup_vals=[cross_total,dup['map_rows_128']['net_saving_with_index'],descriptor['saving_u32_band_index'],dup['pc080_tiles_32']['raw_duplicate_bytes'],dup['pc090_cells_128']['raw_duplicate_bytes']]
fig,ax=plt.subplots(figsize=(10,5));bars=ax.bar(dup_labels,dup_vals,color=['#16a34a','#16a34a','#2563eb','#94a3b8','#94a3b8']);ax.set_ylabel('potential bytes');ax.set_title('Chart C — Duplication and recoverable-space opportunities');
for b,v in zip(bars,dup_vals): ax.text(b.get_x()+b.get_width()/2,v,f'{v:,}',ha='center',va='bottom',fontsize=8)
fig.text(.5,.01,'Green = exact low-risk data dedup; blue = proven compact-index opportunity; gray = theoretical identity remap',ha='center',fontsize=8);fig.tight_layout(rect=(0,.05,1,1));fig.savefig(OUT/'chart_C_duplication.png');plt.close(fig)

fig,ax=plt.subplots(figsize=(9,5));names=['Current behavior','Conservative dedup','Shared library'];vals=[current[1],conservative[1],shared[1]];err=[[v-r[0] for v,r in zip(vals,[current,conservative,shared])],[r[2]-v for v,r in zip(vals,[current,conservative,shared])]]
ax.bar(names,vals,yerr=err,capsize=6,color=['#dc2626','#f59e0b','#16a34a']);ax.axhline(LIMIT,color='black',ls='--',label='4 MiB');ax.set_ylabel('projected final ROM bytes');ax.set_title('Chart D — Six-round projection (low / central / high)');ax.legend();fig.tight_layout();fig.savefig(OUT/'chart_D_projection.png');plt.close(fig)

# Current-behavior central cumulative: Build 0519 already owns the R1/R2 map
# packages, but still lacks R1-S3 and all three R2 authored contexts.
cum=[]; running=ROM.stat().st_size
for rnd in range(1,7):
    running += sum(x['estimated_missing_bytes_current_design'] for x in inv if x['round']==rnd)
    if rnd>=3: running += 35000 # central common future allowance: 140 KiB / four later rounds
    cum.append(running)
assert cum[-1]==current_central,(cum[-1],current_central)
fig,ax=plt.subplots(figsize=(9,5));ax.plot(range(1,7),cum,marker='o',lw=2,color='#dc2626');ax.axhline(LIMIT,color='black',ls='--',label='4 MiB');ax.fill_between(range(1,7),[v-(i*30000) for i,v in enumerate(cum)],[v+(i*60000) for i,v in enumerate(cum)],alpha=.2,color='#f59e0b');ax.set_xticks(range(1,7),[f'Round {i}' for i in range(1,7)]);ax.set_ylabel('cumulative ROM bytes');ax.set_title('Chart E — Current-architecture cumulative growth (shared assets counted once)');ax.legend();fig.tight_layout();fig.savefig(OUT/'chart_E_cumulative.png');plt.close(fig)

summary={'rom_size':ROM.stat().st_size,'rom_sha256':sha(ROM.read_bytes()),'limit':LIMIT,'remaining':LIMIT-ROM.stat().st_size,
         'category_totals':dict(cats),'descriptor':descriptor,'duplication':dup,'cross_library_bytes':cross_total,'projection':projection}
json.dump(summary,(OUT/'audit_summary.json').open('w'),indent=2)
print(json.dumps(summary,indent=2))
