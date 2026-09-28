/* ORIGINAL ARCADE PC: 0x0003C9E8 SAT attribute-word finaliser (optional +0x27 override).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE.
 * The Ghidra export showed this as an empty void; it is NOT — it has an implicit D0 in/out contract.
 * Exact 68000:
 *     3C9E8: btst #6,%a4@(39)     ; test actor +0x27 bit 6
 *     3C9EE: beq  0x3C9F4         ; bit6 clear -> leave D0 unchanged
 *     3C9F0: moveb %a4@(39),%d0   ; bit6 set -> D0.LOW = +0x27 (moveb keeps D0 high byte)
 *     3C9F4: rts                  ; return D0
 *
 * CONTRACT:  in: D0 = compositor program control WORD (high byte = control/flags incl. 0x40 HFLIP
 *                    already OR'd by the caller; low byte = attribute, whose nibble 0..3 = palette
 *                    line); A4 = ActorRecord.
 *            out: D0. If +0x27 bit6==0 -> unchanged (palette line = program control byte & 0x0F).
 *                     If +0x27 bit6==1 -> D0.low replaced by +0x27 (palette line = +0x27 & 0x0F).
 * The caller (0x3C97E / 0x3C9BE in the 0x3C902 general interpreter) writes the returned D0 straight
 * to PC090OJ SAT word 0 (`movew %d0,%a1@+` at 0x3C982 / 0x3C9C2). No later masking changes nibble.
 *
 * IMPLICATION: +0x27 is an OPTIONAL override (set by the field-schedule path 0x45684 for family
 * actors), NOT the unconditional palette source. Boss BODY records come from the record-type path
 * (0x45330->0x4449E->0x453A8->0x4543E), which never calls 0x45684, so their +0x27 stays 0 (bit6
 * clear) and their palette line is the EMBEDDED compositor control nibble (line F for all six). */
#include "raw_common.h"

/* returns the finalised SAT word-0 (D0). r = ActorRecord, program_control = D0 in. */
uint16_t arcade_3c9e8(uint8_t *r, uint16_t program_control){
    if ((B(r,0x27) & 0x40) == 0) return program_control;         /* bit6 clear: keep control byte */
    return (uint16_t)((program_control & 0xFF00) | B(r,0x27));   /* bit6 set: low byte := +0x27 */
}
