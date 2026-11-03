    .section .rodata,"a"
    .global z80_driver_start
    .global z80_driver_end

/* AUDIO-015 permanent driver, assembled independently as real Z80 code and
 * embedded in the Genesis wrapper. Generated music assets are separate ROM
 * objects and are not copied into the 8 KiB Z80 RAM image. */
z80_driver_start:
    .incbin "out/z80_driver.bin"
z80_driver_end:
