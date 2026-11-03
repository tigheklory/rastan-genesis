#include "debug_bus.h"

void genesistan_debug_bus_init(GenesistanDebugBus *bus)
{
    size_t index;

    bus->write_index = 0;
    bus->count = 0;
    bus->enabled_channels_mask = 0xFFFFFFFFu;

    for (index = 0; index < GENESISTAN_DEBUG_BUS_CAPACITY; index++) {
        bus->events[index].frame = 0;
        bus->events[index].address = 0;
        bus->events[index].value = 0;
        bus->events[index].code = 0;
        bus->events[index].channel = 0;
        bus->events[index].severity = 0;
    }
}

void genesistan_debug_bus_emit(
    GenesistanDebugBus *bus,
    GenesistanDebugChannel channel,
    GenesistanDebugSeverity severity,
    uint32_t frame,
    uint32_t address,
    uint32_t value,
    uint16_t code
)
{
    GenesistanDebugEvent *event;

    if ((bus->enabled_channels_mask & (1u << (uint32_t)channel)) == 0) {
        return;
    }

    event = &bus->events[bus->write_index];
    event->frame = frame;
    event->address = address;
    event->value = value;
    event->code = code;
    event->channel = (uint8_t)channel;
    event->severity = (uint8_t)severity;

    bus->write_index = (bus->write_index + 1) % GENESISTAN_DEBUG_BUS_CAPACITY;
    if (bus->count < GENESISTAN_DEBUG_BUS_CAPACITY) {
        bus->count++;
    }
}

const GenesistanDebugEvent *genesistan_debug_bus_latest(
    const GenesistanDebugBus *bus,
    GenesistanDebugChannel channel
)
{
    size_t scanned;
    size_t index;

    for (scanned = 0; scanned < bus->count; scanned++) {
        index = (bus->write_index + GENESISTAN_DEBUG_BUS_CAPACITY - 1 - scanned) %
                GENESISTAN_DEBUG_BUS_CAPACITY;
        if (bus->events[index].channel == (uint8_t)channel) {
            return &bus->events[index];
        }
    }

    return NULL;
}
