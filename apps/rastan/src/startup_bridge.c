#include "main.h"
#include <string.h>

#ifndef RASTAN_ENABLE_STARTUP_HOOK
#define RASTAN_ENABLE_STARTUP_HOOK 1
#endif

#if RASTAN_ENABLE_STARTUP_HOOK

volatile uint16_t genesistan_arcade_workram_words[0x2000];
volatile uint16_t genesistan_shadow_d00000_words[0x0400];
volatile uint16_t genesistan_shadow_c20000_words[2];
volatile uint16_t genesistan_shadow_c40000_words[2];

volatile uint16_t genesistan_shadow_reg_c50000;
volatile uint16_t genesistan_shadow_reg_d01bfe;
volatile uint16_t genesistan_shadow_reg_350008;
volatile uint16_t genesistan_shadow_reg_380000;
volatile uint16_t genesistan_shadow_reg_3c0000;
volatile uint8_t genesistan_shadow_input_390001;
volatile uint8_t genesistan_shadow_input_390003;
volatile uint8_t genesistan_shadow_input_390005;
volatile uint8_t genesistan_shadow_input_390007;
volatile uint8_t genesistan_shadow_reg_3e0001;
volatile uint8_t genesistan_shadow_reg_3e0003;
volatile uint8_t genesistan_shadow_dip1 = GENESISTAN_DIP1_FACTORY;
volatile uint8_t genesistan_shadow_dip2 = GENESISTAN_DIP2_FACTORY;
volatile uint16_t genesistan_shadow_service_word = GENESISTAN_SERVICE_FACTORY;
volatile uint16_t genesistan_startup_result_code = GENESISTAN_STARTUP_RESULT_NONE;
volatile uint8_t genesistan_sound_last_command;
volatile uint8_t genesistan_sound_last_low_nibble;
volatile uint8_t genesistan_sound_last_high_nibble;
volatile uint8_t genesistan_sound_status;
volatile uint16_t genesistan_sound_command_count;

static uint8_t build_player_input_byte(uint16_t state)
{
    uint8_t value = 0xFF;

    /* Arcade inputs are active-low. Keep the mapping simple and final-port-friendly. */
    if ((state & BUTTON_UP) != 0) value &= (uint8_t)~0x01;
    if ((state & BUTTON_DOWN) != 0) value &= (uint8_t)~0x02;
    if ((state & BUTTON_LEFT) != 0) value &= (uint8_t)~0x04;
    if ((state & BUTTON_RIGHT) != 0) value &= (uint8_t)~0x08;
    if ((state & BUTTON_B) != 0) value &= (uint8_t)~0x10;
    if ((state & BUTTON_C) != 0) value &= (uint8_t)~0x20;

    return value;
}

static uint8_t build_aux_input_byte(uint16_t state)
{
    uint8_t value = 0xFF;

    /*
     * The title/service-side code also probes 0x390005 bits 4..6.
     * Mirror the three Genesis face buttons into that auxiliary byte for now.
     */
    if ((state & BUTTON_B) != 0) value &= (uint8_t)~0x10;
    if ((state & BUTTON_C) != 0) value &= (uint8_t)~0x20;
    if ((state & BUTTON_A) != 0) value &= (uint8_t)~0x40;

    return value;
}

static uint8_t build_system_input_byte(uint16_t p1_state, uint16_t p2_state)
{
    uint8_t value = 0xFF;

    /* Proven from the title/front-end code: bit0=coin1, bit3=start1, bit4=start2. */
    if ((p1_state & BUTTON_A) != 0) value &= (uint8_t)~0x01;
    if ((p1_state & BUTTON_START) != 0) value &= (uint8_t)~0x08;
    if ((p2_state & BUTTON_START) != 0) value &= (uint8_t)~0x10;

    /*
     * Use an intentional combo for the service-side trigger so normal play inputs
     * do not accidentally wander into operator/test flows.
     */
    if ((p1_state & (BUTTON_A | BUTTON_B | BUTTON_C)) == (BUTTON_A | BUTTON_B | BUTTON_C))
        value &= (uint8_t)~0x04;

    return value;
}

void genesistan_refresh_arcade_inputs(void)
{
    const uint16_t p1_state = JOY_readJoypad(JOY_1);
    const uint16_t p2_state = JOY_readJoypad(JOY_2);

    genesistan_shadow_input_390001 = build_player_input_byte(p1_state);
    genesistan_shadow_input_390003 = build_player_input_byte(p2_state);
    genesistan_shadow_input_390005 = build_aux_input_byte(p1_state);
    genesistan_shadow_input_390007 = build_system_input_byte(p1_state, p2_state);
}

static void fill_words(volatile uint16_t *words, uint16_t count, uint16_t value)
{
    uint16_t i;

    for (i = 0; i < count; i++) {
        words[i] = value;
    }
}

static void fill_shadow_page_words(uint8_t page, uint16_t count, uint16_t value)
{
    uint16_t i;

    for (i = 0; i < count; i++) {
        shadow_write16(page, (uint16_t)(i * 2), value);
    }
}

void genesistan_reset_startup_shadows(uint8_t dip1, uint8_t dip2, uint16_t service_word)
{
    shadow_init();

    fill_words(genesistan_arcade_workram_words, 0x2000, 0);
    fill_words(genesistan_shadow_d00000_words, 0x0400, 0);
    fill_shadow_page_words(0, 0x2000, 0);
    fill_shadow_page_words(1, 0x2000, 0);
    fill_shadow_page_words(2, 0x2000, 0);
    fill_shadow_page_words(3, 0x2000, 0);
    fill_words(genesistan_shadow_c20000_words, 2, 0);
    fill_words(genesistan_shadow_c40000_words, 2, 0);

    genesistan_shadow_reg_c50000 = 0;
    genesistan_shadow_reg_d01bfe = 0;
    genesistan_shadow_reg_350008 = 0;
    genesistan_shadow_reg_380000 = 0;
    genesistan_shadow_reg_3c0000 = 0;
    genesistan_shadow_input_390001 = 0xFF;
    genesistan_shadow_input_390003 = 0xFF;
    genesistan_shadow_input_390005 = 0xFF;
    genesistan_shadow_input_390007 = 0xFF;
    genesistan_shadow_reg_3e0001 = 0;
    genesistan_shadow_reg_3e0003 = 0;
    genesistan_shadow_dip1 = dip1;
    genesistan_shadow_dip2 = dip2;
    genesistan_shadow_service_word = service_word;
    genesistan_startup_result_code = GENESISTAN_STARTUP_RESULT_NONE;
    genesistan_sound_last_command = 0;
    genesistan_sound_last_low_nibble = 0;
    genesistan_sound_last_high_nibble = 0;
    genesistan_sound_status = 0;
    genesistan_sound_command_count = 0;
    genesistan_refresh_arcade_inputs();
}

void genesistan_reclaim_launcher_wram(void)
{
    const uint8_t saved_dip1 = genesistan_shadow_dip1;
    const uint8_t saved_dip2 = genesistan_shadow_dip2;
    const uint16_t saved_service = genesistan_shadow_service_word;

    /*
     * Reclaim launcher-only state once we hand off to live game flow.
     * Keep DIP/service configuration intact so startup/game behavior stays stable.
     */
    memset((void *)genesistan_shadow_c20000_words, 0, sizeof(genesistan_shadow_c20000_words));
    memset((void *)genesistan_shadow_c40000_words, 0, sizeof(genesistan_shadow_c40000_words));
    genesistan_startup_result_code = GENESISTAN_STARTUP_RESULT_NONE;
    genesistan_sound_last_command = 0;
    genesistan_sound_last_low_nibble = 0;
    genesistan_sound_last_high_nibble = 0;
    genesistan_sound_status = 0;
    genesistan_sound_command_count = 0;

    genesistan_shadow_dip1 = saved_dip1;
    genesistan_shadow_dip2 = saved_dip2;
    genesistan_shadow_service_word = saved_service;
}

#else

void genesistan_reset_startup_shadows(uint8_t dip1, uint8_t dip2, uint16_t service_word)
{
    (void) dip1;
    (void) dip2;
    (void) service_word;
}

void genesistan_refresh_arcade_inputs(void)
{
}

void genesistan_reclaim_launcher_wram(void)
{
}

#endif
