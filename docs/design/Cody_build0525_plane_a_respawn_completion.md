# Build 0525 standalone delivery receipt — Plane A respawn completion

Build 0525 replaces runtime static Plane A scene/checkpoint images with a bounded replay of the retained
live native descriptor producers at arcade semantic boundary `$050538`. The replay preserves the
original 16-by-4 descriptor-source cadence, uses the completed-fill selector saved at `A5+$132C`, and
restores all post-fill state.

The last Build 0524 failure was a stale condition-code bug in selector 0: an authored attribute load of
zero caused `BEQ` to skip residency resolution of logical code `$1731`. Adding `TST.W D3` before the
blank test makes the producer write final Genesis word `$0301`. The 14 R1-S2 discrepancies are now zero;
R1-S1/S2/S3 initial staging equals the authored oracle and actual VDP VRAM. R1-S2 selector-1 scrolling,
death/respawn publication, canonical gates, mandatory trace, variants, and Re-In-Carnation command `$27`
all pass.

Normal ROM: `dist/rastan-direct/rastan_direct_video_test_build_0525.bin`

Size: 3,792,568 bytes

SHA-256: `e5f9b01205ed4a7d535488ab8b5da88522f9df33eeae70ca7d0261a694cbf98d`

This is not an acceptance declaration. Tighe must verify the real R1-S1 record `$000B` checkpoint,
later R1-S2 scrolling/climbing, and R1-S3. Full evidence and limitations are in the PROMT-ID-0043 and
PROMT-ID-0044 reports beside this receipt.

Implementation commits: `c7ac1f1c`, `59260a9e`.
