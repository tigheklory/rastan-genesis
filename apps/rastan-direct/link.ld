ENTRY(_start)

SECTIONS
{
  . = 0x000000;

  .text.boot :
  {
    *(.text.boot)
  }

  . = 0x00070000;

  .text.wrapper :
  {
    *(.text .text.*)
    *(.rodata .rodata.*)
    *(.data .data.*)
  }

  .bss 0xFF0000 (NOLOAD) :
  {
    *(.bss .bss.*)
    *(COMMON)
  }
}
