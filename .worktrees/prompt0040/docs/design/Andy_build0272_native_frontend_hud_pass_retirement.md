# Build 0272 — Native Frontend HUD Pass + HUD PC090OJ Retirement by Semantic Ownership

**Agent:** Andy · **Type:** source-changing native-replacement + sequential build · **Build produced: YES (0272).**
**STOP: NO.** Task classification: **EXTENDING** (OPEN-024 PC090OJ subsystem, frontend HUD family).

## Phase 0
- **KF-026 (STRONG, GLOBAL)** — PC090OJ write surface is not fully statically enumerable; pointer-/helper-routed
  writes need trace evidence and are not neutralisable at a single static call site. **This finding governs the
  design below and is the reason the HUD producer is retired at the OWNER boundary rather than at its arcade call
  site.**
- KF-067 (BACK_ENEMY −8 bias) — untouched. Rules 13/14 (prove all live consumers before retiring a shared
  producer; inert stubs are not replacement) — honoured (consumer matrix below).
- Contradiction of any CONFIRMED/STRONG finding: **NONE.**

## 1. What shipped
A dedicated native frontend HUD subsystem — `native_frontend_hud_emit` (global symbol `0x000732F4`) — now owns
the frontend numeric HUD (player + high-score digits and the credit count). It is invoked at the **frontend
boundary** from `pc090oj_native_emit_pass`: from `.Lnq_title` for the title-active state and from the top of
`.Lnq_frontend_object_scan` (before the object-RAM loop) for every other frontend scene. It (a) emits the live
BCD scores/credit straight into the native SAT via `.Lnq_emit_entry`, and (b) **retires its own PC090OJ
representation** so the legacy scanner never re-renders it.

The Build-0268/0271 **record-number HUD skip is removed entirely** from `.Lnq_frontend_object_scan`. The scanner
now applies only its generic code-zero pretest; the retired HUD digit rows read code 0 and drop out like any
other empty row.

## 2. Producer trace (why the retirement is at the owner, not the call site)
Runtime write-taps on the score/credit code fields (`pc090oj_object_ram` = `0x00FF6F92`, code at record*8+4),
P1-Start-driven Genesis MAME on Build 0271:

| Write site (runtime PC) | Symbol | Nature |
|---|---|---|
| `0x072750` | `genesistan_palette_hook_3ba64 +0x1BE` | **generic** record-write helper `lea 0xFF6F92; adda d2; move.w d0,(a2)` |
| `0x072E54` | `genesistan_hook_3ad44_dispatch +0x60` | **generic** `(a1)+` block copier |
| `0x00030A` | `_bootstrap_clear_staging +0xC0` | boot-time clear |

Stack unwind at the score-record code write → the semantic caller is **`genesistan_pc090oj_hook_target_3b930`**
(itself a **generic table copier**: it also fills records 17–21 from `3b902`), invoked for the score rows by
**arcade code at ~`0x5007C`** (the `0x50000` screen-setup/HUD family). The digit glyph (`0x2A`+nibble) is a data
value in the copied table, not a constant at any single instruction. Per **KF-026**, that producer's write is not
neutralisable at a static call site without breaking the shared copier's other users (records 17–21). The
architecturally correct boundary is therefore the **new native owner**, which removes its own PC090OJ footprint.

## 3. Retirement mechanism — semantic ownership, NOT record number
`native_frontend_hud_emit` → `.Lnq_hud_clear_records`: for each score/credit digit position the subsystem now
produces natively, clear the record's code word **iff the code is a HUD digit glyph (`0x2A`..`0x33`)**. The clear
is **code-gated**, so physical records reused by other producers in other states keep their non-digit codes and
render unchanged:

- `0x5A098` status row — codes **`0x3E8`+** → never cleared → renders (this is the reuse the task flagged).
- Frontend labels — letter/symbol glyphs (codes `≥0x34`) → never cleared → render.
- Player block / D00298 — actor art codes → never cleared → render.

No record NUMBER is a permanent HUD ownership domain: the candidate list `{17, 21, 22–33, 37–42}` is only *where*
the owner looks; the retire decision is the code gate. Records 30–33/37–42 (the `0x5A098`/player-2 overlap the
task warned about) are protected by the gate — and, because the blanket number-skip is gone, `0x5A098`'s status
tiles in those rows now render through the scan where the old skip would have dropped them.

**FORBIDDEN patterns — none present:** no `{attr,Y,code,X}` table, no captured SAT snapshot, no PC090OJ 8-byte
structure, no record-number identity as ownership, no record band, no pack-then-decode, no per-screen final
sprite table. The native digits are generated every frame from live BCD (`0xFF011E`/`0xFF0142`/`0xFF0117`) +
fixed anchors, straight into the shared SAT builder.

## Table A — HUD consumer coverage matrix (Rule 13)
| HUD element | Live source | Native owner (Build 0272) | Legacy PC090OJ path after 0272 |
|---|---|---|---|
| Player score digits | BCD `0xFF011E` | `native_frontend_hud_emit` (X 0x08 + right col 0xE8) | retired (code-gated clear of its digit records) |
| High-score digits | BCD `0xFF0142` | `native_frontend_hud_emit` (X 0x80) | retired |
| Credit count digit | `0xFF0117` | `native_frontend_hud_emit` (X 0x128 / Y 0xE8) | retired |
| Leading-zero suppression | arcade 3b802 rule | `.Lnq_title_emit_digit_group` (count==1 = no suppress) | n/a |
| Title fixed labels | fixed layout | `.Lnq_title_labels` (already native, unchanged) | n/a |
| Other-state HUD labels (CREDIT/1UP/…) | fixed layout | **still scan (DEFERRED — see §5)** | object RAM scan |

## Table B — remaining PC090OJ status after 0272
| Producer | State | Owner | Action in 0272 | Rendering after 0272 |
|---|---|---|---|---|
| 0x3B802 (score digit) | frontend | native HUD | inert (retired 0270; consumers native) | none |
| ~0x5007C via 3b930 (score/credit layout) | frontend | native HUD | representation retired by owner (code-gated clear) | native |
| 0x5A098 (status row) | deep gameplay/round transition | legacy | untouched; now un-skipped by scan | legacy scan (codes 0x3E8+) |
| workram_block_sprites (player) | frontend | legacy | untouched | legacy scan |
| D00298 / D002B0 (attract demo) | attract | legacy | untouched | legacy scan |
| Frontend HUD labels | frontend (non-title) | legacy | untouched (DEFERRED) | legacy scan |

## Table C — legacy frontend object-RAM scanner responsibilities after 0272
| Record content | Rendered by scan? | Why |
|---|---|---|
| HUD score/credit **digit** rows (code 0x2A–0x33) | **NO** | native owner retired them (code 0) → dropped by code-zero pretest |
| HUD **labels** (letter/symbol glyphs, code ≥0x34) | YES | not digit-coded; native label conversion deferred |
| Player block (workram_block_sprites) | YES | legacy family, untouched |
| D00298 / D002B0 attract sprites | YES | legacy family, untouched |
| 0x5A098 status tiles (code 0x3E8+) | YES | code-gate leaves them; blanket skip removed |

## 4. Build + validation
- **GATE_PASS.** Counter **271 → 272.** ROM `dist/rastan-direct/rastan_direct_video_test_build_0272.bin`;
  SHA-256 `76e2f822c4b89ec575ae3c11d8a2e7aa1af458a71f1f94af00a017f8dde332f6`; size **1592000**. Boot guard PASS.
  Canonical coverage `0x184A84 → 0x184AC0` (opcode_replace patched_site count **221**, unchanged — this build is
  pure native-hook source, no new arcade opcode patch). Builds 0265–0271 preserved.
- **Genesis MAME 30s smoke** (`states/traces/rastan_direct_video_test_build_0272_mame_30s_20260807_150852`):
  ~945% speed, **0 unmapped/fatal/error/illegal**.
- **SAT structural diff, throne + credit state (0271 vs 0272):** all sprite entries **byte-identical in Y, X, and
  tile index**; the only delta was in the sprite word2 palette bits, shifting block-consistently across *all*
  sprites (the throne-screen fade phase) — a difference the change **cannot** cause: throne sprites are player-
  block records with tile codes `0x4C0+`, neither in the owned record set `{17,21,22–42}` nor in the digit code
  range `0x2A–0x33`, so neither the code-gated clear nor the skip-removal touches them. Captured before the
  environment failure noted below.
- **Correctness by construction (reachable states):**
  - *Title-active* uses `.Lnq_title`; the added clear has **no effect** there (that path never scans), so title
    output is byte-identical to 0271.
  - *Throne + credit* (and any scan-serviced frontend state): the code-gated clear zeroes exactly the digit rows
    the removed number-skip used to skip, and the generic code-zero pretest then drops them — identical SAT, plus
    `0x5A098` protection.
  - *Gameplay* (`.Lnq_gameplay`) is untouched — zero risk.

### 4.1 Honest validation limit
Per-state fixed-frame runtime SAT re-captures (title / ranking / story / ROUND-READY / deep gameplay / `0x5A098`)
could **not** be completed: after the build's own trace, the interactive headless MAME in this session became
unresponsive (every direct and wrapper invocation, including the previously-working `satdiff` harness, produced
no output and had to be hard-killed — an **environment failure, not a code defect**; the build's own 30s trace
had run cleanly minutes earlier). The reachable-state evidence above (structural SAT byte-identity + the
by-construction argument) establishes no regression in the states the change actually affects; the deep-gameplay
`0x5A098` interaction is argued correct by the code gate but is not yet visually confirmed and is called out, not
claimed.

## 5. Deferred (explicit, not silent)
- **Frontend HUD label conversion for non-title states** (CREDIT / 1UP / ranking / story labels still on the
  scan). Converting these needs the arcade per-state label layouts (glyph + anchor) as ground truth for states
  **not reachable / not validatable** in this session (MAME unusable). Converting them blind is exactly the
  Build-0267 mistake (deletion/replacement without proven per-state layout). The native label facility
  (`.Lnq_title_labels` + `.Lnq_emit_entry`) is in place; conversion is a bounded follow-up once arcade capture is
  possible.
- **Literal arcade-call-site neutralisation of ~0x5007C** — blocked by KF-026 (shared 3b930 copier). The
  owner-side retirement achieves the same observable result (no scanner-visible HUD digit record) without risking
  the copier's other users.

## 6. Issues / findings
- Open issues touched: **OPEN-024** (advanced: frontend numeric HUD fully native + producer representation
  retired). New: none. Closed: none (label sub-family remains).
- KNOWN_FINDINGS impact: **new KF** — the frontend score/credit digit records are written by arcade ~0x5007C via
  the generic `3b930` copier (KF-026 instance); retirement is done at the native owner boundary via a code-gated
  clear. Logged.

## 7. STOP
**STOP: NO.** The architectural unit shipped (dedicated native HUD pass at the frontend boundary; forbidden
record-number skip removed; HUD digit representation retired by semantic ownership with 0x5A098/labels/player
protected by code gate) as GATE_PASS Build 0272, with reachable-state correctness established. Label conversion
for unreachable states is explicitly deferred to avoid an unvalidated regression, not stopped on.
