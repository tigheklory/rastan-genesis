#include "startup_hooks.h"

#include <stddef.h>
#include <string.h>

#define GENESISTAN_DIP1_FACTORY 0xFE
#define GENESISTAN_DIP2_FACTORY 0xFF

static uint16_t *map_word_window(GenesistanStartupRuntime *runtime, uint32_t address)
{
    if ((address >= 0x00200000) && (address < 0x00204000)) {
        return &runtime->ram_200000_words[(address - 0x00200000) >> 1];
    }
    if ((address >= 0x0010C000) && (address < 0x00110000)) {
        return &runtime->workram_words[(address - 0x0010C000) >> 1];
    }
    if ((address >= 0x00C00000) && (address < 0x00C01000)) {
        return &runtime->text_c00000_words[(address - 0x00C00000) >> 1];
    }
    if ((address >= 0x00C08000) && (address < 0x00C09000)) {
        return &runtime->text_c08000_words[(address - 0x00C08000) >> 1];
    }
    if ((address >= 0x00C04000) && (address < 0x00C06000)) {
        return &runtime->text_c04000_words[(address - 0x00C04000) >> 1];
    }
    if ((address >= 0x00C0C000) && (address < 0x00C0E000)) {
        return &runtime->text_c0c000_words[(address - 0x00C0C000) >> 1];
    }

    return NULL;
}

void genesistan_startup_runtime_reset(GenesistanStartupRuntime *runtime)
{
    memset(runtime, 0, sizeof(*runtime));
    runtime->dip_bank_1 = GENESISTAN_DIP1_FACTORY;
    runtime->dip_bank_2 = GENESISTAN_DIP2_FACTORY;
}

uint8_t genesistan_startup_read8(GenesistanStartupRuntime *runtime, uint32_t address)
{
    switch (address) {
    case 0x00390009:
        return runtime->dip_bank_1;
    case 0x0039000B:
        return runtime->dip_bank_2;
    case 0x003E0003:
        return runtime->reg_3e0003;
    default: {
        uint16_t *word = map_word_window(runtime, address & ~1U);
        if (word == NULL) {
            return 0;
        }
        if ((address & 1U) == 0) {
            return (uint8_t)((*word >> 8) & 0xFF);
        }
        return (uint8_t)(*word & 0xFF);
    }
    }
}

uint16_t genesistan_startup_read16(GenesistanStartupRuntime *runtime, uint32_t address)
{
    switch (address) {
    case 0x0005FF9E:
        return runtime->service_word;
    case 0x003C0000:
        return runtime->reg_3c0000;
    default: {
        uint16_t *word = map_word_window(runtime, address);
        if (word == NULL) {
            return 0;
        }
        return *word;
    }
    }
}

void genesistan_startup_write8(
    GenesistanStartupRuntime *runtime, uint32_t address, uint8_t value
)
{
    switch (address) {
    case 0x003E0001:
        runtime->reg_3e0001 = value;
        return;
    case 0x003E0003:
        runtime->reg_3e0003 = value;
        return;
    default: {
        uint16_t *word = map_word_window(runtime, address & ~1U);
        if (word == NULL) {
            return;
        }
        if ((address & 1U) == 0) {
            *word = (uint16_t)((*word & 0x00FF) | ((uint16_t)value << 8));
        } else {
            *word = (uint16_t)((*word & 0xFF00) | value);
        }
        return;
    }
    }
}

void genesistan_startup_write16(
    GenesistanStartupRuntime *runtime, uint32_t address, uint16_t value
)
{
    switch (address) {
    case 0x00C50000:
        runtime->reg_c50000 = value;
        return;
    case 0x00D01BFE:
        runtime->reg_d01bfe = value;
        return;
    case 0x00350008:
        runtime->reg_350008 = value;
        return;
    case 0x00380000:
        runtime->reg_380000 = value;
        return;
    case 0x003C0000:
        runtime->reg_3c0000 = value;
        return;
    default: {
        uint16_t *word = map_word_window(runtime, address);
        if (word == NULL) {
            return;
        }
        *word = value;
        return;
    }
    }
}
