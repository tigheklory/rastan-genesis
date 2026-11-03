# [Cody — Exodus Debugger Frame Extraction]
Build produced: NO  
ROM path: N/A  
Root cause confirmed: N/A (extraction only)  
Fix implemented: NO (out of scope)  
No unrelated changes: YES  
Architecture compliance: CONFIRMED
## Video
- Path: `states/screenshots/Build_53.mp4`
- Metadata: 5120x1394, 30fps, duration 43.072s
- Frame window extracted: source frames 240..390 => local `frame_001..frame_151`
## Bounding Boxes (source-frame coords)
- Main M68K - Registers: x=4580, y=0, w=540, h=1120
- VDP - Port Monitor: x=2500, y=40, w=1400, h=1320
- VDP - VRAM Memory Editor: x=1700, y=0, w=1200, h=1394
- VDP - CRAM Memory Editor: x=1450, y=0, w=350, h=1394
- VDP - VRAM Pattern Viewer: x=0, y=0, w=720, h=780
- VDP - Image Window: x=700, y=0, w=800, h=1180
- VDP - Palette: x=0, y=780, w=720, h=614
- VDP - Plane Viewer: x=3900, y=0, w=780, h=1394
## Key Literal Register Snapshots (manual full-res read)
### Frame 001 (source 240; t=8.000s)
- A0 0xFFFFFFFF A1 0xFFFFFFFF A2 0xFFFFFFFF A3 0xFFFFFFFF A4 0xFFFFFFFF A5 0xFFFFFFFF A6 0xFFFFFFFF A7 0xFFFFFFFF
- D0 0xFFFFFFFF D1 0xFFFFFFFF D2 0xFFFFFFFF D3 0xFFFFFFFF D4 0xFFFFFFFF D5 0xFFFFFFFF D6 0xFFFFFFFF D7 0xFFFFFFFF
- CCR X=1 N=1 Z=1 V=1 C=1
- PC 0xFFFFFFFF USP 0xFFFFFFFF SSP 0xFFFFFFFF S=1 T=1 IPM=7 SR 0xFFFF
### Frame 060 (source 299; t=9.967s)
- A0 0x0017A240 A1 0xFFFFFFFC A2 0x0013F36C A3 0xFFFFFFFF A4 0xFFFFFFFF A5 0xFFFFFFFF A6 0xFFFFFFFF A7 0x00FEFFC6
- D0 0x00002B40 D1 0x6CA00000 D2 0x00000000 D3 0xFFFF0171 D4 0x00046E00 D5 0xFFFFFFFF D6 0x00000000 D7 0x00000001
- CCR X=1 N=0 Z=0 V=0 C=0
- PC 0x00071B5C USP 0xFFFFFFFF SSP 0x00FEFFC6 S=1 T=1 IPM=7 SR 0x2710
### Frame 090 (source 329; t=10.967s)
- A0 0x00FFFFA8 A1 0x00FFC91C A2 0xFFFFFFFF A3 0x00050082 A4 0xFFFFFFFF A5 0x00FF0000 A6 0xFFFFFFFF A7 0x00FEFFB4
- D0 0x00000003 D1 0x00000340 D2 0x00000001 D3 0xFFFFFFFF D4 0x00000005 D5 0x00000085 D6 0x0000000C D7 0xFFFF0030
- CCR X=1 N=0 Z=0 V=0 C=0
- PC 0x0087B304 USP 0xFFFFFFFF SSP 0x00FEFFB4 S=1 T=1 IPM=7 SR 0x2710
### Frame 120 (source 359; t=11.967s)
- A0 0x00FFFFAE A1 0x00FFC91C A2 0xFFFFFFFF A3 0x00050082 A4 0xFFFFFFFF A5 0x00FF0000 A6 0xFFFFFFFF A7 0x00FEFFAE
- D0 0x0000000A D1 0x00000340 D2 0x00000001 D3 0xFFFFFFFF D4 0x00000005 D5 0x00000085 D6 0x0000000C D7 0xFFFF0030
- CCR X=0 N=0 Z=0 V=0 C=0
- PC 0x0000051E USP 0xFFFFFFFF SSP 0x00FEFFAE S=1 T=0 IPM=7 SR 0x2700
### Frame 151 (source 390; t=13.000s)
- A0 0x00FFFFAE A1 0x00FFC91C A2 0xFFFFFFFF A3 0x00050082 A4 0xFFFFFFFF A5 0x00FF0000 A6 0xFFFFFFFF A7 0x00FEFFAE
- D0 0x0000000A D1 0x00000340 D2 0x00000001 D3 0xFFFFFFFF D4 0x00000005 D5 0x00000085 D6 0x0000000C D7 0xFFFF0030
- CCR X=0 N=0 Z=0 V=0 C=0
- PC 0x0000051E USP 0xFFFFFFFF SSP 0x00FEFFAE S=1 T=0 IPM=7 SR 0x2700
## Frame-by-Frame Extraction Index (all 151 frames)
Legend: panel state IDs are per-panel visual states derived from full-resolution crops.
Port Monitor rows visible: **none** in this 8s-13s window; list-size observed `2000`; all five logging checkboxes unchecked in observed states.
| Local Frame | Source Frame | Time(s) | REG | PORT | VRAM | CRAM | PATT | IMG | PAL | PLANE |
|---:|---:|---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 001 | 240 | 8.000 | REG01 | POR01 | VRA01 | CRA01 | PAT01 | IMA01 | PAL01 | PLA01 |
| 002 | 241 | 8.033 | REG02 | POR02 | VRA02 | CRA02 | PAT02 | IMA01 | PAL01 | PLA02 |
| 003 | 242 | 8.067 | REG02 | POR03 | VRA03 | CRA03 | PAT03 | IMA01 | PAL02 | PLA03 |
| 004 | 243 | 8.100 | REG02 | POR03 | VRA03 | CRA03 | PAT04 | IMA01 | PAL02 | PLA04 |
| 005 | 244 | 8.133 | REG02 | POR03 | VRA03 | CRA03 | PAT05 | IMA01 | PAL02 | PLA04 |
| 006 | 245 | 8.167 | REG02 | POR03 | VRA03 | CRA03 | PAT04 | IMA01 | PAL02 | PLA04 |
| 007 | 246 | 8.200 | REG02 | POR03 | VRA03 | CRA03 | PAT06 | IMA01 | PAL02 | PLA04 |
| 008 | 247 | 8.233 | REG02 | POR03 | VRA03 | CRA03 | PAT07 | IMA01 | PAL02 | PLA04 |
| 009 | 248 | 8.267 | REG02 | POR03 | VRA04 | CRA04 | PAT08 | IMA01 | PAL02 | PLA04 |
| 010 | 249 | 8.300 | REG02 | POR03 | VRA04 | CRA04 | PAT07 | IMA01 | PAL02 | PLA04 |
| 011 | 250 | 8.333 | REG02 | POR03 | VRA04 | CRA04 | PAT08 | IMA01 | PAL02 | PLA04 |
| 012 | 251 | 8.367 | REG02 | POR03 | VRA05 | CRA05 | PAT07 | IMA01 | PAL02 | PLA04 |
| 013 | 252 | 8.400 | REG02 | POR03 | VRA06 | CRA06 | PAT08 | IMA01 | PAL02 | PLA04 |
| 014 | 253 | 8.433 | REG02 | POR03 | VRA06 | CRA06 | PAT07 | IMA01 | PAL02 | PLA04 |
| 015 | 254 | 8.467 | REG02 | POR03 | VRA06 | CRA06 | PAT08 | IMA01 | PAL02 | PLA04 |
| 016 | 255 | 8.500 | REG02 | POR03 | VRA06 | CRA06 | PAT07 | IMA01 | PAL02 | PLA04 |
| 017 | 256 | 8.533 | REG02 | POR03 | VRA06 | CRA06 | PAT08 | IMA01 | PAL02 | PLA04 |
| 018 | 257 | 8.567 | REG02 | POR03 | VRA06 | CRA06 | PAT07 | IMA01 | PAL02 | PLA04 |
| 019 | 258 | 8.600 | REG02 | POR03 | VRA06 | CRA06 | PAT08 | IMA01 | PAL02 | PLA04 |
| 020 | 259 | 8.633 | REG02 | POR03 | VRA06 | CRA06 | PAT07 | IMA01 | PAL02 | PLA04 |
| 021 | 260 | 8.667 | REG02 | POR03 | VRA06 | CRA06 | PAT08 | IMA01 | PAL02 | PLA04 |
| 022 | 261 | 8.700 | REG02 | POR03 | VRA06 | CRA06 | PAT07 | IMA01 | PAL02 | PLA04 |
| 023 | 262 | 8.733 | REG02 | POR03 | VRA06 | CRA06 | PAT08 | IMA01 | PAL02 | PLA04 |
| 024 | 263 | 8.767 | REG02 | POR03 | VRA06 | CRA06 | PAT07 | IMA01 | PAL02 | PLA04 |
| 025 | 264 | 8.800 | REG02 | POR03 | VRA06 | CRA06 | PAT08 | IMA01 | PAL02 | PLA04 |
| 026 | 265 | 8.833 | REG02 | POR03 | VRA06 | CRA06 | PAT07 | IMA01 | PAL02 | PLA04 |
| 027 | 266 | 8.867 | REG02 | POR03 | VRA06 | CRA06 | PAT08 | IMA01 | PAL02 | PLA04 |
| 028 | 267 | 8.900 | REG02 | POR03 | VRA06 | CRA06 | PAT07 | IMA01 | PAL02 | PLA04 |
| 029 | 268 | 8.933 | REG02 | POR03 | VRA06 | CRA06 | PAT08 | IMA01 | PAL02 | PLA04 |
| 030 | 269 | 8.967 | REG02 | POR03 | VRA06 | CRA06 | PAT08 | IMA01 | PAL02 | PLA04 |
| 031 | 270 | 9.000 | REG01 | POR01 | VRA07 | CRA07 | PAT09 | IMA01 | PAL01 | PLA01 |
| 032 | 271 | 9.033 | REG02 | POR02 | VRA08 | CRA08 | PAT10 | IMA01 | PAL01 | PLA02 |
| 033 | 272 | 9.067 | REG02 | POR03 | VRA06 | CRA06 | PAT11 | IMA01 | PAL02 | PLA03 |
| 034 | 273 | 9.100 | REG02 | POR03 | VRA06 | CRA06 | PAT12 | IMA01 | PAL02 | PLA04 |
| 035 | 274 | 9.133 | REG02 | POR03 | VRA06 | CRA06 | PAT11 | IMA01 | PAL02 | PLA04 |
| 036 | 275 | 9.167 | REG02 | POR03 | VRA06 | CRA06 | PAT12 | IMA01 | PAL02 | PLA04 |
| 037 | 276 | 9.200 | REG02 | POR03 | VRA06 | CRA06 | PAT11 | IMA01 | PAL02 | PLA04 |
| 038 | 277 | 9.233 | REG02 | POR03 | VRA06 | CRA06 | PAT12 | IMA01 | PAL02 | PLA04 |
| 039 | 278 | 9.267 | REG02 | POR03 | VRA06 | CRA06 | PAT11 | IMA01 | PAL02 | PLA04 |
| 040 | 279 | 9.300 | REG02 | POR03 | VRA06 | CRA06 | PAT12 | IMA01 | PAL02 | PLA04 |
| 041 | 280 | 9.333 | REG02 | POR03 | VRA06 | CRA06 | PAT11 | IMA01 | PAL02 | PLA04 |
| 042 | 281 | 9.367 | REG02 | POR03 | VRA06 | CRA06 | PAT12 | IMA01 | PAL02 | PLA04 |
| 043 | 282 | 9.400 | REG02 | POR03 | VRA06 | CRA06 | PAT11 | IMA01 | PAL02 | PLA04 |
| 044 | 283 | 9.433 | REG02 | POR03 | VRA06 | CRA06 | PAT12 | IMA01 | PAL02 | PLA04 |
| 045 | 284 | 9.467 | REG02 | POR03 | VRA06 | CRA06 | PAT11 | IMA01 | PAL02 | PLA04 |
| 046 | 285 | 9.500 | REG02 | POR03 | VRA06 | CRA06 | PAT12 | IMA01 | PAL02 | PLA04 |
| 047 | 286 | 9.533 | REG02 | POR03 | VRA06 | CRA06 | PAT11 | IMA01 | PAL02 | PLA04 |
| 048 | 287 | 9.567 | REG02 | POR03 | VRA06 | CRA06 | PAT12 | IMA01 | PAL02 | PLA04 |
| 049 | 288 | 9.600 | REG02 | POR03 | VRA06 | CRA06 | PAT11 | IMA01 | PAL02 | PLA04 |
| 050 | 289 | 9.633 | REG02 | POR03 | VRA06 | CRA06 | PAT12 | IMA01 | PAL02 | PLA04 |
| 051 | 290 | 9.667 | REG02 | POR03 | VRA06 | CRA06 | PAT11 | IMA01 | PAL02 | PLA04 |
| 052 | 291 | 9.700 | REG02 | POR03 | VRA06 | CRA06 | PAT12 | IMA01 | PAL02 | PLA04 |
| 053 | 292 | 9.733 | REG02 | POR03 | VRA06 | CRA06 | PAT11 | IMA01 | PAL02 | PLA04 |
| 054 | 293 | 9.767 | REG03 | POR03 | VRA06 | CRA06 | PAT12 | IMA01 | PAL02 | PLA04 |
| 055 | 294 | 9.800 | REG04 | POR03 | VRA06 | CRA06 | PAT13 | IMA01 | PAL02 | PLA04 |
| 056 | 295 | 9.833 | REG05 | POR04 | VRA09 | CRA06 | PAT14 | IMA01 | PAL02 | PLA05 |
| 057 | 296 | 9.867 | REG06 | POR04 | VRA10 | CRA06 | PAT13 | IMA01 | PAL02 | PLA05 |
| 058 | 297 | 9.900 | REG07 | POR04 | VRA11 | CRA06 | PAT14 | IMA01 | PAL02 | PLA05 |
| 059 | 298 | 9.933 | REG06 | POR04 | VRA12 | CRA09 | PAT15 | IMA02 | PAL03 | PLA05 |
| 060 | 299 | 9.967 | REG06 | POR05 | VRA12 | CRA10 | PAT15 | IMA02 | PAL03 | PLA06 |
| 061 | 300 | 10.000 | REG08 | POR06 | VRA13 | CRA11 | PAT16 | IMA02 | PAL04 | PLA07 |
| 062 | 301 | 10.033 | REG09 | POR07 | VRA14 | CRA12 | PAT17 | IMA02 | PAL04 | PLA08 |
| 063 | 302 | 10.067 | REG10 | POR08 | VRA15 | CRA10 | PAT15 | IMA02 | PAL03 | PLA08 |
| 064 | 303 | 10.100 | REG10 | POR08 | VRA16 | CRA10 | PAT18 | IMA02 | PAL03 | PLA09 |
| 065 | 304 | 10.133 | REG10 | POR08 | VRA15 | CRA10 | PAT15 | IMA02 | PAL03 | PLA09 |
| 066 | 305 | 10.167 | REG10 | POR08 | VRA16 | CRA10 | PAT18 | IMA02 | PAL03 | PLA09 |
| 067 | 306 | 10.200 | REG10 | POR08 | VRA17 | CRA13 | PAT15 | IMA02 | PAL03 | PLA09 |
| 068 | 307 | 10.233 | REG10 | POR08 | VRA18 | CRA13 | PAT19 | IMA02 | PAL03 | PLA10 |
| 069 | 308 | 10.267 | REG10 | POR09 | VRA17 | CRA13 | PAT19 | IMA02 | PAL03 | PLA11 |
| 070 | 309 | 10.300 | REG10 | POR09 | VRA18 | CRA13 | PAT20 | IMA02 | PAL03 | PLA12 |
| 071 | 310 | 10.333 | REG10 | POR09 | VRA17 | CRA13 | PAT21 | IMA02 | PAL03 | PLA12 |
| 072 | 311 | 10.367 | REG10 | POR09 | VRA18 | CRA13 | PAT21 | IMA02 | PAL03 | PLA12 |
| 073 | 312 | 10.400 | REG10 | POR09 | VRA17 | CRA13 | PAT21 | IMA02 | PAL03 | PLA12 |
| 074 | 313 | 10.433 | REG11 | POR09 | VRA18 | CRA13 | PAT21 | IMA02 | PAL03 | PLA12 |
| 075 | 314 | 10.467 | REG12 | POR09 | VRA17 | CRA13 | PAT22 | IMA02 | PAL03 | PLA12 |
| 076 | 315 | 10.500 | REG13 | POR09 | VRA18 | CRA13 | PAT23 | IMA02 | PAL03 | PLA12 |
| 077 | 316 | 10.533 | REG14 | POR09 | VRA17 | CRA13 | PAT24 | IMA02 | PAL03 | PLA12 |
| 078 | 317 | 10.567 | REG15 | POR09 | VRA18 | CRA13 | PAT25 | IMA02 | PAL03 | PLA12 |
| 079 | 318 | 10.600 | REG14 | POR09 | VRA17 | CRA13 | PAT26 | IMA02 | PAL03 | PLA12 |
| 080 | 319 | 10.633 | REG15 | POR09 | VRA18 | CRA13 | PAT27 | IMA02 | PAL03 | PLA12 |
| 081 | 320 | 10.667 | REG14 | POR09 | VRA17 | CRA13 | PAT26 | IMA02 | PAL03 | PLA12 |
| 082 | 321 | 10.700 | REG15 | POR09 | VRA18 | CRA13 | PAT27 | IMA02 | PAL03 | PLA12 |
| 083 | 322 | 10.733 | REG14 | POR09 | VRA17 | CRA13 | PAT26 | IMA02 | PAL03 | PLA12 |
| 084 | 323 | 10.767 | REG15 | POR09 | VRA18 | CRA13 | PAT27 | IMA02 | PAL03 | PLA12 |
| 085 | 324 | 10.800 | REG14 | POR09 | VRA17 | CRA13 | PAT26 | IMA02 | PAL03 | PLA12 |
| 086 | 325 | 10.833 | REG16 | POR09 | VRA18 | CRA13 | PAT27 | IMA02 | PAL03 | PLA12 |
| 087 | 326 | 10.867 | REG17 | POR09 | VRA17 | CRA13 | PAT26 | IMA02 | PAL03 | PLA12 |
| 088 | 327 | 10.900 | REG16 | POR09 | VRA18 | CRA13 | PAT27 | IMA02 | PAL03 | PLA12 |
| 089 | 328 | 10.933 | REG18 | POR09 | VRA17 | CRA13 | PAT26 | IMA02 | PAL03 | PLA12 |
| 090 | 329 | 10.967 | REG18 | POR09 | VRA17 | CRA13 | PAT26 | IMA02 | PAL03 | PLA12 |
| 091 | 330 | 11.000 | REG19 | POR10 | VRA19 | CRA14 | PAT28 | IMA02 | PAL04 | PLA13 |
| 092 | 331 | 11.033 | REG20 | POR11 | VRA20 | CRA15 | PAT29 | IMA02 | PAL04 | PLA14 |
| 093 | 332 | 11.067 | REG21 | POR12 | VRA17 | CRA16 | PAT30 | IMA02 | PAL03 | PLA14 |
| 094 | 333 | 11.100 | REG21 | POR12 | VRA18 | CRA16 | PAT31 | IMA02 | PAL03 | PLA14 |
| 095 | 334 | 11.133 | REG21 | POR12 | VRA17 | CRA16 | PAT30 | IMA02 | PAL03 | PLA14 |
| 096 | 335 | 11.167 | REG21 | POR12 | VRA18 | CRA16 | PAT31 | IMA02 | PAL03 | PLA14 |
| 097 | 336 | 11.200 | REG21 | POR12 | VRA17 | CRA16 | PAT30 | IMA02 | PAL03 | PLA14 |
| 098 | 337 | 11.233 | REG22 | POR12 | VRA18 | CRA16 | PAT31 | IMA02 | PAL03 | PLA14 |
| 099 | 338 | 11.267 | REG22 | POR12 | VRA17 | CRA16 | PAT30 | IMA02 | PAL03 | PLA14 |
| 100 | 339 | 11.300 | REG22 | POR12 | VRA18 | CRA16 | PAT31 | IMA02 | PAL03 | PLA14 |
| 101 | 340 | 11.333 | REG23 | POR12 | VRA17 | CRA16 | PAT30 | IMA02 | PAL03 | PLA14 |
| 102 | 341 | 11.367 | REG22 | POR12 | VRA18 | CRA16 | PAT31 | IMA02 | PAL03 | PLA14 |
| 103 | 342 | 11.400 | REG23 | POR12 | VRA17 | CRA16 | PAT30 | IMA02 | PAL03 | PLA14 |
| 104 | 343 | 11.433 | REG22 | POR12 | VRA18 | CRA16 | PAT31 | IMA02 | PAL03 | PLA14 |
| 105 | 344 | 11.467 | REG23 | POR12 | VRA17 | CRA16 | PAT30 | IMA02 | PAL03 | PLA14 |
| 106 | 345 | 11.500 | REG22 | POR12 | VRA18 | CRA16 | PAT31 | IMA02 | PAL03 | PLA14 |
| 107 | 346 | 11.533 | REG23 | POR12 | VRA17 | CRA16 | PAT30 | IMA02 | PAL03 | PLA14 |
| 108 | 347 | 11.567 | REG22 | POR12 | VRA18 | CRA16 | PAT31 | IMA02 | PAL03 | PLA14 |
| 109 | 348 | 11.600 | REG24 | POR12 | VRA17 | CRA16 | PAT30 | IMA02 | PAL03 | PLA14 |
| 110 | 349 | 11.633 | REG25 | POR12 | VRA18 | CRA16 | PAT31 | IMA02 | PAL03 | PLA14 |
| 111 | 350 | 11.667 | REG26 | POR12 | VRA17 | CRA16 | PAT30 | IMA02 | PAL03 | PLA14 |
| 112 | 351 | 11.700 | REG24 | POR12 | VRA18 | CRA16 | PAT31 | IMA02 | PAL03 | PLA14 |
| 113 | 352 | 11.733 | REG26 | POR12 | VRA17 | CRA16 | PAT30 | IMA02 | PAL03 | PLA14 |
| 114 | 353 | 11.767 | REG24 | POR12 | VRA18 | CRA16 | PAT31 | IMA02 | PAL03 | PLA14 |
| 115 | 354 | 11.800 | REG26 | POR12 | VRA17 | CRA16 | PAT30 | IMA02 | PAL03 | PLA14 |
| 116 | 355 | 11.833 | REG24 | POR12 | VRA18 | CRA16 | PAT31 | IMA02 | PAL03 | PLA14 |
| 117 | 356 | 11.867 | REG26 | POR12 | VRA17 | CRA16 | PAT30 | IMA02 | PAL03 | PLA14 |
| 118 | 357 | 11.900 | REG24 | POR12 | VRA18 | CRA16 | PAT31 | IMA02 | PAL03 | PLA14 |
| 119 | 358 | 11.933 | REG26 | POR12 | VRA17 | CRA16 | PAT30 | IMA02 | PAL03 | PLA14 |
| 120 | 359 | 11.967 | REG26 | POR12 | VRA17 | CRA16 | PAT30 | IMA02 | PAL03 | PLA14 |
| 121 | 360 | 12.000 | REG27 | POR10 | VRA19 | CRA17 | PAT28 | IMA02 | PAL04 | PLA13 |
| 122 | 361 | 12.033 | REG28 | POR11 | VRA20 | CRA15 | PAT29 | IMA02 | PAL04 | PLA14 |
| 123 | 362 | 12.067 | REG29 | POR12 | VRA17 | CRA16 | PAT30 | IMA02 | PAL03 | PLA14 |
| 124 | 363 | 12.100 | REG30 | POR12 | VRA18 | CRA16 | PAT31 | IMA02 | PAL03 | PLA14 |
| 125 | 364 | 12.133 | REG29 | POR12 | VRA17 | CRA16 | PAT30 | IMA02 | PAL03 | PLA14 |
| 126 | 365 | 12.167 | REG30 | POR12 | VRA18 | CRA18 | PAT31 | IMA02 | PAL03 | PLA14 |
| 127 | 366 | 12.200 | REG29 | POR12 | VRA17 | CRA18 | PAT30 | IMA02 | PAL03 | PLA14 |
| 128 | 367 | 12.233 | REG30 | POR12 | VRA18 | CRA18 | PAT31 | IMA02 | PAL03 | PLA14 |
| 129 | 368 | 12.267 | REG29 | POR12 | VRA17 | CRA18 | PAT30 | IMA02 | PAL03 | PLA14 |
| 130 | 369 | 12.300 | REG30 | POR12 | VRA18 | CRA18 | PAT31 | IMA02 | PAL03 | PLA14 |
| 131 | 370 | 12.333 | REG29 | POR12 | VRA17 | CRA18 | PAT30 | IMA02 | PAL03 | PLA14 |
| 132 | 371 | 12.367 | REG30 | POR12 | VRA18 | CRA18 | PAT31 | IMA02 | PAL03 | PLA14 |
| 133 | 372 | 12.400 | REG29 | POR12 | VRA17 | CRA18 | PAT30 | IMA02 | PAL03 | PLA14 |
| 134 | 373 | 12.433 | REG30 | POR12 | VRA18 | CRA18 | PAT31 | IMA02 | PAL03 | PLA14 |
| 135 | 374 | 12.467 | REG29 | POR12 | VRA17 | CRA18 | PAT30 | IMA02 | PAL03 | PLA14 |
| 136 | 375 | 12.500 | REG30 | POR12 | VRA18 | CRA18 | PAT31 | IMA02 | PAL03 | PLA14 |
| 137 | 376 | 12.533 | REG29 | POR12 | VRA17 | CRA18 | PAT30 | IMA02 | PAL03 | PLA14 |
| 138 | 377 | 12.567 | REG30 | POR12 | VRA18 | CRA18 | PAT31 | IMA02 | PAL03 | PLA14 |
| 139 | 378 | 12.600 | REG29 | POR12 | VRA17 | CRA18 | PAT30 | IMA02 | PAL03 | PLA14 |
| 140 | 379 | 12.633 | REG30 | POR12 | VRA18 | CRA18 | PAT31 | IMA02 | PAL03 | PLA14 |
| 141 | 380 | 12.667 | REG29 | POR12 | VRA17 | CRA18 | PAT30 | IMA02 | PAL03 | PLA14 |
| 142 | 381 | 12.700 | REG30 | POR12 | VRA18 | CRA18 | PAT31 | IMA02 | PAL03 | PLA14 |
| 143 | 382 | 12.733 | REG29 | POR12 | VRA17 | CRA18 | PAT30 | IMA02 | PAL03 | PLA14 |
| 144 | 383 | 12.767 | REG30 | POR12 | VRA18 | CRA18 | PAT31 | IMA02 | PAL03 | PLA14 |
| 145 | 384 | 12.800 | REG29 | POR12 | VRA17 | CRA18 | PAT30 | IMA02 | PAL03 | PLA14 |
| 146 | 385 | 12.833 | REG30 | POR12 | VRA18 | CRA18 | PAT31 | IMA02 | PAL03 | PLA14 |
| 147 | 386 | 12.867 | REG29 | POR12 | VRA17 | CRA18 | PAT30 | IMA02 | PAL03 | PLA14 |
| 148 | 387 | 12.900 | REG30 | POR12 | VRA18 | CRA18 | PAT31 | IMA02 | PAL03 | PLA14 |
| 149 | 388 | 12.933 | REG29 | POR12 | VRA17 | CRA18 | PAT30 | IMA02 | PAL03 | PLA14 |
| 150 | 389 | 12.967 | REG29 | POR12 | VRA17 | CRA18 | PAT30 | IMA02 | PAL03 | PLA14 |
| 151 | 390 | 13.000 | REG27 | POR10 | VRA19 | CRA19 | PAT28 | IMA02 | PAL04 | PLA13 |

## Panel State Representatives
### registers
- REG01: representative local frame 001 (`/tmp/exodus_manual2/crops/registers_f001.png`)
- REG02: representative local frame 002 (`/tmp/exodus_manual2/crops/registers_f002.png`)
- REG03: representative local frame 054 (`/tmp/exodus_manual2/crops/registers_f054.png`)
- REG04: representative local frame 055 (`/tmp/exodus_manual2/crops/registers_f055.png`)
- REG05: representative local frame 056 (`/tmp/exodus_manual2/crops/registers_f056.png`)
- REG06: representative local frame 057 (`/tmp/exodus_manual2/crops/registers_f057.png`)
- REG07: representative local frame 058 (`/tmp/exodus_manual2/crops/registers_f058.png`)
- REG08: representative local frame 061 (`/tmp/exodus_manual2/crops/registers_f061.png`)
- REG09: representative local frame 062 (`/tmp/exodus_manual2/crops/registers_f062.png`)
- REG10: representative local frame 063 (`/tmp/exodus_manual2/crops/registers_f063.png`)
- REG11: representative local frame 074 (`/tmp/exodus_manual2/crops/registers_f074.png`)
- REG12: representative local frame 075 (`/tmp/exodus_manual2/crops/registers_f075.png`)
- REG13: representative local frame 076 (`/tmp/exodus_manual2/crops/registers_f076.png`)
- REG14: representative local frame 077 (`/tmp/exodus_manual2/crops/registers_f077.png`)
- REG15: representative local frame 078 (`/tmp/exodus_manual2/crops/registers_f078.png`)
- REG16: representative local frame 086 (`/tmp/exodus_manual2/crops/registers_f086.png`)
- REG17: representative local frame 087 (`/tmp/exodus_manual2/crops/registers_f087.png`)
- REG18: representative local frame 089 (`/tmp/exodus_manual2/crops/registers_f089.png`)
- REG19: representative local frame 091 (`/tmp/exodus_manual2/crops/registers_f091.png`)
- REG20: representative local frame 092 (`/tmp/exodus_manual2/crops/registers_f092.png`)
- REG21: representative local frame 093 (`/tmp/exodus_manual2/crops/registers_f093.png`)
- REG22: representative local frame 098 (`/tmp/exodus_manual2/crops/registers_f098.png`)
- REG23: representative local frame 101 (`/tmp/exodus_manual2/crops/registers_f101.png`)
- REG24: representative local frame 109 (`/tmp/exodus_manual2/crops/registers_f109.png`)
- REG25: representative local frame 110 (`/tmp/exodus_manual2/crops/registers_f110.png`)
- REG26: representative local frame 111 (`/tmp/exodus_manual2/crops/registers_f111.png`)
- REG27: representative local frame 121 (`/tmp/exodus_manual2/crops/registers_f121.png`)
- REG28: representative local frame 122 (`/tmp/exodus_manual2/crops/registers_f122.png`)
- REG29: representative local frame 123 (`/tmp/exodus_manual2/crops/registers_f123.png`)
- REG30: representative local frame 124 (`/tmp/exodus_manual2/crops/registers_f124.png`)
### port_monitor
- POR01: representative local frame 001 (`/tmp/exodus_manual2/crops/port_monitor_f001.png`)
- POR02: representative local frame 002 (`/tmp/exodus_manual2/crops/port_monitor_f002.png`)
- POR03: representative local frame 003 (`/tmp/exodus_manual2/crops/port_monitor_f003.png`)
- POR04: representative local frame 056 (`/tmp/exodus_manual2/crops/port_monitor_f056.png`)
- POR05: representative local frame 060 (`/tmp/exodus_manual2/crops/port_monitor_f060.png`)
- POR06: representative local frame 061 (`/tmp/exodus_manual2/crops/port_monitor_f061.png`)
- POR07: representative local frame 062 (`/tmp/exodus_manual2/crops/port_monitor_f062.png`)
- POR08: representative local frame 063 (`/tmp/exodus_manual2/crops/port_monitor_f063.png`)
- POR09: representative local frame 069 (`/tmp/exodus_manual2/crops/port_monitor_f069.png`)
- POR10: representative local frame 091 (`/tmp/exodus_manual2/crops/port_monitor_f091.png`)
- POR11: representative local frame 092 (`/tmp/exodus_manual2/crops/port_monitor_f092.png`)
- POR12: representative local frame 093 (`/tmp/exodus_manual2/crops/port_monitor_f093.png`)
### vram_editor
- VRA01: representative local frame 001 (`/tmp/exodus_manual2/crops/vram_editor_f001.png`)
- VRA02: representative local frame 002 (`/tmp/exodus_manual2/crops/vram_editor_f002.png`)
- VRA03: representative local frame 003 (`/tmp/exodus_manual2/crops/vram_editor_f003.png`)
- VRA04: representative local frame 009 (`/tmp/exodus_manual2/crops/vram_editor_f009.png`)
- VRA05: representative local frame 012 (`/tmp/exodus_manual2/crops/vram_editor_f012.png`)
- VRA06: representative local frame 013 (`/tmp/exodus_manual2/crops/vram_editor_f013.png`)
- VRA07: representative local frame 031 (`/tmp/exodus_manual2/crops/vram_editor_f031.png`)
- VRA08: representative local frame 032 (`/tmp/exodus_manual2/crops/vram_editor_f032.png`)
- VRA09: representative local frame 056 (`/tmp/exodus_manual2/crops/vram_editor_f056.png`)
- VRA10: representative local frame 057 (`/tmp/exodus_manual2/crops/vram_editor_f057.png`)
- VRA11: representative local frame 058 (`/tmp/exodus_manual2/crops/vram_editor_f058.png`)
- VRA12: representative local frame 059 (`/tmp/exodus_manual2/crops/vram_editor_f059.png`)
- VRA13: representative local frame 061 (`/tmp/exodus_manual2/crops/vram_editor_f061.png`)
- VRA14: representative local frame 062 (`/tmp/exodus_manual2/crops/vram_editor_f062.png`)
- VRA15: representative local frame 063 (`/tmp/exodus_manual2/crops/vram_editor_f063.png`)
- VRA16: representative local frame 064 (`/tmp/exodus_manual2/crops/vram_editor_f064.png`)
- VRA17: representative local frame 067 (`/tmp/exodus_manual2/crops/vram_editor_f067.png`)
- VRA18: representative local frame 068 (`/tmp/exodus_manual2/crops/vram_editor_f068.png`)
- VRA19: representative local frame 091 (`/tmp/exodus_manual2/crops/vram_editor_f091.png`)
- VRA20: representative local frame 092 (`/tmp/exodus_manual2/crops/vram_editor_f092.png`)
### cram_editor
- CRA01: representative local frame 001 (`/tmp/exodus_manual2/crops/cram_editor_f001.png`)
- CRA02: representative local frame 002 (`/tmp/exodus_manual2/crops/cram_editor_f002.png`)
- CRA03: representative local frame 003 (`/tmp/exodus_manual2/crops/cram_editor_f003.png`)
- CRA04: representative local frame 009 (`/tmp/exodus_manual2/crops/cram_editor_f009.png`)
- CRA05: representative local frame 012 (`/tmp/exodus_manual2/crops/cram_editor_f012.png`)
- CRA06: representative local frame 013 (`/tmp/exodus_manual2/crops/cram_editor_f013.png`)
- CRA07: representative local frame 031 (`/tmp/exodus_manual2/crops/cram_editor_f031.png`)
- CRA08: representative local frame 032 (`/tmp/exodus_manual2/crops/cram_editor_f032.png`)
- CRA09: representative local frame 059 (`/tmp/exodus_manual2/crops/cram_editor_f059.png`)
- CRA10: representative local frame 060 (`/tmp/exodus_manual2/crops/cram_editor_f060.png`)
- CRA11: representative local frame 061 (`/tmp/exodus_manual2/crops/cram_editor_f061.png`)
- CRA12: representative local frame 062 (`/tmp/exodus_manual2/crops/cram_editor_f062.png`)
- CRA13: representative local frame 067 (`/tmp/exodus_manual2/crops/cram_editor_f067.png`)
- CRA14: representative local frame 091 (`/tmp/exodus_manual2/crops/cram_editor_f091.png`)
- CRA15: representative local frame 092 (`/tmp/exodus_manual2/crops/cram_editor_f092.png`)
- CRA16: representative local frame 093 (`/tmp/exodus_manual2/crops/cram_editor_f093.png`)
- CRA17: representative local frame 121 (`/tmp/exodus_manual2/crops/cram_editor_f121.png`)
- CRA18: representative local frame 126 (`/tmp/exodus_manual2/crops/cram_editor_f126.png`)
- CRA19: representative local frame 151 (`/tmp/exodus_manual2/crops/cram_editor_f151.png`)
### pattern_viewer
- PAT01: representative local frame 001 (`/tmp/exodus_manual2/crops/pattern_viewer_f001.png`)
- PAT02: representative local frame 002 (`/tmp/exodus_manual2/crops/pattern_viewer_f002.png`)
- PAT03: representative local frame 003 (`/tmp/exodus_manual2/crops/pattern_viewer_f003.png`)
- PAT04: representative local frame 004 (`/tmp/exodus_manual2/crops/pattern_viewer_f004.png`)
- PAT05: representative local frame 005 (`/tmp/exodus_manual2/crops/pattern_viewer_f005.png`)
- PAT06: representative local frame 007 (`/tmp/exodus_manual2/crops/pattern_viewer_f007.png`)
- PAT07: representative local frame 008 (`/tmp/exodus_manual2/crops/pattern_viewer_f008.png`)
- PAT08: representative local frame 009 (`/tmp/exodus_manual2/crops/pattern_viewer_f009.png`)
- PAT09: representative local frame 031 (`/tmp/exodus_manual2/crops/pattern_viewer_f031.png`)
- PAT10: representative local frame 032 (`/tmp/exodus_manual2/crops/pattern_viewer_f032.png`)
- PAT11: representative local frame 033 (`/tmp/exodus_manual2/crops/pattern_viewer_f033.png`)
- PAT12: representative local frame 034 (`/tmp/exodus_manual2/crops/pattern_viewer_f034.png`)
- PAT13: representative local frame 055 (`/tmp/exodus_manual2/crops/pattern_viewer_f055.png`)
- PAT14: representative local frame 056 (`/tmp/exodus_manual2/crops/pattern_viewer_f056.png`)
- PAT15: representative local frame 059 (`/tmp/exodus_manual2/crops/pattern_viewer_f059.png`)
- PAT16: representative local frame 061 (`/tmp/exodus_manual2/crops/pattern_viewer_f061.png`)
- PAT17: representative local frame 062 (`/tmp/exodus_manual2/crops/pattern_viewer_f062.png`)
- PAT18: representative local frame 064 (`/tmp/exodus_manual2/crops/pattern_viewer_f064.png`)
- PAT19: representative local frame 068 (`/tmp/exodus_manual2/crops/pattern_viewer_f068.png`)
- PAT20: representative local frame 070 (`/tmp/exodus_manual2/crops/pattern_viewer_f070.png`)
- PAT21: representative local frame 071 (`/tmp/exodus_manual2/crops/pattern_viewer_f071.png`)
- PAT22: representative local frame 075 (`/tmp/exodus_manual2/crops/pattern_viewer_f075.png`)
- PAT23: representative local frame 076 (`/tmp/exodus_manual2/crops/pattern_viewer_f076.png`)
- PAT24: representative local frame 077 (`/tmp/exodus_manual2/crops/pattern_viewer_f077.png`)
- PAT25: representative local frame 078 (`/tmp/exodus_manual2/crops/pattern_viewer_f078.png`)
- PAT26: representative local frame 079 (`/tmp/exodus_manual2/crops/pattern_viewer_f079.png`)
- PAT27: representative local frame 080 (`/tmp/exodus_manual2/crops/pattern_viewer_f080.png`)
- PAT28: representative local frame 091 (`/tmp/exodus_manual2/crops/pattern_viewer_f091.png`)
- PAT29: representative local frame 092 (`/tmp/exodus_manual2/crops/pattern_viewer_f092.png`)
- PAT30: representative local frame 093 (`/tmp/exodus_manual2/crops/pattern_viewer_f093.png`)
- PAT31: representative local frame 094 (`/tmp/exodus_manual2/crops/pattern_viewer_f094.png`)
### image_window
- IMA01: representative local frame 001 (`/tmp/exodus_manual2/crops/image_window_f001.png`)
- IMA02: representative local frame 059 (`/tmp/exodus_manual2/crops/image_window_f059.png`)
### palette
- PAL01: representative local frame 001 (`/tmp/exodus_manual2/crops/palette_f001.png`)
- PAL02: representative local frame 003 (`/tmp/exodus_manual2/crops/palette_f003.png`)
- PAL03: representative local frame 059 (`/tmp/exodus_manual2/crops/palette_f059.png`)
- PAL04: representative local frame 061 (`/tmp/exodus_manual2/crops/palette_f061.png`)
### plane_viewer
- PLA01: representative local frame 001 (`/tmp/exodus_manual2/crops/plane_viewer_f001.png`)
- PLA02: representative local frame 002 (`/tmp/exodus_manual2/crops/plane_viewer_f002.png`)
- PLA03: representative local frame 003 (`/tmp/exodus_manual2/crops/plane_viewer_f003.png`)
- PLA04: representative local frame 004 (`/tmp/exodus_manual2/crops/plane_viewer_f004.png`)
- PLA05: representative local frame 056 (`/tmp/exodus_manual2/crops/plane_viewer_f056.png`)
- PLA06: representative local frame 060 (`/tmp/exodus_manual2/crops/plane_viewer_f060.png`)
- PLA07: representative local frame 061 (`/tmp/exodus_manual2/crops/plane_viewer_f061.png`)
- PLA08: representative local frame 062 (`/tmp/exodus_manual2/crops/plane_viewer_f062.png`)
- PLA09: representative local frame 064 (`/tmp/exodus_manual2/crops/plane_viewer_f064.png`)
- PLA10: representative local frame 068 (`/tmp/exodus_manual2/crops/plane_viewer_f068.png`)
- PLA11: representative local frame 069 (`/tmp/exodus_manual2/crops/plane_viewer_f069.png`)
- PLA12: representative local frame 070 (`/tmp/exodus_manual2/crops/plane_viewer_f070.png`)
- PLA13: representative local frame 091 (`/tmp/exodus_manual2/crops/plane_viewer_f091.png`)
- PLA14: representative local frame 092 (`/tmp/exodus_manual2/crops/plane_viewer_f092.png`)

## Per-Frame Main M68K Register Literal Values
Fields: A0..A7 D0..D7 X N Z V C PC USP SSP S T IPM SR

Frame 001 (source 240, t=8.000s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 002 (source 241, t=8.033s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 003 (source 242, t=8.067s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 004 (source 243, t=8.100s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 005 (source 244, t=8.133s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 006 (source 245, t=8.167s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 007 (source 246, t=8.200s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 008 (source 247, t=8.233s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 009 (source 248, t=8.267s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 010 (source 249, t=8.300s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 011 (source 250, t=8.333s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 012 (source 251, t=8.367s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 013 (source 252, t=8.400s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 014 (source 253, t=8.433s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 015 (source 254, t=8.467s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 016 (source 255, t=8.500s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 017 (source 256, t=8.533s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 018 (source 257, t=8.567s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 019 (source 258, t=8.600s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 020 (source 259, t=8.633s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 021 (source 260, t=8.667s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 022 (source 261, t=8.700s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 023 (source 262, t=8.733s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 024 (source 263, t=8.767s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 025 (source 264, t=8.800s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 026 (source 265, t=8.833s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 027 (source 266, t=8.867s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 028 (source 267, t=8.900s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 029 (source 268, t=8.933s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 030 (source 269, t=8.967s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 031 (source 270, t=9.000s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 032 (source 271, t=9.033s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 033 (source 272, t=9.067s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 034 (source 273, t=9.100s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 035 (source 274, t=9.133s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 036 (source 275, t=9.167s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 037 (source 276, t=9.200s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 038 (source 277, t=9.233s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 039 (source 278, t=9.267s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 040 (source 279, t=9.300s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 041 (source 280, t=9.333s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 042 (source 281, t=9.367s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 043 (source 282, t=9.400s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 044 (source 283, t=9.433s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 045 (source 284, t=9.467s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 046 (source 285, t=9.500s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 047 (source 286, t=9.533s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 048 (source 287, t=9.567s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 049 (source 288, t=9.600s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 050 (source 289, t=9.633s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 051 (source 290, t=9.667s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 052 (source 291, t=9.700s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 053 (source 292, t=9.733s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 054 (source 293, t=9.767s): A0=0xFFFFFFFF A1=0xFFFFFFFF A2=0xFFFFFFFF A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0xFFFFFFFF D0=0xFFFFFFFF D1=0xFFFFFFFF D2=0xFFFFFFFF D3=0xFFFFFFFF D4=0xFFFFFFFF D5=0xFFFFFFFF D6=0xFFFFFFFF D7=0xFFFFFFFF X=1 N=1 Z=1 V=1 C=1 PC=0xFFFFFFFF USP=0xFFFFFFFF SSP=0xFFFFFFFF S=1 T=1 IPM=7 SR=0xFFFF
Frame 055 (source 294, t=9.800s): A0=0x0017A240 A1=0xFFFFFFFF A2=0x0013F36C A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0x00FEFFC6 D0=0x00002B40 D1=0x6CA00000 D2=0x00000000 D3=0xFFFF0171 D4=0x00046E00 D5=0xFFFFFFFF D6=0x00000000 D7=0x00000001 X=1 N=0 Z=0 V=0 C=0 PC=0x00071B5C USP=0xFFFFFFFF SSP=0x00FEFFC6 S=1 T=1 IPM=7 SR=0x2710
Frame 056 (source 295, t=9.833s): A0=0x0017A240 A1=0xFFFFFFFF A2=0x0013F36C A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0x00FEFFC6 D0=0x00002B40 D1=0x6CA00000 D2=0x00000000 D3=0xFFFF0171 D4=0x00046E00 D5=0xFFFFFFFF D6=0x00000000 D7=0x00000001 X=1 N=0 Z=0 V=0 C=0 PC=0x00071B5C USP=0xFFFFFFFF SSP=0x00FEFFC6 S=1 T=1 IPM=7 SR=0x2710
Frame 057 (source 296, t=9.867s): A0=0x0017A240 A1=0xFFFFFFFF A2=0x0013F36C A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0x00FEFFC6 D0=0x00002B40 D1=0x6CA00000 D2=0x00000000 D3=0xFFFF0171 D4=0x00046E00 D5=0xFFFFFFFF D6=0x00000000 D7=0x00000001 X=1 N=0 Z=0 V=0 C=0 PC=0x00071B5C USP=0xFFFFFFFF SSP=0x00FEFFC6 S=1 T=1 IPM=7 SR=0x2710
Frame 058 (source 297, t=9.900s): A0=0x0017A240 A1=0xFFFFFFFF A2=0x0013F36C A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0x00FEFFC6 D0=0x00002B40 D1=0x6CA00000 D2=0x00000000 D3=0xFFFF0171 D4=0x00046E00 D5=0xFFFFFFFF D6=0x00000000 D7=0x00000001 X=1 N=0 Z=0 V=0 C=0 PC=0x00071B5C USP=0xFFFFFFFF SSP=0x00FEFFC6 S=1 T=1 IPM=7 SR=0x2710
Frame 059 (source 298, t=9.933s): A0=0x0017A240 A1=0xFFFFFFFF A2=0x0013F36C A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0x00FEFFC6 D0=0x00002B40 D1=0x6CA00000 D2=0x00000000 D3=0xFFFF0171 D4=0x00046E00 D5=0xFFFFFFFF D6=0x00000000 D7=0x00000001 X=1 N=0 Z=0 V=0 C=0 PC=0x00071B5C USP=0xFFFFFFFF SSP=0x00FEFFC6 S=1 T=1 IPM=7 SR=0x2710
Frame 060 (source 299, t=9.967s): A0=0x0017A240 A1=0xFFFFFFFF A2=0x0013F36C A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0x00FEFFC6 D0=0x00002B40 D1=0x6CA00000 D2=0x00000000 D3=0xFFFF0171 D4=0x00046E00 D5=0xFFFFFFFF D6=0x00000000 D7=0x00000001 X=1 N=0 Z=0 V=0 C=0 PC=0x00071B5C USP=0xFFFFFFFF SSP=0x00FEFFC6 S=1 T=1 IPM=7 SR=0x2710
Frame 061 (source 300, t=10.000s): A0=0x0017A240 A1=0xFFFFFFFF A2=0x0013F36C A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0x00FEFFC6 D0=0x00002B40 D1=0x6CA00000 D2=0x00000000 D3=0xFFFF0171 D4=0x00046E00 D5=0xFFFFFFFF D6=0x00000000 D7=0x00000001 X=1 N=0 Z=0 V=0 C=0 PC=0x00071B5C USP=0xFFFFFFFF SSP=0x00FEFFC6 S=1 T=1 IPM=7 SR=0x2710
Frame 062 (source 301, t=10.033s): A0=0x0017A240 A1=0xFFFFFFFF A2=0x0013F36C A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0x00FEFFC6 D0=0x00002B40 D1=0x6CA00000 D2=0x00000000 D3=0xFFFF0171 D4=0x00046E00 D5=0xFFFFFFFF D6=0x00000000 D7=0x00000001 X=1 N=0 Z=0 V=0 C=0 PC=0x00071B5C USP=0xFFFFFFFF SSP=0x00FEFFC6 S=1 T=1 IPM=7 SR=0x2710
Frame 063 (source 302, t=10.067s): A0=0x0017A240 A1=0xFFFFFFFF A2=0x0013F36C A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0x00FEFFC6 D0=0x00002B40 D1=0x6CA00000 D2=0x00000000 D3=0xFFFF0171 D4=0x00046E00 D5=0xFFFFFFFF D6=0x00000000 D7=0x00000001 X=1 N=0 Z=0 V=0 C=0 PC=0x00071B5C USP=0xFFFFFFFF SSP=0x00FEFFC6 S=1 T=1 IPM=7 SR=0x2710
Frame 064 (source 303, t=10.100s): A0=0x0017A240 A1=0xFFFFFFFF A2=0x0013F36C A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0x00FEFFC6 D0=0x00002B40 D1=0x6CA00000 D2=0x00000000 D3=0xFFFF0171 D4=0x00046E00 D5=0xFFFFFFFF D6=0x00000000 D7=0x00000001 X=1 N=0 Z=0 V=0 C=0 PC=0x00071B5C USP=0xFFFFFFFF SSP=0x00FEFFC6 S=1 T=1 IPM=7 SR=0x2710
Frame 065 (source 304, t=10.133s): A0=0x0017A240 A1=0xFFFFFFFF A2=0x0013F36C A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0x00FEFFC6 D0=0x00002B40 D1=0x6CA00000 D2=0x00000000 D3=0xFFFF0171 D4=0x00046E00 D5=0xFFFFFFFF D6=0x00000000 D7=0x00000001 X=1 N=0 Z=0 V=0 C=0 PC=0x00071B5C USP=0xFFFFFFFF SSP=0x00FEFFC6 S=1 T=1 IPM=7 SR=0x2710
Frame 066 (source 305, t=10.167s): A0=0x0017A240 A1=0xFFFFFFFF A2=0x0013F36C A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0x00FEFFC6 D0=0x00002B40 D1=0x6CA00000 D2=0x00000000 D3=0xFFFF0171 D4=0x00046E00 D5=0xFFFFFFFF D6=0x00000000 D7=0x00000001 X=1 N=0 Z=0 V=0 C=0 PC=0x00071B5C USP=0xFFFFFFFF SSP=0x00FEFFC6 S=1 T=1 IPM=7 SR=0x2710
Frame 067 (source 306, t=10.200s): A0=0x0017A240 A1=0xFFFFFFFF A2=0x0013F36C A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0x00FEFFC6 D0=0x00002B40 D1=0x6CA00000 D2=0x00000000 D3=0xFFFF0171 D4=0x00046E00 D5=0xFFFFFFFF D6=0x00000000 D7=0x00000001 X=1 N=0 Z=0 V=0 C=0 PC=0x00071B5C USP=0xFFFFFFFF SSP=0x00FEFFC6 S=1 T=1 IPM=7 SR=0x2710
Frame 068 (source 307, t=10.233s): A0=0x0017A240 A1=0xFFFFFFFF A2=0x0013F36C A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0x00FEFFC6 D0=0x00002B40 D1=0x6CA00000 D2=0x00000000 D3=0xFFFF0171 D4=0x00046E00 D5=0xFFFFFFFF D6=0x00000000 D7=0x00000001 X=1 N=0 Z=0 V=0 C=0 PC=0x00071B5C USP=0xFFFFFFFF SSP=0x00FEFFC6 S=1 T=1 IPM=7 SR=0x2710
Frame 069 (source 308, t=10.267s): A0=0x0017A240 A1=0xFFFFFFFF A2=0x0013F36C A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0x00FEFFC6 D0=0x00002B40 D1=0x6CA00000 D2=0x00000000 D3=0xFFFF0171 D4=0x00046E00 D5=0xFFFFFFFF D6=0x00000000 D7=0x00000001 X=1 N=0 Z=0 V=0 C=0 PC=0x00071B5C USP=0xFFFFFFFF SSP=0x00FEFFC6 S=1 T=1 IPM=7 SR=0x2710
Frame 070 (source 309, t=10.300s): A0=0x0017A240 A1=0xFFFFFFFF A2=0x0013F36C A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0x00FEFFC6 D0=0x00002B40 D1=0x6CA00000 D2=0x00000000 D3=0xFFFF0171 D4=0x00046E00 D5=0xFFFFFFFF D6=0x00000000 D7=0x00000001 X=1 N=0 Z=0 V=0 C=0 PC=0x00071B5C USP=0xFFFFFFFF SSP=0x00FEFFC6 S=1 T=1 IPM=7 SR=0x2710
Frame 071 (source 310, t=10.333s): A0=0x0017A240 A1=0xFFFFFFFF A2=0x0013F36C A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0x00FEFFC6 D0=0x00002B40 D1=0x6CA00000 D2=0x00000000 D3=0xFFFF0171 D4=0x00046E00 D5=0xFFFFFFFF D6=0x00000000 D7=0x00000001 X=1 N=0 Z=0 V=0 C=0 PC=0x00071B5C USP=0xFFFFFFFF SSP=0x00FEFFC6 S=1 T=1 IPM=7 SR=0x2710
Frame 072 (source 311, t=10.367s): A0=0x0017A240 A1=0xFFFFFFFF A2=0x0013F36C A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0x00FEFFC6 D0=0x00002B40 D1=0x6CA00000 D2=0x00000000 D3=0xFFFF0171 D4=0x00046E00 D5=0xFFFFFFFF D6=0x00000000 D7=0x00000001 X=1 N=0 Z=0 V=0 C=0 PC=0x00071B5C USP=0xFFFFFFFF SSP=0x00FEFFC6 S=1 T=1 IPM=7 SR=0x2710
Frame 073 (source 312, t=10.400s): A0=0x0017A240 A1=0xFFFFFFFF A2=0x0013F36C A3=0xFFFFFFFF A4=0xFFFFFFFF A5=0xFFFFFFFF A6=0xFFFFFFFF A7=0x00FEFFC6 D0=0x00002B40 D1=0x6CA00000 D2=0x00000000 D3=0xFFFF0171 D4=0x00046E00 D5=0xFFFFFFFF D6=0x00000000 D7=0x00000001 X=1 N=0 Z=0 V=0 C=0 PC=0x00071B5C USP=0xFFFFFFFF SSP=0x00FEFFC6 S=1 T=1 IPM=7 SR=0x2710
Frame 074 (source 313, t=10.433s): A0=0x00FF8F88 A1=0x00FF7E5C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB0 D0=0x000003EF D1=0x000000FE D2=0x00000080 D3=0xFFFF0080 D4=0x00000001 D5=0x00008001 D6=0x00000000 D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x000711E6 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2704
Frame 075 (source 314, t=10.467s): A0=0x00FF8F88 A1=0x00FF7E5C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB0 D0=0x000003EF D1=0x000000FE D2=0x00000080 D3=0xFFFF0080 D4=0x00000001 D5=0x00008001 D6=0x00000000 D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x000711E6 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2704
Frame 076 (source 315, t=10.500s): A0=0x00FF8F88 A1=0x00FF7E5C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB0 D0=0x000003EF D1=0x000000FE D2=0x00000080 D3=0xFFFF0080 D4=0x00000001 D5=0x00008001 D6=0x00000000 D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x000711E6 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2704
Frame 077 (source 316, t=10.533s): A0=0x00FF8F88 A1=0x00FF7E5C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB0 D0=0x000003EF D1=0x000000FE D2=0x00000080 D3=0xFFFF0080 D4=0x00000001 D5=0x00008001 D6=0x00000000 D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x000711E6 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2704
Frame 078 (source 317, t=10.567s): A0=0x00FF8F88 A1=0x00FF7E5C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB0 D0=0x000003EF D1=0x000000FE D2=0x00000080 D3=0xFFFF0080 D4=0x00000001 D5=0x00008001 D6=0x00000000 D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x000711E6 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2704
Frame 079 (source 318, t=10.600s): A0=0x00FF8F88 A1=0x00FF7E5C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB0 D0=0x000003EF D1=0x000000FE D2=0x00000080 D3=0xFFFF0080 D4=0x00000001 D5=0x00008001 D6=0x00000000 D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x000711E6 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2704
Frame 080 (source 319, t=10.633s): A0=0x00FF8F88 A1=0x00FF7E5C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB0 D0=0x000003EF D1=0x000000FE D2=0x00000080 D3=0xFFFF0080 D4=0x00000001 D5=0x00008001 D6=0x00000000 D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x000711E6 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2704
Frame 081 (source 320, t=10.667s): A0=0x00FF8F88 A1=0x00FF7E5C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB0 D0=0x000003EF D1=0x000000FE D2=0x00000080 D3=0xFFFF0080 D4=0x00000001 D5=0x00008001 D6=0x00000000 D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x000711E6 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2704
Frame 082 (source 321, t=10.700s): A0=0x00FF8F88 A1=0x00FF7E5C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB0 D0=0x000003EF D1=0x000000FE D2=0x00000080 D3=0xFFFF0080 D4=0x00000001 D5=0x00008001 D6=0x00000000 D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x000711E6 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2704
Frame 083 (source 322, t=10.733s): A0=0x00FF8F88 A1=0x00FF7E5C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB0 D0=0x000003EF D1=0x000000FE D2=0x00000080 D3=0xFFFF0080 D4=0x00000001 D5=0x00008001 D6=0x00000000 D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x000711E6 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2704
Frame 084 (source 323, t=10.767s): A0=0x00FF8F88 A1=0x00FF7E5C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB0 D0=0x000003EF D1=0x000000FE D2=0x00000080 D3=0xFFFF0080 D4=0x00000001 D5=0x00008001 D6=0x00000000 D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x000711E6 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2704
Frame 085 (source 324, t=10.800s): A0=0x00FF8F88 A1=0x00FF7E5C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB0 D0=0x000003EF D1=0x000000FE D2=0x00000080 D3=0xFFFF0080 D4=0x00000001 D5=0x00008001 D6=0x00000000 D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x000711E6 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2704
Frame 086 (source 325, t=10.833s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x0087B304 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 087 (source 326, t=10.867s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x0087B304 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 088 (source 327, t=10.900s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x0087B304 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 089 (source 328, t=10.933s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x0087B304 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 090 (source 329, t=10.967s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x0087B304 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 091 (source 330, t=11.000s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x0087B304 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 092 (source 331, t=11.033s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x0087B304 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 093 (source 332, t=11.067s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x0087B304 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 094 (source 333, t=11.100s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x0087B304 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 095 (source 334, t=11.133s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x0087B304 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 096 (source 335, t=11.167s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x0087B304 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 097 (source 336, t=11.200s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x0087B304 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 098 (source 337, t=11.233s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x009A2A24 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 099 (source 338, t=11.267s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x009A2A24 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 100 (source 339, t=11.300s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x009A2A24 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 101 (source 340, t=11.333s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x009A2A24 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 102 (source 341, t=11.367s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x009A2A24 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 103 (source 342, t=11.400s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x009A2A24 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 104 (source 343, t=11.433s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x009A2A24 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 105 (source 344, t=11.467s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x009A2A24 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 106 (source 345, t=11.500s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x009A2A24 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 107 (source 346, t=11.533s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x009A2A24 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 108 (source 347, t=11.567s): A0=0x00FFFFA8 A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFB4 D0=0x00000003 D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=1 N=0 Z=0 V=0 C=0 PC=0x009A2A24 USP=0xFFFFFFFF SSP=0x00FEFFB4 S=1 T=1 IPM=7 SR=0x2710
Frame 109 (source 348, t=11.600s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 110 (source 349, t=11.633s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 111 (source 350, t=11.667s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 112 (source 351, t=11.700s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 113 (source 352, t=11.733s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 114 (source 353, t=11.767s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 115 (source 354, t=11.800s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 116 (source 355, t=11.833s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 117 (source 356, t=11.867s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 118 (source 357, t=11.900s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 119 (source 358, t=11.933s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 120 (source 359, t=11.967s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 121 (source 360, t=12.000s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 122 (source 361, t=12.033s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 123 (source 362, t=12.067s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 124 (source 363, t=12.100s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 125 (source 364, t=12.133s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 126 (source 365, t=12.167s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 127 (source 366, t=12.200s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 128 (source 367, t=12.233s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 129 (source 368, t=12.267s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 130 (source 369, t=12.300s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 131 (source 370, t=12.333s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 132 (source 371, t=12.367s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 133 (source 372, t=12.400s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 134 (source 373, t=12.433s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 135 (source 374, t=12.467s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 136 (source 375, t=12.500s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 137 (source 376, t=12.533s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 138 (source 377, t=12.567s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 139 (source 378, t=12.600s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 140 (source 379, t=12.633s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 141 (source 380, t=12.667s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 142 (source 381, t=12.700s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 143 (source 382, t=12.733s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 144 (source 383, t=12.767s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 145 (source 384, t=12.800s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 146 (source 385, t=12.833s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 147 (source 386, t=12.867s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 148 (source 387, t=12.900s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 149 (source 388, t=12.933s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 150 (source 389, t=12.967s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700
Frame 151 (source 390, t=13.000s): A0=0x00FFFFAE A1=0x00FFC91C A2=0xFFFFFFFF A3=0x00050082 A4=0xFFFFFFFF A5=0x00FF0000 A6=0xFFFFFFFF A7=0x00FEFFAE D0=0x0000000A D1=0x00000340 D2=0x00000001 D3=0xFFFFFFFF D4=0x00000005 D5=0x00000085 D6=0x0000000C D7=0xFFFF0030 X=0 N=0 Z=0 V=0 C=0 PC=0x0000051E USP=0xFFFFFFFF SSP=0x00FEFFAE S=1 T=0 IPM=7 SR=0x2700

## Port Monitor Table Values
- Visible table rows in frames 240..390: NONE
- Visible controls: List size `2000`; logging options checkboxes unchecked

## Notes
- Extraction is read-only and transcription-focused.
- No analysis, diagnosis, hypotheses, or recommendations included.
