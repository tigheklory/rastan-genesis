# Cody — R1-S2 fourth-chain and castle metatile correction

**Tasks:** `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0005` and resume `...0007`  
**Candidate:** Build 0503, **NOT ACCEPTED**  
**Exact ROM-producing source:** `78fe99b4ea6c92716a9f5b5536f4107b07765459`

## Result

Build 0502's selector-1 block-axis transformation and reverse destination-row correction remain
intact. The later castle corruption had a separate, concrete cause: the native selector-1/2
consumer misclassified `A5+0x1040` as a table of strip-descriptor addresses. Original arcade
`0x055904` reads each live strip descriptor once and rebuilds two parallel products:

- `A5+0x1080`: descriptor word 0, the attribute;
- `A5+0x1040`: `0x200 + descriptor word 1`, the metatile-data pointer consumed directly by
  original `0x055A14`.

The native descriptor-rebuild hook preserves that contract and applies the Genesis copied-ROM
relocation to the pointer. Build 0502 then incorrectly treated the already-resolved pointer as a
second descriptor, rebased it again, and read a new word0/word1 pair from metatile payload. That
selected unrelated native tile and collision records. It explains the widespread wrong walls,
columns, windows, floor bands, and the missing climbability behind visible chain-like graphics in
Tighe's screenshots; it was not merely a palette defect.

Build 0503 removes that second descriptor dereference. It subtracts only the existing copied-ROM
base from the rebuilt metatile pointer, selects the prebuilt native metatile record by the recovered
canonical word1, and takes the attribute from the parallel `A5+0x1080` table.

## Fourth-chain arcade identity and interaction

This castle chain is a static Plane-A stage feature, not a required PC090OJ rope actor. Its visual
cells and gameplay collision cells are independent fields in the same original metatile semantic
record. The collision grid's property 2 is the retained climbable/contact value used by the player
movement state machine; ordinary masonry property 1 remains solid. Existing evidence excludes an
active special-solid rectangle at the reproduced static chains.

The first Build-0502 divergence is therefore before the player decision: selector-1/2 publication
uses the wrong native metatile record because of the extra dereference, so both the final Plane-A
identity and the collision side-channel can come from unrelated source data. The player logic then
correctly refuses attachment when it does not receive the authentic property-2 chain cells. Build
0503 corrects the common producer rather than adding a hitbox, object, coordinate exception, or
collision bypass. The same correction applies to records 17/21 and selector-1 records in R2-S2.

Actual attachment to Tighe's exact fourth-chain location is **not claimed verified**. The maintained
deterministic route reaches the earlier ceiling, not that later camera epoch, and no save state or
deterministic input fixture exists for the supplied route. Tighe must perform the exact-route test
listed below before acceptance.

## Earlier chain

The maintained route again reaches record `0x11`, selector 1, player state 4 at
`X/Y=0x0122/0x003E`, foreground `X/Y=0x0160/0x0166`. Its blocked collision map is byte-identical to
Build 0502, and prior original-arcade evidence reaches the matching state with the same property-1
head ceiling and property-2 feet contact. Up-only stops there in both systems. Tighe's reported
jump-off to the next platform is therefore the intended route distinction; that ceiling was not
modified or conflated with the later fourth chain.

## Native architecture and build-time/runtime split

Semantic cut: retained arcade record, selector, strip/group, rebuilt metatile identity, attribute,
and collision intent -> final Genesis Plane-A words plus the retained gameplay collision map. The
removed chip tail remains the PC080SN C-window/name-RAM writer. No PC080SN device, name-RAM shadow,
runtime rotation/transposition, framebuffer, general-purpose map reconstruction, fallback, player
teleport, or synthetic attachment region was added.

Build time:

- `gen_pc080sn_native_metatiles.py` preconverts every referenced metatile into a compact 64-byte
  native semantic record: 16 tile identities followed by 16 collision words.
- The native index maps the canonical metatile word1 directly to that record.
- Tile graphics and residency packages are already Genesis-formatted/precomputed.

Runtime:

- Retained stage streaming advances the live source descriptors only at semantic strip events.
- The existing native rebuild reads each selected descriptor once to produce the parallel attribute
  and metatile-pointer tables. This is dynamic stage selection state, not graphics transformation or
  PC080SN emulation.
- The corrected selector-1/2 helper no longer reconstructs or dereferences another source descriptor.
  It chooses one preconverted native record and emits its four cells to final staging/collision.

Compared with Build 0502, the helper adds one parallel attribute-table load per four-cell segment
but removes the descriptor range/rebase/read sequence and second word1 fetch. It performs less work,
not more. The established end-to-end benchmark is unchanged at `795/795/795`, median
`13,267.083 ms`; this is route-specific evidence, not a universal CPU-cycle measurement.

## Validation

- Canonical gate and both boot guards: PASS; Build 0503 published normally.
- Gameplay-entry gate: PASS; 240 controlled post-entry frames; no address, bus, illegal, or crash
  exception.
- Seven production epoch gate: PASS; full Plane-A and fixed Plane-B LUT checks pass.
- Selector-1/2 independent gate: 128 destination-row cases; 1,869,856 rebuilt
  metatile/attribute cases; 1,869,856 visual/collision subcell cases; 4,096 residency cases. Every
  source descriptor resolves to the original word0 and word1 record without a second dereference.
- Native metatile gate: 4,733 records, all tile and collision words exact.
- R1-S2 normal-entry **actual Genesis NTSC runtime** versus matched original arcade snapshot:
  Plane A 1,953 scored cells, Plane B 2,048 cells, and collision map all have zero identity,
  orientation, LUT, VDP-publication, or collision mismatches.
- R1-S2 direct-start functional initialization: PASS at record `0x11`, selector 1, active package
  5; both planes contain 2,048 nonzero names; no cache misses.
- Earlier-chain bounded Genesis runtime probe: reaches the known arcade-matched ceiling; collision
  dump unchanged, as required.
- Selector-0 protection: selector-0 exhaustive gate passes 163,840 coordinate/front/wrap/rebase
  cases and 934,928 visual/collision cases. The Build-0500 64-row/full-span coherence gate passes.
- Rope benchmark: `795/795/795`, median `13,267.083 ms`, deterministic YES; identical to Builds
  0500/0502.

The initial runtime capture proves the emitted Genesis data path, while the exhaustive producer gate
proves all source identities. It does **not** substitute for navigating the later upper castle.
Consequently upper-castle presentation through every camera epoch and successful fourth-chain
attachment/climb remain manual acceptance items.

## Candidate artifacts

- Normal: `dist/rastan-direct/rastan_direct_video_test_build_0503.bin`
  - SHA-256 `d8c2cd1aee9d78efb8ec2c780161d21119c03a96a734f2887126b2530b02297d`
  - size 3,399,352 bytes
- R1-S2: `dist/rastan-direct/rastan_direct_video_test_build_0503_S1-2.bin`
  - SHA-256 `ea4098472e48d1d5a412b87953c6d9c07d7228da4c89310835040d0936973fe2`
  - size 3,399,352 bytes
- Counter: 503; Build 0504 was not consumed.

## Tighe manual acceptance test

Using `_S1-2`, follow the exact route in the supplied screenshots and confirm:

1. walls, windows, columns, floor bands, and chains match the arcade sequence structurally (palette
   authorship is separate);
2. jump off the earlier chain onto the next platform;
3. at the later left-side fourth chain, attach at the visible authentic position, enter climbing
   state, climb upward, and scroll through the wrap without detaching incorrectly;
4. nearby walls/floors remain solid and earlier chains still attach/detach;
5. continue through the upper section and stage transition.

Build 0503 remains **CANDIDATE / NOT ACCEPTED** until that test passes.
