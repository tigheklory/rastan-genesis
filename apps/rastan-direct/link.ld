ENTRY(_start)

SECTIONS
{
  . = 0x000000;

  .text :
  {
    *(.text.boot)
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
