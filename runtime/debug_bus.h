#ifndef GENESISTAN_DEBUG_BUS_H
#define GENESISTAN_DEBUG_BUS_H

#ifndef _GENESIS_H_
#include <stdint.h>
#include <stddef.h>
#endif

#define GENESISTAN_DEBUG_BUS_CAPACITY 128

typedef enum GenesistanDebugChannel {
    GENESISTAN_DEBUG_STARTUP = 0,
    GENESISTAN_DEBUG_AUDIO = 1,
    GENESISTAN_DEBUG_VIDEO_TEXT = 2,
    GENESISTAN_DEBUG_VIDEO_SPRITE = 3,
    GENESISTAN_DEBUG_INPUT = 4,
    GENESISTAN_DEBUG_PATCHER = 5,
    GENESISTAN_DEBUG_RUNTIME = 6
} GenesistanDebugChannel;

typedef enum GenesistanDebugSeverity {
    GENESISTAN_DEBUG_TRACE = 0,
    GENESISTAN_DEBUG_INFO = 1,
    GENESISTAN_DEBUG_WARN = 2,
    GENESISTAN_DEBUG_ERROR = 3
} GenesistanDebugSeverity;

typedef struct GenesistanDebugEvent {
    uint32_t frame;
    uint32_t address;
    uint32_t value;
    uint16_t code;
    uint8_t channel;
    uint8_t severity;
} GenesistanDebugEvent;

typedef struct GenesistanDebugBus {
    GenesistanDebugEvent events[GENESISTAN_DEBUG_BUS_CAPACITY];
    size_t write_index;
    size_t count;
    uint32_t enabled_channels_mask;
} GenesistanDebugBus;

void genesistan_debug_bus_init(GenesistanDebugBus *bus);
void genesistan_debug_bus_emit(
    GenesistanDebugBus *bus,
    GenesistanDebugChannel channel,
    GenesistanDebugSeverity severity,
    uint32_t frame,
    uint32_t address,
    uint32_t value,
    uint16_t code
);
const GenesistanDebugEvent *genesistan_debug_bus_latest(
    const GenesistanDebugBus *bus,
    GenesistanDebugChannel channel
);

#endif
