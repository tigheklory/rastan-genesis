# Whole-Game Original-Arcade Enemy/Sprite Lexicon Evidence

Unknown palettes are always rendered in grayscale and never contribute colors to the optimizer.

## round1_boss_composite
- Name/category: Round 1 boss composite (semantic name unresolved) / BOSS
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 2772 at round1_boss
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## round2_boss_composite
- Name/category: Round 2 boss composite (semantic name unresolved) / BOSS
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 2944 at round2_boss
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## round3_boss_composite
- Name/category: Round 3 boss composite (semantic name unresolved) / BOSS
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 3600 at round3_boss
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## round4_boss_composite
- Name/category: Round 4 boss composite (semantic name unresolved) / BOSS
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 2772 at round4_boss
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## round5_boss_composite
- Name/category: Round 5 boss composite (semantic name unresolved) / BOSS
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 3674 at round5_boss
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## round6_boss_composite
- Name/category: Round 6 boss composite (semantic name unresolved) / BOSS
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 2772 at round6_boss
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## aux_8c8_base0268_compositor0
- Name/category: ACTOR_8C8_BASE_0268_COMPOSITOR_0 / EFFECT / TRANSIENT
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 3808 at round1_phase1
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## aux_8c8_base0275_compositor0
- Name/category: ACTOR_8C8_BASE_0275_COMPOSITOR_0 / EFFECT / TRANSIENT
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 3912 at round1_phase1
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## transient_effect
- Name/category: Transient effect classes / EFFECT / TRANSIENT
- Resolution: unresolved; palette: unknown
- Static proof: conservative semantic class for legal graphics-bearing effects not otherwise resolved
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: exact family/route merge; composer pieces; palette bank

## collision_marker40_route
- Name/category: Marker 0x40 hostile-route candidate / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: original arcade map semantics; conservatively retained until the marker route is classified
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: exact family/route merge; composer pieces; palette bank

## collision_marker41_route
- Name/category: Marker 0x41 hostile-route candidate / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: original arcade map semantics; conservatively retained until the marker route is classified
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: exact family/route merge; composer pieces; palette bank

## collision_marker49_special_route
- Name/category: Marker 0x49 special-route candidate / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: original arcade map and spawn switch; conservatively retained until the special route is classified
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: exact family/route merge; composer pieces; palette bank

## collision_marker4f_behavior20_route
- Name/category: Marker 0x4F behavior-0x20 candidate / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: original arcade map and spawn switch; conservatively retained as a legal graphics-bearing candidate
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: exact family/route merge; composer pieces; palette bank

## four_armed_enemy
- Name/category: Four-armed enemy / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: legal graphics-bearing Stage-1 enemy; retained as a conservative feasibility blocker
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: exact family/route merge; composer pieces; palette bank

## hostile_base004b_compositor0
- Name/category: Stage-1 Lizardman / ENEMY / HOSTILE
- Resolution: resolved; palette: proven
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 2806 at round1_phase1
- Merge/split: Family-0 classes observed with base 0x004B share the established Lizardman producer/composer vocabulary; animation/class variants remain one family.
- Blockers: none

## hostile_base00d0_compositor0
- Name/category: HOSTILE_BASE_00D0_COMPOSITOR0_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 3250 at round5_phase1
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## hostile_base0179_compositor0
- Name/category: HOSTILE_BASE_0179_COMPOSITOR0_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 3430 at round1_phase1
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## hostile_base01cb_compositor0
- Name/category: HOSTILE_BASE_01CB_COMPOSITOR0_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 3288 at round6_castle
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## hostile_base0275_compositor0
- Name/category: HOSTILE_BASE_0275_COMPOSITOR0_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 3132 at round3_castle
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## hostile_base02e8_compositor0
- Name/category: HOSTILE_BASE_02E8_COMPOSITOR0_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 2802 at round3_phase1
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## hostile_base033e_multi_compositor
- Name/category: HOSTILE_BASE_033E_MULTI_COMPOSITOR_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 2654 at round1_castle
- Merge/split: Compositor forms [0, 3, 4] share the same actor-record base 0x033E; they remain forms of one unresolved semantic candidate rather than independent enemies.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## hostile_base03b3_compositor0
- Name/category: HOSTILE_BASE_03B3_COMPOSITOR0_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 3100 at round4_phase1
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## hostile_base0400_compositor1
- Name/category: HOSTILE_BASE_0400_COMPOSITOR1_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 2780 at round2_phase1
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## hostile_base0420_compositor0
- Name/category: HOSTILE_BASE_0420_COMPOSITOR0_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 2816 at round3_phase1
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## hostile_base0a5a_compositor2
- Name/category: HOSTILE_BASE_0A5A_COMPOSITOR2_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 2876 at round1_castle
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## hostile_base0a73_compositor2
- Name/category: HOSTILE_BASE_0A73_COMPOSITOR2_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 2846 at round1_castle
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## hurry_up_bat
- Name/category: Hurry-up Bat / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: group-4 records 48-56; palette deliberately unresolved
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: exact family/route merge; composer pieces; palette bank

## large_bat
- Name/category: Large bat enemy / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: legal graphics-bearing Stage-1 enemy; retained as a conservative feasibility blocker
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: exact family/route merge; composer pieces; palette bank

## normal_small_bat
- Name/category: Normal/small bat enemy / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: legal graphics-bearing Stage-1 enemy; retained as a conservative feasibility blocker
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: exact family/route merge; composer pieces; palette bank

## static_mode2_base033e_unresolved
- Name/category: STATIC_MODE2_BASE_033E_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x0454BA; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_normal_base0241_unresolved
- Name/category: STATIC_NORMAL_BASE_0241_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x045542; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_normal_base043a_unresolved
- Name/category: STATIC_NORMAL_BASE_043A_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x04553A; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_normal_base06e2_unresolved
- Name/category: STATIC_NORMAL_BASE_06E2_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x04554A; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_normal_base0889_unresolved
- Name/category: STATIC_NORMAL_BASE_0889_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x045552; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_seed_selector_08_1c_00
- Name/category: STATIC_SELECTOR_08_1C_00_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x045592; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_seed_selector_08_1c_01
- Name/category: STATIC_SELECTOR_08_1C_01_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x04559A; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_seed_selector_08_1c_02
- Name/category: STATIC_SELECTOR_08_1C_02_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x0455A2; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_seed_selector_08_1c_03
- Name/category: STATIC_SELECTOR_08_1C_03_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x0455AA; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_seed_selector_08_1c_04
- Name/category: STATIC_SELECTOR_08_1C_04_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x0455B2; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_seed_selector_08_1c_05
- Name/category: STATIC_SELECTOR_08_1C_05_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x0455BA; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_seed_selector_08_1c_06
- Name/category: STATIC_SELECTOR_08_1C_06_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x0455C2; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_seed_selector_08_1c_07
- Name/category: STATIC_SELECTOR_08_1C_07_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x0455CA; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_seed_selector_08_1c_08
- Name/category: STATIC_SELECTOR_08_1C_08_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x0455D2; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_seed_selector_08_1c_09
- Name/category: STATIC_SELECTOR_08_1C_09_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x0455DA; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_seed_selector_08_1c_10
- Name/category: STATIC_SELECTOR_08_1C_10_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x0455E2; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_seed_selector_08_1c_11
- Name/category: STATIC_SELECTOR_08_1C_11_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x0455EA; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_seed_selector_08_1c_12
- Name/category: STATIC_SELECTOR_08_1C_12_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x0455F2; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_seed_selector_08_1c_13
- Name/category: STATIC_SELECTOR_08_1C_13_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x0455FA; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_seed_selector_08_1c_14
- Name/category: STATIC_SELECTOR_08_1C_14_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x045602; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_seed_selector_08_1c_15
- Name/category: STATIC_SELECTOR_08_1C_15_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x04560A; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_seed_selector_08_1c_16
- Name/category: STATIC_SELECTOR_08_1C_16_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x045612; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_seed_selector_08_1c_17
- Name/category: STATIC_SELECTOR_08_1C_17_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x04561A; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_seed_selector_08_1c_18
- Name/category: STATIC_SELECTOR_08_1C_18_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x045622; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_seed_selector_08_1c_19
- Name/category: STATIC_SELECTOR_08_1C_19_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x04562A; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## static_seed_selector_08_1c_20
- Name/category: STATIC_SELECTOR_08_1C_20_UNRESOLVED / ENEMY / HOSTILE
- Resolution: unresolved; palette: unknown
- Static proof: actor record 0x045632; arcade_pc 0x04543E or 0x04544E actor record loader
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: record-to-semantic-family merge; round/phase reachability; composer pieces; palette bank

## axe_item
- Name/category: Axe item/drop / ITEM / DROP
- Resolution: unresolved; palette: unknown
- Static proof: legal graphics-bearing Stage-1 item; retained as a conservative feasibility blocker
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: exact family/route merge; composer pieces; palette bank

## other_item_drop
- Name/category: Other item/drop classes / ITEM / DROP
- Resolution: unresolved; palette: unknown
- Static proof: conservative semantic class for legal graphics-bearing drops/items not otherwise resolved
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: exact family/route merge; composer pieces; palette bank

## aux_5c8_base0275_compositor0
- Name/category: ACTOR_5C8_BASE_0275_COMPOSITOR_0 / OTHER PROVEN NON-ENEMY
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 4004 at round1_phase1
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## aux_5c8_base03f6_compositor0
- Name/category: ACTOR_5C8_BASE_03F6_COMPOSITOR_0 / OTHER PROVEN NON-ENEMY
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 3808 at round1_phase1
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## aux_5c8_base050b_compositor0
- Name/category: ACTOR_5C8_BASE_050B_COMPOSITOR_0 / OTHER PROVEN NON-ENEMY
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 3808 at round1_phase1
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## aux_748_base019d_compositor0
- Name/category: ACTOR_748_BASE_019D_COMPOSITOR_0 / PROJECTILE / WEAPON
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 2858 at round3_phase1
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## aux_748_base01cb_compositor0
- Name/category: ACTOR_748_BASE_01CB_COMPOSITOR_0 / PROJECTILE / WEAPON
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 2952 at round6_castle
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## aux_748_base0268_compositor0
- Name/category: ACTOR_748_BASE_0268_COMPOSITOR_0 / PROJECTILE / WEAPON
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 3808 at round1_phase1
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## aux_748_base0275_compositor0
- Name/category: ACTOR_748_BASE_0275_COMPOSITOR_0 / PROJECTILE / WEAPON
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 3912 at round1_phase1
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## aux_748_base02e8_compositor0
- Name/category: ACTOR_748_BASE_02E8_COMPOSITOR_0 / PROJECTILE / WEAPON
- Resolution: unresolved; palette: unknown
- Static proof: arcade_pc 0x03D054 renderer/compositor dispatch; PC090OJ record ownership from arcade_pc 0x041DAE or boss arcade_pc 0x041F30
- Dynamic proof: original arcade MAME actor/PC090OJ sweep; sample frame 2810 at round3_phase1
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: semantic family name; exact object-to-palette-bank relationship

## projectile_weapon
- Name/category: Projectile/weapon classes / PROJECTILE / WEAPON
- Resolution: unresolved; palette: unknown
- Static proof: conservative semantic class for legal graphics-bearing projectiles/weapons not otherwise resolved
- Dynamic proof: not observed in bounded sweep
- Merge/split: Not merged with another candidate without arcade semantic proof.
- Blockers: exact family/route merge; composer pieces; palette bank
