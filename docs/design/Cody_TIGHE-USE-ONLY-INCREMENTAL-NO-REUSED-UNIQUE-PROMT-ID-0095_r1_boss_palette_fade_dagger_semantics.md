# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0095

## TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0095 Result

The original arcade R1 boss does **not** use master line 25 at ROM `$4EE16`, nor the ordinary
round-working line-F pool at `$4FE62`. R1-S3 selects sprite control `$80`; embedded compositor
line F therefore resolves to physical CLCS line `$4F` (79), `$2009E0-$2009FF`. Boss-specific
routine `$47004` fades the 15 0RGB words at `$4708C` into entries 1-15 of that live line. Entry 0
is retained black.

The body and the five known type-15 auxiliary records all use compositor 1, `+$27=$00`, embedded
line F, and physical line `$4F`. Static program/pattern decoding and live actor records prove that
those type-15 records are the flying-dagger projectile pool. One 16-colour Genesis line is the
minimum faithful requirement for the normal body-plus-dagger presentation. Damage and boss-death
effects were deliberately not exercised, so whether a separate transient effect line is needed is
still pending; that does not change the one-line body/dagger result.

## Repository Baseline

- Branch: `rastan-direct-proposal`.
- Starting HEAD: `406ff54bd2495995fbe25f68aed748fd636fdca9`.
- Build counter: 539 before and after; no Genesis build was run.
- Pre-existing modified runtime outputs preserved and not staged:
  `build/mame/home/rastanmon/rastan_monitor.log`, `tools/mame/cheat/output.json`.
- `specs/palette_decisions.json` was consulted and was not changed, as required.

## R1 Boss Known Geometry / Palette Selector

The body remains `object:boss.r1.body`: base `$061D`, type `$0E`, compositor 1, initial anim `$00`,
program `$47908`, and `+$27=$00`. `$3C9E8` therefore retains the embedded compositor control nibble
F rather than applying an actor override.

The missing physical-bank fact is at `$452DA-$4530C`. Stage setup starts with D0=`$60`, but when
`stage-within-round >= 16` it changes D0 to `$80`, sets A5+`$2A2=1`, combines the retained low
nibble, and writes both `$380000` and A5+`$14`. Thus:

```text
physical line = ((sprite_control & $00E0) >> 1) | embedded_nibble
              = (($0080 & $00E0) >> 1) | $F
              = $40 | $0F = $4F (79)
```

The live trace observed `$380000=$0080` throughout the boss scene. The destination did not change.

## Field-Pool Rejection

`$3BA88[R1][F] -> pool 11 -> $4FE62` describes the ordinary working-palette publisher, not this
boss-specific fade. `$47004` bypasses A5+`$1600` and writes the special target directly to line
`$4F`. Therefore `$4FE62` is rejected as the R1 boss source: **YES**.

## Live Palette-RAM Trace

The reusable read-only script is `tools/mame/scripts/r1_boss_palette_fade_trace.lua`. It uses the
established original-arcade selector `$05FF9F=$F7`, standard coin/start fields, and stock work-RAM
survival cheats. It records all writes in `$200000-$200FFF`, the callback PC, frame state, lines
25/63/79, and actor records through the R1 auxiliary pool.

Trace: `states/traces/prompt0095_original_arcade_r1_boss_palette/`.

- Platform: ORIGINAL ARCADE MAME `rastan`.
- 5,600 frames; boss scene appeared at frame 2,587.
- Fade writes: 855 = 57 frames × 15 words.
- MAME's post-store tap reports PC `$47072`; the actual `move.w D2,(A0)+` writer is `$4706E`.
- The previous full-line state in `frames.tsv` plus each chronological new value gives the exact
  old/new history; the distilled transition old/new relation is encoded by consecutive `words`
  arrays and `changed_indices` in the machine-readable JSON.

The full recording under `docs/arcade_reference/Round 1 Playthough with Invincibility On/` visually
corroborates a black-to-lit entrance and airborne white dagger forms. It is corroboration only;
RAM writes and original code determine values and timing.

## Physical Boss Palette Destination

- Logical source line: embedded compositor line F.
- Scene sprite control: `$0080`.
- Physical line: `$4F` / decimal 79.
- Full live range: `$2009E0-$2009FF`.
- Fade writer range: `$2009E2-$2009FE`, entries 1-15.
- Entry 0: `$2009E0`, retained `$0000`.

## Final Fully Faded-In Palette

`#RRGGBB` uses MAME's xBGR-555 `pal5bit` expansion. Body usage covers indices 0-15. Dagger usage
comes from decoding programs `$47E54/$47E7A/$47E7F/$47E84/$47E8D/$47E92/$47E97` and pattern codes
`$67B,$67C,$683-$689`.

|i|live address|source|final word|0RGB|RGB|body|dagger|
|---:|---:|---:|---:|---:|---:|:---:|:---:|
|0|`2009E0`|retained|`0000`|`0000`|`#000000`|yes|yes|
|1|`2009E2`|`4708C`|`01D0`|`0870`|`#423900`|yes|no|
|2|`2009E4`|`4708E`|`3B18`|`0CC7`|`#636339`|yes|no|
|3|`2009E6`|`47090`|`7BDE`|`0FFF`|`#7B7B7B`|yes|yes|
|4|`2009E8`|`47092`|`730E`|`07CE`|`#396373`|yes|yes|
|5|`2009EA`|`47094`|`61C0`|`007C`|`#003963`|yes|yes|
|6|`2009EC`|`47096`|`3842`|`0117`|`#080839`|yes|yes|
|7|`2009EE`|`47098`|`23DE`|`0FF4`|`#7B7B21`|yes|no|
|8|`2009F0`|`4709A`|`1118`|`0C42`|`#632110`|yes|yes|
|9|`2009F2`|`4709C`|`0012`|`0900`|`#4A0000`|yes|no|
|10|`2009F4`|`4709E`|`298C`|`0665`|`#313129`|yes|yes|
|11|`2009F6`|`470A0`|`290A`|`0545`|`#292129`|yes|yes|
|12|`2009F8`|`470A2`|`000A`|`0500`|`#290000`|yes|no|
|13|`2009FA`|`470A4`|`4AD4`|`0AB9`|`#525A4A`|yes|yes|
|14|`2009FC`|`470A6`|`014E`|`0750`|`#392900`|yes|no|
|15|`2009FE`|`470A8`|`0000`|`0000`|`#000000`|yes|no|

Exact final live words:

```text
0000 01D0 3B18 7BDE 730E 61C0 3842 23DE
1118 0012 298C 290A 000A 4AD4 014E 0000
```

## `0x4EE16` Candidate Confirmation / Rejection

**NO.** `$4EE16` is cold-start master line 25. Its converted live words are:

```text
0000 5B1A 0000 3000 2908 314A 318C 31D4
3A56 6B5A 001E 0010 000A 02DE 2BDE 39CE
```

The trace independently retains those values on physical line 25 while `$4706E` writes the
different boss target to physical line 79. The visual resemblance was real but not provenance.

## Boss Palette Source / Staging Chain

For R1, `$47004` selects `$4708C + (round-1)*30`; `$4703C` consumes 15 target 0RGB words;
`$47076` applies `$46F84[source_nibble][A5+$270]`; `$4706E` writes xBGR-555 directly to CLCS.
There is no A5+`$1600` staging in this chain and no precomputed set of intermediate palettes.

## Entrance-Fade Writer

- Frame-spine caller: `$41F46 -> $47004` once per game frame.
- Gate/trigger: `$42332` sets A5+`$26E=1` when the R1 type `$0E` boss is positioned for entrance.
- Writer entry: `$47004`; inner loop `$4703C`; component helper `$47076`; store `$4706E`.
- Source: round-selected 15-word target table at `$4708C` (R1).
- Destination: `$2009E2-$2009FE`.
- State: A5+`$26E` enable, A5+`$270` step, boss actor `+$09` cadence counter.
- Completion: at step 7, `$47004` clears A5+`$26E` but still publishes that final pass.

## Arcade Fade Algorithm

This is a boss-specific, table-driven **4-bit component** fade. For each source 0RGB nibble `c`:

```text
faded_nibble = ROM[$46F84 + c*8 + step]
CLCS_word = (faded_B << 11) | (faded_G << 6) | (faded_R << 1)
```

The 16×8 LUT is durably transcribed in `rastan_r1_boss_palette_fade.c`. Its rows are monotonic but
not a uniform add: for example source F follows `0,1,3,5,8,B,D,F`, while source 1 follows
`0,0,0,0,1,1,1,1`. Components therefore start changing at different steps. Every pass evaluates
all 15 entries simultaneously; entries whose quantized component is unchanged simply repeat.
Index 0 is never written and remains black. The immutable target is never modified.

## Fade Timing / State Machine

The trace's body record exists hidden at Y=`$0180` before the entrance. On frame 2,715 it moves to
X=`$0050`, Y=`$0084`, A5+`$26E` becomes 1, and step 0 is first published. `$46ED2-$46F04`
increments the boss actor's `+$09` every actor update; at 8 it resets that byte and increments
A5+`$270`. Thus steps 0-6 each last eight frames. Step 7 is written on frame 2,771, after 56 frame
intervals / 57 inclusive writer frames. It is then held without more fade writes.

Reaching step 7 also sets A5+`$272=4`, calls `$457B2`, creates the five dagger records, and advances
the body from anim `$00` to its active state on the following captured frame. The trace had an
active player state during the entrance; the source timing is owned by the boss actor counter, not
an NTSC millisecond timer.

## Fade-Step Sequence

Each row is the distinct first-publication frame. `Δ` lists entries changed from the previous row;
within each eight-frame plateau the routine rewrites the same 15 values each frame.

|step|frame|raw live line 0..15|Δ|
|---:|---:|---|---|
|0|2715|`0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000`|none|
|1|2723|`0000 0042 0842 0842 0842 0840 0800 0842 0042 0002 0842 0842 0002 0842 0042 0000`|1-14|
|2|2731|`0000 0086 10C6 18C6 18C4 1880 1000 08C6 0846 0006 1084 1044 0004 18C6 0084 0000`|1-14|
|3|2739|`0000 00C8 194A 294A 2946 28C0 1800 114A 088A 000A 10C6 1084 0004 294A 0086 0000`|1-11,13-14|
|4|2747|`0000 010A 21CE 4210 39C8 3900 2042 1210 088E 000C 1908 1886 0006 31CE 00C8 0000`|1-14|
|5|2755|`0000 014C 2A52 5AD6 524A 4940 2842 1AD6 10D2 000E 2108 20C8 0008 3A50 010A 0000`|1-14|
|6|2763|`0000 018E 32D6 6B5A 62CC 5980 3042 1B5A 10D6 0010 214A 20C8 0008 4292 010C 0000`|1-10,13-14|
|7|2771|`0000 01D0 3B18 7BDE 730E 61C0 3842 23DE 1118 0012 298C 290A 000A 4AD4 014E 0000`|1-14; target|

## Durable C Added / Updated

- `analysis/decompilation/c/raw/00047004.c`: entry-matched `$47004/$4703C/$47076` mechanics.
- `analysis/decompilation/c/rastan_r1_boss_palette_fade.c`: maintained LUT, R1 target, cadence,
  CLCS conversion, and later Genesis quantization rule.
- Coverage rows and the decompilation README were updated. The old blanket `$3F/$4FE62` boss claim
  in `rastan_boss_composite.c` was corrected to distinguish ordinary stages from boss stages.

## Boss Auxiliary Palette Relationship

The known R1 type-15 auxiliaries are the five records at A5+`$748,$788,$7C8,$808,$848`. `$457D0`
sets type `$0F`, compositor 1, `+$21=0`, invokes the type loader (base `$061D`, initial anim `$14`),
and leaves `+$27=$00`. Their programs embed nibble F. They therefore use the same physical `$4F`
line and the same 16 live values as the body. These are not separately coloured structural pieces.

## Flying-Dagger Actor Identification

- Human identity: Round-1 boss flying daggers (live screenshots/video corroborate the decoded form).
- Creator: `$457B2` five-record loop, member initializer `$457D0`.
- Trigger: `$46EF6-$46F02` when fade step reaches 7.
- Type/base: `$0F` / `$061D`; compositor 1; `+$27=$00`.
- Initial anim/program: `$14` / `$47E54`; flight anims `$1A-$1F`.
- Pattern domain: `$067B,$067C,$0683-$0689`.
- Initial positions: X `$98,$9C,$A0,$A4,$A8`, Y `$10`.
- Lifecycle: `$421FC-$42214` detects type `$0F`, retires it, restores A5+`$27C` from A5+`$212`,
  and respawns through `$457D0`.
- Scene reachability: live records appear on frame 2,771 and continue through normal R1 boss play.

The type `$0F` record pool can later be reused for a base `$0275` burst presentation. That later
reuse is not the flying-dagger identity and must not be merged with it.

## Flying-Dagger Palette Relationship

**YES** for entrance and normal fight. Body and daggers have `+$27=$00`, compositor 1 programs with
embedded F, scene sprite control `$80`, and physical line `$4F`. The dagger patterns use only the
subset `{0,3,4,5,6,8,10,11,13}` of the body's full 0-15 index domain, with no conflicting meaning.
The final source line is therefore exactly shared, not merely visually similar.

The trace deliberately did not damage or kill the boss. Normal animation, repeated dagger cycles,
and the later player/game-over state left line `$4F` unchanged through frame 5,600. Damage flash
and boss-death palette behavior remain **not established**, so no claim is made that their transient
effect presentation uses only this line.

## Minimum Faithful Genesis Palette-Line Requirement

For the requested R1 boss body plus its flying daggers: **1 line**. One shared canonical context,
`R1 Boss + Flying Daggers`, is recommended. A second line would duplicate the same source palette
and is not source-faithful or necessary. R1-S3 Plane-B/Genesis Line-2 ownership is outside this
proof and is not freed or changed. Separate damage/death effect allocation remains pending.

## Genesis-Native Arcade-Faithful Fade Specification

Later runtime implementation should use Tighe's authored final Genesis boss line as the final
mapping, but retain the original eight-state counter and eight-frame cadence:

1. Trigger where the native R1 boss entrance reaches the `$42332` semantic event.
2. Keep step 0..7 and an 8-update actor counter; steps 0-6 last eight updates, step 7 is published
   once and then held; completion clears the enable after the final publication.
3. Reproduce the original `$46F84` nibble trajectory first. For source nibble result `f`, reduce to
   Genesis channel `f >> 1` (equivalent to `(f*2)>>2`) and pack `0000 BBB0 GGG0 RRR0`.
4. Preserve repeated CRAM values when adjacent arcade steps collapse under 3-bit quantization.
   In particular, source steps 0 and 1 may collapse for some/all mapped channels; do not invent a
   new curve or redistribute time.
5. Apply the resulting intensity state to Tighe's final mapped line in a deterministic per-channel
   manner, with final step exactly equal to the authored final line. Publish one native CRAM line;
   do not emulate CLCS palette RAM or maintain intermediate authored palettes.
6. At step 7 preserve the original boss activation/dagger-creation event.

The source-derived quantized reference states are present in the maintained C and can be generated
from the JSON source words. If Tighe's authored final Genesis colours differ from direct top-bit
quantization, use the same eight source intensity states as monotonic gates/scales whose step 7 is
the authored target; do not substitute a linear per-frame fade.

## Andy Palette Composer Handoff

Andy should expose exactly one source palette for **Round 1 → Sub-Round 3 / Boss → Round 1 Boss**:
the final 16-word/RGB table above, with provenance `$4708C -> $47004 -> $2009E2`, physical line
`$4F`. Mark body, type-15 auxiliaries, and flying daggers as sharing it. Intermediate entrance
states are runtime behavior and must **not** become mapping screens or authored palette choices.
No Palette Composer or Bestiary file was changed here.

## Verification

- Independent static body-line proof: `$3C9E8` embedded F + `$452DA-$4530C` control `$80` → `$4F`.
- Independent live destination proof: 855 writes to line 79, `$2009E2-$2009FE`, store `$4706E`.
- Final source proof: ROM `$4708C` plus `$46F84[..][7]` produces the captured final words.
- Candidate rejection: line 25 retained `$4EE16` conversion while line 79 held different values.
- Field-pool rejection: `$47004` has no `$3BA88/$4FD02/A5+$1600` dependency.
- Timing proof: A5+`$26E/$270`, actor `+$09`, and live frame sequence agree exactly.
- Dagger proof: creator/type/base/program/pattern decoding agrees with five live records at frame
  2,771 and video/screenshot appearance.
- Palette sharing proof: identical embedded nibble, no override, same scene control and destination;
  decoded pixel-index domains have no collision.
- Task C files pass `gcc -std=c11 -fsyntax-only`. The repository-wide coverage guard still reports
  its six pre-existing COMPLETE rows without raw files (`41CFA`, `4734A`, `4205C`, `4736A`,
  `41D26`, `4A02A`); all three new 0095 rows independently pass their raw/semantic/status checks.

## Files / Local Commit / Logs

Machine-readable evidence:
`analysis/actor_decompilation/r1_boss_palette_fade_dagger_semantics.json`.

Raw trace evidence remains under
`states/traces/prompt0095_original_arcade_r1_boss_palette/`; the reusable capture script is
`tools/mame/scripts/r1_boss_palette_fade_trace.lua`. This task created no Genesis ROM, did not run
the Genesis build, did not change the build counter, and did not push.

Verification commands/results:

- JSON parse: PASS.
- Independent ROM `$4708C`/`$4EE16` extraction plus 855 live line-79 writes against the distilled
  eight states: PASS.
- `gcc -std=c11 -fsyntax-only -I analysis/decompilation/c` on the two new C files: PASS.
- PROMT-0095 coverage-row audit: PASS.
- `git diff --check`: PASS.
- Repository-wide coverage guard: pre-existing FAIL described above; no new-row failure.

Source/evidence local commit: `888245e10563d80effd96191d2b7e1b1d196ce12`. The documentation
commit is reported in the final response because a commit cannot contain its own final hash. No
GitHub push was made.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0095`
