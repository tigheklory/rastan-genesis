# Rastan Startup To Gameplay Flow

This is a compact address-based flow diagram for the path from title/start into
stage initialization and the first active gameplay loop.

It is not the whole program. It is the part currently most useful for finding
the true start of gameplay and the player spawn/drop handoff.

## High-level flow

```mermaid
flowchart TD
    A["0x3a79c\nHigh-level mode dispatch\nreads a5+0x04"] -->|mode 0| B["0x3a7ae\npre-game / title-credit-start path"]
    A -->|mode 1| C["0x3a832\nwait for gameplay-ready condition"]
    A -->|mode 2| D["0x55ddc\nlater controller path"]

    B --> E["0x3a772\nread/update raw input state"]
    B --> F["0x41f0e\nmain gameplay-style update"]
    B --> G{"start / commit condition?"}
    G -->|no| B
    G -->|yes| H["0x3a7fa\nstage-init handoff"]

    H --> H1["clear 0x02c8 actor list"]
    H --> H2["0x45dfa"]
    H --> H3["0x3b902"]
    H --> H4["a5+0x13ac = 8"]
    H --> H5["a5+0x04 = 1"]
    H --> C

    C --> I{"a5+0x10e8 == 16 ?"}
    I -->|no| C
    I -->|yes| J["0x41f5e"]
    J --> K["a5+0x46 = 2"]
    J --> L["a5+0x1394 = 1"]
    J --> M["a5+0x13aa = 9"]
    J --> N["a5+0x04 = 2"]
    N --> D

    D --> O["gameplay/stage controller set"]
```

## Stage initialization chain

This is the setup sequence reached from `0x3a7fa`.

```mermaid
flowchart TD
    A["0x501ea\nstage init master"] --> B["0x54052"]
    A --> C["0x50248\nselect stage id\nwrites a5+0x013e"]
    A --> D["0x502ba\nclear core stage state"]
    A --> E["0x502cc\ninstall stage-specific pointer tables"]
    A --> F["0x503dc\nbackground / map / camera setup"]
    A --> G["0x504fa\nload per-stage spawn data"]
    A --> H["0x5053a\nclear and seed gameplay/drop/script globals"]
    A --> I{"a5+0x46 branch"}
    I -->|2| J["0x504f2"]
    I -->|not 1| K["0x5049a"]
```

## Stage-start spawn and drop path

This is the strongest current path for the first live player placement.

```mermaid
flowchart TD
    A["0x504fa\nspawn table loader"] --> B["0x5052e\nload per-stage setup record"]
    B --> B1["a5+0x10ae / 0x10b0"]
    B --> B2["a5+0x10b8 / 0x10ba"]
    B --> B3["a5+0x10be = player X"]
    B --> B4["a5+0x10c0 = player Y"]

    A --> C["0x5053a\nreset gameplay/drop/event state"]
    C --> C1["a5+0x1388 = 0xff"]
    C --> C2["a5+0x12f0 = 0xff"]
    C --> C3["a5+0x130e = 0xff"]
    C --> C4["a5+0x1354 = 160"]
    C --> C5["a5+0x1356 = 128"]
    C --> C6["a5+0x1376 = 0xff"]
    C --> C7["a5+0x1372 = 1"]

    D["0x52816\ncopy staged coords into live player coords"] --> D1["a5+0x1354 -> a5+0x10be"]
    D --> D2["a5+0x1356 -> a5+0x10c0"]

    E["0x528ca\nstaged entry motion"] --> E1["0x5291e / 0x52918\nleft / right"]
    E --> E2["0x5290c / 0x52912\nup / down"]

    F["0x5126e\nside-entry threshold detector"] --> F1{"a5+0x10be >= 216?"}
    F --> F2{"a5+0x10be <= 80?"}
    F1 -->|yes| G["set a5+0x1376 = 1\na5+0x1384 = 1\na5+0x13c6 = 1"]
    F2 -->|yes| H["set a5+0x1376 = 1\na5+0x1384 = 2\na5+0x13c6 = 1"]
```

## First active gameplay loop

This is the frame loop I would currently treat as the best "gameplay has begun"
anchor.

```mermaid
flowchart TD
    A["0x41f0e\nmain active gameplay update"] --> B["0x5100a"]
    B --> C["0x51024\ncore frame update"]

    C --> C1["0x510fe\nselect event bank index -> a5+0x1418"]
    C --> C2["latch current control word -> a5+0x137a"]
    C --> C3["0x59f92\nstage-entry event display helper"]
    C --> C4["0x5126e\nthreshold detector"]
    C --> C5["0x52bb6"]
    C --> C6["0x52b38"]
    C --> C7["0x52b4a\nentry script feeder"]
    C --> C8["0x54a2c -> 0x54a32\nstage-entry event dispatcher"]
    C --> C9["0x5132a"]
    C --> C10["0x55650"]
    C --> C11["0x55ad6"]
    C --> C12["0x59de8"]
    C --> C13["0x512c8\nmovement flag consumers"]

    A --> D["0x40b66\nupdate 0x02c8 actor group"]
    A --> E["0x420e6\nupdate 0x0508 actor group"]
    A --> F["0x443e0\nbridge 0x0508 into 0x02c8 gating"]
    A --> G["0x449b4\n0x02c8 proximity/player-linked pass"]
    A --> H["0x450d8\nstage/event actor systems"]
    A --> I["0x49fa6"]
```

## What to watch if you want to find "gameplay starts here"

- `0x3a7fa`
  This is the cleanest known handoff out of the pre-game/title-credit phase.
- `0x501ea`
  This is the stage initialization master.
- `0x5052e`
  This is where the first stage/player coordinates are loaded.
- `0x52816`
  This is where staged entry coordinates become the live player position.
- `0x41f0e / 0x51024`
  This is the first confirmed recurring gameplay update loop worth treating as
  active play.

## Suggested next reverse-engineering checkpoints

- Find who first calls or enables `0x41f0e` from the title/credit/start flow.
- Find where `a5 + 0x10be / 0x10c0` first become visible-body actor
  coordinates.
- Find the first actor constructor after `0x501ea` that seeds the player body
  with its true class/family/palette data.
