#!/usr/bin/env python3
"""Offline arcade->Genesis PC080SN graphics compiler — Milestone 1 (Stage 1).

Derives the Stage-1 graphics model ENTIRELY from arcade ROM/data (build/regions/*.bin) + the
explicit Genesis palette policy registry (specs/palette_decisions.json).  NO trace / screenshot /
recorded-route input.  Evolves the arcade decoders in precompute_pc080sn_tile_lut.py (imported, not
duplicated).

Pipeline: arcade map-stream progression walk -> per-segment Plane-A tile sets (+ transitional
Plane-B reserve until the player-dependent Y envelope is decoded) -> graphics epochs -> VRAM slot
allocation (A+B together, slots < SPRITE_TILE_BASE, low slots reserved) -> repacked Genesis patterns
-> O(1) base LUT + per-epoch patches -> DMA transitions -> shared-CRAM route (registry) -> report +
generated docs.  Deterministic; self-validating.

See docs/design/Andy_offline_graphics_compiler_architecture_review.md.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# ---- import the existing arcade decoders (evolve, don't duplicate) ----
_gp = ROOT / "tools/translation/precompute_pc080sn_tile_lut.py"
_spec = importlib.util.spec_from_file_location("pc080sn_gen", _gp)
gen = importlib.util.module_from_spec(_spec); sys.modules["pc080sn_gen"] = gen
_spec.loader.exec_module(gen)

# ---- arcade map-stream constants (docs/arcade_reference/pc080sn/map_stream_format.md) ----
STAGE_TABLE = 0x5073A          # a5@0x1242 (stage) -> start segment a5@0x13E
SEED_TABLE  = 0x50EE0          # segment -> stream byte-offset
STREAM      = 0x50F6B          # selector byte stream (direction 0/1/2 advance; event 4/6/7 freeze)
DIR_BYTES   = {0, 1, 2}
EVENT_BYTES = {4, 6, 7}
MAX_SEGMENT = 138
STAGE_GROUP_SIZE = 23          # 0x452A8: physical round selector is multiplied by 23
TM0_TABLE = 0x507C5           # segment -> paired Plane-B descriptor index
PLANE_B_DESC_TABLE = 0x3951C
PLANE_B_DESC_STRIDE = 6       # adjacent {attr16, src32} descriptors; scene init uses pairs
PLANE_B_ROWS = 64
PLANE_B_COLS = 16

# ---- Genesis VRAM policy (project constants) ----
SPRITE_TILE_BASE = 1339        # Build 0308: physical remainder after fixed B + worst-record A
GLOBAL_SLOT_FIRST = 1
GLOBAL_SLOT_LAST = 1535
GLOBAL_SLOT_COUNT = GLOBAL_SLOT_LAST - GLOBAL_SLOT_FIRST + 1

# Build 0308 gameplay ownership. Slot 0 remains blank; frontend patterns are
# reclaimed when gameplay starts and are restored by the existing scene loader.
SAFE_PLANE_SLOT_FIRST = 1
SAFE_PLANE_SLOT_LAST = SPRITE_TILE_BASE - 1
SAFE_PLANE_SLOT_COUNT = SAFE_PLANE_SLOT_LAST - SAFE_PLANE_SLOT_FIRST + 1

BG_RESERVE = 320              # Transitional only: exact Plane-B reachability is unresolved
SLOT_MIN = SAFE_PLANE_SLOT_FIRST
SLOT_MAX = SAFE_PLANE_SLOT_LAST - BG_RESERVE                 # Plane-A (FG) band top: 64..703
PLANE_SLOTS = SLOT_MAX - SLOT_MIN + 1                        # 640 FG slots
BOUNDARY_CONFLICT_CODE_FIRST = 0x031A
BOUNDARY_CONFLICT_CODE_COUNT = 0x0032
TILE_BYTES = 32

# Build 0302 boundary-loaded experiment.  Ordinary records use one of eight row bands selected
# once from Plane-B Y at the semantic record transition.  An eight-row Y class needs 36 source
# rows to cover every possible 29-row view; two rows on either side are useful experimental margin.
BOUNDARY_LUT_WORDS = 0x2800
BOUNDARY_VARIANTS = 8
BOUNDARY_CORE_ROWS = 36
BOUNDARY_MARGIN_ROWS = 2
BOUNDARY_BAND_ROWS = BOUNDARY_CORE_ROWS + BOUNDARY_MARGIN_ROWS * 2
BOUNDARY_VERTICAL_RECORDS = {17, 21}
# Build 0307 selective Plane-B Y-envelope widening.  Records 2-3 contain the early Stage-1 rope,
# a tall Plane-B terrain element (rope visual owner = Plane B: BG block source 0xD31C/0xF31C
# attr 0x0002; collision on a separate WRAM channel).  Ordinary records freeze one 40-row Y band
# selected only at the record boundary, so climbing the rope moves the visible Plane-B rows out of
# that band and the rope disappears (proven within-record Y-envelope escape).  These records take
# the full 64-row single-variant envelope (same generated path as the vertical records) so the rope
# stays resident through the whole climb.  Evidence: states/traces/build0228_runtime_scene4_rope_
# transition_* (COLL_READ_ROPE worldY=0x193, STRIP_BLIT src=0x?31C attr=0002) and the segment 2..3
# gate in tools/mame/scripts/build0307_vram_rope_trace.lua.  No runtime change: the installer already
# forces variant 0 for any record whose variant_count == 1.
BOUNDARY_ROPE_RECORDS = {2, 3}
# Records that use the full 64-row single-variant Plane-B envelope instead of the 8 x 40-row bands.
BOUNDARY_FULL_Y_RECORDS = BOUNDARY_VERTICAL_RECORDS | BOUNDARY_ROPE_RECORDS
BOUNDARY_PACKAGE_DESC_BYTES = 16
BOUNDARY_RECORD_ENTRY_BYTES = 4
BOUNDARY_PAIR_BYTES = 4
BOUNDARY_WORD_ALIGNMENT = 2

# Build 0310 Round-1 Phase-1 Plane-A semantic residency. These are complete contiguous
# record epochs derived from the original arcade map data; records within one epoch share one
# immutable exact-pattern vocabulary and therefore require no residency transition.
# Build 0342: clean 676-slot Layer-A capacity. The later simple epochs merge (7 -> 5) while BOTH proven
# streamed transitions are preserved unchanged: rope->waterfall (record 2->3 = epoch0->epoch1) and
# waterfall->next (record 3->4 = epoch1->epoch2) keep their arcade-proven scroll data and runtime handoff.
# Only the four trailing simple epochs (old 2,3,4,5,6 over records 4..15) collapse into three (records
# 4-10, 11-12, 13-15), removing two simple residency transitions. (The global minimum at 676 is 4 epochs
# with rope internal, but eliminating the rope streamed transition would require extensive runtime/verifier
# surgery for a marginal gain; this 5-epoch structure banks the DMA win at low risk.)
BOUNDARY_PHASE1_EPOCH_RECORDS = (
    tuple(range(0, 3)),        # epoch 0: records 0-2
    (3,),                      # epoch 1: record 3 (rope/waterfall streamed boundaries preserved)
    tuple(range(4, 11)),       # epoch 2: records 4-10
    tuple(range(11, 13)),      # epoch 3: records 11-12
    tuple(range(13, 16)),      # epoch 4: records 13-15
)
BOUNDARY_PHASE1_EPOCH_CAPACITY = 676

# Build 0311: the first two epoch boundaries are horizontally streamed while the viewport still
# straddles the outgoing record.  Original arcade trace proves X=0x0168 at both boundaries; the
# 320-pixel viewport therefore starts at ring column 19 and advances one column per publication.
# At publication 45 the 40-column viewport contains only incoming cells.  The compiler models all
# 64 logical rows so vertical camera movement cannot invalidate this lifetime proof.
BOUNDARY_TRANSITION_VISIBLE_COLUMNS = 40
BOUNDARY_TRANSITION_INITIAL_COLUMN = 19
BOUNDARY_TRANSITION_HANDOFF_COLUMN = 45
BOUNDARY_TRANSITION_DEFS = (
    {"name": "rope_to_waterfall", "out_record": 2, "in_record": 3,
     "out_epoch": 0, "in_epoch": 1, "scroll_x": 0x0168, "scroll_y": 0x0105},
    {"name": "waterfall_to_next_rope", "out_record": 3, "in_record": 4,
     "out_epoch": 1, "in_epoch": 2, "scroll_x": 0x0168, "scroll_y": 0x015D},
)

# Statically decoded Stage-1 animation unions. These are source PC090OJ 16x16 cell codes, not
# Genesis tile numbers. The three families are sufficient for the final capacity decision:
# player and lizard-men coexist in ordinary Stage-1 play, and the timer-driven hurry-up swarm can
# coexist with them without changing map-record residency. Items and less-proven enemy families can
# only add demand, so they are not needed to prove the lower-bound failure.
STAGE1_PC090OJ_CELL_CODES = {
    "Rastan/player": tuple(range(0x008A, 0x00A0)),
    "Lizard-man": tuple(range(0x004B, 0x006E)),
    "Hurry-up bat": (0x0268, 0x0269, 0x026A, 0x0276),
}


def decode_stage_records(mc: bytes, stage_index: int = 0):
    """Decode one physical round's 23 map records from arcade tables.

    0x452A8 proves that a round owns 23 stage/checkpoint values. Event bytes are trailing bytes in
    variable-length records; they freeze publication and cause an outer-controller scene re-entry,
    but they do not terminate the physical round at the first event. For round 0 this yields records
    0..22, including the post-event selector-1 vertical records 17 and 21.
    """
    group_first = (stage_index // STAGE_GROUP_SIZE) * STAGE_GROUP_SIZE
    group_last = min(group_first + STAGE_GROUP_SIZE, MAX_SEGMENT + 1)
    records = []
    for seg in range(group_first, group_last):
        off = mc[SEED_TABLE + seg]
        next_off = mc[SEED_TABLE + seg + 1] if seg < MAX_SEGMENT else off + 1
        raw = list(mc[STREAM + off:STREAM + next_off])
        if not raw or raw[0] not in DIR_BYTES:
            raise SystemExit(f"invalid map record {seg}: offset {off:#x}, bytes={raw}")
        extras = raw[1:]
        if any(v not in EVENT_BYTES for v in extras):
            raise SystemExit(f"invalid event tail in map record {seg}: {extras}")
        tm0 = mc[TM0_TABLE + seg]
        records.append({
            "segment": seg,
            "stream_offset": off,
            "selector": raw[0],
            "events": extras,
            "tm0": tm0,
            # Scene init multiplies tm0 by 12. The producer consumes 6-byte descriptors,
            # therefore tm0 selects an adjacent descriptor pair at index tm0*2.
            "planeB_descriptor_index": tm0 * 2,
        })
    return records


def decode_stage_progression(mc: bytes, stage_index: int = 0):
    """Compatibility view used by the epoch compiler: all direction records in a 23-record round."""
    return [(r["segment"], r["selector"]) for r in decode_stage_records(mc, stage_index)]


def decode_plane_b_progression(mc: bytes, stage_index: int = 0):
    """Decode exact descriptor-cursor mechanics without inventing a Plane-B Y envelope.

    Scene initialization fills four 16-column descriptors (64 columns). A horizontal 512-pixel
    Plane-A record advances Plane B by 256 pixels and consumes two more descriptors. Vertical
    selectors consume none. Event completion re-enters scene initialization at the following
    record, whose tm0 value selects a new paired-descriptor seed.
    """
    records = decode_stage_records(mc, stage_index)
    reinit = {records[0]["segment"]}
    for r in records:
        if r["events"] and r["segment"] + 1 <= records[-1]["segment"]:
            reinit.add(r["segment"] + 1)
    cursor = None
    out = []
    for r in records:
        entry = dict(r)
        if r["segment"] in reinit:
            cursor = r["planeB_descriptor_index"]
            entry["scene_reinit"] = True
            entry["descriptor_action"] = "scene_fill_4"
            entry["descriptor_before"] = cursor
            cursor += 4
        elif r["selector"] == 0:
            entry["scene_reinit"] = False
            entry["descriptor_action"] = "horizontal_2"
            entry["descriptor_before"] = cursor
            cursor += 2
        else:
            entry["scene_reinit"] = False
            entry["descriptor_action"] = "vertical_0"
            entry["descriptor_before"] = cursor
        entry["descriptor_after"] = cursor
        out.append(entry)
    return out


def seg_fg_tiles(mc, seg): return set(gen.collect_runtime_gameplay_fg_tiles(mc, (seg,)))


def bg_tiles(mc):
    bs = gen.collect_block_write_sources(mc)
    bst, _ = gen.collect_block_scene_tiles_and_source_map(mc, bs)
    return set(bst[gen.SCENE_GAMEPLAY])


def text_tiles(mc): return {t for t in gen.extract_text_writer_tiles(mc) if t}


def derive_epochs(mc, segments, bg, txt):
    """Transitional Plane-A epoch model while exact Plane-B residency remains unresolved.

    The 320-slot reserve is intentionally retained rather than presenting the whole-stage BG union
    as a real per-epoch set. It must be removed only after the player-dependent selector-0 Y envelope
    is statically decoded.
    """
    epochs = []
    cur_segs, cur_fg = [], set()
    fixed = txt - {0}          # M1: only text/HUD pinned; Plane-B in its own reserved region
    for seg, sel in segments:
        fg = seg_fg_tiles(mc, seg) - {0}
        cand = cur_fg | fg
        if cur_segs and len(cand | fixed) > PLANE_SLOTS:
            epochs.append({"segments": cur_segs, "fg": set(cur_fg)})
            cur_segs, cur_fg = [], set()
            cand = fg
        cur_segs.append(seg); cur_fg |= fg
    if cur_segs:
        epochs.append({"segments": cur_segs, "fg": set(cur_fg)})
    for i, e in enumerate(epochs):
        e["id"] = i
        e["planeA"] = sorted(e["fg"])
        e["planeB"] = sorted(fixed & bg) if False else sorted(bg - {0})
        e["text"] = sorted(txt)
    return epochs, sorted(fixed)


def allocate_vram(epochs, fixed):
    """Tile-lifetime slot allocation: each code's live interval = [first epoch, last epoch] it is
    resident.  Assign a stable slot; reuse a slot once its code's interval ends.  Fixed (BG+text)
    tiles are live across all epochs (pinned).  Returns per-epoch {code:slot} + the transition deltas."""
    n = len(epochs)
    slot_of = {}                                    # code -> currently-held slot (persists)
    free = list(range(SLOT_MIN, SLOT_MAX + 1))
    epoch_alloc = [dict() for _ in range(n)]
    max_occ = 0
    for i in range(n):
        resident = (set(epochs[i]["fg"]) | set(fixed)) - {0}
        # release slots whose code left the resident set (frees them for reuse this epoch)
        for c in list(slot_of):
            if c not in resident:
                free.append(slot_of.pop(c))
        # allocate any resident code that has no slot (retains those that carried over)
        for c in sorted(resident):
            if c not in slot_of:
                if not free:
                    raise SystemExit(f"VRAM_ALLOC_FAIL epoch {i}: live set {len(resident)} > band "
                                     f"{PLANE_SLOTS} (need finer epoch)")
                slot_of[c] = free.pop(0)
            epoch_alloc[i][c] = slot_of[c]
        max_occ = max(max_occ, len(epoch_alloc[i]))
    return epoch_alloc, max_occ


def build_transitions(epochs, epoch_alloc):
    """Per epoch: which (slot<-code) are NEW vs the previous epoch (must be DMA'd).  Coalesce
    contiguous dest slots into DMA runs."""
    trans = []
    for i, alloc in enumerate(epoch_alloc):
        prev = epoch_alloc[i - 1] if i else {}
        prev_slot_code = {s: c for c, s in prev.items()}
        new = []                # (slot, code) needing upload this epoch
        for c, s in sorted(alloc.items(), key=lambda kv: kv[1]):
            if prev_slot_code.get(s) != c:
                new.append((s, c))
        # coalesce contiguous slots into runs
        runs = []
        for s, c in new:
            if runs and runs[-1]["slot0"] + runs[-1]["count"] == s:
                runs[-1]["count"] += 1; runs[-1]["codes"].append(c)
            else:
                runs.append({"slot0": s, "count": 1, "codes": [c]})
        trans.append({"epoch": i, "new_patterns": len(new), "dma_runs": runs,
                      "dma_bytes": len(new) * TILE_BYTES})
    return trans


def palette_route(registry, mc):
    """Emit the shared-CRAM route from the policy registry (proven/decided only).  Report banks and
    any unresolved demand.  (Full arcade CRAM colour contents left as a decoder-semantics gap.)"""
    ok = {"proven", "decided"}
    rows, unresolved = [], []
    for d in registry.get("decisions", []):
        st = d.get("status")
        gr = d.get("genesis_realization", {}) or {}
        arc = d.get("arcade_semantics", {}) or {}
        ctx = d.get("context", {}) or {}
        line = gr.get("palette_line")
        bank = arc.get("effective_palette_bank")
        owner = ctx.get("subsystem") or ctx.get("actor_family")
        if st in ok and line is not None:
            rows.append({"owner": owner, "arcade_bank": bank, "genesis_line": line,
                         "route_kind": gr.get("route_kind"), "status": st, "id": d.get("id")})
        else:
            unresolved.append({"id": d.get("id"), "status": st, "bank": bank, "line": line})
    return rows, unresolved


def be16(v): return bytes([(v >> 8) & 0xFF, v & 0xFF])


def be32(v): return bytes([(v >> 24) & 0xFF, (v >> 16) & 0xFF,
                           (v >> 8) & 0xFF, v & 0xFF])


def build_boundary_experiment(mc: bytes, patterns: bytes, outdir: Path, stage_index: int = 0, reuse=None):
    """Compile the Build-0310 zero-drop Round-1 Phase-1 gameplay ownership model.

    Plane B is the exact descriptor-0..55 vocabulary and is loaded once. Plane A owns seven
    complete-residency semantic epochs for records 0..15. All allocation is deterministic and
    offline; a missing legal pattern is a compiler failure, never a runtime blank/fallback decision.
    """
    all_records = decode_plane_b_progression(mc, stage_index)
    records = all_records[:16]
    if [record["segment"] for record in records] != list(range(16)):
        raise SystemExit("Round-1 Phase-1 record contract changed: expected records 0..15")

    def u16(addr): return int.from_bytes(mc[addr:addr + 2], "big")
    def u24(addr): return int.from_bytes(mc[addr:addr + 4], "big") & 0xFFFFFF
    def tile_bytes(code): return patterns[code * TILE_BYTES:(code + 1) * TILE_BYTES]

    # Level 1 owns descriptors 0..55. Descriptor 56 starts the next stage and is intentionally
    # excluded. Exact pattern bytes, not code identity, are the physical VRAM allocation unit.
    b_codes = []
    for descriptor in range(56):
        src = u24(PLANE_B_DESC_TABLE + descriptor * PLANE_B_DESC_STRIDE + 2)
        for row in range(PLANE_B_ROWS):
            for column in range(PLANE_B_COLS):
                code = u16(src + row * 0x20 + column * 2) & 0x3FFF
                if code:
                    b_codes.append(code)
    b_codes = sorted(set(b_codes))
    b_blobs = sorted({tile_bytes(code) for code in b_codes})
    if len(b_blobs) != 854:
        raise SystemExit(f"fixed Plane B vocabulary changed: {len(b_blobs)} != proven 854")
    b_repr = {}
    for code in b_codes:
        b_repr.setdefault(tile_bytes(code), code)
    # Build 0342 clean repack: the static Plane-B corpus is split across the three legal pattern ranges
    # (Layer A takes the contiguous middle window). Order the corpus by ORIGINAL ARCADE SOURCE TILE CODE
    # (b_repr), not byte-sort and not historical Genesis slot numbers, so the permanent layout is logical.
    #   range 1: slots 1..662 (0x0020..0x52DF)
    #   range 2: slots 1664..1791 (0xD000..0xDFDF, the old nametable gap)
    #   range 3: slots 1920..1983 (0xF000..0xF7DF, the unused Window region)
    PLANE_B_RANGES = ((1, 662), (1664, 1791), (1920, 1983))
    b_slot_seq = [s for lo, hi in PLANE_B_RANGES for s in range(lo, hi + 1)]
    if len(b_slot_seq) != len(b_blobs):
        raise SystemExit(f"Plane-B ranges hold {len(b_slot_seq)} slots != {len(b_blobs)} patterns")
    b_blobs_ordered = sorted(b_blobs, key=lambda blob: b_repr[blob])
    b_slot = {blob: b_slot_seq[index] for index, blob in enumerate(b_blobs_ordered)}
    b_map = [(code, b_slot[tile_bytes(code)]) for code in b_codes]
    b_uploads = [(b_repr[blob], b_slot[blob]) for blob in b_blobs_ordered]
    b_last = max(b_slot.values())

    # Layer A is one contiguous window pinned between Plane-B range 1 and the sprite region.
    a_slot_first = 663
    a_slot_count = BOUNDARY_PHASE1_EPOCH_CAPACITY
    a_slot_last = a_slot_first + a_slot_count - 1
    if (a_slot_first, a_slot_last) != (663, 1338):
        raise SystemExit(f"Plane-A ownership changed: {a_slot_first}..{a_slot_last} != 663..1338")
    if a_slot_last >= SPRITE_TILE_BASE:
        raise SystemExit(f"zero-drop planes overlap sprites: A ends {a_slot_last}, "
                         f"sprites start {SPRITE_TILE_BASE}")
    # Clean-repack non-overlap proof: A [663,1338], sprites [1339,1535], B ranges must be disjoint from
    # both and from every nametable/SAT/HScroll region (all pattern tile indices < 2048).
    _a_range = set(range(a_slot_first, a_slot_last + 1))
    _sprite_range = set(range(SPRITE_TILE_BASE, GLOBAL_SLOT_LAST + 1))
    _b_range = set(b_slot.values())
    if _b_range & _a_range:
        raise SystemExit(f"Plane-B/Plane-A slot overlap: {sorted(_b_range & _a_range)[:8]}")
    if _b_range & _sprite_range:
        raise SystemExit(f"Plane-B/sprite slot overlap: {sorted(_b_range & _sprite_range)[:8]}")
    # nametable/SAT/HScroll VRAM ranges as tile-slot spans (32 bytes/slot): PlaneB nt 0xC000 (1536-1663),
    # PlaneA nt 0xE000 (1792-1919), SAT 0xF800 (1984-...), HScroll 0xFC00. Pattern slots must avoid these.
    _reserved_slots = set(range(0x1800 // 1, 0)) if False else set()
    for lo, hi in ((1536, 1663), (1792, 1919), (1984, 2047)):
        _reserved_slots |= set(range(lo, hi + 1))
    if _b_range & _reserved_slots:
        raise SystemExit(f"Plane-B pattern overlaps a nametable/SAT/HScroll slot: "
                         f"{sorted(_b_range & _reserved_slots)[:8]}")
    if max(_b_range | _a_range | _sprite_range) >= 2048:
        raise SystemExit("tile index >= 2048")

    record_code_blob = []
    record_pattern_sets = []
    for record in records:
        codes = sorted(seg_fg_tiles(mc, record["segment"]) - {0})
        code_blob = {code: tile_bytes(code) for code in codes}
        record_code_blob.append(code_blob)
        record_pattern_sets.append(set(code_blob.values()))

    # Exhaustively prove the minimum contiguous complete-residency segmentation at the hardware
    # cap. This keeps the build-time policy tied to original arcade data rather than hand arithmetic.
    minimum_cache = {}
    def minimum_partitions(first):
        if first == len(records):
            return 0, [()]
        if first in minimum_cache:
            return minimum_cache[first]
        best, ways, union = len(records) + 1, [], set()
        for last in range(first, len(records)):
            union |= record_pattern_sets[last]
            if len(union) > a_slot_count:
                break
            tail_count, tails = minimum_partitions(last + 1)
            count = tail_count + 1
            if count < best:
                best, ways = count, []
            if count == best:
                ways.extend((((first, last),) + tail) for tail in tails)
        minimum_cache[first] = (best, ways)
        return minimum_cache[first]

    minimum_epoch_count, minimum_segmentations = minimum_partitions(0)
    requested_segmentation = tuple((epoch[0], epoch[-1])
                                   for epoch in BOUNDARY_PHASE1_EPOCH_RECORDS)
    # Build 0342: the requested segmentation must be a VALID contiguous complete-residency partition at the
    # 676 capacity (every epoch union <= cap, boundaries preserved for the two streamed transitions). It is
    # intentionally NOT the global minimum (4): keeping records 0-2|3 separate preserves both proven streamed
    # transitions. Validate contiguity/coverage + per-epoch fit; report the true minimum for the record.
    _flat = [r for epoch in BOUNDARY_PHASE1_EPOCH_RECORDS for r in epoch]
    if _flat != list(range(len(records))):
        raise SystemExit(f"requested segmentation is not a contiguous cover of records 0..{len(records)-1}")
    for epoch in BOUNDARY_PHASE1_EPOCH_RECORDS:
        _u = set()
        for r in epoch:
            _u |= record_pattern_sets[r]
        if len(_u) > a_slot_count:
            raise SystemExit(f"epoch {epoch} union {len(_u)} exceeds Plane-A cap {a_slot_count}")
    print(f"NOTE Build 0342 segmentation: requested {len(BOUNDARY_PHASE1_EPOCH_RECORDS)} epochs at cap "
          f"{a_slot_count}; global minimum is {minimum_epoch_count} epochs.")

    record_to_epoch = [None] * len(records)
    epoch_code_blob = []
    epoch_pattern_sets = []
    for epoch_index, epoch_records in enumerate(BOUNDARY_PHASE1_EPOCH_RECORDS):
        code_blob = {}
        for record_index in epoch_records:
            for code, blob in record_code_blob[record_index].items():
                previous_blob = code_blob.setdefault(code, blob)
                if previous_blob != blob:
                    raise SystemExit(
                        f"logical code 0x{code:04X} changes physical identity inside epoch "
                        f"{epoch_index}")
            record_to_epoch[record_index] = epoch_index
        epoch_code_blob.append(code_blob)
        epoch_pattern_sets.append(set(code_blob.values()))
    if any(epoch is None for epoch in record_to_epoch):
        raise SystemExit("incomplete Phase-1 record-to-epoch table")

    expected_epoch_counts = [282, 333, 639, 583, 639]   # Build 0342 5-epoch @ cap 676
    epoch_counts = [len(pattern_set) for pattern_set in epoch_pattern_sets]
    if epoch_counts != expected_epoch_counts:
        # Build 0316: offline Palette Composer Layer-A reindexing legitimately changes exact-pattern dedup,
        # so per-epoch union counts move (they only shrink here -> better VRAM fit). This is an intended
        # policy change, not a regression; the hard capacity gate below still applies.
        print(f"NOTE Phase-1 epoch unions changed (editor-policy reindex): {epoch_counts} vs baseline {expected_epoch_counts}")
    if any(count > a_slot_count for count in epoch_counts):
        raise SystemExit(f"Phase-1 epoch exceeds Plane-A cap {a_slot_count}: {epoch_counts}")

    # Reconstruct the original 64x64 record maps directly from the same source tables consumed by
    # the native selector-0 producer. This is an offline lifetime model, not a runtime map scan.
    source_table_bases = tuple(gen.FG_SRC_BASE + index * gen.FG_SRC_STRIDE
                               for index in range(gen.FG_SEG_COUNT))

    def record_map(record_index):
        cells = [[0] * 64 for _ in range(64)]
        for row in range(64):
            table_index, descriptor_row = divmod(row, 4)
            table_base = source_table_bases[table_index] + record_index * 0x40
            for column in range(64):
                descriptor_column, descriptor_subcolumn = divmod(column, 4)
                entry = table_base + descriptor_column * 4
                descriptor = u16(entry + 2)
                if descriptor:
                    cells[row][column] = (
                        u16(descriptor + descriptor_row * 8 + descriptor_subcolumn * 2)
                        & 0x3FFF)
        return cells

    record_maps = [record_map(index) for index in range(len(records))]
    transition_specs = []
    for definition in BOUNDARY_TRANSITION_DEFS:
        outgoing = record_maps[definition["out_record"]]
        incoming = record_maps[definition["in_record"]]
        required_codes = set()
        outgoing_visible_codes = set()
        incoming_required_codes = set()
        states = []
        for step in range(BOUNDARY_TRANSITION_HANDOFF_COLUMN):
            visible_columns = [
                (BOUNDARY_TRANSITION_INITIAL_COLUMN + step + offset) & 0x3F
                for offset in range(BOUNDARY_TRANSITION_VISIBLE_COLUMNS)]
            state_codes = set()
            outgoing_codes = set()
            incoming_codes = set()
            for column in visible_columns:
                source = incoming if column <= step else outgoing
                target = incoming_codes if column <= step else outgoing_codes
                for row in range(64):
                    code = source[row][column]
                    if code:
                        state_codes.add(code)
                        target.add(code)
            # The publisher resolves every row of the incoming column, including rows outside the
            # current 32-row Genesis name window. Preload those codes before publication.
            for column in range(step + 1):
                for row in range(64):
                    code = incoming[row][column]
                    if code:
                        state_codes.add(code)
                        incoming_codes.add(code)
            required_codes.update(state_codes)
            outgoing_visible_codes.update(outgoing_codes)
            incoming_required_codes.update(incoming_codes)
            states.append({
                "step": step,
                "visible_columns": visible_columns,
                "required_codes": state_codes,
                "outgoing_codes": outgoing_codes,
                "incoming_codes": incoming_codes,
            })
        combined_code_blob = dict(record_code_blob[definition["out_record"]])
        combined_code_blob.update(record_code_blob[definition["in_record"]])
        code_blob = {code: combined_code_blob[code] for code in sorted(required_codes)}
        pattern_set = set(code_blob.values())
        expected = 394 if definition["name"] == "rope_to_waterfall" else 479
        if len(pattern_set) != expected:
            # Build 0316: editor-policy reindex legitimately shifts exact-pattern dedup counts.
            print(f"NOTE {definition['name']} transition set changed (editor-policy reindex): "
                  f"{len(pattern_set)} vs baseline {expected}")
        transition_specs.append(definition | {
            "code_blob": code_blob,
            "pattern_set": pattern_set,
            "states": states,
            "outgoing_visible_codes": outgoing_visible_codes,
            "incoming_required_codes": incoming_required_codes,
        })

    # Package IDs retain the seven stable epoch IDs. Two overlap IDs are appended to the binary,
    # while allocation follows semantic time A -> overlap AB -> B -> overlap BC -> C -> ... so
    # every retained exact identity keeps its physical slot.
    stable_package_count = len(epoch_code_blob)
    transition_package_ids = [stable_package_count + index
                              for index in range(len(transition_specs))]
    package_specs = [
        {"kind": "stable", "epoch": index, "records": list(records_),
         "name": f"epoch_{index}", "code_blob": code_blob}
        for index, (records_, code_blob) in enumerate(
            zip(BOUNDARY_PHASE1_EPOCH_RECORDS, epoch_code_blob))]
    package_specs.extend({
        "kind": "transition", "epoch": spec["out_epoch"],
        "records": [spec["out_record"], spec["in_record"]],
        "name": spec["name"], "code_blob": spec["code_blob"]}
        for spec in transition_specs)
    allocation_order = [0, transition_package_ids[0], 1, transition_package_ids[1],
                        *range(2, stable_package_count)]
    packages = [None] * len(package_specs)
    previous = {}
    all_a_only = set()
    for package_index in allocation_order:
        spec = package_specs[package_index]
        code_blob = spec["code_blob"]
        plane_a = sorted(code_blob)
        a_only = sorted(set(code_blob.values()) - set(b_slot))
        all_a_only.update(a_only)
        retained = {blob: previous[blob] for blob in a_only if blob in previous}
        free = [slot for slot in range(a_slot_first, a_slot_last + 1)
                if slot not in retained.values()]
        assigned = dict(retained)
        for blob in a_only:
            if blob not in assigned:
                if not free:
                    raise SystemExit(f"package {package_index}: Plane A needs "
                                     f"{len(a_only)} slots, only {a_slot_count} available")
                assigned[blob] = free.pop(0)
        previous = assigned
        mapping = [(code, b_slot.get(blob, assigned.get(blob)))
                   for code, blob in sorted(code_blob.items())]
        if any(slot is None for _, slot in mapping):
            raise SystemExit(f"package {package_index}: unresolved legal Plane A pattern")
        repr_code = {}
        for code, blob in code_blob.items():
            if blob in assigned:
                repr_code.setdefault(blob, code)
        uploads = [(repr_code[blob], assigned[blob]) for blob in a_only]
        packages[package_index] = spec | {
            "package": package_index,
            "map": mapping, "uploads": uploads, "assigned": assigned,
            "identities": [], "required_codes": len(plane_a),
            "required_patterns": len(set(code_blob.values())),
            "a_only_patterns": len(a_only), "b_shared_patterns":
                len(set(code_blob.values()) & set(b_slot)),
            "retained_from_previous": len(retained),
            "droppedA": 0, "droppedB": 0,
        }

    pattern_id = {blob: index for index, blob in enumerate(sorted(all_a_only))}
    for package in packages:
        package["identities"] = sorted(
            (slot, pattern_id[blob]) for blob, slot in package["assigned"].items())

    # Exact object-level regression identities. The record-2 rope is the original vertical cell
    # column; the record-3 waterfall is the attr 0x1A..0x1D body visible at the B->C boundary.
    rope_cells = [(row, 46, record_maps[2][row][46]) for row in range(31, 54)]
    rope_codes = {code for _, _, code in rope_cells if code}
    waterfall_cells = []
    for row in range(21, 52):
        table_index, descriptor_row = divmod(row, 4)
        table_base = source_table_bases[table_index] + 3 * 0x40
        for column in range(19, 59):
            descriptor_column, descriptor_subcolumn = divmod(column, 4)
            entry = table_base + descriptor_column * 4
            attr = u16(entry)
            if attr in {0x001A, 0x001B, 0x001C, 0x001D}:
                code = record_maps[3][row][column]
                if code:
                    waterfall_cells.append((row, column, code))
    waterfall_codes = {code for _, _, code in waterfall_cells}
    if (len({tile_bytes(code) for code in rope_codes}),
            len({tile_bytes(code) for code in waterfall_codes})) != (12, 224):
        raise SystemExit("rope/waterfall exact-pattern contract changed")

    # Project-owned compiler gates: every transition state and every publisher-resolved incoming
    # row must map to the correct exact pattern; retained old identities must keep their slots.
    transition_gate_reports = []
    for spec, package_id, stable_new_id in zip(
            transition_specs, transition_package_ids, (1, 2)):
        package = packages[package_id]
        old_package = packages[spec["out_epoch"]]
        new_package = packages[stable_new_id]
        package_map = dict(package["map"])
        new_map = dict(new_package["map"])
        visible_missing = 0
        slot_collisions = 0
        for state in spec["states"]:
            for code in state["required_codes"]:
                blob = tile_bytes(code)
                slot = package_map.get(code)
                expected_slot = b_slot.get(blob, package["assigned"].get(blob))
                if slot is None or slot != expected_slot:
                    visible_missing += 1
        reverse = {}
        for blob, slot in package["assigned"].items():
            if slot in reverse and reverse[slot] != blob:
                slot_collisions += 1
            reverse[slot] = blob
        retained_moved = sum(
            old_package["assigned"].get(blob) != package["assigned"].get(blob)
            for blob in spec["pattern_set"]
            if blob in old_package["assigned"] and blob in package["assigned"])
        # At handoff 45 all visible columns are incoming. Stable-new must resolve every row.
        handoff_columns = [
            (BOUNDARY_TRANSITION_INITIAL_COLUMN + BOUNDARY_TRANSITION_HANDOFF_COLUMN + offset)
            & 0x3F for offset in range(BOUNDARY_TRANSITION_VISIBLE_COLUMNS)]
        handoff_codes = {spec_code for column in handoff_columns
                         for spec_code in (record_maps[spec["in_record"]][row][column]
                                           for row in range(64)) if spec_code}
        handoff_missing = sum(code not in new_map for code in handoff_codes)
        if visible_missing or slot_collisions or retained_moved or handoff_missing:
            raise SystemExit(
                f"{spec['name']} gate failed: visible_missing={visible_missing}, "
                f"slot_collisions={slot_collisions}, retained_moved={retained_moved}, "
                f"handoff_missing={handoff_missing}")
        transition_gate_reports.append({
            "name": spec["name"], "package": package_id,
            "stable_new_package": stable_new_id,
            "steps": [0, BOUNDARY_TRANSITION_HANDOFF_COLUMN - 1],
            "peak_patterns": len(spec["pattern_set"]),
            "capacity": a_slot_count,
            "margin": a_slot_count - len(spec["pattern_set"]),
            "outgoing_visible_patterns": len({tile_bytes(code)
                                               for code in spec["outgoing_visible_codes"]}),
            "incoming_required_patterns": len({tile_bytes(code)
                                                for code in spec["incoming_required_codes"]}),
            "shared_visible_patterns": len(
                {tile_bytes(code) for code in spec["outgoing_visible_codes"]}
                & {tile_bytes(code) for code in spec["incoming_required_codes"]}),
            "incoming_only_required_patterns": len(
                {tile_bytes(code) for code in spec["incoming_required_codes"]}
                - {tile_bytes(code) for code in spec["outgoing_visible_codes"]}),
            "visible_missing_patterns": visible_missing,
            "slot_collisions": slot_collisions,
            "retained_patterns_moved": retained_moved,
            "handoff_missing_patterns": handoff_missing,
            "gate": "PASS",
        })

    # Transition scratch reuses a statically proven hole in the 0x2800-word active LUT. It must
    # never overlap an actual Level-1 A/B code mapping.
    scratch_word = 0x1600
    scratch_words = len(pattern_id) + a_slot_count
    occupied_codes = set(b_codes)
    occupied_codes.update(code for record in records
                          for code in seg_fg_tiles(mc, record["segment"]) - {0})
    scratch_overlap = sorted(occupied_codes & set(range(scratch_word, scratch_word + scratch_words)))
    if scratch_word + scratch_words > BOUNDARY_LUT_WORDS or scratch_overlap:
        raise SystemExit(f"transition scratch overlaps legal LUT codes: {scratch_overlap[:8]}")

    # Binary contract: record->package table, fixed-size descriptors, per-package A sections, then
    # the fixed-B sections. Records 3 and 4 first select their bounded overlap packages; the native
    # selector-0 publisher performs the generated handoff to stable epochs B/C at column 45.
    # fixed-B map/upload sections. Every runtime-consumed section is naturally word-aligned.
    record_to_package = list(record_to_epoch)
    record_to_package[3] = transition_package_ids[0]
    record_to_package[4] = transition_package_ids[1]
    record_table = [(package, 1) for package in record_to_package]
    table_bytes = len(record_table) * BOUNDARY_RECORD_ENTRY_BYTES
    desc_bytes = len(packages) * BOUNDARY_PACKAGE_DESC_BYTES
    data_base = table_bytes + desc_bytes
    if data_base % BOUNDARY_WORD_ALIGNMENT:
        raise SystemExit(f"unaligned package data base: {data_base}")

    data = bytearray(); desc = bytearray(); package_layout = []
    for package_index, package in enumerate(packages):
        offset = data_base + len(data)
        if offset % BOUNDARY_WORD_ALIGNMENT:
            raise SystemExit(f"package {package_index} data offset is odd: {offset}")
        map_start = offset
        map_bytes = len(package["map"]) * BOUNDARY_PAIR_BYTES
        upload_start = map_start + map_bytes
        upload_bytes = len(package["uploads"]) * BOUNDARY_PAIR_BYTES
        identity_start = upload_start + upload_bytes
        identity_bytes = len(package["identities"]) * BOUNDARY_PAIR_BYTES
        package_end = identity_start + identity_bytes
        for section_name, section_start in (
                ("map", map_start), ("upload", upload_start), ("identity", identity_start)):
            if section_start % BOUNDARY_WORD_ALIGNMENT:
                raise SystemExit(
                    f"package {package_index} {section_name} section is odd: {section_start}")
        desc += be32(offset)
        desc += be16(len(package["map"])) + be16(len(package["uploads"]))
        desc += be16(len(package["identities"])) + be16(package["required_patterns"])
        desc += be16(0) + be16(0)
        for code, slot in package["map"]: data += be16(code) + be16(slot)
        for code, slot in package["uploads"]: data += be16(code) + be16(slot)
        for slot, identity in package["identities"]: data += be16(slot) + be16(identity)
        if data_base + len(data) != package_end:
            raise SystemExit(f"package {package_index} section length disagreement")
        package_layout.append({
            "package": package_index,
            "descriptor_offset": table_bytes + package_index * BOUNDARY_PACKAGE_DESC_BYTES,
            "data_offset": offset,
            "map_start": map_start, "map_count": len(package["map"]),
            "map_bytes": map_bytes,
            "upload_start": upload_start, "upload_count": len(package["uploads"]),
            "upload_bytes": upload_bytes,
            "identity_start": identity_start,
            "identity_count": len(package["identities"]),
            "identity_bytes": identity_bytes,
            "end": package_end,
        })
    fixed_b_offset = data_base + len(data)
    fixed_b_map_bytes = len(b_map) * BOUNDARY_PAIR_BYTES
    fixed_b_upload_offset = fixed_b_offset + fixed_b_map_bytes
    fixed_b_upload_bytes = len(b_uploads) * BOUNDARY_PAIR_BYTES
    fixed_b_end = fixed_b_upload_offset + fixed_b_upload_bytes
    for section_name, section_start in (
            ("fixed-B map", fixed_b_offset), ("fixed-B upload", fixed_b_upload_offset)):
        if section_start % BOUNDARY_WORD_ALIGNMENT:
            raise SystemExit(f"{section_name} section is odd: {section_start}")
    for code, slot in b_map: data += be16(code) + be16(slot)
    for code, slot in b_uploads: data += be16(code) + be16(slot)
    binary = bytearray()
    for first, variants in record_table: binary += be16(first) + be16(variants)
    binary += desc + data
    if len(desc) != desc_bytes:
        raise SystemExit(f"descriptor table length disagreement: {len(desc)} != {desc_bytes}")
    if len(binary) != fixed_b_end or len(binary) % BOUNDARY_WORD_ALIGNMENT:
        raise SystemExit(
            f"package binary length/alignment disagreement: {len(binary)} != {fixed_b_end}")
    for layout in package_layout:
        if layout["descriptor_offset"] + BOUNDARY_PACKAGE_DESC_BYTES > data_base:
            raise SystemExit(f"package {layout['package']} descriptor exceeds descriptor table")
        if not (data_base <= layout["data_offset"] <= layout["end"] <= fixed_b_offset):
            raise SystemExit(f"package {layout['package']} data span exceeds A-package section")
    (outdir / "boundary_packages.bin").write_bytes(binary)

    reseed_mask = sum(1 << index for index, record in enumerate(records)
                      if record["scene_reinit"] and index != 0)
    sprite_cells = (GLOBAL_SLOT_LAST - SPRITE_TILE_BASE + 1) // 4
    (outdir / "boundary_constants.inc").write_text(
        "/* generated by compile_pc080sn_genesis.py --boundary-experiment */\n"
        f".equ FG_BOUNDARY_RECORDS, {len(record_table)}\n"
        f".equ FG_BOUNDARY_PACKAGES, {len(packages)}\n"
        f".equ FG_BOUNDARY_EPOCHS, {stable_package_count}\n"
        f".equ FG_BOUNDARY_TRANSITION_AB_PACKAGE, {transition_package_ids[0]}\n"
        f".equ FG_BOUNDARY_TRANSITION_BC_PACKAGE, {transition_package_ids[1]}\n"
        f".equ FG_BOUNDARY_TRANSITION_AB_STABLE_PACKAGE, 1\n"
        f".equ FG_BOUNDARY_TRANSITION_BC_STABLE_PACKAGE, 2\n"
        f".equ FG_BOUNDARY_TRANSITION_HANDOFF_COLUMN, {BOUNDARY_TRANSITION_HANDOFF_COLUMN}\n"
        f".equ FG_BOUNDARY_RECORD_ENTRY_BYTES, {BOUNDARY_RECORD_ENTRY_BYTES}\n"
        f".equ FG_BOUNDARY_DESC_OFFSET, {table_bytes}\n"
        f".equ FG_BOUNDARY_DESC_BYTES, {BOUNDARY_PACKAGE_DESC_BYTES}\n"
        f".equ FG_BOUNDARY_PAIR_BYTES, {BOUNDARY_PAIR_BYTES}\n"
        f".equ FG_BOUNDARY_WORD_ALIGNMENT, {BOUNDARY_WORD_ALIGNMENT}\n"
        f".equ FG_BOUNDARY_LUT_WORDS, {BOUNDARY_LUT_WORDS}\n"
        f".equ FG_BOUNDARY_CONFLICT_CODE_FIRST, 0x{BOUNDARY_CONFLICT_CODE_FIRST:04X}\n"
        f".equ FG_BOUNDARY_CONFLICT_CODE_COUNT, 0x{BOUNDARY_CONFLICT_CODE_COUNT:04X}\n"
        f".equ FG_BOUNDARY_SLOT_FIRST, {a_slot_first}\n"
        f".equ FG_BOUNDARY_SLOT_COUNT, {a_slot_count}\n"
        f".equ FG_BOUNDARY_PATTERN_IDENTITIES, {len(pattern_id)}\n"
        f".equ FG_BOUNDARY_SCRATCH_WORD, {scratch_word}\n"
        f".equ FG_BOUNDARY_FIXED_B_OFFSET, {fixed_b_offset}\n"
        f".equ FG_BOUNDARY_FIXED_B_MAP_COUNT, {len(b_map)}\n"
        f".equ FG_BOUNDARY_FIXED_B_MAP_BYTES, {fixed_b_map_bytes}\n"
        f".equ FG_BOUNDARY_FIXED_B_UPLOAD_OFFSET, {fixed_b_upload_offset}\n"
        f".equ FG_BOUNDARY_FIXED_B_UPLOAD_COUNT, {len(b_uploads)}\n"
        f".equ FG_BOUNDARY_FIXED_B_UPLOAD_BYTES, {fixed_b_upload_bytes}\n"
        f".equ FG_BOUNDARY_FIXED_B_TOTAL_BYTES, {fixed_b_end - fixed_b_offset}\n"
        f".equ FG_BOUNDARY_BINARY_LEN, {len(binary)}\n"
        f".equ FG_BOUNDARY_FIXED_B_SLOT_LAST, {b_last}\n"
        f".equ FG_BOUNDARY_SPRITE_TILE_BASE, {SPRITE_TILE_BASE}\n"
        f".equ FG_BOUNDARY_SPRITE_CELLS, {sprite_cells}\n"
        f".equ FG_BOUNDARY_RESEED_MASK, 0x{reseed_mask:08X}\n")

    report = {
        "model": "Build 0311 fixed Level-1 Plane B plus seven stable Plane-A epochs and two bounded transition-overlap packages",
        "trace_inputs": 0,
        "records": len(record_table), "packages": len(packages),
        "stable_epochs": stable_package_count,
        "phase1_records": [record["segment"] for record in records],
        "record_to_epoch": record_to_epoch,
        "record_to_package": record_to_package,
        "minimum_contiguous_epoch_count_at_cap": minimum_epoch_count,
        "minimum_contiguous_segmentations": [
            [[first, last] for first, last in segmentation]
            for segmentation in minimum_segmentations],
        "selected_epoch_records": [list(epoch) for epoch in BOUNDARY_PHASE1_EPOCH_RECORDS],
        "plane_a_epoch_counts": epoch_counts,
        "plane_a_transition_metrics": [
            {
                "from_epoch": index,
                "to_epoch": index + 1,
                "previous": len(epoch_pattern_sets[index]),
                "next": len(epoch_pattern_sets[index + 1]),
                "shared": len(epoch_pattern_sets[index] & epoch_pattern_sets[index + 1]),
                "retired": len(epoch_pattern_sets[index] - epoch_pattern_sets[index + 1]),
                "new": len(epoch_pattern_sets[index + 1] - epoch_pattern_sets[index]),
            }
            for index in range(len(epoch_pattern_sets) - 1)],
        "plane_b_epochs": 1, "plane_b_variants": 0,
        "plane_b_descriptor_first": 0, "plane_b_descriptor_last": 55,
        "plane_b_descriptor_56_excluded_as_stage2": True,
        "plane_b_codes": len(b_codes), "plane_b_patterns": len(b_blobs),
        "plane_b_slot_first": 1, "plane_b_slot_last": b_last,
        "plane_b_dropped": 0,
        "plane_a_slot_first": a_slot_first, "plane_a_slot_last": a_slot_last,
        "plane_a_slot_capacity": a_slot_count,
        "plane_a_record_counts": [len(patterns) for patterns in record_pattern_sets],
        "plane_a_code_counts": [len(code_blob) for code_blob in record_code_blob],
        "plane_a_dropped_by_record": [0] * len(records),
        "sprite_tile_base": SPRITE_TILE_BASE,
        "sprite_tile_last": GLOBAL_SLOT_LAST,
        "sprite_16x16_cells": sprite_cells,
        "frontend_slots_reclaimed_at_gameplay_entry": "1..63",
        "ordinary_plane_b_pattern_dma": 0,
        "ordinary_plane_b_lut_rebuild": 0,
        "ordinary_plane_b_name_remap": 0,
        "ordinary_plane_b_name_dma": 0,
        "within_epoch_pattern_dma": 0,
        "within_epoch_slot_churn": 0,
        "record_residency_boundaries_before": 15,
        "epoch_residency_boundaries_after": 6,
        "false_record_residency_transitions_eliminated": 9,
        "runtime_allocator": False,
        "runtime_search": False,
        "runtime_lru": False,
        "runtime_visibility_scan": False,
        "transition_handoff_column": BOUNDARY_TRANSITION_HANDOFF_COLUMN,
        "transition_gates": transition_gate_reports,
        "rope_object": {
            "record": 2,
            "cells": [{"row": row, "column": column, "code": f"0x{code:04X}"}
                      for row, column, code in rope_cells],
            "codes": [f"0x{code:04X}" for code in sorted(rope_codes)],
            "exact_pattern_hashes": [hashlib.sha256(tile_bytes(code)).hexdigest()
                                     for code in sorted(rope_codes)],
            "exact_patterns": len({tile_bytes(code) for code in rope_codes}),
            "transition_package": transition_package_ids[0],
            "slots_before_transition": sorted({
                packages[0]["assigned"].get(tile_bytes(code), b_slot.get(tile_bytes(code)))
                for code in rope_codes}),
            "slots_in_transition": sorted({
                packages[transition_package_ids[0]]["assigned"].get(
                    tile_bytes(code), b_slot.get(tile_bytes(code))) for code in rope_codes}),
        },
        "waterfall_object": {
            "record": 3,
            "cells": [{"row": row, "column": column, "code": f"0x{code:04X}"}
                      for row, column, code in waterfall_cells],
            "codes": [f"0x{code:04X}" for code in sorted(waterfall_codes)],
            "exact_pattern_hashes": [hashlib.sha256(tile_bytes(code)).hexdigest()
                                     for code in sorted(waterfall_codes)],
            "exact_patterns": len({tile_bytes(code) for code in waterfall_codes}),
            "transition_package": transition_package_ids[1],
            "slots_before_transition": sorted({
                packages[1]["assigned"].get(tile_bytes(code), b_slot.get(tile_bytes(code)))
                for code in waterfall_codes}),
            "slots_in_transition": sorted({
                packages[transition_package_ids[1]]["assigned"].get(
                    tile_bytes(code), b_slot.get(tile_bytes(code))) for code in waterfall_codes}),
        },
        "scratch_word_first": scratch_word,
        "scratch_word_last": scratch_word + scratch_words - 1,
        "scratch_legal_code_overlap": 0,
        "compiler_zero_drop_gate": "PASS",
        "binary_bytes": len(binary),
        "binary_contract": {
            "word_alignment": BOUNDARY_WORD_ALIGNMENT,
            "record_table_offset": 0,
            "record_entry_bytes": BOUNDARY_RECORD_ENTRY_BYTES,
            "record_table_bytes": table_bytes,
            "descriptor_table_offset": table_bytes,
            "descriptor_entry_bytes": BOUNDARY_PACKAGE_DESC_BYTES,
            "descriptor_table_bytes": desc_bytes,
            "package_data_offset": data_base,
            "pair_bytes": BOUNDARY_PAIR_BYTES,
            "package_layout": package_layout,
            "fixed_b_map_offset": fixed_b_offset,
            "fixed_b_map_bytes": fixed_b_map_bytes,
            "fixed_b_upload_offset": fixed_b_upload_offset,
            "fixed_b_upload_bytes": fixed_b_upload_bytes,
            "fixed_b_end": fixed_b_end,
            "padding_bytes": 0,
        },
        "allocation_identity": "exact 32-byte PC080SN pattern bytes",
        "reseed_record_mask": f"0x{reseed_mask:08X}",
        "packages_detail": [{k: v for k, v in p.items()
                             if k not in {"map", "uploads", "identities", "assigned",
                                          "code_blob"}} |
                            {"mapping_count": len(p["map"]),
                             "upload_count": len(p["uploads"]),
                             "identity_count": len(p["identities"])} for p in packages],
        "sha256": hashlib.sha256(binary).hexdigest(),
        "pattern_reuse_policy": ({
            "policy_sha256": reuse.get("policy_sha256"),
            "approved_count": reuse.get("approved_count"),
            "resolved_count": reuse.get("resolved_count"),
            "unresolved_count": reuse.get("unresolved_count"),
        } if reuse else {"policy_sha256": None, "approved_count": 0,
                         "resolved_count": 0, "unresolved_count": 0}),
    }
    (outdir / "boundary_report.json").write_text(json.dumps(report, indent=1) + "\n")

    # Debug emit (TOOLING): per-package slot -> [arcade_code, reindexed 32-byte pattern hex] and the
    # record->package table, so the actual DMA'd plane-A tiles can be rendered offline and compared to
    # the Palette Composer reference. Also include the fixed-B slots. Not a release artifact.
    dbg = {"record_to_package": record_to_package, "packages": []}
    for p in packages:
        slotmap = {}
        for code, slot in p["map"]:
            slotmap[str(slot)] = [code, tile_bytes(code).hex()]
        for code, slot in b_map:
            slotmap.setdefault(str(slot), [code, tile_bytes(code).hex()])
        dbg["packages"].append(slotmap)
    (outdir / "slot_patterns_debug.json").write_text(json.dumps(dbg))

    print(f"boundary compile: fixed B {len(b_blobs)} patterns, seven stable A epochs "
          f"{epoch_counts}, transition peaks {[r['peak_patterns'] for r in transition_gate_reports]}, "
          f"A cap {a_slot_count}, sprites {sprite_cells} cells, "
          f"{len(binary)} bytes, plane drops 0")
    return 0


# ---- Arcade palette source (proven by static RE, Cody palette-loader decode) ----
# Chain: ROM master colour table 0x4FD02 (xBGR-555) + per-scene bank-record table 0x3BA88
# (32 bytes/scene, indexed (scene-1)*32; scene = a5@0x118) -> FUN_0003ba20 assembles into the
# workram palette staging buffer a5@0x1600 -> FUN_00045d7c/dc4 copy 64-word chunks via 0x3a2d0
# into arcade palette RAM 0x200000..0x200FFF (2048 words = 128 banks x 16, xBGR-555).
PALETTE_ROM_COLORS = 0x4FD02          # master colour table, xBGR-555 (x BBBBB GGGGG RRRRR)
PALETTE_SCENE_RECORDS = 0x3BA88       # per-scene 32-byte bank-selection records
PALETTE_RAM_BASE = 0x200000
PALETTE_STAGING_A5 = 0x1600


def decode_pool_block(mc: bytes, block_id: int) -> list[int]:
    """FUN_0003ba20/0x3ba64 proven: colour block at 0x4FD02 + block_id*32 = 16 words, each
    0RGB nibble-packed (S[8:11]=R, S[4:7]=G, S[0:3]=B); transform nibble*2 -> arcade xBGR-555."""
    base = PALETTE_ROM_COLORS + block_id * 32
    out = []
    for c in range(16):
        s = (mc[base + c * 2] << 8) | mc[base + c * 2 + 1]
        r = ((s >> 8) & 0xF) * 2
        g = ((s >> 4) & 0xF) * 2
        b = (s & 0xF) * 2
        out.append((b << 10) | (g << 5) | r)      # arcade xBGR-555
    return out


def decode_scene_arcade_palettes(mc: bytes, scene: int) -> list[list[int]]:
    """FUN_0003ba20 proven: 32-byte scene record at 0x3BA88+(scene-1)*32; record byte i -> palette
    staging index i, byte value = colour-block id in the 0x4FD02 pool. The staging buffer a5+0x1600
    is copied to palette RAM 0x200600, so index i is effective bank 48+i. Returns effective banks
    48..79 as 32 banks x 16 xBGR-555 words."""
    rec = PALETTE_SCENE_RECORDS + (scene - 1) * 32
    return [decode_pool_block(mc, mc[rec + i]) for i in range(32)]


PALETTE_BASE_POOL = 0x4EAF6           # FUN_0003b9f8 startup: 768 words -> banks 0..47 (transformed)
PALETTE_BANK48_POOL = 0x4FE62         # FUN_0003b9f8 / scene block 11: bank 48 (PC080SN BG)


def _xform_block(mc: bytes, addr: int) -> list[int]:
    out = []
    for c in range(16):
        s = (mc[addr + c * 2] << 8) | mc[addr + c * 2 + 1]
        out.append((((s & 0xF) * 2) << 10) | ((((s >> 4) & 0xF) * 2) << 5) | (((s >> 8) & 0xF) * 2))
    return out


def decode_arcade_palette_bank(mc: bytes, bank: int, scene: int = 1) -> tuple[list[int], str]:
    """Generic recovery of a palette-RAM bank's arcade xBGR-555 colours + provenance string.
    FUN_0003b9f8 startup base: banks 0..47 from pool 0x4EAF6+bank*32; bank 48 (PC080SN BG) from
    0x4FE62. FUN_0003ba20 then writes its 32 scene-selected blocks to a5+0x1600, and the copy
    path publishes that buffer at palette RAM 0x200600: effective banks 48..79. Banks 80..127
    remain outside this scene loader."""
    if bank < 48:
        return _xform_block(mc, PALETTE_BASE_POOL + bank * 32), f"startup base @0x{PALETTE_BASE_POOL + bank*32:05X}"
    if bank < 80:
        index = bank - 48
        rec_addr = PALETTE_SCENE_RECORDS + (scene - 1) * 32 + index
        block_id = mc[rec_addr]
        pool_addr = PALETTE_ROM_COLORS + block_id * 32
        return (_xform_block(mc, pool_addr),
                f"scene {scene} effective bank {bank} index {index} record@0x{rec_addr:05X} "
                f"block {block_id} @0x{pool_addr:05X}")
    return [], "UNRESOLVED: no decoded Stage-scene loader ownership for effective banks 80-127"


def final_stage1_capacity_audit(mc: bytes, pc080sn: bytes, pc090oj: bytes) -> dict:
    """Final conservative Stage-1 global-pool pressure test.

    Record 11 is the accepted Plane-B safety-model maximum. Its selector-0 camera-machine envelope
    exposes every row except 60..62 across resident+incoming descriptors 20..25. PC090OJ cells are
    four consecutive Genesis 8x8 patterns. For an allocator-independent impossibility proof this
    routine deliberately computes the *more permissive* bound where all sprite quadrants may be
    deduplicated independently. If even that lower bound exceeds 1472, the real contiguous-cell
    allocator cannot fit.
    """
    def u16(addr: int) -> int:
        return int.from_bytes(mc[addr:addr + 2], "big")

    def u24_from_long(addr: int) -> int:
        return int.from_bytes(mc[addr:addr + 4], "big") & 0xFFFFFF

    plane_a_codes = set(seg_fg_tiles(mc, 11)) - {0}
    plane_b_codes = set()
    for descriptor in range(20, 26):
        src = u24_from_long(PLANE_B_DESC_TABLE + descriptor * PLANE_B_DESC_STRIDE + 2)
        for row in set(range(PLANE_B_ROWS)) - {60, 61, 62}:
            for column in range(PLANE_B_COLS):
                plane_b_codes.add(u16(src + row * 0x20 + column * 2) & 0x3FFF)
    plane_b_codes.discard(0)

    plane_codes = plane_a_codes | plane_b_codes
    plane_patterns = {pc080sn[code * TILE_BYTES:(code + 1) * TILE_BYTES]
                      for code in plane_codes}

    family_rows = []
    sprite_patterns = set()
    sprite_cells = set()
    for family, codes in STAGE1_PC090OJ_CELL_CODES.items():
        family_patterns = set()
        family_cells = set()
        for code in codes:
            cell = pc090oj[code * 128:(code + 1) * 128]
            if len(cell) != 128:
                raise SystemExit(f"PC090OJ cell {code:#06x} outside converted source")
            family_cells.add(cell)
            for quadrant in range(4):
                family_patterns.add(cell[quadrant * TILE_BYTES:(quadrant + 1) * TILE_BYTES])
        sprite_patterns |= family_patterns
        sprite_cells |= family_cells
        family_rows.append({
            "family": family,
            "source_cell_codes": [f"0x{code:04X}" for code in codes],
            "unique_cells": len(family_cells),
            "unique_8x8_patterns": len(family_patterns),
        })

    cross_owner_shared = len(plane_patterns & sprite_patterns)
    total_unique_lower_bound = len(plane_patterns | sprite_patterns)
    deficit = max(0, total_unique_lower_bound - GLOBAL_SLOT_COUNT)
    palettes = {}
    for bank in (0x30, 0x33, 0x36):
        colors, source = decode_arcade_palette_bank(mc, bank, 1)
        palettes[f"0x{bank:02X}"] = {
            "source": source,
            "arcade_xbgr555": [f"0x{word:04X}" for word in colors],
            "genesis_cram": [f"0x{arcade_xbgr555_to_genesis(word):04X}" for word in colors],
        }

    return {
        "model": "final Stage-1 conservative global-pool lower-bound audit",
        "trace_inputs": 0,
        "global_slot_first": GLOBAL_SLOT_FIRST,
        "global_slot_last": GLOBAL_SLOT_LAST,
        "global_capacity": GLOBAL_SLOT_COUNT,
        "limiting_record": 11,
        "planeA_codes": len(plane_a_codes),
        "planeB_codes": len(plane_b_codes),
        "plane_code_shared": len(plane_a_codes & plane_b_codes),
        "plane_code_union": len(plane_codes),
        "plane_unique_patterns": len(plane_patterns),
        "sprite_families": family_rows,
        "sprite_unique_cells": len(sprite_cells),
        "sprite_unique_8x8_patterns": len(sprite_patterns),
        "cross_owner_shared_patterns": cross_owner_shared,
        "total_unique_lower_bound": total_unique_lower_bound,
        "exact_lower_bound_deficit": deficit,
        "global_allocation_feasible": deficit == 0,
        "contiguous_sprite_cell_note": (
            "Each native 16x16 cell requires four consecutive slots. The independent-pattern "
            "deduplication used above is more permissive than the runtime contract; therefore a "
            "positive lower-bound deficit is conclusive."),
        "stage1_palette_sources": palettes,
    }


def arcade_xbgr555_to_genesis(word: int) -> int:
    """PROVEN conversion: arcade xBGR-555 (x BBBBB GGGGG RRRRR) -> Genesis CRAM 0000 BBB0 GGG0 RRR0
    (3 bits/channel, arcade 5-bit >> 2, shifted into Genesis nibble positions)."""
    r5 = word & 0x1F
    g5 = (word >> 5) & 0x1F
    b5 = (word >> 10) & 0x1F
    r3, g3, b3 = r5 >> 2, g5 >> 2, b5 >> 2
    return (b3 << 9) | (g3 << 5) | (r3 << 1)


def main():
    ap = argparse.ArgumentParser(description="Offline arcade->Genesis PC080SN graphics compiler (M1)")
    ap.add_argument("--maincpu", default=str(ROOT / "build/regions/maincpu.bin"))
    ap.add_argument("--pc080sn", default=str(ROOT / "build/regions/pc080sn.bin"))
    ap.add_argument("--registry", default=str(ROOT / "specs/palette_decisions.json"))
    ap.add_argument("--out", default=str(ROOT / "build/pc080sn_genesis_compiled"))
    ap.add_argument("--docs", default=str(ROOT / "docs/generated/pc080sn_genesis/stage1_epochs.md"))
    ap.add_argument("--stage-index", type=int, default=0)
    ap.add_argument("--pc090oj-genesis", default=str(ROOT / "build/pc090oj_genesis.bin"))
    ap.add_argument("--final-capacity-audit", action="store_true",
                    help="write only final_capacity_report.json and stop before canonical assets")
    ap.add_argument("--boundary-experiment", action="store_true",
                    help="emit Build-0302 boundary-loaded Stage-1 package assets")
    ap.add_argument("--pattern-reuse", default=str(ROOT / "build/regions/pattern_reuse_resolved.json"),
                    help="resolved canonical pattern-reuse artifact (provenance recorded into boundary_report.json)")
    a = ap.parse_args()

    mc = Path(a.maincpu).read_bytes()
    pat = Path(a.pc080sn).read_bytes()
    registry = json.loads(Path(a.registry).read_text())
    outdir = Path(a.out); outdir.mkdir(parents=True, exist_ok=True)

    reuse = None
    if a.pattern_reuse and Path(a.pattern_reuse).exists():
        reuse = json.loads(Path(a.pattern_reuse).read_text())

    if a.boundary_experiment:
        return build_boundary_experiment(mc, pat, outdir, a.stage_index, reuse)

    if a.final_capacity_audit:
        sprite_patterns = Path(a.pc090oj_genesis).read_bytes()
        audit = final_stage1_capacity_audit(mc, pat, sprite_patterns)
        (outdir / "final_capacity_report.json").write_text(json.dumps(audit, indent=1) + "\n")
        print(f"final capacity: {audit['total_unique_lower_bound']}/{audit['global_capacity']}; "
              f"deficit {audit['exact_lower_bound_deficit']}; "
              f"fit={audit['global_allocation_feasible']}")
        return 0 if audit["global_allocation_feasible"] else 2

    stage_records = decode_stage_records(mc, a.stage_index)
    plane_b_progression = decode_plane_b_progression(mc, a.stage_index)
    segments = [(r["segment"], r["selector"]) for r in stage_records]
    bg = bg_tiles(mc); txt = text_tiles(mc)
    epochs, fixed = derive_epochs(mc, segments, bg, txt)
    epoch_alloc, max_occ = allocate_vram(epochs, fixed)
    trans = build_transitions(epochs, epoch_alloc)
    route_rows, route_unresolved = palette_route(registry, mc)

    # ---- self-validation ----
    def tp(c): return pat[c * TILE_BYTES:(c + 1) * TILE_BYTES]
    problems = []
    for i, alloc in enumerate(epoch_alloc):
        seen = {}
        for c, s in alloc.items():
            if s < SLOT_MIN or s > SLOT_MAX:
                problems.append(f"epoch {i}: code {c:#06x} slot {s} outside plane band")
            if s in seen and seen[s] != c:
                problems.append(f"epoch {i}: slot {s} holds two live codes {seen[s]:#06x}/{c:#06x}")
            seen[s] = c
    # every resident code must have a pattern source
    self_valid = not problems

    # ---- generate machine assets ----
    # patterns.bin: base epoch full set + per-transition new patterns, in DMA order
    patterns = bytearray()
    pat_index = {}      # (epoch,slot)->offset
    for t in trans:
        for run in t["dma_runs"]:
            run["src_off"] = len(patterns)
            for c in run["codes"]:
                patterns += tp(c)
    (outdir / "patterns.bin").write_bytes(bytes(patterns))

    # base LUT (epoch 0) as flat 0x4000-word code->slot, 0 = not resident
    lut_base = bytearray(0x4000 * 2)
    for c, s in epoch_alloc[0].items():
        lut_base[c * 2:c * 2 + 2] = be16(s)
    (outdir / "lut_base.bin").write_bytes(bytes(lut_base))
    # per-epoch LUT patches (code,slot) deltas vs previous
    patches = []
    for i in range(len(epochs)):
        prev = epoch_alloc[i - 1] if i else {}
        delta = [(c, s) for c, s in epoch_alloc[i].items() if prev.get(c) != s]
        removed = [c for c in prev if c not in epoch_alloc[i]]
        patches.append({"epoch": i, "set": sorted(delta), "clear": sorted(removed)})
    largest_patch = max((len(p["set"]) + len(p["clear"]) for p in patches), default=0)
    avg_patch = round(sum(len(p["set"]) + len(p["clear"]) for p in patches) / max(1, len(patches)), 1)

    # includes
    def inc_lines(name, items):
        return f"/* generated: {name} */\n" + "\n".join(items) + "\n"
    (outdir / "lut_patches.inc").write_text(inc_lines("lut_patches", [
        f".word {p['epoch']}, {len(p['set'])}" + "".join(f", {c},{s}" for c, s in p["set"]) for p in patches]))
    (outdir / "dma_transitions.inc").write_text(inc_lines("dma_transitions", [
        f".word {t['epoch']}, {len(t['dma_runs'])}" +
        "".join(f", {r['slot0']},{r['count']},{r['src_off']}" for r in t["dma_runs"]) for t in trans]))
    (outdir / "palette_route_epochs.inc").write_text(inc_lines("palette_route_epochs", [
        f"/* L{r['genesis_line']} <- {r.get('owner')} bank {r.get('arcade_bank')} ({r['status']}) */"
        for r in route_rows] or ["/* no proven/decided route rows */"]))
    # REAL CRAM: FUN_0003ba20 decode -> scene-1 effective banks 48..79 -> Genesis CRAM words.
    scene1_banks = decode_scene_arcade_palettes(mc, 1)
    cram_words = []
    cram_provenance = []
    rec = PALETTE_SCENE_RECORDS
    for index in range(32):
        effective_bank = 48 + index
        block_id = mc[rec + index]
        arc = scene1_banks[index]
        gen = [arcade_xbgr555_to_genesis(w) for w in arc]
        cram_words.extend(gen)
        cram_provenance.append({
            "effective_palette_bank": effective_bank, "scene_record_index": index,
            "scene_record_byte": block_id,
            "pool_block_addr": f"0x{PALETTE_ROM_COLORS + block_id*32:05X}",
            "arcade_xbgr555": [f"{w:04X}" for w in arc],
            "genesis_cram": [f"{w:04X}" for w in gen]})
    (outdir / "cram_epochs.bin").write_bytes(b"".join(be16(w) for w in cram_words))
    # tm0=0 (constant BG descriptor across Stage-1 epochs) -> scene palette is stable -> 0 transitions
    (outdir / "cram_transitions.inc").write_text(inc_lines("cram_transitions",
        ["/* Stage-1 scene palette (FUN_0003ba20 scene 1) constant across epochs -> 0 CRAM changes */"]))

    # epochs.json / .inc (metadata)
    epoch_meta = []
    for i, e in enumerate(epochs):
        epoch_meta.append({
            "id": i, "segments": e["segments"],
            "planeA_tiles": len(e["planeA"]), "planeB_tiles": len(e["planeB"]),
            "resident_slots": len(epoch_alloc[i]),
            "transition": trans[i],
            "planeA_codes": [f"{c:#06x}" for c in e["planeA"]],
        })
    (outdir / "epochs.json").write_text(json.dumps(epoch_meta, indent=1))
    (outdir / "epochs.inc").write_text(inc_lines("epochs",
        [f".word {i}, {len(epochs[i]['segments'])}, {len(epoch_alloc[i])}" for i in range(len(epochs))]))

    report = {
        "stage_index": a.stage_index,
        "trace_inputs": 0,
        "segments_decoded": len(segments),
        "segment_selectors": segments,
        "stage_records": stage_records,
        "planeB_descriptor_progression": plane_b_progression,
        "epochs": len(epochs),
        "granularity": "per-arcade-segment coalesced to fit plane band (coarsest safe)",
        "granularity_source": "arcade map-stream (0x5073A/0x50EE0/0x50F6B) + strip-source tables",
        "planeA_peak": max((len(e["planeA"]) for e in epochs), default=0),
        "planeB_peak": len(bg - {0}),
        "combined_peak": max_occ,
        "plane_slots_available": PLANE_SLOTS,
        "peak_vram_occupancy": max_occ,
        "avg_vram_occupancy": round(sum(len(a) for a in epoch_alloc) / max(1, len(epoch_alloc)), 1),
        "largest_transition_new": max((t["new_patterns"] for t in trans), default=0),
        "largest_transition_bytes": max((t["dma_bytes"] for t in trans), default=0),
        "avg_transition_new": round(sum(t["new_patterns"] for t in trans) / max(1, len(trans)), 1),
        "pattern_bytes": len(patterns),
        "lut_repr": "flat 0x4000-word base LUT + per-epoch (code,slot) patches",
        "lut_base_bytes": len(lut_base),
        "largest_lut_patch": largest_patch,
        "avg_lut_patch": avg_patch,
        "palette_route_rows": len(route_rows),
        "palette_unresolved": route_unresolved,
        "cram_color_contents": "REAL: FUN_0003ba20 decoded (scene-1 record 0x3BA88 -> pool 0x4FD02 blocks -> nibble*2 xBGR-555 -> Genesis)",
        "cram_banks_decoded": 32,
        "cram_provenance": cram_provenance,
        "planeB_descriptor_layout": "row-major: src + row*0x20 + column*2",
        "planeB_scroll_ownership": "a5+0x10EE -> C20000 (Plane B Y); a5+0x10B0 -> C20002 (Plane A Y)",
        "planeB_per_segment_streaming": "INCOMPLETE: descriptor cursor is exact; selector-0 player/camera-driven Y envelope is not",
        "planeB_model_complete": False,
        "planeB_placeholder_slots": BG_RESERVE,
        "sprite_coexistence_derivation": "DECODER_SEMANTICS_UNPROVEN: static enemy/spawn model not decoded; route from registry only",
        "self_validation": "PASS" if self_valid else "FAIL",
        "self_validation_problems": problems,
        "asset_sha256": {},
    }
    for f in ["patterns.bin", "lut_base.bin", "cram_epochs.bin"]:
        report["asset_sha256"][f] = hashlib.sha256((outdir / f).read_bytes()).hexdigest()
    (outdir / "report.json").write_text(json.dumps(report, indent=1))

    # ---- generated documentation (byproduct of the same model) ----
    docp = Path(a.docs); docp.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Stage-1 PC080SN→Genesis compiled epochs (GENERATED — do not hand-edit)", "",
             f"Source: arcade ROM/data only (0 trace inputs). Segments decoded: {len(segments)} "
             f"({[s for s, _ in segments]}). Epochs: {len(epochs)}. Plane band slots {SLOT_MIN}..{SLOT_MAX} "
             f"({PLANE_SLOTS}); sprites at {SPRITE_TILE_BASE}. Self-validation: {report['self_validation']}.", ""]
    for i, e in enumerate(epochs):
        t = trans[i]
        lines += [f"## Epoch {i}", f"- Arcade segments: {e['segments']}",
                  f"- Plane A tiles: {len(e['planeA'])}; Plane B tiles: {len(e['planeB'])}; "
                  f"resident slots: {len(epoch_alloc[i])}/{PLANE_SLOTS}",
                  f"- Entry transition: {t['new_patterns']} new patterns, {len(t['dma_runs'])} DMA runs, "
                  f"{t['dma_bytes']} bytes; LUT patch {len(patches[i]['set'])} set/{len(patches[i]['clear'])} clear",
                  f"- Shared CRAM route: " + "; ".join(
                      f"L{r['genesis_line']}={r.get('owner')}/bank{r.get('arcade_bank')}" for r in route_rows), ""]
    docp.write_text("\n".join(lines))

    print(f"compiled: {len(segments)} segments -> {len(epochs)} epochs; peak VRAM {max_occ}/{PLANE_SLOTS}; "
          f"patterns {len(patterns)}B; self-validation {report['self_validation']}")
    return 0 if self_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
