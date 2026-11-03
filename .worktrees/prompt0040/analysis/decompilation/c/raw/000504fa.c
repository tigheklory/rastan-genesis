/* ORIGINAL ARCADE PC: 0x000504FA scene scroll-state initializer.
 * RECONSTRUCTED_FROM_68000. COMPLETE. NOT original Taito source. */
#include <stdint.h>

typedef struct SceneScrollRecord504fa {
    uint16_t scroll_y_10ae_and_x_10ec;
    uint16_t scroll_10b0_and_10ee;
    uint16_t direction_10b8;
    uint16_t field_10ba;
    uint16_t camera_x_10be;
    uint16_t camera_y_10c0;
} SceneScrollRecord504fa;

extern const SceneScrollRecord504fa table_50850[];
extern uint16_t g_prog13e;
extern uint16_t g_scroll_y_10ae, g_scroll_x_10ec;
extern uint16_t g_scroll_10b0, g_scroll_10ee;
extern uint16_t g_direction_10b8, g_field_10ba;
extern uint16_t g_camera_x_10be, g_camera_y_10c0;

void arcade_504fa(void)
{
    const SceneScrollRecord504fa *r = &table_50850[g_prog13e];
    g_scroll_y_10ae = g_scroll_x_10ec = r->scroll_y_10ae_and_x_10ec;
    g_scroll_10b0 = g_scroll_10ee = r->scroll_10b0_and_10ee;
    g_direction_10b8 = r->direction_10b8;
    g_field_10ba = r->field_10ba;
    g_camera_x_10be = r->camera_x_10be;
    g_camera_y_10c0 = r->camera_y_10c0;
}
