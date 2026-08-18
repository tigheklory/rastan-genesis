ENTRY(_start)

SECTIONS
{
  . = 0x000000;

  .text.boot :
  {
    *(.text.boot)
  }

  /* Pin the postpatch's preserved-low-ROM boundary to the Build0292/Build0287
   * value.  postpatch_startup_rom.py splices the arcade copy at
   * preserve_low_rom_end = max(0x400, genesistan_crash_handler_end).  The crash
   * handler now lives in the high .text.crash section (below), but the arcade
   * splice must stay exactly where Build0292 had it (0x117E), so this symbol is
   * pinned here rather than following the handler's real end.  The freed low
   * area 0x0003A4..0x00117E becomes objcopy zero-fill (no normal code moves). */
  genesistan_crash_handler_end = 0x0000117E;

  . = 0x00070000;

  .text.wrapper :
  {
    *(.text .text.*)
    *(.rodata .rodata.*)
    *(.data .data.*)
  }

  /* Dedicated high-ROM crash section, placed AFTER all existing normal ROM
   * content (boot, arcade copy, and Genesis-only .text.wrapper).  The old
   * Build0287 crash handler (stubs + common + renderer + font/strings) lives
   * here.  Because it is above every normal symbol, future growth of the crash
   * handler extends only the high ROM end and never moves normal code or the
   * arcade splice.  The 68000 vector table (in .text.boot) holds absolute 32-bit
   * pointers straight to these high-ROM stubs. */
  . = ALIGN(0x1000);
  .crash :
  {
    *(.crash)
  }

  .bss 0xFF4000 (NOLOAD) :
  {
    *(.bss .bss.*)
    *(COMMON)
  }
}
