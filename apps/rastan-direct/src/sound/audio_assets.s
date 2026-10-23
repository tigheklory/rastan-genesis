    .section .audio,"a"
    .balign 0x8000

    .global genesistan_audio_aggressive_start
    .global genesistan_audio_aggressive_loop
    .global genesistan_audio_aggressive_end

/* Generated files are build outputs from the user-supplied arcade capture and
 * persisted Audio Composer profile. They are intentionally not committed. */
genesistan_audio_aggressive_start:
    .incbin "out/aggressive_world_intro.bin"
genesistan_audio_aggressive_loop:
    .incbin "out/aggressive_world_loop.bin"
genesistan_audio_aggressive_end:
