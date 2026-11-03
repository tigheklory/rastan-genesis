# Cody Genesis staged_bg_buffer Dump (Task 4/5)

## Address Resolution Method

- `staged_bg_buffer` address was resolved from linker symbol output: `apps/rastan-direct/out/symbol.txt` (`staged_bg_buffer = 0xFF19BC` in the instrumented run).

## 5.1 staged_bg_buffer Content Summary

- `REAL_DATA` count: 0
- `CHECKERBOARD_1` count: 1024
- `CHECKERBOARD_2` count: 1024

Sample dump rows (full CSV in `build/analysis225/genesis_staged_bg_words.csv`):

```csv
buf_offset,row,col,nametable_word
0x0000,0,0,0x0001
0x0002,0,1,0x0002
0x0004,0,2,0x0001
0x0006,0,3,0x0002
0x0008,0,4,0x0001
0x000A,0,5,0x0002
0x000C,0,6,0x0001
0x000E,0,7,0x0002
0x0010,0,8,0x0001
0x0012,0,9,0x0002
0x0014,0,10,0x0001
0x0016,0,11,0x0002
0x0018,0,12,0x0001
0x001A,0,13,0x0002
0x001C,0,14,0x0001
0x001E,0,15,0x0002
0x0020,0,16,0x0001
0x0022,0,17,0x0002
0x0024,0,18,0x0001
0x0026,0,19,0x0002
0x0028,0,20,0x0001
0x002A,0,21,0x0002
0x002C,0,22,0x0001
0x002E,0,23,0x0002
0x0030,0,24,0x0001
0x0032,0,25,0x0002
0x0034,0,26,0x0001
0x0036,0,27,0x0002
0x0038,0,28,0x0001
0x003A,0,29,0x0002
0x003C,0,30,0x0001
0x003E,0,31,0x0002
```

## 5.2 4x4 Arcade/Genesis Correlation Table

| screen_col | screen_row | arcade_tile_number | genesis_buf_offset | genesis_nametable_word | match |
|-----------:|-----------:|-------------------:|-------------------:|-----------------------:|:-----:|
| 0 | 0 | 1190 | 0x0000 | 0x0001 | NO |
| 1 | 0 | 1191 | 0x0002 | 0x0002 | NO |
| 2 | 0 | 1192 | 0x0004 | 0x0001 | NO |
| 3 | 0 | 1193 | 0x0006 | 0x0002 | NO |
| 0 | 1 | 1202 | 0x0080 | 0x0002 | NO |
| 1 | 1 | 1203 | 0x0082 | 0x0001 | NO |
| 2 | 1 | 1204 | 0x0084 | 0x0002 | NO |
| 3 | 1 | 1205 | 0x0086 | 0x0001 | NO |
| 0 | 2 | 1218 | 0x0100 | 0x0001 | NO |
| 1 | 2 | 1219 | 0x0102 | 0x0002 | NO |
| 2 | 2 | 1220 | 0x0104 | 0x0001 | NO |
| 3 | 2 | 1221 | 0x0106 | 0x0002 | NO |
| 0 | 3 | 1234 | 0x0180 | 0x0002 | NO |
| 1 | 3 | 1234 | 0x0182 | 0x0001 | NO |
| 2 | 3 | 1234 | 0x0184 | 0x0002 | NO |
| 3 | 3 | 1234 | 0x0186 | 0x0001 | NO |

## 5.3 4x4 REAL_DATA Verification

- No REAL_DATA entries were present in the 4x4 block in this capture; all 16 entries remained checkerboard values.
