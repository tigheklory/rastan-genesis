/*
 * Rastan arcade Z80 sound driver — maintained semantic reference (AUDIO-015).
 *
 * This is instruction-backed pseudocode, not a Genesis build input and not a
 * claim that the complete 0x0000..0x3fff program has been decompiled. Original
 * addresses are retained in function names and comments. Unknown helper tails
 * remain explicitly named rather than filled with guessed behavior.
 *
 * Authority: build/regions/audiocpu.bin and
 * build/audio/audiocpu.disasm.txt. Hardware: YM2151 address/data 9000/9001,
 * PC060HA A000/A001, MSM5205 address/start/stop B000/C000/D000.
 */
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Reference-machine adapters. They make hardware effects explicit without
 * pretending normal C pointers reproduce Z80 memory-mapped I/O. */
uint8_t z80_mem_read(uint16_t address);
void z80_mem_write(uint16_t address, uint8_t value);
uint16_t z80_mem_read16le(uint16_t address);
void z80_mem_write16le(uint16_t address, uint16_t value);
void z80_enable_interrupts(void);
void z80_disable_interrupts(void);

enum {
    YM_ADDR = 0x9000, YM_DATA_STATUS = 0x9001,
    PC060HA_MASTER = 0xA000, PC060HA_SLAVE = 0xA001,
    ADPCM_ADDRESS = 0xB000, ADPCM_START = 0xC000, ADPCM_STOP = 0xD000,
    PRIMARY_HEAD = 0x8F00, PRIMARY_TAIL = 0x8F01, PRIMARY_DATA = 0x8F02,
    SECONDARY_HEAD = 0x8E80, SECONDARY_TAIL = 0x8E81, SECONDARY_DATA = 0x8E82
};

/* 0x158C: exact YM2151 writer. B supplies the register in the Z80 routine;
 * A supplies data; HL conventionally points to 0x9000. */
void z80_ym2151_write_158c(uint8_t reg, uint8_t data)
{
    while (z80_mem_read(YM_DATA_STATUS) & 0x80) {}
    z80_mem_write(YM_ADDR, reg);
    while (z80_mem_read(YM_DATA_STATUS) & 0x80) {}
    z80_mem_write(YM_DATA_STATUS, data);
}

/* 0x00C0: primary 16-slot enqueue. The original advances head first and, on
 * collision, advances tail: it overwrites the oldest item. Carry is set only
 * for command classes >= F0, which the NMI handles in its inline path. */
bool z80_ring16_enqueue_00c0(uint8_t command)
{
    uint8_t next, tail;
    if (command >= 0xF0)
        return false;                       /* original SCF return */
    tail = z80_mem_read(PRIMARY_TAIL);
    next = (z80_mem_read(PRIMARY_HEAD) + 1) & 0x0F;
    if (next == tail)
        ++tail;
    z80_mem_write(PRIMARY_HEAD, next);
    z80_mem_write(PRIMARY_TAIL, tail & 0x0F);
    z80_mem_write(PRIMARY_DATA + next, command);
    return true;                            /* original AND A clears carry */
}

/* 0x00E9: secondary 32-slot overwrite-oldest ring. */
void z80_ring32_enqueue_00e9(uint8_t value)
{
    uint8_t tail = z80_mem_read(SECONDARY_TAIL);
    uint8_t next = (z80_mem_read(SECONDARY_HEAD) + 1) & 0x1F;
    if (next == tail)
        ++tail;
    z80_mem_write(SECONDARY_HEAD, next);
    z80_mem_write(SECONDARY_TAIL, tail & 0x1F);
    z80_mem_write(SECONDARY_DATA + next, value);
}

static void primary_inline_f0_fe(uint8_t command)
{
    uint8_t tail = z80_mem_read(PRIMARY_TAIL);
    uint8_t next = (z80_mem_read(PRIMARY_HEAD) + 1) & 0x0F;
    if (next == tail)
        ++tail;
    z80_mem_write(PRIMARY_HEAD, next);
    z80_mem_write(PRIMARY_TAIL, tail & 0x0F);
    z80_mem_write(PRIMARY_DATA + next, command);
}

/* 0x0066: exact PC060HA NMI receive shape. Two low-nibble reads reconstruct
 * one byte. Every byte enters the secondary ring; every value below FF also
 * enters the primary command ring. F0..FE use the NMI's inline enqueue because
 * 00C0 deliberately returns carry for that class. */
void z80_nmi_cmd_receive_0066(void)
{
    uint8_t command;
    z80_mem_write(PC060HA_MASTER, 5);
    z80_mem_write(PC060HA_SLAVE, 5);
    z80_mem_write(PC060HA_MASTER, 0);
    command  = z80_mem_read(PC060HA_SLAVE) & 0x0F;
    command |= (z80_mem_read(PC060HA_SLAVE) & 0x0F) << 4;
    if (!z80_ring16_enqueue_00c0(command) && command < 0xFF)
        primary_inline_f0_fe(command);
    z80_ring32_enqueue_00e9(command);
    z80_mem_write(PC060HA_MASTER, 6);
    z80_mem_write(PC060HA_SLAVE, 6);
}

/* Necessary callees whose lower-level arithmetic is independently indexed.
 * These declarations are explicit incompleteness, not fabricated bodies. */
void z80_sequence_tick_0479(void);
void z80_adpcm_stream_19a8(void);
void z80_song_select_02aa(uint8_t command);
void z80_control_e0_ef_0368(uint8_t command);
void z80_sfx_class_03e5(uint8_t command);
void z80_channel_install_02fe(uint8_t identifier, uint16_t descriptor,
                              uint8_t song_command);

/* 0x01C2: PC060HA housekeeping. It is not the musical clock. */
void z80_perframe_01c2(void)
{
    if (z80_mem_read(0x8F27) & 1) {
        uint8_t v = z80_mem_read(0x8F28);
        z80_mem_write(PC060HA_MASTER, 0);
        z80_mem_write(PC060HA_SLAVE, v);
        z80_mem_write(PC060HA_SLAVE, (v >> 4) | (v << 4));
        return;
    }
    z80_mem_write(PC060HA_MASTER, 4);
    if (!(z80_mem_read(PC060HA_SLAVE) & 4)) {
        z80_mem_write(PC060HA_MASTER, 0);
        z80_mem_write(PC060HA_SLAVE, 0xE0);
        z80_mem_write(PC060HA_SLAVE, 0x0E);
    }
}

/* 0x01F9, reached from IM1 vector 0038. YM timer A is the music clock.
 * Init programs 10=00,11=00,12=C0,14=35: 4MHz/(64*1024)=61.03515625 Hz.
 * Timer A service clears/reloads with reg14=15, advances FM sequencing and
 * ADPCM together, and optionally installs a pending timer-A reload. */
void z80_irq_timer_service_01f9(void)
{
    uint8_t status;
    do { status = z80_mem_read(YM_DATA_STATUS) & 3; } while (!status);
    if (status & 1) {
        uint16_t reload;
        z80_ym2151_write_158c(0x14, 0x15);
        z80_sequence_tick_0479();
        z80_adpcm_stream_19a8();
        if (z80_mem_read(0x8F22) & 1) {
            z80_mem_write(0x8F22, z80_mem_read(0x8F22) & 0xFE);
            reload = z80_mem_read16le(0x8F1F);
            z80_ym2151_write_158c(0x10, (uint8_t)(reload >> 2));
            z80_ym2151_write_158c(0x11, (uint8_t)reload & 3);
            z80_ym2151_write_158c(0x14, 0x15);
        }
    }
}

/* 0x0254 drains the primary queue completely on each main-loop pass. */
void z80_command_dispatch_0254(void)
{
    z80_mem_write(PC060HA_MASTER, 5);
    z80_mem_write(PC060HA_SLAVE, 5);
    for (;;) {
        uint8_t tail = z80_mem_read(PRIMARY_TAIL);
        uint8_t command;
        if (tail == z80_mem_read(PRIMARY_HEAD))
            break;
        tail = (tail + 1) & 0x0F;
        z80_mem_write(PRIMARY_TAIL, tail);
        command = z80_mem_read(PRIMARY_DATA + tail);
        if (command < 0xE0) {
            if (z80_mem_read(0x8F27) & 1)
                z80_mem_write(0x8F28, command);
            else if (command < 0x2C)
                z80_song_select_02aa(command);
        } else if (command < 0xF0) {
            z80_control_e0_ef_0368(command);
        } else if (command < 0xFF) {
            z80_sfx_class_03e5(command);
        }
    }
    z80_mem_write(PC060HA_MASTER, 6);
    z80_mem_write(PC060HA_SLAVE, 6);
}

/* 0x02AA: command -> table 2300 -> descriptor. For a counted descriptor,
 * high==0 republishes a direct command; otherwise the pair is a little-endian
 * subdescriptor pointer whose identifier is installed by 02FE. */
void z80_song_select_02aa(uint8_t command)
{
    uint16_t p = z80_mem_read16le(0x2300 + 2u * command);
    uint8_t lead = z80_mem_read(p);
    uint8_t i;
    z80_mem_write(PC060HA_MASTER, 6);
    z80_mem_write(PC060HA_SLAVE, 6);
    if (!lead)
        return;
    if (lead >= 0x12) {
        z80_channel_install_02fe(lead, p, command);
        return;
    }
    for (i = 0; i < lead; ++i) {
        uint8_t low = z80_mem_read(++p);
        uint8_t high = z80_mem_read(++p);
        if (!high) {
            z80_ring16_enqueue_00c0(low);
        } else {
            uint16_t sub = (uint16_t)low | ((uint16_t)high << 8);
            uint8_t identifier = z80_mem_read(sub);
            if (identifier >= 0x12)
                z80_channel_install_02fe(identifier, sub, command);
        }
    }
}

/* 0x02FE semantic core. 82/83 select ADPCM state 8E00. Other identifiers are
 * normalized through the 0348 channel-state table. The existing active owner
 * may reject a lower-priority descriptor by comparing state+5 to the new
 * descriptor high nibble. */
void z80_channel_install_02fe(uint8_t identifier, uint16_t descriptor,
                              uint8_t song_command)
{
    uint16_t state;
    uint8_t normalized;
    if (!z80_mem_read(0x8F26))
        return;
    if (identifier >= 0xF0) {
        /* 0395 performs paired music/SFX takeover and restoration setup. */
        return;
    }
    normalized = identifier & 0xFE;
    if (normalized == 0x82) {
        state = 0x8E00;
    } else {
        uint8_t index = normalized - 0x8C;
        if (index >= 0x20)
            return;
        state = z80_mem_read16le(0x0348 + index);
    }
    if ((z80_mem_read(state) & 2) &&
        z80_mem_read(state + 5) >= (z80_mem_read(descriptor + 1) & 0xF0))
        return;
    z80_mem_write(state, 1);
    z80_mem_write16le(state + 1, descriptor);
    z80_mem_write(state + 3, song_command);
}

/* 0x03E5: exact computed dispatch shape. Table 041B contains 15 LE handlers:
 * F0 -> 03F7, F1..F3 -> 0408, F4..FE -> the table's default handler. */
void z80_sfx_class_03e5(uint8_t command)
{
    uint16_t handler = z80_mem_read16le(0x041B + 2u * (command - 0xF0));
    /* Semantic call through original Z80 address; handler details remain
     * CONTROL_FLOW_VERIFIED rather than falsely marked complete. */
    (void)handler;
}

/* 0x0479 orchestration recovered. Eight 0x100-stride music blocks at 8000..
 * 8700 are paired with eight SFX blocks at 8080..8780. Music ticks first.
 * Active SFX marks the channel-owned bit in 8F1C; when it ends, the music
 * block is dirtied for register restoration while its sequence has continued
 * to progress. Full note/control arithmetic lives in 0764/09A6/0A56. */
void z80_sequence_tick_0479(void)
{
    unsigned channel;
    uint8_t owned = z80_mem_read(0x8F1C);
    for (channel = 0; channel < 8; ++channel) {
        uint16_t music = 0x8000 + (uint16_t)channel * 0x100;
        uint16_t sfx = music + 0x80;
        /* sequence_channel_tick_12ed/music_publish_1366 are retained as named
         * dependencies because their detailed register math is not COMPLETE. */
        if (z80_mem_read(music) & 2) {
            owned |= (uint8_t)(1u << channel);
        } else {
            if ((owned & (1u << channel)) && (z80_mem_read(sfx) & 2)) {
                owned &= (uint8_t)~(1u << channel);
                z80_mem_write(sfx + 0x0F, 7);
                z80_mem_write(sfx + 0x12, z80_mem_read(sfx + 0x12) | 0x80);
                if (z80_mem_read(sfx) & 0x80)
                    z80_mem_write(sfx + 0x12, z80_mem_read(sfx + 0x12) | 0x40);
            }
        }
    }
    z80_mem_write(0x8F1C, owned);
}

/* 0x09A6/0x0A56 grammar summary, instruction-backed but not COMPLETE:
 * - state+0B/0C is the sequence pointer; state+13 is duration countdown.
 * - zero event calls 08AC (rest/termination path).
 * - a nonzero duration is copied to +13 and gate length derived into +15.
 * - 0A56 consumes bytes recursively. bit7 clear returns a note/event byte.
 * - bit7 set, low nibble < C selects one of 12 pitch entries at 0B2C and
 *   updates +1A..+1E; low nibble >= C dispatches through table 0AEC.
 * - handlers update pointer, instrument, volume/pitch, branch/loop state,
 *   key-on/off dirty flags, and termination. Exact per-opcode naming remains
 *   CONTROL_FLOW_VERIFIED and is intentionally not guessed here.
 */

/* 0x19A8/0x1A00: MSM5205 is advanced on the same timer-A tick as FM. State is
 * rooted at 8E00; sample metadata is read from table 2400. B000 receives the
 * sample address, C000 starts, D000 stops. This proves a future Genesis design
 * must reserve a timed PCM/DAC service independently of music channel state. */
void z80_adpcm_stream_19a8(void)
{
    if (!(z80_mem_read(0x8E00) & 1))
        return;
    /* Detailed nibble/length arithmetic below this proven hardware contract
     * remains CONTROL_FLOW_VERIFIED; no invented sample identity is supplied. */
}

/* 0x010B, semantically bounded form. The real routine initializes PC060HA,
 * clears 8000..8FFF, sets channel flags, installs YM timers, then loops. */
void z80_main_010b(void)
{
    uint16_t p;
    z80_disable_interrupts();
    z80_mem_write(PC060HA_MASTER, 5);
    z80_mem_write(PC060HA_SLAVE, 5);
    z80_mem_write(PC060HA_MASTER, 0);
    (void)z80_mem_read(PC060HA_SLAVE);
    (void)z80_mem_read(PC060HA_SLAVE);
    for (p = 0x8000; p != 0x9000; ++p)
        z80_mem_write(p, 0);
    z80_mem_write(PC060HA_MASTER, 4);
    z80_mem_write(PC060HA_SLAVE, 0);
    z80_mem_write(ADPCM_STOP, 0);
    for (p = 0x8010; p <= 0x8710; p += 0x100)
        z80_mem_write(p, 0x0F);
    z80_mem_write(0x8806, 0x9D);
    z80_mem_write16le(0x8F1F, 0);
    z80_ym2151_write_158c(0x10, 0x00);
    z80_ym2151_write_158c(0x11, 0x00);
    z80_mem_write(0x8F21, 0xC0);
    z80_ym2151_write_158c(0x12, 0xC0);
    z80_ym2151_write_158c(0x14, 0x35);
    z80_enable_interrupts();
    for (;;) {
        z80_disable_interrupts();
        z80_ym2151_write_158c(0x1B, z80_mem_read(0x8F23) | 0x40);
        z80_command_dispatch_0254();
        z80_enable_interrupts();
        z80_perframe_01c2();
    }
}
