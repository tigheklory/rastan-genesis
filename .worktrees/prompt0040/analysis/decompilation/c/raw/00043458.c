/* ORIGINAL ARCADE PC: 0x00043450; internal entry 0x00043458.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * A4=parent/body, A6=output child, D0=table index.  The public 0x43450 entry
 * also clears child+0x38 and stores the index at child+0x23; callers that enter
 * at 0x43458 intentionally skip those two initializations. */
#include "raw_common.h"

typedef struct { int8_t dx, dy; } Offset43484;
static const Offset43484 table_43484[27] = {
    { 40,-16},{ 34, 28},{ 48,-16},{ 20, -5},{  6,-16},{ 20,-20},{  8,-20},
    { 20,-11},{  8,-11},{  8, 32},{ 52,-60},{ 76, -4},{ 48, -4},{ -3, -8},
    {  7, -8},{ 16, -8},{ -7,-16},{  2,-16},{ 42,-19},{ 24,-36},{  8,-44},
    { -8,-52},{  0,-61},{-46,-61},{-62,-34},{-72,-20},{  0,-72}
};

void arcade_43458(uint8_t *parent_a4, uint8_t *child_a6, uint16_t index)
{
    int16_t dx = table_43484[index].dx;
    int16_t dy = table_43484[index].dy;
    if (B(parent_a4, 0x02) == 0) dx = (int16_t)-dx;
    W(child_a6, 0x16) = (uint16_t)(W(parent_a4, 0x16) + dx);
    W(child_a6, 0x1a) = (uint16_t)(W(parent_a4, 0x1a) + dy);
}

void arcade_43450(uint8_t *parent_a4, uint8_t *child_a6, uint16_t index)
{
    B(child_a6, 0x38) = 0;
    B(child_a6, 0x23) = (uint8_t)index;
    arcade_43458(parent_a4, child_a6, index);
}
