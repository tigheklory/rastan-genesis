    .section .rodata,"a"
    .align 2
    .global rastan_pc090oj
rastan_pc090oj:
    .incbin "../../build/pc090oj_genesis.bin"

    .global pc090oj_slot_lut
    .align 2
pc090oj_slot_lut:
    .incbin "../../build/pc090oj_slot_lut.bin"
