/* ORIGINAL ARCADE PC: 0x0003BB48 — generic PC080SN text writer.
 * RECONSTRUCTED_FROM_68000. Status: COMPLETE for 0x3BB48..0x3BB7A.
 * Positive selector: write descriptor attribute + character code pairs.
 * Negative selector: write the same count as attribute + ASCII spaces. */
#include <stdint.h>

typedef struct ArcadeTextDescriptor {
    uint32_t destination;
    uint16_t attribute;
    const uint8_t *text;
} ArcadeTextDescriptor;

extern const ArcadeTextDescriptor *arcade_text_descriptor(uint16_t index);
extern void arcade_pc080sn_write(uint32_t address, uint16_t value);

void arcade_3bb48_text(uint16_t selector)
{
    const ArcadeTextDescriptor *desc =
        arcade_text_descriptor((uint16_t)(selector & 0x007f));
    uint32_t destination = desc->destination;
    const uint8_t *text = desc->text;
    const uint16_t code = (selector & 0x0080) ? 0x0020 : 0;

    while (*text != 0) {
        arcade_pc080sn_write(destination, desc->attribute);
        arcade_pc080sn_write(destination + 2,
            (selector & 0x0080) ? code : *text);
        destination += 4;
        text++;
    }
}
