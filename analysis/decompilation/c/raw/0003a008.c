/* ORIGINAL ARCADE PC: 0x0003A008  L5/VBlank interrupt service routine (the per-frame engine spine).
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE. Byte-faithful transcription of the authoritative
 * arcade program (build/maincpu.disasm.txt, variant world_rev1). CHECKPOINT H21.
 *
 * Rastan is INTERRUPT-DRIVEN: after reset init (0x3AE86) the 68000 sits in the idle loop 0x3A080
 * (jsr 0x510C6; bra self). All per-frame work happens here, in the vertical-blank ISR whose vector
 * target is 0x3A008. This routine is short and closes cleanly; the 8 game-state handlers it
 * dispatches to remain on the code frontier (INTERRUPTS_TIMING_VBLANK_SYSTEM / per-state files).
 *
 * EXACT DISASSEMBLY (build/maincpu.disasm.txt):
 *   3a008: 007c 0f00        oriw  #0x0f00,%sr           ; mask interrupts to level 7 (enter critical)
 *   3a00c: 4279 0035 0008   clrw  0x350008              ; acknowledge the interrupt (int-ack latch)
 *   3a012: 33c0 003c 0000   movew %d0,0x3c0000          ; push D0 (raster/beam latch) to VDP-side reg
 *   3a018: 302d 0002        movew %a5@(2),%d0           ; D0 = A5+0x02  (frame/phase sub-state word)
 *   3a01c: 0c40 0002        cmpiw #2,%d0
 *   3a020: 651c             bcss  0x3a03e               ; if (unsigned)A5+0x02 < 2  -> skip actor pass
 *   3a022: 0c40 0004        cmpiw #4,%d0
 *   3a026: 6416             bccs  0x3a03e               ; if (unsigned)A5+0x02 >= 4 -> skip actor pass
 *   3a028: 6100 00fc        bsrw  0x3a126               ; (2 or 3) input/attract-or-play pre-pass
 *   3a02c: 4a6d 0000        tstw  %a5@(0)               ; A5+0x00 = master game-state selector
 *   3a030: 670c             beqs  0x3a03e               ; if state 0 -> skip actor update
 *   3a032: 0c6d 0001 1394   cmpiw #1,%a5@(0x1394)       ; A5+0x1394 = "actors frozen" flag
 *   3a038: 6704             beqs  0x3a03e               ; if frozen==1 -> skip actor update
 *   3a03a: 6100 7ef4        bsrw  0x41f30               ; ACTOR UPDATE (whole live cast this frame)
 *   3a03e: 6100 0b3c        bsrw  0x3ab7c               ; pre-frame subsystem A (warm_restart_gate)
 *   3a042: 6100 0b9e        bsrw  0x3abe2               ; pre-frame subsystem B
 *   3a046: 6100 0060        bsrw  0x3a0a8               ; pre-frame subsystem C
 *   3a04a: 6100 4eae        bsrw  0x3eefa               ; pre-frame subsystem D
 *   3a04e: 6100 4f0c        bsrw  0x3ef5c               ; pre-frame subsystem E
 *   3a052: 487a 0020        pea   %pc@(0x3a074)         ; push return addr = 0x3a074 (RTE tail)
 *   3a056: 302d 0000        movew %a5@(0),%d0           ; D0 = master game-state (0..7)
 *   3a05a: d040             addw  %d0,%d0               ; *2 (word index)
 *   3a05c: 41fa 000e        lea   %pc@(0x3a06c),%a0     ; A0 = &dispatch_table
 *   3a060: d0c0             addaw %d0,%a0               ; A0 = &table[state]
 *   3a062: 3010             movew %a0@,%d0              ; D0 = table[state] (16-bit signed disp)
 *   3a064: 41fa 0006        lea   %pc@(0x3a06c),%a0     ; A0 = &dispatch_table (base again)
 *   3a068: d0c0             addaw %d0,%a0               ; A0 = base + disp = handler entry
 *   3a06a: 4ed0             jmp   %a0@                  ; TAIL-CALL the state handler; it RTEs via 0x3a074
 *
 * DISPATCH TABLE @0x3a06c (16-bit signed displacements from 0x3a06c; decoded from maincpu.bin):
 *   state0 word=0x0992 -> 0x3a9fe   state4 word=0x4eb9 -> 0x3ef25
 *   state1 word=0x0840 -> 0x3a8ac   state5 word=0x0005 -> 0x3a071
 *   state2 word=0x00ee -> 0x3a15a   state6 word=0x5ca2 -> 0x3fd0e
 *   state3 word=0x0b02 -> 0x3ab6e   state7 word=0x027c -> 0x3a2e8
 *
 * Ghidra confirms the same control flow (vector_1d_target_03a008), incl. the recovered indirect
 * jumptable warning at 0x3a06a. HW addresses: 0x350008 int-ack, 0x3c0000 VDP-side latch.
 */

/* Faithful C transcription (control flow 1:1 with the bytes above). A5 = 0x10C000 arcade work RAM. */
extern volatile unsigned short INT_ACK;      /* 0x350008 */
extern volatile unsigned short VDP_LATCH;    /* 0x3c0000 */
extern short A5[];                           /* arcade work RAM, word-addressed from 0x10C000 */

extern void pre_pass_2or3_3a126(void);       /* 0x3a126 */
extern void actor_update_41f30(void);        /* 0x41f30 */
extern void preframe_A_3ab7c(void);          /* 0x3ab7c */
extern void preframe_B_3abe2(void);          /* 0x3abe2 */
extern void preframe_C_3a0a8(void);          /* 0x3a0a8 */
extern void preframe_D_3eefa(void);          /* 0x3eefa */
extern void preframe_E_3ef5c(void);          /* 0x3ef5c */
extern void (*const vblank_state_dispatch[8])(void); /* logical view of table @0x3a06c */

void vblank_isr_3a008(unsigned short d0_beam)
{
    /* 3a008-3a012 */
    __asm__("");                 /* oriw #0x0f00,%sr : enter interrupt-masked critical section */
    INT_ACK = 0;                 /* 3a00c acknowledge */
    VDP_LATCH = d0_beam;         /* 3a012 push incoming D0 to VDP-side register */

    /* 3a018-3a03a : per-frame actor update, gated on sub-state, master-state, and freeze flag */
    unsigned short sub = (unsigned short)A5[0x02/2];   /* A5+0x02 */
    if (sub >= 2 && sub < 4) {                          /* 3a01c/3a022 window [2,4) */
        pre_pass_2or3_3a126();                          /* 3a028 */
        if (A5[0x00/2] != 0 && A5[0x1394/2] != 1) {     /* 3a02c master-state, 3a032 freeze flag */
            actor_update_41f30();                       /* 3a03a whole live cast */
        }
    }

    /* 3a03e-3a04e : five fixed pre-frame subsystems, every frame regardless of state */
    preframe_A_3ab7c();
    preframe_B_3abe2();
    preframe_C_3a0a8();
    preframe_D_3eefa();
    preframe_E_3ef5c();

    /* 3a052-3a06a : dispatch the master game-state handler (tail-call; handler RTEs via 0x3a074) */
    vblank_state_dispatch[A5[0x00/2]]();                /* table @0x3a06c, 8 entries */
    /* on real HW this path returns through the pushed 0x3a074 RTE tail */
}
