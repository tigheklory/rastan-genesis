# Cody Build 0415 — BG-A Incremental Background

## Scope and baseline

Build 0415 implements BG-A only: visible-span native Plane A/Plane B work,
full-span collision maintenance, and gathered column DMA. It does not fuse the
name/collision resolver (BG-B) and does not install generated native map records
(BG-C).

The existing Build 0414 family was preserved. Its interrupted `_c` closeout was
rerun against the existing ROM and ended `NO_PROGRESS` after four of eighteen
subrounds, with player fallback `0`, generic fallback `0`, adapter `0`, and crash
`0000`. This was recorded as a 0414 closeout FAIL; Build 0414 was not rebuilt.

## Resolved unit and producer model

- Arcade tile = logical cell = Genesis name cell = 8x8 pixels.
- A segment is four cells / 32 pixels.
- The logical ring is 64x64 cells; the physical Genesis planes are 64x32.
- The visible contract is 40 columns x 28 rows.
- A horizontal tile crossing produces one entering column. A vertical tile
  crossing produces one entering row.

The bounded Build 0414 trace in
`states/traces/build0415_step1_baseline0414_bfixed/` measured the representative
heavy vertical-scroll event as one pan invocation containing two 64-cell visual
producers: 64 Plane-A resolves plus 64 Plane-B resolves. Thus `M=2` for that
event. Selector 12 remained zero throughout the pure-pan interval, so it does
not duplicate the pan publisher on that retained-state route. It remains in
production for its distinct selector-1/2 route.

Horizontal measurement also exposed a useful correction to the estimate: the
Build 0414 Plane-B directional loop iterated 64 logical rows, but its resident
gate invoked the Plane-B name resolver for 32 physical rows. Build 0415 reduces
that to the 28 visible rows.

Exact per-entering-strip work is:

| Route | Metric | 0414 | 0415 |
|---|---|---:|---:|
| horizontal | Plane-A resolves | 64 | 28 |
| horizontal | Plane-B resolves | 32 | 28 |
| horizontal | collision resolves/writes | 64 | 64 |
| horizontal | total descriptor-backed resolver calls | 160 | 120 |
| horizontal | staged name writes | 64 | 56 |
| vertical pan entering row | Plane-A resolves/writes | 64 | 40 |
| vertical pan entering row | Plane-B resolves/writes | 64 | 40 |
| vertical pan entering row | total descriptor-backed resolver calls | 128 | 80 |
| selector-1/2 entering row | collision resolves/writes | 64 | 64 |

Plane-B horizontal work follows its retained parallax crossing cadence rather
than necessarily occurring in the same worker as every Plane-A crossing; the
table describes one invocation of each relevant entering-strip producer.

## Build 0414 packed-bank guard

`verify_pc090oj_direct_dispatch.py` now rejects any full-word
`native_sprite_lane` source consumer and verifies the normalized effective-bank
hoist at `native_stage_dispatch_41dae`, `native_stage_dispatch_45dfa`, and
`pc090oj_native_emit_pass`. The direct-dispatch, fast-enqueue, A4/A5 non-clobber,
variable-count, and packed-bank checks pass.

## BG-A implementation

Private assembly macros provide the future BG-C seam:

- `MAP_GET_NAME_A` expands to the current `resolve_plane_a_cell` call;
- `MAP_GET_NAME_B` expands to the current `fg_boundary_resolve_b` call;
- `MAP_GET_COLLISION` expands to the current
  `resolve_plane_a_collision_cell` call.

The macros preserve the existing resolver leaves and register contracts; there
is no new runtime call layer.

Horizontal selector 0 still writes all 64 collision words for the entering
column, but performs Plane-A name resolution/staging for only 28 rows starting
at the existing live-scroll-derived visible top. The separate Plane-B
directional producer now performs the same 28-row visual span and marks its
physical column dirty. Every retained tile-crossing call processes one entering
column; multiple crossings therefore set/process multiple columns in existing
call order.

Vertical selector 1/2 still writes all 64 collision words for the entering row
and resolves/stages only 40 visible columns. The established pan-up/pan-down
path remains and its Plane-A and Plane-B row publishers are likewise bounded to
40 visible columns. No selector path was removed.

The collision ring remains 64x64 words with index
`((world_y >> 3) & 63) * 64 + ((world_x >> 3) & 63)`. Visual span reduction is
independent of this full gameplay contract.

## Column dirty state and DMA

`fg_col_dirty` and `bg_col_dirty` are independent 64-bit masks (two longs per
plane). Row masks remain independent, so a row and column may be dirty in the
same frame and their intersection is idempotent.

Each plane owns a 32-word / 64-byte contiguous gather buffer. A dirty column is
gathered from the row-major staged plane at a 128-byte source stride for
physical rows 0..31. The VDP transfer is exactly 32 words with destination
autoincrement 128 bytes, after which autoincrement is restored to 2. There is no
64-word column DMA and no destination wrap: logical rows fold through `row &
31`; the authoritative DMA source is the already-folded 32-row staged plane.
The four physical rows outside the 28-row horizontal visual span retain their
previous authoritative staged values and are included in the 32-word physical
column transfer.

## Mechanical equivalence

`tools/translation/verify_bg_a_incremental_background.py` is a build gate. It
locks the source-level span/order/DMA contracts and runs a deterministic 64x64
semantic-ring comparison for right, left, up, down, horizontal and vertical
wrap, multiple crossings, a segment/package reseed, and combined H+V work. It
compares complete Plane-A staging, complete Plane-B staging, and the 64x64
collision ring against the bulk reference, and verifies gathered-column VRAM
addressing for both planes. Result: PASS.

## Measured result

Apples-to-apples controlled traces:

- Build 0414: `states/traces/build0415_step1_baseline0414_bfixed/`
- Build 0415 candidate:
  `states/traces/build0415_candidate_step1_final/`

For the 22 full representative pan events:

| Metric | 0414 | 0415 | Change |
|---|---:|---:|---:|
| Plane-A resolves | 64 | 40 | -37.5% |
| Plane-B resolves | 64 | 40 | -37.5% |
| Descriptor-resolver calls | 128 | 80 | -37.5% |
| Row/map cycles, median | 153,890 | 98,298 | -36.1% |
| Complete worker cycles, median | 230,636 | 172,396 | -25.2% |
| Complete IRQ cycles, median | 233,829 | 179,471 | -23.2% |

For selector-0 horizontal events, Plane A changed 64 resolves to 28 while the
full 64 collision resolves remained. The associated row/map average fell
135,704 to 92,608 cycles (-31.8%). Plane-B directional events changed 32
resolver calls to 28.

Non-scroll behavior did not regress in the same controlled interval:
zero-resolver worker average changed 93,463 to 93,100 cycles (-0.4%), and IRQ
average was effectively identical (99,433 to 99,435). The dense six-enemy,
zero-resolver IRQ median changed 102,056 to 101,001 cycles (-1.0%). The earlier
dedicated Build 0414 quiet/static and one-enemy/static baselines remain 72,593
and 87,443 cycles respectively; they were not separately re-recorded because
the same-interval zero-resolver comparison already showed no BG-A regression.

The representative scroll IRQ remains above the 128,009-cycle frame budget, as
expected for BG-A. BG-B remains the next proposed phase after hardware review.

## Gates, closeout, and hardware status

- mechanical BG-A equivalence/DMA gate: PASS;
- generator: PASS; 49 sprite cells retained, no reachable unresolved entry;
- direct dispatch / packed bank / fast enqueue / A4-A5 / queue contracts: PASS;
- canonical gate: PASS;
- gameplay-entry gate: PASS, exceptions `0/0/0/0`;
- existing seven-epoch label: FAIL (pre-existing labeled gate);
- 0415 `_c` closeout: COMPLETE, 18/18, fallback/adapter/crash `0/0/0/0000`;
- steady-state VDP ownership gate: PASS, zero writes outside the publication
  bracket (`states/traces/build0415_vdp_ownership_gate/`). The earlier
  immediate-arm measurement saw 17 initial package-install/display writes in
  both 0414 and 0415 before the steady-state bracket; delaying only the host
  observer arm by 90 record-1 frames cleanly separates that initialization.

Visual identity, scrolling/collision behavior, Four-Armed presentation, dynamic
cave-block behavior, and the real-Genesis black-bar result require Tighe's
hardware test.

## Artifacts

All five Build 0415 ROMs are 1,998,520 bytes:

- canonical: `c3392a9dfa9d2162298571ade4e7346ef3096dd52cefd0c2fefb2829c3ce9e9f`
- `_c`: `9a5ad0d93816bc12c7548685f81ac744379aa3af945ad86b40012c8658ec6373`
- `_d`: `7593f5888e0993b6f7e9ffc857fa53877d2933b275fd9e5b9d6346f9ab5a2fe7`
- `_do`: `0655291118e9baf70807a313ce9ec74ef1d04fce34af2ae383e6d62b30c261c9`
- `_s`: `32420d647437a87c1675e0e3fd646da313902d5142d09153fadb5ee54406b125`
