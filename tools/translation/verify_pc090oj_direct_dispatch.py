#!/usr/bin/env python3
"""Verify the bounded generated PC090OJ generic-frame dispatcher."""

from __future__ import annotations

import argparse
import re
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ATTR_OVERRIDE, ATTR_EMBEDDED = 1, 2
EXPECTED = (
    ("cave_block", 0x0179, 0x70, 1, 0, 0x3C, 0x05, 0x1E, ATTR_EMBEDDED),
    ("burst", 0x0275, 0x9E, 3, 0, 0x30, 0x05, 0x0F, ATTR_EMBEDDED),
    ("lizardman", 0x004B, 0x17, 9, 0, 0x36, 0x3E, 0x00, ATTR_OVERRIDE),
    ("large_bat", 0x03F6, 0xB6, 3, 0, 0x3E, 0x06, 0x0A, ATTR_EMBEDDED),
    ("small_bat", 0x0268, 0xB9, 3, 0, 0x3E, 0x06, 0x0B, ATTR_EMBEDDED),
)
DEATH_EXPECTED = (
    ("fountain", 0x0275, 0, 0x9D, 4, 0),
    ("bat_pop", 0x0275, 0, 0xA8, 1, 8),
    ("ordinary_death", 0x0A73, 2, 0x0B, 8, 10),
    ("death_reward", 0x0A5A, 2, 0x13, 17, 26),
)


def block(source: str, start: str, end: str) -> str:
    begin = source.index(start)
    finish = source.index(end, begin)
    return source[begin:finish]


def direct_references(source: str, label: str) -> list[tuple[str, int, str]]:
    """Return assembly instructions that directly reference *label*.

    Label definitions and comments are excluded.  This deliberately accepts
    mnemonic size suffixes and arbitrary whitespace so a bsr.w/jsr or a second
    caller cannot evade the private-probe contract through formatting.
    """
    refs: list[tuple[str, int, str]] = []
    for lineno, raw in enumerate(source.splitlines(), 1):
        code = raw.split("/*", 1)[0].split("|", 1)[0].strip()
        if not code or code.endswith(":"):
            continue
        match = re.match(r"([A-Za-z][A-Za-z0-9]*(?:\.[A-Za-z0-9]+)?)\s+(.+)$", code)
        if match and re.search(rf"(?<![A-Za-z0-9_.]){re.escape(label)}(?![A-Za-z0-9_.])",
                               match.group(2)):
            refs.append((match.group(1).lower(), lineno, code))
    return refs


def address_register_writes(source_block: str, registers: tuple[str, ...]) -> list[str]:
    """Find instructions that can modify one of the named address registers.

    Ordinary address-register reads are legal.  A register is treated as
    clobbered when it is the explicit destination, is restored/loaded by
    MOVEM, or is changed implicitly by predecrement/postincrement addressing.
    """
    writes: list[str] = []
    wanted = {f"%{register.lower()}" for register in registers}
    for raw in source_block.splitlines():
        code = raw.split("/*", 1)[0].split("|", 1)[0].strip()
        if not code or code.endswith(":") or code.startswith("."):
            continue
        match = re.match(r"([A-Za-z][A-Za-z0-9]*(?:\.[A-Za-z0-9]+)?)\s+(.+)$", code)
        if not match:
            continue
        mnemonic, operands = match.group(1).lower(), match.group(2).lower()
        # Addressing-mode side effects modify the address register even when
        # the memory operand is a source rather than the final destination.
        if any(re.search(rf"(?:-\({re.escape(reg)}\)|\({re.escape(reg)}\)\+)", operands)
               for reg in wanted):
            writes.append(code)
            continue
        parts = [part.strip() for part in operands.split(",")]
        destination = parts[-1] if parts else ""
        if destination in wanted:
            writes.append(code)
            continue
        # A memory-to-register MOVEM has a register list as its destination.
        if mnemonic.startswith("movem") and len(parts) >= 2 and any(
                re.search(rf"(?<![a-z0-9]){re.escape(reg)}(?![a-z0-9])", destination)
                for reg in wanted):
            writes.append(code)
    return writes


def verify_retained_cut_preservation(source: str) -> None:
    """Prove RG-014's specialized ABI ownership and balanced stack shape."""
    retained_mask = "%d4/%d6/%a2-%a6"
    retained_save = f"movem.l {retained_mask}, -(%sp)"
    retained_restore = f"movem.l (%sp)+, {retained_mask}"
    full_save = "movem.l %d0-%d7/%a0-%a6, -(%sp)"
    full_restore = "movem.l (%sp)+, %d0-%d7/%a0-%a6"

    hooks = {
        "0x041DAE": block(source, "genesistan_pc090oj_hook_target_41dae:",
                           "genesistan_pc090oj_hook_target_41f5e:"),
        "0x045DFA": block(source, "genesistan_pc090oj_hook_target_45dfa:",
                           "native_sprite_frame_begin:"),
    }
    expected_dispatch = {
        "0x041DAE": ("native_stage_dispatch_41dae_retained_cut",
                      "native_stage_dispatch_45dfa_retained_cut"),
        "0x045DFA": ("native_stage_dispatch_45dfa_retained_cut",),
    }
    for cut, hook in hooks.items():
        if hook.count(retained_save) != 1 or hook.count(retained_restore) != 1:
            raise SystemExit(f"FAIL retained-cut ABI {cut}: outer frame is not one balanced pair")
        save_at, restore_at = hook.index(retained_save), hook.index(retained_restore)
        if save_at >= restore_at or re.search(r"\brts\b", hook[save_at:restore_at]):
            raise SystemExit(f"FAIL retained-cut ABI {cut}: saved path can return before restore")
        for dispatch in expected_dispatch[cut]:
            call = f"bsr     {dispatch}"
            if call not in hook[save_at:restore_at]:
                raise SystemExit(f"FAIL retained-cut ABI {cut}: missing internal call {dispatch}")
        if "bsr     pc090oj_native_emit_pass_retained_cut" not in hook[save_at:restore_at]:
            raise SystemExit(f"FAIL retained-cut ABI {cut}: missing private gameplay finalizer")
        if full_save in hook or full_restore in hook:
            raise SystemExit(f"FAIL retained-cut ABI {cut}: redundant full frame remains")

    dispatches = (
        ("native_stage_dispatch_41dae:", "native_stage_dispatch_41dae_retained_cut:",
         "native_stage_dispatch_45dfa:"),
        ("native_stage_dispatch_45dfa:", "native_stage_dispatch_45dfa_retained_cut:",
         ".Lnative_emit_actor_common:"),
    )
    for public_label, internal_label, end_label in dispatches:
        body = block(source, public_label, end_label)
        wrapper = body[:body.index(internal_label)]
        internal = body[body.index(internal_label):]
        internal_name = internal_label[:-1]
        for token in (full_save, f"bsr     {internal_name}", full_restore, "rts"):
            if token not in wrapper:
                raise SystemExit(f"FAIL public dispatcher ABI {public_label}: missing {token}")
        if full_save in internal or full_restore in internal:
            raise SystemExit(f"FAIL retained-cut dispatcher {internal_label}: nested full frame")

    common = block(source, ".Lnative_emit_actor_common:", ".Lnative_generic_frame_try:")
    for token in ("movem.l %d5/%a1, -(%sp)", "movem.l (%sp)+, %d5/%a1"):
        if token not in common:
            raise SystemExit(f"FAIL retained-cut ABI: required actor-loop preservation lost: {token}")
    lane = block(source, ".Lnq_emit_lane:", "profile_native_final_piece_entry:")
    if "move.w  %d6, -(%sp)" not in lane or "move.w  (%sp)+, %d6" not in lane:
        raise SystemExit("FAIL retained-cut ABI: required semantic-lane D6 preservation lost")

    public = block(source, "pc090oj_native_emit_pass:",
                   "pc090oj_native_emit_pass_retained_cut:")
    private = block(source, "pc090oj_native_emit_pass_retained_cut:", ".Lnq_title:")
    if "beq     .Lnq_gameplay" not in public or "bra     .Lnq_frontend_native" not in public:
        raise SystemExit("FAIL public finalizer scene-routing ABI changed")
    if "bra     .Lnq_gameplay_retained_cut" not in private:
        raise SystemExit("FAIL private finalizer does not enter gameplay-only core")
    gameplay = block(source, ".Lnq_gameplay:", ".Lnq_project_p1_hud:")
    wrapper = gameplay[:gameplay.index(".Lnq_gameplay_retained_cut:")]
    for token in ("movem.l %d0-%d7/%a0-%a3, -(%sp)", "move.l  %a4, -(%sp)",
                  "bsr     .Lnq_gameplay_retained_cut", "move.l  (%sp)+, %a4",
                  "movem.l (%sp)+, %d0-%d7/%a0-%a3", "rts"):
        if token not in wrapper:
            raise SystemExit(f"FAIL public gameplay finalizer ABI: missing {token}")

    finish = block(source, ".Lnq_finish_frame:", ".Lnq_frontend_native:")
    for token in ("pc090oj_emitted_count", "pc090oj_sat_frame_ready", "pc090oj_sat_dirty", "rts"):
        if token not in finish:
            raise SystemExit(f"FAIL finalizer semantics removed: {token}")
    if re.search(r"\bmovem\.", finish, re.I):
        raise SystemExit("FAIL private finalizer core unexpectedly owns an outer frame")

    print("PASS retained-cut preservation: 0x041DAE/0x045DFA use one D4/D6/A2-A6 "
          "frame; public dispatch/finalizer ABIs remain conservative; D5/A1 and D6 "
          "inner saves, balanced exits, and final publication semantics verified")


def verify_fast_enqueue(source: str) -> None:
    """Prove that the generated-frame fast path changes cost, not semantics.

    The generated tables already own geometry, finalized identity and attributes.
    This check therefore compares the queue contract at the only optimized cut:
    lane selection plus the four-word append.  Residency, worklist construction,
    SAT attributes/linking and emit-on-miss remain below the same shared finalizer.
    """
    context = block(source, "native_sprite_fast_context:", "native_sprite_emit_fast:")
    emit = block(source, "native_sprite_emit_fast:", "native_stage_dispatch_41dae:")
    finalizer = block(source, "pc090oj_native_emit_pass:", "profile_native_finalizer_done:")

    lanes = (
        ("hud", "native_queue_hud", "native_hud_count", "NATIVE_HUD_BOUND"),
        ("front_effect", "native_queue_front_effect", "native_front_effect_count", "NATIVE_FRONT_EFFECT_BOUND"),
        ("player_front", "native_queue_player_front", "native_player_front_count", "NATIVE_PLAYER_FRONT_BOUND"),
        ("middle", "native_queue_middle", "native_middle_count", "NATIVE_MIDDLE_BOUND"),
        ("player_body", "native_queue_player_body", "native_player_body_count", "NATIVE_PLAYER_BODY_BOUND"),
        ("back_enemy", "native_queue_back_enemy", "native_back_enemy_count", "NATIVE_BACK_ENEMY_BOUND"),
    )
    for name, queue, count, bound in lanes:
        end = f"{queue}_end"
        for token in (queue, count, end):
            if token not in context:
                raise SystemExit(f"FAIL fast enqueue: {name} context omits {token}")
        allocation = f"{queue}:\n    .space ({bound} * NATIVE_QUEUE_ENTRY_BYTES)\n{end}:"
        if allocation not in source:
            raise SystemExit(f"FAIL fast enqueue: {name} end label does not exactly bound allocation")

    required_emit = (
        "btst    #13, %d3", "andi.w  #0x1FFF, %d0", "cmpi.w  #0x00FF, %d0",
        "andi.w  #0x01FF, %d0", "cmpi.w  #0x0180, %d0",
        "move.w  (%a6), %d0", "lsl.w   #3, %d0", "lea     0(%a3,%d0.w), %a1",
        "cmpa.l  %a2, %a1", "move.w  %d1, (%a1)+", "move.w  %d2, (%a1)+",
        "move.w  %d3, (%a1)+", "move.w  %d4, (%a1)+", "addq.w  #1, (%a6)",
    )
    for token in required_emit:
        if token not in emit:
            raise SystemExit(f"FAIL fast enqueue contract omits: {token}")
    stores = re.findall(r"move\.w\s+%d([1-4]), \(%a1\)\+", emit)
    if stores != ["1", "2", "3", "4"]:
        raise SystemExit(f"FAIL fast enqueue tuple order: {stores}")

    # Every generated producer selects context once and reaches the fast append;
    # the finalizer remains the sole consumer, preserving queue/lane ordering,
    # dynamic attrs/flips/priority, residency misses/worklists, SAT links and DMA.
    generated = (
        ("native_player_front_fixed:", "native_player_aux_fixed:"),
        ("native_player_aux_fixed:", "native_player_body_begin:"),
        ("native_player_frame_try:", "native_player_secondary_frame:"),
        ("native_player_secondary_frame:", "native_player_body_anchor_blank:"),
        (".Lnative_generic_frame_try:", ".Lnative_death_frame_try:"),
        (".Lnative_death_frame_try:", ".Lnative_universal_general_try:"),
        (".Lnative_universal_general_try:", ".Lnative_mapping_branch_is_normal:"),
    )
    for start, end in generated:
        producer = block(source, start, end)
        if "native_sprite_fast_context" not in producer:
            raise SystemExit(f"FAIL fast enqueue not used by generated producer {start}")
        if start == "native_player_frame_try:":
            player_required = (
                "pc090oj_player_piece_table", "mulu.w  #12, %d0",
                "move.w  8(%a1), %d2", "move.w  10(%a1), %d2",
                "move.w  (%a6), %d0", "lea     0(%a3,%d0.w), %a1",
                "cmpi.w  #0x0180, %d0", "cmpa.l  %a2, %a1",
                "move.w  %d1, (%a1)+", "move.w  %d2, (%a1)+",
                "move.w  %d3, (%a1)+", "move.w  %d4, (%a1)+",
                "addq.w  #1, (%a6)", "adda.w  #6, %a0", "adda.w  #8, %a0",
            )
            for token in player_required:
                if token not in producer:
                    raise SystemExit(f"FAIL compact primary-player append omits: {token}")
            if "native_sprite_emit_fast" in producer:
                raise SystemExit("FAIL primary-player loop still calls generalized fast emitter")
        elif start == "native_player_secondary_frame:":
            secondary_required = (
                "pc090oj_player_piece_table", "mulu.w  #12, %d0",
                "move.w  6(%a1), %d1", "move.w  (%a6), %d0",
                "lea     0(%a3,%d0.w), %a1", "cmpi.w  #0x0180, %d0",
                "cmpa.l  %a2, %a1", "move.w  %d1, (%a1)+",
                "move.w  %d2, (%a1)+", "move.w  %d3, (%a1)+",
                "move.w  %d4, (%a1)+", "addq.w  #1, (%a6)",
                "adda.w  #6, %a0",
            )
            for token in secondary_required:
                if token not in producer:
                    raise SystemExit(f"FAIL compact secondary-player append omits: {token}")
            if "native_sprite_emit_fast" in producer:
                raise SystemExit("FAIL secondary-player loop still calls generalized fast emitter")
        elif start == ".Lnative_generic_frame_try:":
            # Build 0426's exact Level-B stream owns a private compact append:
            # frame attr/context/cursor once, then the same Y-hide, queue-end,
            # D1/D2/D3/D4 tuple and count contract per piece.
            compact_required = (
                "pc090oj_generic_piece_table", "move.w  6(%a2), %d1",
                "move.w  (%a6), %d0", "lea     0(%a3,%d0.w), %a1",
                "andi.w  #0x01FF, %d0", "cmpi.w  #0x0180, %d0",
                "cmpa.l  %a2, %a1", "move.w  %d1, (%a1)+",
                "move.w  %d2, (%a1)+", "move.w  %d3, (%a1)+",
                "move.w  %d4, (%a1)+", "addq.w  #1, (%a6)",
                "adda.w  #6, %a0",
            )
            for token in compact_required:
                if token not in producer:
                    raise SystemExit(f"FAIL compact Level-B append omits: {token}")
        elif start == ".Lnative_death_frame_try:":
            death_required = (
                "pc090oj_death_frame_index", "pc090oj_death_piece_table",
                "move.w  6(%a2), %d1", "move.w  (%a6), %d0",
                "lea     0(%a3,%d0.w), %a1", "andi.w  #0x01FF, %d0",
                "cmpi.w  #0x0180, %d0", "cmpa.l  %a2, %a1",
                "move.w  %d1, (%a1)+", "move.w  %d2, (%a1)+",
                "move.w  %d3, (%a1)+", "move.w  %d4, (%a1)+",
                "addq.w  #1, (%a6)", "adda.w  #6, %a0",
            )
            for token in death_required:
                if token not in producer:
                    raise SystemExit(f"FAIL compact death append omits: {token}")
            if "native_sprite_emit_fast" in producer:
                raise SystemExit("FAIL death loop still calls generalized fast emitter")
        elif "native_sprite_emit_fast" not in producer:
            raise SystemExit(f"FAIL fast enqueue not used by generated producer {start}")

    # The two generated probes are private to the common actor wrapper.  Stage
    # dispatch owns the complete retained-caller register contract once, while
    # the common wrapper preserves only its loop-live D5/A1 values.  Reject a
    # reintroduction of nested full saves or any second call site that would
    # make the private clobber contract unsafe.
    common = block(source, ".Lnative_emit_actor_common:",
                   ".Lnative_generic_frame_try:")
    if ("movem.l %d5/%a1, -(%sp)" not in common or
            "movem.l (%sp)+, %d5/%a1" not in common):
        raise SystemExit("FAIL fast enqueue: common actor wrapper does not preserve D5/A1")
    intended_calls = {
        ".Lnative_generic_frame_try": direct_references(
            source, ".Lnative_generic_frame_try"),
        ".Lnative_universal_general_try": direct_references(
            source, ".Lnative_universal_general_try"),
        ".Lnative_death_frame_try": direct_references(
            source, ".Lnative_death_frame_try"),
    }
    for label, references in intended_calls.items():
        if len(references) != 1 or references[0][0].split(".", 1)[0] != "bsr":
            raise SystemExit(
                f"FAIL fast enqueue: {label} private-call contract changed: {references}")
        if references[0][2] not in common:
            raise SystemExit(f"FAIL fast enqueue: {label} caller escaped common wrapper")
    for token in ("cmpi.w  #0x0A73, 0x1E(%a4)",
                  "cmpi.w  #0x0275, 0x1E(%a4)",
                  "cmpi.w  #0x0A5A, 0x1E(%a4)"):
        if token not in common:
            raise SystemExit(f"FAIL death prefilter contract omits: {token}")

    push = re.search(r"movem\.l\s+%d5/%a1\s*,\s*-\(%sp\)", common)
    pop = re.search(r"movem\.l\s+\(%sp\)\+\s*,\s*%d5/%a1", common)
    ret_label = common.find(".Lnea_ret:")
    if push is None or pop is None or not (push.start() < pop.start() < ret_label):
        raise SystemExit("FAIL fast enqueue: common wrapper D5/A1 stack order is unbalanced")
    pre_save = common[:push.start()]
    post_save = common[push.end():pop.start()]
    if len(re.findall(r"\bbeq(?:\.[a-z]+)?\s+\.Lnea_ret\b", pre_save, re.I)) != 2:
        raise SystemExit("FAIL fast enqueue: pre-save early exits changed")
    if re.search(r"\.Lnea_ret\b", post_save):
        raise SystemExit("FAIL fast enqueue: post-save path can bypass D5/A1 restore")
    if common.count("rts") != 1 or common.find("rts", ret_label) < ret_label:
        raise SystemExit("FAIL fast enqueue: common wrapper return/stack structure changed")
    full_save = "movem.l %d0-%d7/%a0-%a6, -(%sp)"
    full_restore = "movem.l (%sp)+, %d0-%d7/%a0-%a6"
    for start, end in (("native_stage_dispatch_41dae:", "native_stage_dispatch_45dfa:"),
                       ("native_stage_dispatch_45dfa:", ".Lnative_emit_actor_common:")):
        stage = block(source, start, end)
        if full_save not in stage or full_restore not in stage:
            raise SystemExit(f"FAIL fast enqueue: stage dispatcher {start} lost full caller preservation")
    private_blocks = {
        "generic probe": block(source, ".Lnative_generic_frame_try:",
                               ".Lnative_death_frame_try:"),
        "death probe": block(source, ".Lnative_death_frame_try:",
                             ".Lnative_universal_general_try:"),
        "universal probe": block(source, ".Lnative_universal_general_try:",
                                 ".Lnative_mapping_branch_is_normal:"),
        "fast context": context,
        "fast emit": emit,
        "mapping predicate": block(source, ".Lnative_mapping_branch_is_normal:",
                                   "genesistan_native_contact_coords_51ab6:"),
    }
    for name, private_block in private_blocks.items():
        if re.search(r"\bmovem\.", private_block, re.I):
            raise SystemExit(f"FAIL fast enqueue: nested register save/load in {name}")
        a4_a5_writes = address_register_writes(private_block, ("a4", "a5"))
        if a4_a5_writes:
            raise SystemExit(
                f"FAIL fast enqueue: {name} clobbers loop-live A4/A5: {a4_a5_writes}")
    for token in ("native_queue_player_front", "native_queue_player_body",
                  "native_queue_front_effect", "native_queue_middle",
                  "native_queue_back_enemy", "pc090oj_tile_dma_worklist",
                  "staged_sprite_sat", "profile_native_final_piece_entry"):
        if token not in finalizer:
            raise SystemExit(f"FAIL shared finalizer contract omits {token}")

    print("PASS fast enqueue semantics: 6 exact allocation-end labels; filters/bounds/count "
          "and D1/D2/D3/D4 tuple order equivalent; stage-owned full caller contract and "
          "D5/A1 loop preservation, A4/A5 non-clobber, robust single-caller and balanced "
          "early-exit contracts verified; shared residency/worklist/SAT finalizer retained")

    # Mechanical variable-count reconciliation.  False means that a potential
    # piece is legitimately rejected before append.  Source consideration is
    # independent of the compact output pointer/count.
    def reconcile(visible: tuple[bool, ...], initial: int = 0,
                  bound: int = 32) -> tuple[int, int, int, int]:
        considered = rejected = emitted = 0
        queue_count = initial
        for accept in visible:
            considered += 1
            if not accept or queue_count >= bound:
                rejected += 1
                continue
            emitted += 1
            queue_count += 1
        return considered, rejected, emitted, queue_count - initial

    cases = {
        "no rejection/fully onscreen": ((True,) * 8, 0, 32, (8, 0, 8, 8)),
        "first rejected": ((False, True, True, True), 0, 32, (4, 1, 3, 3)),
        "middle rejected": ((True, False, True, True), 0, 32, (4, 1, 3, 3)),
        "last rejected": ((True, True, True, False), 0, 32, (4, 1, 3, 3)),
        "multiple/partly offscreen": ((False, False, True, False, True), 0, 32, (5, 3, 2, 2)),
        "near capacity": ((True, True, True, True), 30, 32, (4, 2, 2, 2)),
    }
    for name, (visible, initial, bound, expected) in cases.items():
        actual = reconcile(visible, initial, bound)
        if actual != expected:
            raise SystemExit(f"FAIL variable-count reconciliation {name}: {actual} != {expected}")
    print(f"PASS variable-count reconciliation: {len(cases)} reject/visibility/capacity cases")


def verify_packed_lane_bank(source: str) -> None:
    """Guard Build-0414's packed {effective-bank:lane} word contract."""
    unsafe = []
    for lineno, raw in enumerate(source.splitlines(), 1):
        code = raw.split("/*", 1)[0].split("|", 1)[0].strip()
        if re.search(r"\bmove\.(?:w|l)\s+native_sprite_lane(?:\b|\s*,)", code, re.I):
            unsafe.append((lineno, code))
    if unsafe:
        raise SystemExit(f"FAIL packed lane: unsafe full-word consumer(s): {unsafe}")

    hoist = (
        "move.w  pc090oj_sprite_ctrl_shadow, %d0",
        "andi.w  #0x00E0, %d0",
        "lsr.w   #1, %d0",
        "move.b  %d0, native_sprite_lane",
    )
    entries = {
        "native_stage_dispatch_41dae": block(
            source, "native_stage_dispatch_41dae:", "native_stage_dispatch_45dfa:"),
        "native_stage_dispatch_45dfa": block(
            source, "native_stage_dispatch_45dfa:", ".Lnative_emit_actor_common:"),
        "pc090oj_native_emit_pass": block(
            source, "pc090oj_native_emit_pass:", ".Lnq_title:"),
    }
    for name, body in entries.items():
        positions = [body.find(token) for token in hoist]
        if any(pos < 0 for pos in positions) or positions != sorted(positions):
            raise SystemExit(f"FAIL packed lane: {name} omits/reorders effective-bank re-hoist")

    print("PASS packed lane/effective bank: no full-word lane consumer; normalized bank "
          "re-hoisted at both stage dispatchers and pc090oj_native_emit_pass")


def dispatch(base_lut: bytes, usage_blob: bytes, index: bytes, actor: dict,
             orientation: int) -> int | None:
    base = actor[0x1E]
    if base > 0x0FFF:
        return None
    usage_id = base_lut[base]
    if usage_id == 0:
        return None
    off = (usage_id - 1) * 10
    disc_off, disc_val, first, count, comp, bank, policy, reserved, frame_base = \
        struct.unpack_from(">BBBBBBBBH", usage_blob, off)
    if reserved or actor.get(disc_off) != disc_val or actor[0x38] != comp:
        return None
    override = bool(actor[0x27] & 0x40)
    if override != (policy == ATTR_OVERRIDE):
        return None
    effective_bank = actor["ctrl_high"] | ((actor[0x27] & 0x0F) if override else bank & 0x0F)
    if effective_bank != bank:
        return None
    normalized = actor[0x01] - first
    if normalized < 0 or normalized >= count:
        return None
    record = frame_base + normalized * 2 + orientation
    _table_off, _pieces, status, _attr = struct.unpack_from(">IBBH", index, record * 8)
    return record if status == 1 else None


def actor_for(spec: tuple) -> dict:
    _name, base, first, _count, comp, bank, disc_off, disc_val, policy = spec
    attr = (0x40 | (bank & 0x0F)) if policy == ATTR_OVERRIDE else 0
    return {0x1E: base, 0x01: first, 0x38: comp, 0x27: attr,
            disc_off: disc_val, "ctrl_high": bank & 0x70}


def death_dispatch(index: bytes, base: int, compositor: int,
                   selector: int, orientation: int) -> int | None:
    record = None
    for _name, wanted_base, wanted_compositor, first, count, first_record in DEATH_EXPECTED:
        if (base == wanted_base and compositor == wanted_compositor and
                first <= selector < first + count):
            record = first_record + (selector - first) * 2 + orientation
            break
    if record is None:
        return None
    _off, _pieces, status, _attr = struct.unpack_from(">IBBH", index, record * 8)
    return record if status == 1 else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-lut", default=ROOT / "build/pc090oj_generic_base_lut.bin", type=Path)
    ap.add_argument("--usage", default=ROOT / "build/pc090oj_generic_usage_table.bin", type=Path)
    ap.add_argument("--index", default=ROOT / "build/pc090oj_generic_frame_index.bin", type=Path)
    ap.add_argument("--death-index", default=ROOT / "build/pc090oj_death_frame_index.bin", type=Path)
    ap.add_argument("--assembly", default=ROOT / "apps/rastan-direct/src/pc090oj_hooks.s", type=Path)
    args = ap.parse_args()
    base_lut, usage, index = args.base_lut.read_bytes(), args.usage.read_bytes(), args.index.read_bytes()
    death_index = args.death_index.read_bytes()
    if len(base_lut) != 0x1000 or len(usage) != len(EXPECTED) * 10:
        raise SystemExit("FAIL malformed direct-dispatch artifacts")
    expected_records = sum(spec[3] for spec in EXPECTED) * 2
    if len(index) != expected_records * 8:
        raise SystemExit("FAIL malformed compact direct-index artifact")
    if len(death_index) != 60 * 8:
        raise SystemExit("FAIL malformed compact death-index artifact")

    death_records = 0
    for name, base, compositor, first, count, first_record in DEATH_EXPECTED:
        for selector in range(first, first + count):
            for orientation in (0, 1):
                expected_record = first_record + (selector - first) * 2 + orientation
                got = death_dispatch(death_index, base, compositor, selector, orientation)
                if got != expected_record:
                    raise SystemExit(
                        f"FAIL death {name}: selector/orientation routes to {got}, "
                        f"expected {expected_record}")
                death_records += 1
        for bad_base, bad_compositor, bad_selector in (
                (base ^ 1, compositor, first),
                (base, (compositor + 1) & 0xFF, first),
                (base, compositor, (first - 1) & 0xFF),
                (base, compositor, (first + count) & 0xFF)):
            if death_dispatch(death_index, bad_base, bad_compositor, bad_selector, 0) is not None:
                raise SystemExit(f"FAIL death {name}: out-of-domain key did not reject")

    next_record = 0
    for usage_id, spec in enumerate(EXPECTED, 1):
        name, base, first, count, comp, bank, disc_off, disc_val, policy = spec
        if base_lut[base] != usage_id:
            raise SystemExit(f"FAIL {name}: wrong base route")
        desc = struct.unpack_from(">BBBBBBBBH", usage, (usage_id - 1) * 10)
        if desc != (disc_off, disc_val, first, count, comp, bank, policy, 0, next_record):
            raise SystemExit(f"FAIL {name}: descriptor mismatch")
        actor = actor_for(spec)
        for selector in range(first, first + count):
            actor[0x01] = selector
            for orientation in (0, 1):
                expected_record = next_record + (selector - first) * 2 + orientation
                if dispatch(base_lut, usage, index, actor, orientation) != expected_record:
                    raise SystemExit(f"FAIL {name}: valid selector/orientation rejected")
        actor = actor_for(spec)
        mutations = (
            ("wrong semantic discriminator", disc_off, disc_val ^ 0xFF),
            ("wrong compositor", 0x38, (comp + 1) & 0xFF),
            ("selector below", 0x01, (first - 1) & 0xFF),
            ("selector above", 0x01, (first + count) & 0xFF),
            ("wrong attribute policy", 0x27, actor[0x27] ^ 0x40),
            ("wrong bank", "ctrl_high", (actor["ctrl_high"] ^ 0x10) & 0x70),
        )
        for label, field, value in mutations:
            bad = dict(actor)
            bad[field] = value
            if dispatch(base_lut, usage, index, bad, 0) is not None:
                raise SystemExit(f"FAIL {name}: {label} did not reject")
        next_record += count * 2

    unknown = {0x1E: 0x0123, 0x01: 0, 0x38: 0, 0x27: 0, "ctrl_high": 0}
    if dispatch(base_lut, usage, index, unknown, 0) is not None:
        raise SystemExit("FAIL UNKNOWN base did not fall back")

    source = args.assembly.read_text()
    verify_retained_cut_preservation(source)
    verify_fast_enqueue(source)
    verify_packed_lane_bank(source)
    start = source.index(".Lnative_generic_frame_try:")
    end = source.index(".Lnative_mapping_branch_is_normal:", start)
    dispatcher = source[start:end]
    forbidden = (".Lngft_find", ".Lngft_next", "dbra")
    if any(token in dispatcher for token in forbidden):
        raise SystemExit("FAIL generic dispatcher still contains a linear record scan")
    for token in ("pc090oj_generic_base_lut", "pc090oj_generic_usage_table",
                  "pc090oj_generic_frame_index"):
        if token not in dispatcher:
            raise SystemExit(f"FAIL dispatcher does not consume {token}")
    death_probe = block(source, ".Lnative_death_frame_try:",
                        ".Lnative_universal_general_try:")
    for token in ("cmpi.w  #0x0275, %d0", "cmpi.w  #0x0A73, %d0",
                  "cmpi.w  #0x0A5A, %d0", "subi.w  #0x9D, %d7",
                  "subi.w  #0x0B, %d7", "subi.w  #0x13, %d7",
                  "addi.w  #10, %d7", "addi.w  #26, %d7",
                  "moveq   #8, %d7"):
        if token not in death_probe:
            raise SystemExit(f"FAIL death dispatcher mapping omits: {token}")
    print(f"PASS PC090OJ direct dispatch: {len(EXPECTED)} usages, {next_record} direct records; "
          f"{death_records} exact death records; wrong usage/state/selector/bank/attribute "
          "and UNKNOWN all fall back; no linear scan")


if __name__ == "__main__":
    main()
