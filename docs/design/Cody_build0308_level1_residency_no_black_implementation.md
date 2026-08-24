# Cody Build 0308 Level-1 Residency / No-Black Implementation

Date: 2026-08-23

## Baseline and artifact

- Input baseline: Build 0307, SHA-256
  `c46ed6b8ba6bbe2ee055e70147f4b8476250f754eba71f9143afdde385b96ac9`.
- Produced checkpoint: Build 0308.
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0308.bin`.
- SHA-256: `32f7523f450fb929db1f689a96eb844dde0611c709ed5f1acc67a1ab86467a65`.
- Size: 1,679,032 bytes.
- Counter: 308.
- Rolling ROM is byte-identical to the numbered artifact.

Build 0308 is a meaningful residency checkpoint. It completes fixed Level-1 Plane-B
residency and zero-drop per-record Plane-A residency. It does **not** complete the
Strategy-C no-black transition engine.

## Proven arcade semantics retained

- The slow/parallax source rooted at arcade data `0x03951C`, with scroll at
  hardware addresses `0x00C40000` / `0x00C20000`, feeds Genesis Plane B at VRAM
  `0xC000`.
- The fast source rooted at arcade data `0x01691C`, with scroll at hardware
  addresses `0x00C40002` / `0x00C20002`, feeds Genesis Plane A at VRAM `0xE000`.
- Level 1 uses Plane-B descriptors 0 through 55. Descriptor 56 belongs to the next
  stage and is excluded.
- Exact 32-byte pattern identity is the allocation identity. Arcade code equality
  alone is not treated as pattern equality.
- Level-1 Plane B has one fixed 854-pattern vocabulary. It does not acquire a new
  vocabulary at ordinary records, the cave/descent, or the boss phase.
- Plane A remains per semantic record. Required exact-pattern counts are:
  `49, 124, 236, 333, 209, 89, 239, 154, 132, 78, 368, 483, 225, 217,
  250, 349, 219, 70, 54, 54, 85, 116, 219`.

## Build 0308 implementation choices

### Offline allocation

`tools/translation/compile_pc080sn_genesis.py` now emits one deterministic package
for each of 23 Level-1 records:

- blank slot: 0;
- fixed Plane B: slots 1 through 854;
- per-record Plane A: slots 855 through 1338;
- native PC090OJ: slots 1339 through 1534, 49 contiguous 16x16 cells;
- spare physical pattern slot: 1535.

Frontend slots 1 through 63 are reclaimed when gameplay starts. Existing scene-load
behavior restores frontend graphics on a later frontend load. No other physical hole
is claimed. Maximum physical slot is 1535, below the YM7101 limit of 1536 slots.

The compiler fails if the fixed B vocabulary is not exactly 854 patterns, if any
legal Plane-A or Plane-B pattern lacks a slot, if planes overlap sprites, if a slot is
outside physical VRAM, or if temporary LUT scratch overlaps a legal Level-1 code.
The temporary identity and slot-translation tables use the statically empty LUT word
range 5632 through 7969; legal-code overlap is zero.

### Runtime ownership

- Fixed Plane B is mapped and uploaded once at gameplay entry.
- Ordinary record transitions perform zero Plane-B map rebuilds, pattern uploads,
  name remaps, or name DMAs.
- Plane-A transitions retain exact shared identities in stable slots and update only
  Plane-A mappings/residency.
- Old Plane-A code mappings are cleared without disturbing fixed-B mappings.
- The runtime has no plane allocator, search, hash, eviction, or LRU path.
- The native sprite residency cache is bounded to the physical 49-cell band and uses
  a bounded fully associative lookup rather than the obsolete 32-set/4-way layout.
- `worklist_entry_for_slot` is sized for all 49 cells rather than four bytes.

The 49-cell value is the proven physical remainder after fixed B plus worst-record A,
not a completed semantic proof that every possible Stage-1 sprite combination fits.
Existing runtime evidence has stayed below this limit, but a user-driven Level-1
sprite stress test remains the acceptance check. The task explicitly allowed this
uncertainty not to block a useful residency build.

## Required residency metrics

| Metric | Build 0308 |
|---|---:|
| Level-1 fixed B identities | 854 |
| B residency epochs | 1 |
| B Y variants | 0 |
| B required drops | 0 |
| B pattern DMA at ordinary record | 0 |
| B remap at ordinary record | 0 |
| A required drops | 0 for every record |
| Compiler residency assertion misses | 0 |
| Frontend slots reclaimed | 1..63 (63 slots) |
| Maximum physical slot | 1535 |
| Static plane/sprite slot conflicts | 0 |
| Runtime plane allocator/search/LRU | none |

## Black-frame status

Build 0308 intentionally preserves the existing synchronous Plane-A package install
so that the zero-drop residency work can be tested independently. On an ordinary
record transition, `fg_boundary_advance_segment` or
`fg_boundary_install_post_reseed` still calls `fg_boundary_install` outside VBlank.
That routine still writes VDP register 1 value `0x34` (display off), performs the
Plane-A transition, and writes `0x74` (display on).

- Ordinary-record display-off calls: one per actual Plane-A package transition.
- False Plane-B installs removed: all ordinary-record B installs, including the old
  Y variants for records 2/3 and 17/21.
- A prepare/commit implemented: NO.
- Display disabled during A transition: YES.
- Expected completely black frames at a sufficiently large transition: at least one.
- Black-frame mechanism remains reachable: `fg_boundary_install` from the two
  semantic record-transition hooks above.

### Why Build 0309 was not produced speculatively

Adjacent Plane-A exact-pattern unions peak at 654 identities, exceeding the 484-slot
Plane-A band. A naive double buffer would overwrite patterns still referenced by the
old displayed frame. With Build-0308 stable-slot allocation, safe preload and
boundary-conflict counts were measured for every adjacent transition. The largest
boundary-conflict set is 220 patterns, or 7,040 bytes. Adding a full 4,096-byte
Plane-A name-table commit exceeds one NTSC VBlank.

Therefore merely removing display-off, moving the current synchronous routine into
VBlank, or uploading into reused slots over several visible frames would expose mixed
pattern/name state. Those are not acceptable substitutes for Strategy C.

The next safe implementation boundary is compiler-generated transition data that:

1. separates safe preloads from live-slot conflicts;
2. prepares safe patterns over bounded VBlanks while suppressing premature Plane-A
   strip publication for the pending package;
3. emits a minimal name-table patch rather than a full 2048-word recommit;
4. proves the remaining conflicting pattern DMA plus name patch fits one VBlank;
5. swaps the active LUT and applies the patch atomically before retiring old slots;
6. removes the ordinary mid-frame display-off only after those assertions pass.

This is the exact unresolved no-black boundary, not a reason to weaken the completed
0308 residency model.

## Preserved behavior

- Build-0306 arcade data-pointer correction at arcade PC `0x0503CE` is preserved.
- Build-0305 WRAM scratch correction is preserved.
- Build-0303 exact 32-byte identity and stable-retention semantics are preserved.
- Build-0297 native PC090OJ architecture remains active; no object-RAM compatibility
  renderer was restored.
- Collision, scrolling, map placement, palettes, input, audio, and gameplay state
  were not changed by this task.

## Validation

- Offline compiler: PASS; fixed B 854, max A 484-slot envelope, zero plane drops.
- Generated JSON metric assertions: PASS.
- Python syntax checks for compiler and both canonical verifiers: PASS.
- Canonical gate: `GATE_PASS`.
- Opcode-replacement site count: unchanged at 227.
- Canonical Genesis coverage: `0x199EB8`, equal to the complete 1,679,032-byte ROM;
  no gaps or overlaps.
- Mandatory MAME Genesis smoke: PASS, 1,798 frames, average 481.52%, no unique
  unmapped memory address and no fatal/error/exception marker.
- Smoke limitation: the automatic trace remained frontend-only; gameplay residency,
  sprites, visuals, and collision require Tighe's empirical test.

## Tighe test requested

1. Start Level 1 and confirm gameplay/collision still behaves like 0306/0307.
2. Confirm Plane B remains populated through ordinary movement, cave/descent, rope,
   vertical movement, and boss approach.
3. Confirm previously missing B patterns no longer become deliberate holes.
4. Confirm Plane-A patterns are resident even where map placement remains wrong.
5. Confirm Rastan, lizard men, bats, and items remain visible with no major sprite
   residency regression.
6. Observe and report the still-expected ordinary Plane-A transition black frame;
   Build 0308 does not claim that portion complete.

Scrolling and map placement are explicitly deferred.
