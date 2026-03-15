#ifndef GENESISTAN_STARTUP_HOOKS_H
#define GENESISTAN_STARTUP_HOOKS_H

#include <stdint.h>

typedef struct GenesistanStartupRuntime {
    uint8_t dip_bank_1;
    uint8_t dip_bank_2;
    uint16_t service_word;

    uint16_t reg_c50000;
    uint16_t reg_d01bfe;
    uint16_t reg_350008;
    uint16_t reg_380000;
    uint16_t reg_3c0000;

    uint8_t reg_3e0001;
    uint8_t reg_3e0003;

    uint16_t ram_200000_words[0x2000];
    uint16_t workram_words[0x2000];

    /* Startup slice clears 0x1000 bytes at 0xC00000 / 0xC08000 and
       0x2000 bytes at 0xC04000 / 0xC0C000. */
    uint16_t text_c00000_words[0x0800];
    uint16_t text_c08000_words[0x0800];
    uint16_t text_c04000_words[0x1000];
    uint16_t text_c0c000_words[0x1000];
} GenesistanStartupRuntime;

void genesistan_startup_runtime_reset(GenesistanStartupRuntime *runtime);

uint8_t genesistan_startup_read8(GenesistanStartupRuntime *runtime, uint32_t address);
uint16_t genesistan_startup_read16(GenesistanStartupRuntime *runtime, uint32_t address);
void genesistan_startup_write8(
    GenesistanStartupRuntime *runtime, uint32_t address, uint8_t value
);
void genesistan_startup_write16(
    GenesistanStartupRuntime *runtime, uint32_t address, uint16_t value
);

#endif
