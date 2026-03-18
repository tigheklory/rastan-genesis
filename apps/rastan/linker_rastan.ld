OUTPUT_ARCH(m68k)
SEARCH_DIR(.)
__DYNAMIC = 0;

MEMORY
{
	rom (rx) : ORIGIN = 0x00000000, LENGTH = 0xE0000000
	ram : ORIGIN = 0xE0FF0000, LENGTH = 0x00010000
	SRAM (w!x) : ORIGIN = 0x200000, LENGTH = 64K
}

PROVIDE(__stack = 0xE1000000);
PROVIDE(__GENESISTAN_APP_ROM_BASE = 0x00200000);
genesistan_shadow_c00000_words = 0x00200000;
genesistan_shadow_c04000_words = 0x00204000;
genesistan_shadow_c08000_words = 0x00208000;
genesistan_shadow_c0c000_words = 0x0020C000;

SECTIONS
{
  .boot 0x00000000 :
  {
    KEEP(*(.text.keepboot))
  } > rom

  .text __GENESISTAN_APP_ROM_BASE :
  {
    *(.text.*) *(.text)
    . = ALIGN(0x4);
    __CTOR_LIST__ = .;
    LONG((__CTOR_END__ - __CTOR_LIST__) / 4 - 2)
    *(.ctors)
    LONG(0)
    __CTOR_END__ = .;
    __DTOR_LIST__ = .;
    LONG((__DTOR_END__ - __DTOR_LIST__) / 4 - 2)
    *(.dtors)
    LONG(0)
    __DTOR_END__ = .;

    *(.rodata .rodata.*)
    *(.gcc_except_table .gcc_except_table.*)

    . = ALIGN(0x4);
    __INIT_SECTION__ = .;
    *(.init)
    SHORT(0x4E75)	/* rts */

    __FINI_SECTION__ = .;
    *(.fini)
    SHORT(0x4E75)	/* rts */

    _etext = .;
    *(.lit)

    *(.rodata_bin)
    *(.rodata_binf)
  } > rom

  .data 0xE0FF0000 :
  AT ( ADDR(.text) + SIZEOF(.text) )
  {
    *(.got.plt) *(.got)
    *(.shdata)
    *(.data .data.*)
    *(.ramprog .ramprog.*)
    _edata = .;
  } > ram
  _sdata = SIZEOF(.data);
  _stext = LOADADDR(.data);

  .bss 0xE0FF0000 + SIZEOF(.data) :
  {
    _start = .;
    *(.shbss)
    *(.bss .bss.*)
    *(COMMON)
    _bend = .;
  } > ram

  .stab 0 (NOLOAD) :
  {
    *(.stab)
  }

  .stabstr 0 (NOLOAD) :
  {
    *(.stabstr)
  }

  .eh_frame 0 (NOLOAD) :
  {
    *(.eh_frame)
  }
}
