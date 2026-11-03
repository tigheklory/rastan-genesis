#include "genesis.h"

__attribute__((externally_visible))
const ROMHeader rom_header = {
#if (ENABLE_BANK_SWITCH != 0)
    "SEGA SSF        ",
#elif (MODULE_MEGAWIFI != 0)
    "SEGA MEGAWIFI   ",
#else
    "SEGA MEGA DRIVE ",
#endif
    "(C)TAITO 1987   ",
    "RASTAN                                          ",
    "RASTAN                                          ",
    "GM RASTAN-0111",
    0x000,
    "J               ",
    0x00000000,
#if (ENABLE_BANK_SWITCH != 0)
    0x003FFFFF,
#else
    0x000FFFFF,
#endif
    0xE0FF0000,
    0xE0FFFFFF,
    "\x00\x00",
    0x0000,
    0x00000000,
    0x00000000,
    "            ",
    "DEMONSTRATION PROGRAM                   ",
    "JUE             "
};
