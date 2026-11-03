# RG-021 — Native stage implementation

RG-021 is implemented in candidate Build 0499. The permanent build-numbered report is:

`docs/design/Cody_build0499_native_stage_graphics_and_level_data.md`

The implementation uses the arcade semantic stage/record boundary to generate and install final Genesis-native Plane A/B assets. It adds the Round-1 castle/boss tail (records 16–22), parameterizes the same offline compiler/runtime package contract for Round 2 (records 23–45), corrects a fixed-B installer count-clobber defect, prevents unapproved Round-1 palette ownership from leaking into later rounds, classifies Rounds 3–6, and preserves the deterministic 795-frame rope result.

Build 0499 is a test candidate, not an accepted baseline. Visual correctness, the R1-S2 collision/progression report, and the live R1 boss-defeat transition require Tighe's real-hardware verification. RG-022 palette exports were not present; Palette Composer and the canonical palette decision registry were not modified.
