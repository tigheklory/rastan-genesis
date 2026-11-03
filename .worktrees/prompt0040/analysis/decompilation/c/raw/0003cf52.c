/* ORIGINAL ARCADE PC: 0x0003CF52 frame -> velocity applier (+ axis-lock flags) and 0x3CFB0 helper.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * d0 = frame index (1-based). Index the 2-byte velocity table 0x3CFD4 at (frame-1)*2:
 *     +0x14 (vx) = sign_extend(tbl[i].byte0);  +0x18 (vy) = sign_extend(tbl[i].byte1).
 * Then apply the +0x13 axis-lock flags:
 *     bit0 -> clear +0x18 (lock vy)
 *     bit1 -> clear +0x14 (lock vx)
 *     bit2 -> if 0x3CFB0(frame) != 0 clear +0x14 (conditional vx lock by frame band)
 *     bit3 -> copy +0x14 into +0x18 (mirror vx to vy, diagonal)
 * 0x3CFB0 returns 1 when frame is OUTSIDE the bands [4,26) and [32,54) (i.e. the "cardinal" frames),
 * else 0. Table 0x3CFD4 = 56 signed {vx,vy} pairs (a 56-step direction/velocity ring). */
#include "raw_common.h"

/* arcade 0x3CFD4: 56 signed {vx,vy} byte pairs. */
static const int8_t vel_3cfd4[56][2] = {
 {0x00,-3},{ 1,-4},{ 1,-3},{ 1,-3},{ 2,-3},{ 2,-3},{ 3,-3},{ 3,-3},
 { 3,-2},{ 3,-2},{ 3,-1},{ 3,-1},{ 4,-1},{ 3, 0},{ 3, 0},{ 4, 1},
 { 3, 1},{ 3, 1},{ 3, 2},{ 3, 2},{ 3, 3},{ 3, 3},{ 2, 3},{ 2, 3},
 { 1, 3},{ 1, 3},{ 1, 4},{ 0, 3},{ 0, 3},{-1, 4},{-1, 3},{-1, 3},
 {-2, 3},{-2, 3},{-3, 3},{-3, 3},{-3, 2},{-3, 2},{-3, 1},{-3, 1},
 {-4, 1},{-3, 0},{-3, 0},{-4,-1},{-3,-1},{-3,-1},{-3,-2},{-3,-2},
 {-3,-3},{-3,-3},{-2,-3},{-2,-3},{-1,-3},{-1,-3},{-1,-4},{ 0,-3}
};

/* 0x3CFB0: frame-band test used by +0x13 bit2. */
static int band_3cfb0(uint8_t frame){
    if (frame < 4)  return 1;
    if (frame < 26) return 0;
    if (frame < 32) return 1;
    if (frame < 54) return 0;
    return 1;
}

void arcade_3cf52(uint8_t d0, uint8_t *r){
    unsigned i = (unsigned)(d0 - 1);
    W(r,0x14) = (uint16_t)(int16_t)vel_3cfd4[i][0];   /* vx sign-extended */
    W(r,0x18) = (uint16_t)(int16_t)vel_3cfd4[i][1];   /* vy sign-extended */
    uint8_t fl = B(r,0x13);
    if (fl & 0x01){ W(r,0x18)=0; return; }            /* lock vy */
    if (fl & 0x02){ W(r,0x14)=0; return; }            /* lock vx */
    if (fl & 0x04){ if (band_3cfb0(B(r,0x0d))) W(r,0x14)=0; }
    if (fl & 0x08){ W(r,0x18)=W(r,0x14); }            /* mirror vx -> vy */
}
