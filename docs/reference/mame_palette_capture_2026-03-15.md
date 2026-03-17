# MAME Palette Capture 2026-03-15

Source capture:
- `/home/tighe/projects/rastan-genesis/build/mame/home/rastanmon/rastan_monitor.log`
- `/home/tighe/projects/rastan-genesis/build/mame/home/rastanmon/snapshots/`

Session notes from play:
- title was allowed to progress further than the earlier short run
- one continue was used
- gameplay coverage only reached the first part of stage 1 and then into the second part of stage 1
- later follow-up testing showed that forcing stage 2 via cheat produced incorrect palette state, so stage-select should not be treated as palette-valid capture for later stages

## Confirmed capture quality

The `rastanmon` logger was fixed before this run:
- frame subscriptions are now kept alive correctly
- periodic heartbeat logging confirms the monitor stayed active throughout the session

This run is therefore suitable for scene/palette analysis.

## Confirmed scene coverage

First-seen scene labels from the log:

- `frontend_title_or_attract` at frame `1`
- `frontend_page_0000_0001` at frame `14`
- `wait_for_play` at frame `223`
- `runtime_other` at frame `224`
- `frontend_page_0002_0000` at frame `385`
- `frontend_page_0002_0002` at frame `548`
- `death_game_over_continue_01` at frame `550`
- `death_game_over_continue_02` at frame `552`
- `death_game_over_continue_03` at frame `553`
- `death_game_over_continue_04` at frame `808`
- `frontend_credit_ready` at frame `927`
- `death_game_over_continue_05` at frame `2296`
- `death_game_over_continue_06` at frame `2552`
- `death_game_over_continue_07` at frame `2553`
- `death_game_over_continue_08` at frame `2554`
- `frontend_page_0002_0003` at frame `2587`
- `frontend_page_0002_0004` at frame `6879`
- `active_runtime_stage_06` at frame `6881`
- `active_runtime_stage_02` at frame `10073`
- `active_runtime_stage_03` at frame `11487`
- `active_runtime_stage_0d` at frame `19496`
- `active_runtime_stage_11` at frame `24653`

Important practical result:
- the front-end/title cycle was captured well enough to expose multiple distinct `page2` values
- at least one continue path was definitely captured
- gameplay/runtime entry was captured multiple times

## Confirmed mode flow patterns

Observed `mode4` transitions:

- `0000 -> 0001` x20
- `0001 -> 0002` x6
- `0000 -> 0002` x10
- `0001 -> 0006` x9
- `0006 -> 0007` x6
- `0007 -> 0004` x6
- `0004 -> 0000` x8

Practical interpretation:
- `mode4 = 0000` still behaves like front-end/title-page ownership
- `mode4 = 0001` is a short gate before runtime or continue processing
- `mode4 = 0002` is a real runtime/gameplay-side mode
- `mode4 = 0006 -> 0007 -> 0004` is part of the death/game-over/continue controller

This lines up well with the earlier disassembly-side interpretation around:
- front-end/title controller
- wait-for-play gate
- death/game-over/continue controller

## Confirmed continue-path controller states

Observed `13aa` transitions:

- `0000 -> 0001` x9
- `0001 -> 0002` x3
- `0002 -> 0003` x3
- `0003 -> 0004` x3
- `0004 -> 0005` x1
- `0005 -> 0006` x1
- `0006 -> 0007` x1
- `0007 -> 0008` x1
- `0008 -> 00ff` x1
- `00ff -> 0000` x1

Practical interpretation:
- the capture reached the full `1..8` continue/death controller range at least once
- this is strong evidence that the current scene labeling for `13aa = 1..8` is fundamentally correct
- `00ff` appears to be a reset/terminal marker in that controller path

## Confirmed palette usage patterns

### Startup / early front-end

At startup (`frame 8`):
- active palette blocks: `48`
- active block range: mostly `00..30`

By later gameplay/front-end/continue scenes:
- active palette blocks: `72`
- active block range: `00..47`

Practical meaning:
- runtime scenes are materially broader in palette-block usage than the earliest title state
- this matters for Genesis planning because later scenes are likely to put much more pressure on line assignment than the first title frame does

### Stable front-end vs runtime differences

Confirmed repeated block changes:
- block `01` changes with front-end page/state changes
- block `02` changes with runtime/stage changes and is sometimes cleared during continue transitions
- blocks `1a..1d` change very frequently
- block `33` toggles repeatedly between two values
- block `43` toggles repeatedly between two values later in the run

Most frequently changed blocks in the session:
- `1a` x505
- `1b` x505
- `1c` x505
- `1d` x505
- `33` x54
- `02` x23
- `01` x21
- `43` x15

Practical interpretation:
- `1a..1d` are likely animated or cycling palette blocks, not static scene setup
- `33` and `43` look like blinking/toggling blocks used for UI or effect states
- `02` looks like a strong candidate for a scene/stage-sensitive gameplay palette block
- `01` is a strong candidate for front-end/title/ready-state palette ownership

These are interpretations, but they are grounded in repeated behavior across the real session.

## Snapshot-backed stage differences

Saved runtime snapshots now exist for:
- `active_runtime_stage_02`
- `active_runtime_stage_03`
- `active_runtime_stage_06`
- `active_runtime_stage_0d`
- `active_runtime_stage_11`

Across those snapshots, block `02` changes in a way that looks stage-sensitive:

- stage `0002`: `palblk 02 @200040 0000 3946 3948 390a ...`
- stage `0003`: `palblk 02 @200040 0000 3946 3948 390a ...`
- stage `0006`: `palblk 02 @200040 0000 3948 3948 390a ...`
- stage `000d`: `palblk 02 @200040 0000 390a 4108 3108 ...`
- stage `0011`: `palblk 02 @200040 0000 390a 4108 3108 ...`

Practical interpretation:
- block `02` is definitely not fixed across the whole game
- it is a good first-stage candidate for “per-scene or per-stage palette block”
- if we build a palette extraction/conversion tool, block `02` should be treated as a tracked scene-dependent bank

## Confirmed continue/return palette behavior

When the continue path is entered:
- block `02` is explicitly cleared to all zeroes at frames like `19501` and `24658`

When returning toward runtime/front-end ownership:
- block `02` is restored with stage-specific values

Practical interpretation:
- block `02` is involved in a controlled transition, not just passive background color state
- this is the kind of evidence we need for later Genesis dynamic palette upload logic

## Credits and front-end ready state

The capture includes `frontend_credit_ready` snapshots:
- frame `927`
- frame `8131`

Those snapshots show:
- `credits=0001`

Practical interpretation:
- the monitor did capture a credit-ready front-end state
- that gives us a grounded front-end palette snapshot distinct from the earliest attract/title boot state

## Important caution about the `stage` field

The tracked word at `0x10c13e` clearly changes through values like:
- `0001`
- `0002`
- `0003`
- `0006`
- `000d`
- `0011`

This is useful for distinguishing scene clusters, but it should not yet be treated as a proven “human stage number” field.

The latest play-session note makes this even clearer:
- the run only covered early stage 1 and then stage 1 part 2
- yet the tracked field advanced through values like `0001` to `0011`

So this field is almost certainly one of:
- sub-stage / area progression
- room or segment id
- stage controller state

and not a literal “world/stage number reached by the player”

It is safer to interpret it as:
- a runtime progression/state identifier that correlates with stage ownership

and only later prove whether it is:
- actual stage number
- room/segment id
- stage controller state
- or a mixed progression value

## Porting-relevant conclusions

Confirmed:
- front-end palette state is not static; it changes across title/credit/ready/story-style pages
- runtime scenes activate more palette blocks than the earliest title frame
- there are dedicated dynamic palette behaviors during continue/death handling
- at least one palette block is clearly stage-sensitive (`02`)
- several blocks are clearly animation/blink candidates (`1a..1d`, `33`, `43`)

Likely:
- faithful Genesis palette handling will require scene-specific uploads, not a single global palette mapping
- we should classify palette blocks into:
  - stable scene blocks
  - stage-sensitive blocks
  - animated/blink blocks
  - continue/death transition blocks

## Capture policy note

For future palette-capture runs:
- invincibility is acceptable
- direct stage-select / forced stage advance should be treated with caution
- if a cheat visibly produces broken palette state, that run should not be used as authoritative palette evidence for that stage

Best-practice capture path:
- allow normal progression through the game flow
- use invincibility to reduce failure noise
- only use stage-skip cheats when the resulting scene is visually confirmed to have sane palette state

Open:
- exact hardware ownership of each block by layer/sprite/UI
- exact meaning of the tracked `stage` field beyond “runtime progression / segment discriminator”
- exact mapping from these shadow blocks to the arcade custom video hardware’s live palette usage

## Best next step

Use this capture to produce a machine-readable report that groups blocks into:
- front-end stable
- runtime stable
- stage-sensitive
- animated/blinking
- continue-transition

That report should drive the first Genesis-side palette packing experiment.
