#ifndef GENESISTAN_STARTUP_COMMON_ROM_MAIN_H
#define GENESISTAN_STARTUP_COMMON_ROM_MAIN_H

#include <genesis.h>

#define GENESISTAN_DIP1_FACTORY 0xFE
#define GENESISTAN_DIP2_FACTORY 0xFF
#define GENESISTAN_SERVICE_FACTORY 0xFFFF

#define GENESISTAN_STARTUP_RESULT_NONE 0
#define GENESISTAN_STARTUP_RESULT_NORMAL 1
#define GENESISTAN_STARTUP_RESULT_TEST 2

extern volatile uint16_t genesistan_shadow_200000_words[0x400];
extern volatile uint16_t genesistan_arcade_workram_words[0x2000];
extern volatile uint16_t genesistan_shadow_d00000_words[0x400];
extern volatile uint16_t genesistan_shadow_c00000_words[0x800];
extern volatile uint16_t genesistan_shadow_c08000_words[0x2000];
extern volatile uint16_t genesistan_shadow_c04000_words[0x1000];
extern volatile uint16_t genesistan_shadow_c0c000_words[0x1000];
extern volatile uint16_t genesistan_shadow_c20000_words[2];
extern volatile uint16_t genesistan_shadow_c40000_words[2];

extern volatile uint16_t genesistan_shadow_reg_c50000;
extern volatile uint16_t genesistan_shadow_reg_d01bfe;
extern volatile uint16_t genesistan_shadow_reg_350008;
extern volatile uint16_t genesistan_shadow_reg_380000;
extern volatile uint16_t genesistan_shadow_reg_3c0000;

extern volatile uint8_t genesistan_shadow_reg_3e0001;
extern volatile uint8_t genesistan_shadow_reg_3e0003;
extern volatile uint8_t genesistan_shadow_dip1;
extern volatile uint8_t genesistan_shadow_dip2;
extern volatile uint16_t genesistan_shadow_service_word;
extern volatile uint16_t genesistan_startup_result_code;
extern volatile uint16_t genesistan_panic_code;
extern volatile uint32_t genesistan_panic_original_sp;
extern volatile uint16_t genesistan_panic_frame_words[8];
extern volatile uint16_t genesistan_panic_entered;
extern volatile uint8_t genesistan_exception_stack[512];

void genesistan_run_original_startup_common(void);
void genesistan_reset_startup_shadows(uint8_t dip1, uint8_t dip2, uint16_t service_word);
void genesistan_exception_enter(void);

#endif
