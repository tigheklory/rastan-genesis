    .section .rodata,"a"
    .align 2
    .global rastan_pc090oj
rastan_pc090oj:
    /* Build 0325: offline Palette-Composer-reindexed R1/P1 sprite art (Test index_maps applied per
     * resolved (code,bank); all other codes byte-identical to the preconverted region). */
    .incbin "../../build/regions/pc090oj_editor.bin"

    /* Native Graphics Task 1: dedicated Rastan compositor frame pilot. */
    .global pc090oj_frame_table
    .global pc090oj_player_frame_table
    .align 2
pc090oj_frame_table:
pc090oj_player_frame_table:
    .incbin "../../build/pc090oj_frame_table.bin"

    /* Build 0428: player-only Genesis-native pieces. Primary frames use a
     * 6-byte compact form when attr is frame-wide and an 8-byte mixed form
     * only where body/weapon priority genuinely differs. Secondary is compact. */
    .global pc090oj_player_piece_table
    .align 2
pc090oj_player_piece_table:
    .incbin "../../build/pc090oj_player_piece_table.bin"

    .global pc090oj_player_frame_index
    .align 2
pc090oj_player_frame_index:
    .incbin "../../build/pc090oj_frame_index.bin"

    .global pc090oj_secondary_frame_index
    .align 2
pc090oj_secondary_frame_index:
    .incbin "../../build/pc090oj_secondary_frame_index.bin"

    .global pc090oj_generic_frame_index
    .align 2
pc090oj_generic_frame_index:
    .incbin "../../build/pc090oj_generic_frame_index.bin"

    /* Build 0426: compact exact-Level-B pieces: s16 dx, s16 dy, u16 finalized key.
     * Frame-invariant attributes live once in the corresponding 8-byte index. */
    .global pc090oj_generic_piece_table
    .align 2
pc090oj_generic_piece_table:
    .incbin "../../build/pc090oj_generic_piece_table.bin"

    .global pc090oj_universal_frame_index
    .align 2
pc090oj_universal_frame_index:
    .incbin "../../build/pc090oj_universal_frame_index.bin"

    .global pc090oj_special_frame_index
    .align 2
pc090oj_special_frame_index:
    .incbin "../../build/pc090oj_special_frame_index.bin"

    /* Genesis-native death presentation: 8-byte frame records and compact
     * {dx,dy,raw-pattern-code} pieces shared by every effective-bank context. */
    .global pc090oj_death_frame_index
    .align 2
pc090oj_death_frame_index:
    .incbin "../../build/pc090oj_death_frame_index.bin"

    .global pc090oj_death_piece_table
    .align 2
pc090oj_death_piece_table:
    .incbin "../../build/pc090oj_death_piece_table.bin"

    .global pc090oj_generic_base_lut
    .align 2
pc090oj_generic_base_lut:
    .incbin "../../build/pc090oj_generic_base_lut.bin"

    .global pc090oj_generic_usage_table
    .align 2
pc090oj_generic_usage_table:
    .incbin "../../build/pc090oj_generic_usage_table.bin"

    .global pc090oj_player_frame_residency
    .align 2
pc090oj_player_frame_residency:
    .incbin "../../build/pc090oj_frame_residency.bin"

    /* Build 0459: semantic GAME OVER / score / P1 glyph slice (codes
     * 0x02A..0x048), reindexed from each current Test object index_map.
     * Bit-15-tagged native producers select this data; ordinary sprite
     * residency remains separate. */
    .global rastan_pc090oj_semantic_profile
    .align 2
rastan_pc090oj_semantic_profile:
    .incbin "../../build/pc090oj_semantic_profile_genesis.bin"

    .global pc090oj_slot_lut
    .align 2
pc090oj_slot_lut:
    .incbin "../../build/pc090oj_slot_lut.bin"

    .global pc090oj_blank_code_bitset
    .align 2
pc090oj_blank_code_bitset:
    .incbin "../../build/pc090oj_blank_bitset.bin"

    /* Build 0359: exact pre-oriented opaque bounding boxes (16 bytes/code).
     * The four N/H/V/HV variants are stored component-major so the native
     * finalizer indexes directly by the two attribute flip bits. */
    .global pc090oj_opaque_bbox
    .align 2
pc090oj_opaque_bbox:
    .incbin "../../build/pc090oj_opaque_bbox.bin"
