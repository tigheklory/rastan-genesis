# Build 0311 Rope/Waterfall Transition Retention Fix

## Baseline and scope

- Accepted input checkpoint: Build 0310, `dist/rastan-direct/rastan_direct_video_test_build_0310.bin`, SHA-256 `998dc6efa7060572120a4b0055c0b71a5301e478718b6dfa17fa47398b7959e8`.
- Produced checkpoint: Build 0311, `dist/rastan-direct/rastan_direct_video_test_build_0311.bin`, SHA-256 `a3a1e32beba2e36a5ef17d7dcf61e1da089520740bfeaf06f1f591a677cc362c`, 1,670,840 bytes.
- Counter: 310 -> 311. Build 0310 remains present and unchanged.
- Scope was limited to the first observed Plane-A lifetime failures: record 2 -> 3 (coarse epoch A -> B) and record 3 -> 4 (coarse epoch B -> C).
- Plane B, native sprite capacity/PC090OJ, scrolling, collision, palette, Phase 2, and Phase 3 were not changed.

## Architecture compliance

The retained semantic cut is the original arcade selector-0 record/source-column and scroll/progression decision. The replaced chip-specific tail is the PC080SN destination/write behavior below that decision: the native helper installs precompiled Genesis Plane-A code-to-slot/pattern packages and the selector publishes direct Genesis name words. No runtime cache, LRU, allocator, hashing, visibility solver, or software PC080SN device was added.

The generated package/LUT installer remains an explicitly isolated transitional compatibility structure. It is deterministic and compiler-owned, not a virtual PC080SN memory device. This task did not broaden or promote that structure into the final architecture.

## Proven boundaries

The compiler reconstruction uses the original selector-0 64x64 record map, a 40-column legal display window, all 64 legal logical rows, and both original scroll axes. It does **not** assume a fixed vertical viewport.

| Failure | Outgoing record/epoch | Incoming record/epoch | Arcade scroll X | Arcade scroll Y | Compile-time overlap steps | Handoff logical column |
|---|---:|---:|---:|---:|---:|---:|
| rope -> waterfall | 2 / A (0) | 3 / B (1) | `0x0168` | `0x0105` | 0..44 | 45 |
| waterfall -> next rope/exterior | 3 / B (1) | 4 / C (2) | `0x0168` | `0x015D` | 0..44 | 45 |

These boundaries are encoded by `TRANSITION_DEFS` in `tools/translation/compile_pc080sn_genesis.py` and materialized as runtime packages 7 and 8. Stable semantic epochs remain exactly:

| Epoch | Records | Exact Plane-A patterns |
|---:|---|---:|
| A / 0 | 0-2 | 282 |
| B / 1 | 3 | 333 |
| C / 2 | 4-9 | 444 |
| D / 3 | 10 | 368 |
| E / 4 | 11 | 483 |
| F / 5 | 12-14 | 433 |
| G / 6 | 15 | 349 |

The semantic record-to-epoch table is unchanged: `0,0,0,1,2,2,2,2,2,2,3,4,5,5,5,6`.

## Build 0310 root cause

Build 0310 installed the complete incoming stable package at an epoch boundary. That package omitted outgoing-only identities even though the two-dimensional viewport could still reference their old name words. The first invalidating operation was the final store in `.Linstall_remap_plane`:

```asm
.Linstall_remap_plane_store:
    move.w  %d0, (%a0)
```

For an outgoing-only visible cell, this rewrote the existing Plane-A name word using an LUT that no longer represented its old code, before the old cell had left the legal viewport. The same immediate full-package replacement caused both failures:

- At record 2 -> 3, rope cells remained in the name table, but their old identities were removed by stable epoch B installation.
- At record 3 -> 4, waterfall cells remained in the name table, but their old identities were removed by stable epoch C installation.

The defect was therefore not an absent map cell, Plane-B capacity issue, sprite issue, or fixed-Y assumption. It was a mismatch between coarse epoch change and the last legal visible use of outgoing Plane-A identities.

## Transition working sets

### Whole-epoch context

| Boundary | Outgoing epoch | Incoming epoch | Shared whole-epoch | Retired whole-epoch | New whole-epoch |
|---|---:|---:|---:|---:|---:|
| A -> B | 282 | 333 | 33 | 249 | 300 |
| B -> C | 333 | 444 | 38 | 295 | 406 |

Whole-epoch union is not used as the transition requirement. The compiler reconstructs only the legal two-dimensional overlap window.

### Exact bounded overlap

| Boundary | Outgoing visible | Incoming required | Shared visible | Outgoing-only visible | Incoming-only required | Peak resident | Capacity | Margin |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| rope -> waterfall | 236 | 191 | 33 | 203 | 158 | 394 | 484 | 90 |
| waterfall -> next rope | 333 | 179 | 33 | 300 | 146 | 479 | 484 | 5 |

Both peaks fit the existing 484-slot Plane-A allocation. Sprite capacity remains unchanged. Both generated gates report zero visible missing patterns, zero slot collisions, zero moved retained identities, and zero missing identities at stable-package handoff.

## Generated lifetime schedule

The seven stable packages remain packages 0..6. Two bounded overlap packages were added:

- Package 7: record 2/A -> record 3/B, 394 identities. It preserves all 236 outgoing visible identities in their existing slots and adds the 158 incoming-only identities into safe slots.
- Package 8: record 3/B -> record 4/C, 479 identities. It preserves all 333 outgoing visible identities in their existing slots and adds the 146 incoming-only identities into safe slots.
- At logical source column 45, `fg_boundary_transition_step` replaces package 7 with stable package 1, or package 8 with stable package 2. Reclaim occurs only at this precomputed safe handoff.

The runtime mapping is `0,0,0,7,8,2,2,2,2,2,3,4,5,5,5,6`; the semantic epoch mapping remains unchanged. The selector-0 source-column producer invokes the handoff before publishing the incoming column. Runtime performs only explicit known package installs; there is no generic per-frame residency scan.

The current display-off/install/display-on bracket remains present for both overlap and handoff installs. Black-frame removal was deliberately not broadened into this build.

## Rope identity proof

- Record: 2.
- Exact cells: column 46, rows 31..53 (23 referenced cells).
- Exact unique arcade codes/patterns: 12.
- Slots before transition: `1124, 1125, 1126, 1127, 1128, 1129, 1130, 1131, 1132, 1134, 1135, 1136`.
- Slots in package 7: `1124, 1125, 1126, 1127, 1128, 1129, 1130, 1131, 1132, 1134, 1135, 1136`.
- Slot movement: zero.

### Rope cells

- row 31: 46:0x0260
- row 32: 46:0x0261
- row 33: 46:0x0262
- row 34: 46:0x0263
- row 35: 46:0x0260
- row 36: 46:0x0261
- row 37: 46:0x0262
- row 38: 46:0x0263
- row 39: 46:0x0260
- row 40: 46:0x0494
- row 41: 46:0x0498
- row 42: 46:0x049C
- row 43: 46:0x04A0
- row 44: 46:0x04A2
- row 45: 46:0x04A3
- row 46: 46:0x04A4
- row 47: 46:0x04A5
- row 48: 46:0x04A2
- row 49: 46:0x04A3
- row 50: 46:0x04A4
- row 51: 46:0x04A5
- row 52: 46:0x04A2
- row 53: 46:0x04A3

### Rope code and exact 32-byte pattern hash

| Arcade code | SHA-256 of exact physical pattern |
|---|---|
| 0x0260 | `024c1844116abf8e7c764c12bc5350eac16e83c4d1c3d895a611888e371d1e91` |
| 0x0261 | `1f0b99a5cc9b98e02501f841dd645003a34e25ac5433f9df91aa8b5e2e42c369` |
| 0x0262 | `ea34766d00c87e3eb02c71ad2bd74d5e0f046db575db2d773a3d72125d5688ec` |
| 0x0263 | `f90841d0770ceb9cb8c67988b4b9b034fc551726a7aefca0497c1da564062ae2` |
| 0x0494 | `82e6305bab4cf0933b403dcc836568640e8635f194220eaad370cfd85f69c30b` |
| 0x0498 | `6daac57c7e9b9dcd8f51d8ad866fc82340fa8bfb247c65c746008e555d10bbf6` |
| 0x049C | `8fbdf96e4cdd52aa7caa4ff65f0d44317dc3d91a5eb79eda1514497168f33602` |
| 0x04A0 | `caa742118387d23010c7511e44cbb6db83b7e1ccb94530d92f23b147ec306b64` |
| 0x04A2 | `1fe0c03608102fe1e39da1b9d152eb2846798011b3b1ce9747b5ba2fa9bf4c4a` |
| 0x04A3 | `51a5c432afd7452991834d4a3619a4d04006d0c12785b213b3d209177a56c628` |
| 0x04A4 | `9cf3f04ee71f15efe67b8a14964e6a6c1ef92669a15d2af38c27c647faad48d7` |
| 0x04A5 | `38a2d2e41d5a37f0ef27fa42a0b64881f4d99a6ff42e11141e0f6d0806739218` |

## Waterfall identity proof

- Record: 3.
- Exact selected map-cell envelope: rows 36..51, columns 36..55.
- Selected waterfall map cells: 288.
- Exact unique arcade codes/patterns: 224.
- Slots before transition (224): `856, 857, 858, 859, 860, 861, 862, 864, 865, 866, 867, 868, 869, 870, 871, 872, 873, 874, 875, 876, 877, 878, 879, 881, 882, 884, 885, 886, 887, 888, 889, 890, 892, 893, 894, 895, 897, 899, 900, 901, 904, 906, 907, 909, 911, 912, 913, 915, 916, 917, 918, 921, 922, 923, 924, 925, 927, 928, 929, 930, 931, 932, 935, 936, 937, 938, 939, 942, 943, 944, 945, 947, 948, 949, 950, 951, 952, 954, 956, 959, 960, 962, 964, 966, 967, 968, 969, 970, 971, 972, 973, 974, 975, 978, 981, 982, 983, 984, 985, 986, 987, 989, 990, 991, 993, 994, 996, 997, 1003, 1023, 1024, 1025, 1027, 1032, 1038, 1044, 1046, 1047, 1048, 1054, 1057, 1064, 1067, 1070, 1071, 1074, 1075, 1084, 1087, 1089, 1092, 1104, 1106, 1107, 1111, 1137, 1139, 1140, 1141, 1142, 1143, 1144, 1145, 1147, 1148, 1149, 1150, 1152, 1154, 1155, 1156, 1157, 1159, 1160, 1161, 1162, 1163, 1164, 1165, 1166, 1167, 1168, 1169, 1170, 1171, 1172, 1173, 1174, 1176, 1177, 1178, 1179, 1180, 1183, 1184, 1185, 1186, 1187, 1188, 1189, 1191, 1192, 1193, 1194, 1195, 1196, 1197, 1198, 1200, 1201, 1202, 1203, 1204, 1205, 1206, 1207, 1209, 1211, 1212, 1213, 1214, 1215, 1216, 1217, 1218, 1219, 1220, 1223, 1225, 1226, 1227, 1228, 1229, 1230, 1231, 1232, 1233, 1234, 1236, 1237, 1238, 1240, 1243, 1244`.
- Slots in package 8 (224): `856, 857, 858, 859, 860, 861, 862, 864, 865, 866, 867, 868, 869, 870, 871, 872, 873, 874, 875, 876, 877, 878, 879, 881, 882, 884, 885, 886, 887, 888, 889, 890, 892, 893, 894, 895, 897, 899, 900, 901, 904, 906, 907, 909, 911, 912, 913, 915, 916, 917, 918, 921, 922, 923, 924, 925, 927, 928, 929, 930, 931, 932, 935, 936, 937, 938, 939, 942, 943, 944, 945, 947, 948, 949, 950, 951, 952, 954, 956, 959, 960, 962, 964, 966, 967, 968, 969, 970, 971, 972, 973, 974, 975, 978, 981, 982, 983, 984, 985, 986, 987, 989, 990, 991, 993, 994, 996, 997, 1003, 1023, 1024, 1025, 1027, 1032, 1038, 1044, 1046, 1047, 1048, 1054, 1057, 1064, 1067, 1070, 1071, 1074, 1075, 1084, 1087, 1089, 1092, 1104, 1106, 1107, 1111, 1137, 1139, 1140, 1141, 1142, 1143, 1144, 1145, 1147, 1148, 1149, 1150, 1152, 1154, 1155, 1156, 1157, 1159, 1160, 1161, 1162, 1163, 1164, 1165, 1166, 1167, 1168, 1169, 1170, 1171, 1172, 1173, 1174, 1176, 1177, 1178, 1179, 1180, 1183, 1184, 1185, 1186, 1187, 1188, 1189, 1191, 1192, 1193, 1194, 1195, 1196, 1197, 1198, 1200, 1201, 1202, 1203, 1204, 1205, 1206, 1207, 1209, 1211, 1212, 1213, 1214, 1215, 1216, 1217, 1218, 1219, 1220, 1223, 1225, 1226, 1227, 1228, 1229, 1230, 1231, 1232, 1233, 1234, 1236, 1237, 1238, 1240, 1243, 1244`.
- Slot movement: zero.

The exhaustive per-cell `row/column/code` set is preserved in `build/pc080sn_boundary/boundary_report.json`; the compact row listing below is the same generated set.

### Waterfall cells

- row 36: 36:0x026D 37:0x026E 38:0x026F 39:0x0270 40:0x027D 41:0x027E 42:0x027F 43:0x0280 44:0x0289 45:0x028A 46:0x028B 47:0x028C 48:0x0299 49:0x029A 50:0x029B 51:0x029C 52:0x02A9 53:0x02AA 54:0x02AB 55:0x02AC
- row 37: 36:0x0271 37:0x0272 38:0x0273 39:0x0274 40:0x0281 41:0x00A5 42:0x0096 43:0x0282 44:0x028D 45:0x028E 46:0x028F 47:0x0290 48:0x029D 49:0x029E 50:0x029F 51:0x02A0 52:0x02AD 53:0x02AE 54:0x02AF 55:0x02B0
- row 38: 36:0x0275 37:0x0276 38:0x0277 39:0x0278 40:0x0283 41:0x0099 42:0x009A 43:0x0284 44:0x0291 45:0x0292 46:0x0293 47:0x0294 48:0x02A1 49:0x02A2 50:0x02A3 51:0x02A4 52:0x02B1 53:0x02B2 54:0x02B3 55:0x02B4
- row 39: 36:0x0279 37:0x027A 38:0x027B 39:0x027C 40:0x0285 41:0x0286 42:0x0287 43:0x0288 44:0x0295 45:0x0296 46:0x0297 47:0x0298 48:0x02A5 49:0x02A6 50:0x02A7 51:0x02A8 52:0x02B5 53:0x02B6 54:0x02B7 55:0x02B8
- row 40: 36:0x02B9 37:0x02BA 38:0x02BB 39:0x02BC 40:0x02C9 41:0x02CA 42:0x02CB 43:0x02CC 44:0x02D9 45:0x02DA 46:0x02DB 47:0x02DC 48:0x02C9 49:0x02CA 50:0x02CB 51:0x02CC 52:0x02E9 53:0x02EA 54:0x02EB 55:0x02EC
- row 41: 36:0x02BD 37:0x02BE 38:0x02BF 39:0x02C0 40:0x02CD 41:0x02CE 42:0x02CF 43:0x02D0 44:0x02DD 45:0x02DE 46:0x02DF 47:0x02E0 48:0x02CD 49:0x02CE 50:0x02CF 51:0x02D0 52:0x02ED 53:0x02EE 54:0x02EF 55:0x02F0
- row 42: 36:0x02C1 37:0x02C2 38:0x02C3 39:0x02C4 40:0x02D1 41:0x02D2 42:0x02D3 43:0x02D4 44:0x02E1 45:0x02E2 46:0x02E3 47:0x02E4 48:0x02D1 49:0x02D2 50:0x02D3 51:0x02D4 52:0x02F1 53:0x02F2 54:0x02A3 55:0x02F3
- row 43: 36:0x02C5 37:0x02C6 38:0x02C7 39:0x02C8 40:0x02D5 41:0x02D6 42:0x02D7 43:0x02D8 44:0x02E5 45:0x02E6 46:0x02E7 47:0x02E8 48:0x02D5 49:0x02D6 50:0x02D7 51:0x02D8 52:0x02F4 53:0x02F5 54:0x02F6 55:0x02F7
- row 44: 36:0x02F8 37:0x02F9 38:0x02FA 39:0x02FB 40:0x0308 41:0x0309 42:0x030A 43:0x030B 44:0x0318 45:0x0319 46:0x031A 47:0x031B 48:0x0328 49:0x0329 50:0x032A 51:0x032B
- row 45: 36:0x02FC 37:0x02FD 38:0x02FE 39:0x02FF 40:0x030C 41:0x030D 42:0x030E 43:0x030F 44:0x031C 45:0x031D 46:0x031E 47:0x031F 48:0x032C 49:0x032D 50:0x032E 51:0x032F
- row 46: 36:0x0300 37:0x0301 38:0x0302 39:0x0303 40:0x0310 41:0x0311 42:0x0312 43:0x0313 44:0x0320 45:0x0321 46:0x0322 47:0x0323 48:0x0330 49:0x0331 50:0x0332 51:0x0333
- row 47: 36:0x0304 37:0x0305 38:0x0306 39:0x0307 40:0x0314 41:0x0315 42:0x0316 43:0x0317 44:0x0324 45:0x0325 46:0x0326 47:0x0327 48:0x0334 49:0x0335 50:0x0336 51:0x0337
- row 48: 36:0x02B9 37:0x02BA 38:0x02BB 39:0x02BC 40:0x0318 41:0x0319 42:0x031A 43:0x031B 44:0x0318 45:0x0338 46:0x0339 47:0x031B 48:0x033B 49:0x033C 50:0x033D 51:0x032B
- row 49: 36:0x02BD 37:0x02BE 38:0x02BF 39:0x02C0 40:0x031C 41:0x031D 42:0x031E 43:0x031F 44:0x031C 45:0x033A 46:0x031E 47:0x031F 48:0x033E 49:0x033F 50:0x0340 51:0x0341
- row 50: 36:0x02C1 37:0x02C2 38:0x02C3 39:0x02C4 40:0x0320 41:0x0321 42:0x0322 43:0x0323 44:0x0320 45:0x0321 46:0x0322 47:0x0323 48:0x0342 49:0x0343 50:0x0344 51:0x0333
- row 51: 36:0x02C5 37:0x02C6 38:0x02C7 39:0x02C8 40:0x0324 41:0x0325 42:0x0326 43:0x0327 44:0x0324 45:0x0325 46:0x0326 47:0x0327 48:0x0345 49:0x0346 50:0x0347 51:0x0348

### Waterfall code and exact 32-byte pattern hash

| Arcade code | SHA-256 of exact physical pattern |
|---|---|
| 0x0096 | `3bb75b1afa5386407eca87aa3255009ef973833c237996564efce22b94b099cb` |
| 0x0099 | `582cebf0c760b46de4c5cbc55c80dc11a1fe6eca6170f9b26e22db7da6f72fa7` |
| 0x009A | `4fcfc58452c7bef620cd16b4f1d73a7c74d4e505e5f9ee5b8157be05540d370f` |
| 0x00A5 | `17529f4ea743672cab69eb3bacb2948d100cc6ec29548ec3cb486e11653c8514` |
| 0x026D | `c975b6574ad63108f96f41f168c72faf05a4af3afa3b23f572c168dbd7b8c455` |
| 0x026E | `997e176e3161ff9db69be1803a56d517b31d868cb86939e8beed86780f500848` |
| 0x026F | `a3ff3f993c94d3ddb437520dc20df97e512421ad8ba50a3a366ff70f87dc2be0` |
| 0x0270 | `4f45a60beb912c95f9544c77a1933f75c95a8cee47d7b21bee8754b209c4996f` |
| 0x0271 | `1abd771d6bb18ea5ec415f4c327ded3fe223b1eb44cae99a6f21dc363ed688b7` |
| 0x0272 | `68fbd216bbb3213f0d4b1a6040e358407f57c6029a8494dc9dae6c980166bff0` |
| 0x0273 | `7c64db3c34d50562eac47897ef823a3b55fdf1978828e3feb7e576cebcce3644` |
| 0x0274 | `17475fe643ccaf8081a07beab73ffc0110f734900b0d1c679eab662440a5f7e3` |
| 0x0275 | `8cccc2687499a778008524675cc52fb16f9da1335589f14291160415f7d7b8a8` |
| 0x0276 | `12655496b8d9a0c6dc749a3d995cd8348efd83c0ee8f539404cf6550f4611c45` |
| 0x0277 | `6d406435db576a20392438d1dddcda8cf950d08b2c6204daad7c23d39b9c9f34` |
| 0x0278 | `3b88f3027004ecb3fb18944c2b44606ab116d941305ce81bcc42ac7f19fc3932` |
| 0x0279 | `99d89ae8854c25a2cea3eee473c03f6f8c8b88ea0549b73e3e76938472a56f32` |
| 0x027A | `d54210ca4f76337d7e87112002364ba12d4f1b310b47aed38f1ead0a2dfda569` |
| 0x027B | `d18fd239d10e7e90ebc158531e231c429070d31cc083616f4cfce2a3dac6230f` |
| 0x027C | `0a7cd248118c0c05cbb9a7de3e8be9a5e69e8fb72eede9dad3023404022e913e` |
| 0x027D | `c7e98298e5763dbb5ff313368987ab3777c1d4d4d314f278c5d4428e4248a482` |
| 0x027E | `63fa28e326f1f6061c134d8cd869f738d572a85dd918c0cff6d93eb3f19dd7ff` |
| 0x027F | `8aa948402a9e36069027f0d4db44ac10d7d91068c238ebdf0c163b16e3c15e29` |
| 0x0280 | `8602f4e30b9dce0aaab1bbcc4cc81fe1c9c2b907f2875db54480314eaa0aa8a6` |
| 0x0281 | `873d54da9442fd2fb343691f9796634c6b7de90d2d0eb080447ee7bc9721cccf` |
| 0x0282 | `5ad847483641b3da116953640aa9aa87b38c402f44ffae7d1690d60895252177` |
| 0x0283 | `dfdebd76272f5c1e555449838157b320e965b87ead237da546895d3a5de62266` |
| 0x0284 | `f6f1c6cd6c05dcdd06bdc904d23ca462b65daba5ec0cac4f4725fe09b6d5c2e7` |
| 0x0285 | `c4be07c71c5ccbd9e9329402010e5dbbe1fa989466bd859ac6f6005c624bb03d` |
| 0x0286 | `496b487714a0dc040640cb601459d13b6583ef1a4a0edb98051b635253b7019d` |
| 0x0287 | `9aaef7a25273dfd54871be333539fecceca352d290c5a17b0cd96e95b9975056` |
| 0x0288 | `af0182aa2034a7e28478cfa9ff1c983fd88daa1786353028ef21cbc0a1e73923` |
| 0x0289 | `e7b97504620e6fb0760627b8924d73f3ffef1ba449d3a4c7b6ef4cd951d50c2c` |
| 0x028A | `ca5e4b98e4f622cf20f14e429551c7a6b4bf69d4bec09be35dce50d9618471a9` |
| 0x028B | `b6ce242c8b80efe904a10a9161d412edaef46284a38eac1788c775e294b96b7c` |
| 0x028C | `2fed2bbf0b0093bfe7f7f326d40d3268d03a078e45e9d1b0e97bf04b5d4ab476` |
| 0x028D | `466da9ed2b0cf633ecbbe65d163d58ee23288837de62ac9232a848de5f3bc747` |
| 0x028E | `daa45ecbc693f57c3e0d93ad664c34c0365f653d1cf619dcc0d0be2366681c2c` |
| 0x028F | `9fef74181a58438b46c07fe681ce242f4bb4a3b86aa1e2cd833c28777faaf003` |
| 0x0290 | `1916798066715877e314c146c3b491a7f3e4a9aea933ceeed3e065b8efa7b3ba` |
| 0x0291 | `fde8fce43090f284239bc131b07307ed175de4365d7ce1a6a9daef705c83e494` |
| 0x0292 | `f230fdc4cc6ce4667c57f37e30d950214e301cd22f426d9b80ae84b00771a54c` |
| 0x0293 | `f860a38a8aa6a375630561ade2650886604268c81cca908cfbd2b7c5e5966161` |
| 0x0294 | `0067eb52ec6ab81294dafa6355adf1ce2f209d152c7548a0ac446a950c73fb0b` |
| 0x0295 | `209a46241307919b46916404b530efd44345d4965413bc91b465d936f9fa42d8` |
| 0x0296 | `c851c609862e42b9c046b7201a546c24b77354ce35662be70bc56795d3cd7148` |
| 0x0297 | `c0258870902ffff0f4376ca5946fec1b06e4ff240e4f3ad93f6c54481096821b` |
| 0x0298 | `d6d8f8afe792a9ea559c13af5a921f1b930469955397a155eb12e0d7bdf05add` |
| 0x0299 | `3730bb49d270163a82731d812460eda3e6c3b4791eb6b713a0ed5a46cbd4bbe0` |
| 0x029A | `5f9cdc1b5733c5dfc40464cb5f84035431d51a9a314978db17ce4d60246e2397` |
| 0x029B | `4a30cbb28914b0256c808112290c00920c5a37b3b5c0507d68564248c885a4c0` |
| 0x029C | `ac03032c60d6eb9d0ca2d7e620f42c3369b88b182be7bb7fc08c17880610d34a` |
| 0x029D | `81d323deebf6c642f729b246f0facd539d82d09ee5bb43296b09e233e8994424` |
| 0x029E | `a8c4c5de20c15363cf44679d6218c3b31c3db7a0f4d95924ebcab326c7e007a9` |
| 0x029F | `a884ff880b51d403716faa39fbdf2342f9a6ef8f6ad3fea07fe9390ca5e3edf4` |
| 0x02A0 | `73bbe4a04425196cf7486dbaeac57cb2a32b055b8123fc32595c86e1803bdb4e` |
| 0x02A1 | `3c3bbcda8226af6c1943d76e6db205d69258f6f90c1d3c72c72740cca4ada5d3` |
| 0x02A2 | `e0cac5f5620684f671c05a4d47bd378c8a45269e878f6455da66baa6e61036e7` |
| 0x02A3 | `434360e9c2d829452833514ef906dde0760984f3a7f67ddcb3750eced4cada3f` |
| 0x02A4 | `2cce2c4e7327d53896e171e9289643e8121c4bf08c9a7f604172186edc0bbe66` |
| 0x02A5 | `a7a17920f53e656fec14caf2d8867c808514fba7442161145366e29fb7cd0063` |
| 0x02A6 | `2658cc39c35cb12fe97fa220836d510403688849f458cab16866648353b92041` |
| 0x02A7 | `ec28b81e1ca4e3338e95129bea9a4d5458fe3a23f482baea3a83144b06ca800d` |
| 0x02A8 | `9d37c132de6629e0574ccc60302c35f1465a929eecdcbe84b9f6829441f01fb7` |
| 0x02A9 | `eea85a5b3802677bcffc492236e804cc7c2f2c04df46d27a7f0d2add4972c463` |
| 0x02AA | `5a5d122410a1f0d7b17c51a59521b97103ca0851bebd9ebeeaac302852b653dd` |
| 0x02AB | `6c9aac71e4b1c6f089ba955af87b1fecf44464bc77ee2045b942babbfc53eb7e` |
| 0x02AC | `966bfd73b85250ae40dd5b8733ea876370aa297af376c5b96c9b131eb5fba22d` |
| 0x02AD | `63e11601a5c98956a9f9d5b1c5f572ba5c883b04dff5e43a06cd8e2cb8577ac7` |
| 0x02AE | `3475cf49ed7da8b021bdb38ebaa639e1e9c559678fae46c354074ceba1575d9d` |
| 0x02AF | `319682c432f286ed02c6de80d2c60a5e63e7a13f9160946c92acdc58112800c0` |
| 0x02B0 | `4b89a8b873a01b41de9000a3d2d5916ed4410754dc5dfe1b5970534354ad6353` |
| 0x02B1 | `b13a5a27cbec259214c08f7b5d01a3672aeb345e54cd86c3f46e57ba1e9def3f` |
| 0x02B2 | `88d7f600d4dd170893c463b81f51d31f7383918938a854a8fdb5e3821dc1633d` |
| 0x02B3 | `1a61ab6bd50853ef4c91dfc773d2178ae3694b11c9ecf8a92071fc60b7546941` |
| 0x02B4 | `f4ff2f096222a95cf793ad12c20b4f5d2a222f02363d860eeefff5fe53ebca12` |
| 0x02B5 | `cea8330cb01ac28be5dd01091c6fb6069f59a55a186ecc63e511a973f6d157bd` |
| 0x02B6 | `5ba3db66818f5cd6a7be2ab52104ac652cee49588acfdbe2b53ffcdd3079bac6` |
| 0x02B7 | `b09655522a574201e17a1fabeca953a73300a8fa5d7b0002faa28a33863dea0b` |
| 0x02B8 | `80583cf1c567a09fb07a3cdba0d162babf52b441ec6d0cc6dffa807552997936` |
| 0x02B9 | `43f75e3f60b504ba800313548eb5243319e21ca4584debb6c51a2855143cec37` |
| 0x02BA | `9dc9b6a4bc0258a9bdc5245c9f7ca2fb332cf7790d64b277b452e334dce5fef1` |
| 0x02BB | `be01d2a7a84b398fcefdd2fe1005598cac9cb89d7e66ac47127ced9e186ccc6f` |
| 0x02BC | `2fd012d781b116ae76dce0b2ce60a21afc7091d8e3e91dc98797fbfdcaec072b` |
| 0x02BD | `2a96d3ea959a4c01e6dea33ca99b9a5e16e4eff2862bd385a0b1ab437ad0616b` |
| 0x02BE | `e86535c249072262cede2b0a41c8d2a64288239a09aa43a898cf38e9e2a6d2a0` |
| 0x02BF | `f5c0d40ea4288b2bcc2fc4f26d97729aad5dd278352d11e704a475701038f99f` |
| 0x02C0 | `ee9872232f73bae09963dda39217024e758ed97cf803da07f40176039f30aad6` |
| 0x02C1 | `913bf18d432c17ca56394967b21d1c0ccbcf8237aa380aa6a663c16d38229854` |
| 0x02C2 | `7e8e8c1e38df4adf8a87329c5dd98626bd3c387e668af16e7b1fd12b129704cf` |
| 0x02C3 | `5077e309d45c9312431b45b9a0ed723dd3fce883f33989cebe4e20713a7bfe9f` |
| 0x02C4 | `3ea449e860a6dd93a834da1d6bf31c4c7a918db319a7f1c5a31a6a6ad69af2d8` |
| 0x02C5 | `0930928d1fff4d9c4b17f02445795ad2b164491da01e3772d9747b570e4a6215` |
| 0x02C6 | `b90e1ff7dc17104ba777457df158c4568579356febea9871c38d7f8bb260c43b` |
| 0x02C7 | `f41a2531840cdb6a38b6648f52775be1cf48c5fea8d40857b7ea5ad47aac8729` |
| 0x02C8 | `362c132db7ea911e93054345ae58d237f952075eb4a1b3c6c66d5072661df3a0` |
| 0x02C9 | `ccd8b441698c5342d6cd1fec2110eddea1fb8a88b0fb39f3a4379b2d8f6e2616` |
| 0x02CA | `9d52332aabbf8d7a7442c7817bebce75c27b3dfc6e452d78314b8b520b734e10` |
| 0x02CB | `10afd0aae0fa3668f2afda61cdfd514e867d850cb5999a5dc48c60e94535ffc7` |
| 0x02CC | `5d7f0e80b57bee03a558a0177facee7caea3349683828352b69378acd66982d5` |
| 0x02CD | `e3e63c50ff5926b4dc05512b8ffc9b77cd4acd452ba87b0114808fa5e6e30f9f` |
| 0x02CE | `e750cc34e0326433adcad8a36dd776c6f1292b2bb4fabbbef11c4e396782a001` |
| 0x02CF | `a5a0294c91980ab5fb6a5541589c5e838294d847f266851dbc9563c2c6ff8c53` |
| 0x02D0 | `ff8d4f0d9300b07b769b5a1495718c4cdf38111fda13794f6b00ee3b7f1eeeac` |
| 0x02D1 | `adb5d5affcb6acc4ccf0d6eb99ff16d4969d32079907966604347164746ee2ea` |
| 0x02D2 | `6a553245e71365de5dcbdfd011a95244cd02f1e65be6f58890febdbf882fbf44` |
| 0x02D3 | `1588febf3971059f2ea48128e0e4ec59b1f95996069949401749896d9a09e88a` |
| 0x02D4 | `8a0c6830b24f97366b30ab83d72ae4914d28bb85e8873ce708a7bb7c795e429e` |
| 0x02D5 | `e3d2e2b6e7a1e0722aa6afe9555cc7d10b464799c3a8656b99df00440d7fa662` |
| 0x02D6 | `683fb6c9a7211674aa7c606b85e7b49607bed80a2330140b912ef68170a70731` |
| 0x02D7 | `ff8d553c53fa8f22f969907239a884754d132d6154e3e7ad10f77aaee96a98c8` |
| 0x02D8 | `c01a16f3aea5afd9a267e7c558b46c7a51d1a0e78d9b08795ab1e1ecfa09a0fd` |
| 0x02D9 | `339253c612d8b76ac79846246003146443aeaf1650425c02eea7ec43c1cb2e31` |
| 0x02DA | `51c9a0bd7d025e9c3b2e7193c95dbb15d27a4c54b74b8aaf138b66d77c99d000` |
| 0x02DB | `7ee1aa88b9dba162ae8172cac638602d2d87e2acd993a80daaf4a7de9a4aa28f` |
| 0x02DC | `6d21b3b68a60baaa647f0c5913b4c1c61380c5d70e84d8f783ab22aa6cf9513d` |
| 0x02DD | `9212ac445c45012528c687b65b38701ad1fce96ff5aa0b53907284fcdfce4a90` |
| 0x02DE | `5b6c07d2f2a811de735f77dae0b9d1682b4963df2f13e22cbebb0647db71e196` |
| 0x02DF | `04eab25f3c839447e911c66df2053b55c1215447da75f971d3fb891ed354a131` |
| 0x02E0 | `dcf9d3e7e9b4b59977bd3eaa0e1f21815b5f94c2a0a8b68a8e3db075a16f781b` |
| 0x02E1 | `6ab3b54204c380fecde12d1a21f04ccbb3d7564b48f10fb3dff4954d72b358a6` |
| 0x02E2 | `f019f31b832bfccf21148450afae837433299020f7191f4e43c950a0b48fdb2e` |
| 0x02E3 | `ed0f0ce8d19c4fcde7508f2b0bd03f5e4a6cc567f3e305eb791d0cd48046a010` |
| 0x02E4 | `a563c587267a44b9fc4588790a9d96e87167fc8c5b0c5d7d8417592f5f7873f7` |
| 0x02E5 | `010a03d39a93afe706747f90973a7ca71e28fcb4b6e236df16529673b473aec2` |
| 0x02E6 | `add88e3f471986be89b4c48ed985b14babdc1f393eadb7c2583853bec9bef0a9` |
| 0x02E7 | `b0c3e68d583d719f46fd2dfc48bf9d60ba4a82a48b7d4477f8cda7ccd2ca9daf` |
| 0x02E8 | `99d56cd960b466f21eb8b657c3ec817ae76322836cb2eb0ae71df96329480213` |
| 0x02E9 | `e3c4b5538f5dbaee582180f1950d48d8137452856e6c7431bc26479e010eb233` |
| 0x02EA | `0381ef1c3c3d0222f0c6e2a8685e15a760dc6f8fe83057a5f5d9b5fb9c80bd8c` |
| 0x02EB | `9c99df749f9f93c2bcc4b72fb95bf1f613574aba2345d090b7132e77a6399840` |
| 0x02EC | `730b1f01cde7513243467be62c1cb444c327d0ea55ff3be3d348b5e190925d5e` |
| 0x02ED | `0324ecaf09668db31a7d77cc52fa1147c800597d8dc1fe1fe6804c13ea86d907` |
| 0x02EE | `88fa387b7525ea39c1080909e31e7bdab104cf74eed5925fa28ada7fd03437c5` |
| 0x02EF | `2d1aa6708ed6529087a4e0a7ae1992c4d60eab70d4cb6398fed67486f45aa3d2` |
| 0x02F0 | `975d921b3e35c1128957095b39571a15e684e7e25ffe71569c4cc67e37daedfc` |
| 0x02F1 | `57eba8ba0a99aa34ea21fd2d4e1c6803de6f8a7b7b8f1512de31d0c3cbba3a4b` |
| 0x02F2 | `07a34f1e7d289fae08b6b7efe47c9b0a1ef6d2256d6991e50f95a2118a4594d5` |
| 0x02F3 | `4b1b7bb9e830ea02c2aaf16788a90c33f2970b5ef3b17cf0864148fe57f90877` |
| 0x02F4 | `a2fc7da7077e527bf35999885f62d63fcf94c144af86ddbc3738c56b30430c80` |
| 0x02F5 | `06a4570eb307228ecdffc995969d8c9c8beeab304d90d6ccacfdd0013b04ea29` |
| 0x02F6 | `a3fb50ebe52203898da9ea5a114b1b9be4926ab899955a04e41d456fbce942e1` |
| 0x02F7 | `3d76e5e79a5ed3c7db98164d22413882dc2ba1669370f852a4c8b5ff93c9d453` |
| 0x02F8 | `f2a7709269996719091c6c348c92d19d27d9e605db9b3ce35dab6dec2e1125c1` |
| 0x02F9 | `52d2b82d0a15e8568d21d63b03d3010c88c46e0b5c2aa88ae8dc95c4c9ed559a` |
| 0x02FA | `16f562b892540e812406d971f4a79d260e29ccb941ad89f03287a38ad5d15d10` |
| 0x02FB | `d6ea93e864e98b6f237d514a1ea0fc622bcd6afee1568d8a4708eb862cc5e13d` |
| 0x02FC | `1edfcb9d774200a33c9ef749577621066d0b7a840790f6c5b7eea9429d2eb9a7` |
| 0x02FD | `e1ac52e6bd33226b6abe8bfcdcf3e2e8676f78033097f8ecaf5c7e5424404717` |
| 0x02FE | `fc52b3ee75392c33cac79ec08da7828c25caf20f2ede2d1c6e9696b35be22b9d` |
| 0x02FF | `86b94aea275a250e335246fc8b021bc6fecf8d77786372bd9121e6c2e975380b` |
| 0x0300 | `7dfe331864f486676d0d1fbee2fc60a85bde1a6a56360490116f997a4d1286db` |
| 0x0301 | `96c38dba3494022508b4df4516d49347dabfe2019599430548a5d634dde0cfd0` |
| 0x0302 | `07d8d40cc5fe82ec806d7eb2c7fe5591dc385cbffaafcaec79063aee0c63fc67` |
| 0x0303 | `b4a2d53d5d3fc0d300aa7d808961884a5e731b673285d065dac7888235c639ae` |
| 0x0304 | `883c0c3802c4431e8d2f03afa8f70181aca4c745443c1b9d91309e8a6a781ce0` |
| 0x0305 | `5aa2d84ec690d120b4da021b5d415f632698f3183d265f68516a153334ce3f7f` |
| 0x0306 | `775330800172099323c6baaa0eeefe941636dd9c2c1444a6c92e7a22aaf32cd2` |
| 0x0307 | `8d846dc0a24eb61c72328e41195a9f445fa68ad1f14e5348d5cf6fe7ecd4305e` |
| 0x0308 | `4755d6ec0564213d9ffe0b6f5dfe59d028ecac21ea8312ab48c512b9a44d6dc0` |
| 0x0309 | `63c94291622cb4556dc917763664261917ccf9523c193403988b1be3fee57303` |
| 0x030A | `6ca4ebb1d98fd74c9052006f2fc91524fcd68e52124d9d83882b5db1d460e595` |
| 0x030B | `a7317af9595d7b02338e761469aa9ed88ebbac2b83f40be2c5668c3fedde5f38` |
| 0x030C | `7b900920aa179b719a453d4b733a2b8a22b03f027df6419a7917300578cc650b` |
| 0x030D | `ecc9bb199b2d0159fa3cc8ce7d58bfac9e208d260dc6c461b815e035817fec89` |
| 0x030E | `74629be9a4c1122221ba89bb06d16c3f3e3a4d47239f793345fba6bde08a77d0` |
| 0x030F | `6930430f663bdc420e9b5e3991d71912e16f6a3b611c267ea2eb911b19274037` |
| 0x0310 | `7cebd55491efd42acf9bcd9d3791651ea8fa1b4543dc2cc1167a87dfc71a4af4` |
| 0x0311 | `aff5d01aecbfd66ff154350b024714c3be98f7bee095ec76f39c96fd5adf6bb8` |
| 0x0312 | `29da5ddd75cf12f4484a95e4be1babdf5177dd8b542adad5296b8faba6eab128` |
| 0x0313 | `80b1bc855de490608cc8b236641c62ecd6b2b1b02734ab1c02c3f1703cc86bdc` |
| 0x0314 | `381192fdae43005ffda6901f4faaa1b749616b0bc886f70b00d6929954ddfe86` |
| 0x0315 | `09732b40a422144466c8bad86fd4bf8d73edc918fc5731637485b78ee011f84f` |
| 0x0316 | `214a8669b07c9254ef5eaf1b6bb13c765b3a8a8f485e8500042daa4186a73d16` |
| 0x0317 | `5a33ecaee92e35b7f708cc5e18ba19e0a3d196a66640c890b4f2b52c7002c4da` |
| 0x0318 | `5ca08b108b1498a00a83ae41235216f3e3b9a78016566fa774155af57dc91dd4` |
| 0x0319 | `da908cb02da400fef71f22457fa3a509124c11722b035279abdb3c98eecc01fb` |
| 0x031A | `c3f1f3548cd785eeec8055f325be6ec7f9eebd42aa476b9edc0d09d78e061db3` |
| 0x031B | `1e6236817e77eb389a33d67c24331198de204f0a013d7c9899b352ae4f81f783` |
| 0x031C | `af190ba7ae9fe48a16a4f42eaa3858195894c0dd6852e82323d5213ec61a8d3b` |
| 0x031D | `1ce5e5a2335c65b28e432407e39aa5b5302eb1573beea48b06423e4a108e3e70` |
| 0x031E | `591cfe0692c077f9c9e4d0d38dad0892456d0940d35816ae6df79ed140983382` |
| 0x031F | `d472f48b2787a4dc6ef1b00e9b682e110d6911beba6896366cafd12a21fec985` |
| 0x0320 | `9e59c6cabade39d2b6b32e3ae66e51c03b6e54a58a308ab72dc634abc653bde8` |
| 0x0321 | `caad5b1173509f1e8c73fbc441055de0d107e59adfa62b0d75ebb2f82f94a55e` |
| 0x0322 | `96b7895065b91fc0f4d7b4a64ed1c7836bb6d0a280c51a5f119bc992b638f866` |
| 0x0323 | `ba0e050a83adb3ed466c98c6b2bca524a66529a670c101eae247e3b83f94a005` |
| 0x0324 | `295ae147183af571ff7a223183ba13f733214f8e41a823bd1ed6ed3af69ffcc7` |
| 0x0325 | `81aabf0bda2e38933656b6db35e59b2e024320d2b7613341bd222f4d799bdc92` |
| 0x0326 | `d0381c0ef082b07a5fb9b8c9ef297ccfe60db9944e44dae11947481c2383f276` |
| 0x0327 | `cda69864af526d160ec614c473c3331730c1a20622e2d41857e15b423b74001b` |
| 0x0328 | `c625195449cd4b513e446c979c6e228eb3d469948fc8d6251fab4cd6f19524d9` |
| 0x0329 | `8d8bc2060031aeff0e3bff18db0b2b45e0f738d377c9ea306c7d14760698e2bd` |
| 0x032A | `9550fdd8f7693ff17a85472f328509dce12222b13e8ee115179463dfa480977e` |
| 0x032B | `5cf9301349abdd7e19842b3c92d3f4b5e2376e2793e7067352e3a7b48207ae73` |
| 0x032C | `88ca5b6b6be14d8c4fdbfd484f618a278bd081b1cbe0c044ef596e7fb06dabf8` |
| 0x032D | `c5b2ca521c0faa7fd9887ee5e78615a17b5f08dc63becb423166423918a7693e` |
| 0x032E | `ba3f06017df1fb3ced84f5de914bfa4e8b69ad7d0aa990139b25a7cc672a6310` |
| 0x032F | `5ab5ed1dc35c3843340e2e635dcd55583a20ae66d0f2f4fcd6a74f3e2849edc3` |
| 0x0330 | `6336a973d8d3edb889fca61a2dab720ebf411fb40e0a30339bcd0a9ab0d7c5ad` |
| 0x0331 | `51fccc3faa350c61b813de9bca15cd6fc3b37d72f50154d6356b7b10ee9a263e` |
| 0x0332 | `34ebf527b926ebce8c83e4bc51776d92f06e40ad1220e09f5b5aae8cfa26a77c` |
| 0x0333 | `d25055401d938bd570ea2f05b6c2650f418857578d77dd8dd8f32c23ca239d55` |
| 0x0334 | `167fba1754bec6fc9f2e1d61618c76a284b4c32304387b215346862770e528e3` |
| 0x0335 | `d7defb1a85d9718a8f5b57ac876cd8c55c2e50e73cb6f37b3f604f2284def360` |
| 0x0336 | `9cb4ae678d9936acc3fe3ddb9ee5a519b840c03df2b952ef17b467098f61a284` |
| 0x0337 | `e0e0ac28f68f963fa19dedfdf8bcbb1cfaa66ba7f237bcb3cfdaf83fe8aaef7a` |
| 0x0338 | `0dd47721d8fde5e87ebb457e3091258c4b148ae3c90719994df137e29f7c2da8` |
| 0x0339 | `1fefad60b7ff429d687153403f36808ec157adecb368a1f60f77a6ce06216524` |
| 0x033A | `18cc136965867d420f8961f35454969e2a57799c99cb6d1546674ed3229cd234` |
| 0x033B | `aced5f7cae8759ffa94f9a9bb0623114a4bd6d4a49f69ba7894e909ed5c52c05` |
| 0x033C | `7f2a2caeeae8cc4444c1286eba200c576e203abbddd032c743295662e8113d81` |
| 0x033D | `a48aa7d82cddcf4cc17cab0c0eed7819930d155d5f16f32a23b2b8d473e61566` |
| 0x033E | `2bc17cb4a18dbc4eadda5d1351bedf5aa289812b6796536b2fd04f89e0a2cdc5` |
| 0x033F | `e893428b59a799b042b96bc8a065554e59aea07967556959a51d5dab21ba5af8` |
| 0x0340 | `9bb3247a2a5b671d286a9ff8faef1325c4cd4d11a0cfb8cff7bff8b39ac12a59` |
| 0x0341 | `cf98928a9865a600070dfeff2d23b2e0cf1d2b9384631fa5682c7015887671ed` |
| 0x0342 | `d0ccf11c7be4a7731e70ee87e951fe34e6ccb34dfdfb49507a65e137023580a7` |
| 0x0343 | `c201c8146b4f3e7fd90046e575b78f8f8f45ded11de5d156aadb4b38dfc7f538` |
| 0x0344 | `c8af1a5d9474999f70c4d6821615ebc7b9edb06b1da3a597eb2a009b5a240844` |
| 0x0345 | `7e55bbb4b6e8d6634997b7653bead6c486742c472d0f06475c68543bed696ff5` |
| 0x0346 | `38ab0d375a0003a61f67f1a851edb01b3751b4c39facec07a033116ff23385f9` |
| 0x0347 | `d59810628b8cc79317274d37791144cc92779205ce096144ee1b246175558b7f` |
| 0x0348 | `1cc084a7f3263478972924f4264e45b6985d170340c3ee4daac5e00033ef233a` |

## Bounded LUT alias correction

The first runtime seven-epoch gate found a mechanical WRAM ownership collision unrelated to transition capacity: dense LUT entries for arcade codes `0x031A..0x034B` at Genesis-WRAM `0xFF6800..0xFF6862` overlap the established crash-record area. For example, waterfall code `0x031B` should resolve to slot `0x04BC`, but the dense address held crash-record word `0x0004`.

The correction is strictly bounded:

- `fg_boundary_active_lut` remains at Genesis-WRAM `0xFF61CC`.
- Only codes `0x031A..0x034B` route through `fg_boundary_conflict_lut` at Genesis-WRAM `0xFFB1CC`.
- Count is `0x0032` words.
- All fixed-B, clear, package-install, and resolver accesses use the same bounded address helper.

This is a 50-word deterministic LUT ownership correction, not a cache, search path, fallback, or visibility solver.

## Regression gates

### Static transition contract

`tools/translation/verify_build0311_transition_retention.py` independently reads the generated package binary, constants, PC080SN pattern ROM, and boundary report. It asserts:

- all 12 rope identities/hashes and exact slots survive package 7;
- all 224 waterfall identities/hashes and exact slots survive package 8;
- transition peaks are 394 and 479, both <= 484;
- visible missing identities = 0;
- slot collisions = 0;
- retained movement = 0;
- handoff missing identities = 0.

Result:

```text
BUILD0311_TRANSITION_GATE PASS: rope 12 retained; waterfall 224 retained; peaks 394/479 <= 484; missing=0; collisions=0
```

### Gameplay entry

`states/traces/build0311_gameplay_entry_gate_20260823_172734/gameplay_entry_gate_summary.txt`:

- PASS over 564 frames.
- Credit, Start, READY, fixed Plane B, record 0, gameplay, and player control all observed.
- Address Error 0, Bus Error 0, Illegal Instruction 0, crash handler 0.
- Package binary contract: 49,852 bytes.

### Seven stable epochs plus transition packages

`states/traces/build0311_phase1_epoch_gate_20260823_172736/phase1_epoch_gate_summary.txt`:

- PASS for semantic records 0, 3, 4, 10, 11, 12, and 15.
- Runtime packages 0, 7, 8, 3, 4, 5, and 6 selected as designed.
- Plane-A complete LUT gate PASS.
- Fixed Plane-B LUT gate PASS.
- Seven semantic epochs retained.
- Same-epoch ordinary pattern DMA = 0 and slot churn = 0.

### Canonical and MAME smoke

- Canonical gate: PASS (`opcode_replace` remains 227; complete coverage changes only by the generated package growth from `0x194EB8` to `0x197EB8`).
- Standard MAME Genesis smoke: `states/traces/rastan_direct_video_test_build_0311_mame_30s_20260823_172746/genesis_exec_summary.txt`.
- 1,798 frames, final runtime Genesis PC `0x00073AA0`, SP `0x00FEFF6A`, unique unmapped memory addresses: none.
- Address Error 0, Bus Error 0, Illegal Instruction 0.

## Files changed for Build 0311

- `tools/translation/compile_pc080sn_genesis.py`
- `tools/translation/verify_build0311_transition_retention.py`
- `apps/rastan-direct/src/fg_tile_cache.s`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/Makefile`
- `tools/mame/run_build0310_epoch_gate.sh`
- `tools/mame/scripts/build0310_epoch_gate.lua`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`
- `docs/design/Cody_build0311_rope_waterfall_transition_retention_fix.md`
- `AGENTS_LOG.md`

Generated build/manifests and trace artifacts were regenerated by the Makefile. No numbered ROM was deleted or overwritten.

## Acceptance status

The ownership/lifetime root cause is closed and both machine-checkable transition contracts pass. Build 0311 is runnable and preserves Build 0310's stable epoch behavior. Actual screen visibility at the rope and waterfall boundaries is **USER MUST VERIFY**, because the automated gates prove code -> slot -> physical-pattern validity rather than visual composition in Tighe's photographed play path.

Focused user test:

1. Load Build 0311.
2. Reach the first waterfall transition.
3. Confirm the rope remains visible/intact while waterfall graphics enter.
4. Continue through the waterfall.
5. Confirm waterfall graphics remain visible/intact while next rope/exterior graphics enter.
6. Note whether either transition still flashes black.
7. Report other disappearing graphics separately.
8. Keep unrelated map/scroll-position observations separate unless clearly residency-caused.

Next build after this visual checkpoint: Build 0312 only after Tighe reports Build 0311 results.
