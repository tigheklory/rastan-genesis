wp d00000,800,w,,{ printf "WP_D00 cyc=%d pc=%X addr=%X pre=%X post=%X d0=%X d1=%X d2=%X d3=%X d4=%X d5=%X d6=%X d7=%X a0=%X a1=%X a2=%X a3=%X a4=%X a5=%X a6=%X sp=%X sr=%X\n",totalcycles(),pc,wpaddr,wpdata,w@wpaddr,d0,d1,d2,d3,d4,d5,d6,d7,a0,a1,a2,a3,a4,a5,a6,sp,sr ; go }
bp 3AD44,,{ printf "BP_03AD44_FILL_PRIMITIVE cyc=%d pc=%X d0=%X a0=%X sp=%X sr=%X\n",totalcycles(),pc,d0,a0,sp,sr ; go }
bp 3C9C2,,{ printf "BP_03C9C2_WORD_LOOP cyc=%d pc=%X d0=%X a1=%X sp=%X sr=%X\n",totalcycles(),pc,d0,a1,sp,sr ; go }
bp 510EA,,{ printf "BP_510EA_FU1_TARGET cyc=%d pc=%X d0=%X sp=%X sr=%X\n",totalcycles(),pc,d0,sp,sr ; go }
bp 510F4,,{ printf "BP_510F4_FU1_TARGET cyc=%d pc=%X d0=%X sp=%X sr=%X\n",totalcycles(),pc,d0,sp,sr ; go }
go
