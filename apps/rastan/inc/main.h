#ifndef RASTAN_APP_MAIN_H
#define RASTAN_APP_MAIN_H

#include <genesis.h>

#define GENESISTAN_DIP1_FACTORY 0xFE
#define GENESISTAN_DIP2_FACTORY 0xFF
#define GENESISTAN_SERVICE_FACTORY 0xFFFF

#define GENESISTAN_STARTUP_RESULT_NONE 0
#define GENESISTAN_STARTUP_RESULT_NORMAL 1
#define GENESISTAN_STARTUP_RESULT_TEST 2

extern volatile uint16_t genesistan_arcade_workram_words[0x2000];
extern volatile uint16_t genesistan_shadow_d00000_words[0x0400];
extern volatile uint16_t genesistan_shadow_c00000_words[0x2000];
extern volatile uint16_t genesistan_shadow_c04000_words[0x2000];
extern volatile uint16_t genesistan_shadow_c08000_words[0x2000];
extern volatile uint16_t genesistan_shadow_c0c000_words[0x2000];
extern volatile uint16_t genesistan_shadow_c20000_words[2];
extern volatile uint16_t genesistan_shadow_c40000_words[2];

extern volatile uint16_t genesistan_shadow_reg_c50000;
extern volatile uint16_t genesistan_shadow_reg_d01bfe;
extern volatile uint16_t genesistan_shadow_reg_350008;
extern volatile uint16_t genesistan_shadow_reg_380000;
extern volatile uint16_t genesistan_shadow_reg_3c0000;
extern volatile uint8_t genesistan_shadow_input_390001;
extern volatile uint8_t genesistan_shadow_input_390003;
extern volatile uint8_t genesistan_shadow_input_390005;
extern volatile uint8_t genesistan_shadow_input_390007;
extern volatile uint8_t genesistan_shadow_reg_3e0001;
extern volatile uint8_t genesistan_shadow_reg_3e0003;
extern volatile uint8_t genesistan_shadow_dip1;
extern volatile uint8_t genesistan_shadow_dip2;
extern volatile uint16_t genesistan_shadow_service_word;
extern volatile uint16_t genesistan_startup_result_code;
extern volatile uint8_t genesistan_sound_last_command;
extern volatile uint8_t genesistan_sound_last_low_nibble;
extern volatile uint8_t genesistan_sound_last_high_nibble;
extern volatile uint8_t genesistan_sound_status;
extern volatile uint16_t genesistan_sound_command_count;

void genesistan_run_original_startup_common(void);
void genesistan_run_original_frontend_tick(void);
void genesistan_reset_startup_shadows(uint8_t dip1, uint8_t dip2, uint16_t service_word);
void genesistan_anchor_required_symbols(void);
void genesistan_init_workram_direct(uint8_t dip1, uint8_t dip2);
void genesistan_refresh_arcade_inputs(void);
void genesistan_reclaim_launcher_wram(void);
void genesistan_sound_send_command(void);
void genesistan_sound_read_status(void);
void shadow_init(void);
void shadow_write16(uint8_t page, uint16_t offset, uint16_t value);
uint16_t shadow_read16(uint8_t page, uint16_t offset);

#endif
