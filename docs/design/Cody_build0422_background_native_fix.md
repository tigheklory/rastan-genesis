# Build 0422 native background correction

Build 0422 corrects only the rejected Build-0421 Plane-A grouping defect,
adds collision/visual semantic gates, and adds the repeatable MAME rope metric.
It includes no further optimization.

The generated `visual[16]` and `collision[16]` fields remain co-stored but
semantically independent. The generic correction detects the one aligned
four-cell row block that straddles the live ring front and resolves its cells
through the established authoritative per-cell accessor. All other blocks
retain the Build-0421 batched lookup.

Matched NTSC MAME state at player X `0x0081`, foreground Y `0x0149`, record 1:

- Build 0419 vs Build 0422 Plane A: zero differing words;
- Plane B: zero differing words;
- full 64×64 collision map: zero differing words.

Mechanical gates pass: exhaustive 4,733-record equivalence, collision/visual
independence, full-span background coherence, VDP DMA boundary, boot guard,
canonical ROM, gameplay entry, zero crash-handler entries, 30-second MAME
trace (1,798 frames), and complete five-ROM family. The standing seven-epoch
label remains FAIL after its epoch-0 PASS, as on the accepted baseline.

The MAME rope metric is deterministic: Build 0419 is 878 frames / 14652.200 ms;
Build 0422 is 879 frames / 14668.888 ms (`+0.114%` elapsed). Tighe subsequently
verified the Segment-0 visuals and destructible block on real Genesis and
accepted Build 0422 as the forward baseline.

All five artifacts are 2,694,840 bytes:

| artifact | SHA-256 |
|---|---|
| `rastan_direct_video_test_build_0422.bin` | `3828222d36e689b6f000ffe3b72509d555fb237a147e0e066dfff105e295d3cb` |
| `_c` | `c9db0f5c280964c9afec4742882db305dabf6da1186c32662ba3f6cf598d774c` |
| `_d` | `0458cc45691a885dba58e0e9ced139001a4bef2723e97a3dfdb491b34d785b5d` |
| `_do` | `d60ad86b19e68959ad7138a9840e63c90d95eaaf36bc2e041c7042381cf6f008` |
| `_s` | `b24c786646d9be86b0ff23efc0be3aa4617195921367c3f896e374e4e52d7d70` |
