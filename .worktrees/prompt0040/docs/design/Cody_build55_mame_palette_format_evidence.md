# Cody Build 55 MAME Palette Format Evidence

Type: Read-only local-reference review (local files only)
Build context: rastan-direct Build 0054

## §1.1 Local Reference Material Inventory

Locations checked:
- Project-vendored reference snapshot:
  - `docs/reference/mame/rastan/`
- Project docs/reference trees:
  - `docs/reference/`
  - `docs/project/`
  - `docs/design/`
- Project source/tool trees:
  - `apps/`
  - `tools/`
- Local installed reference locations:
  - `/usr/src`
  - `/usr/local/src`
  - `/opt`
  - `/usr/share/doc`

Relevant material found: **YES**

Relevant files:
- `docs/reference/mame/rastan/README.md`
  - local MAME Rastan snapshot manifest (pinned commit + included files)
- `docs/reference/mame/rastan/src/mame/taito/rastan.cpp`
  - arcade memory map, palette RAM mapping, palette format binding
- `apps/rastan/src/main.c`
  - local xBGR-555 decode implementation (`convert_xbgr555_to_genesis`)
- `apps/rastan/src/startup_trampoline.s`
  - local assembly conversion block labeled `raw xBGR-555`
- `docs/design/build318_palette_regression_and_offline_runtime_conversion_audit.md`
  - project-local record stating CLCS captures at `0x200000` are xBGR-555

Inventory notes:
- `docs/reference/mame/rastan/README.md:7-14` lists included MAME files and `rastan.cpp`.
- Search of `/usr/src`, `/usr/local/src`, `/opt` found no additional local `rastan.cpp`/`pc050cm` source files.
- `/usr/share/doc` had `mame` docs/example ini, but no local arcade palette device source in those paths.

## §1.2 Palette Device Path (Local References)

Address range evidence:
- `docs/reference/mame/rastan/src/mame/taito/rastan.cpp:32`
  - `CLCS palette RAM` in memory-map table
- `docs/reference/mame/rastan/src/mame/taito/rastan.cpp:305`
  - `map(0x200000, 0x200fff).ram().w("palette", FUNC(palette_device::write16)).share("palette");`

Palette decode format binding evidence:
- `docs/reference/mame/rastan/src/mame/taito/rastan.cpp:455`
  - `PALETTE(config, "palette").set_format(palette_device::xBGR_555, 2048);`

Local bit-field decode evidence for xBGR-555:
- `apps/rastan/src/main.c:1008-1017`
  - `r = (raw >> 0) & 0x1F`
  - `g = (raw >> 5) & 0x1F`
  - `b = (raw >> 10) & 0x1F`
- `apps/rastan/src/startup_trampoline.s:141-152`
  - conversion loop comments/ops labeled `raw xBGR-555` and shift/mask conversion to Genesis
- `docs/design/build318_palette_regression_and_offline_runtime_conversion_audit.md:55`
  - states CLCS captures at `0x200000` are xBGR-555

16-bit value decode (from local evidence above):
- Bit fields:
  - `R5 = bits [4:0]`
  - `G5 = bits [9:5]`
  - `B5 = bits [14:10]`

`0x59AD4` output format match check:
- Prior Cody evidence formula (`Cody_build55_palette_bank_mapping_evidence.md`):
  - `out = ((raw & 0x0F00) >> 7) | ((raw & 0x00F0) << 2) | ((raw & 0x000F) << 11)`
- Local observation against xBGR-555 bit fields:
  - `out[4:1]` populated, `out[0]=0`
  - `out[9:6]` populated, `out[5]=0`
  - `out[14:11]` populated, `out[10]=0`
- Result: **YES** — values written by `0x59AD4` fit xBGR-555 layout (with low bit of each 5-bit channel zeroed).

## §1.3 Comparison Table

Sample inputs required by task:
- `0x0000`, `0x0FFF`, `0x0FF8`, `0x0EC0`, `0x0C90`, `0x0A70`, `0x0850`, `0x0530`

Definitions used in table:
- `0x59AD4 output`: from prior Cody evidence formula above
- `MAME-decoded RGB`: decoded as xBGR-555 per local evidence (`main.c:1008-1012`) shown as `(R5,G5,B5)`
- `project CLCS Genesis output`: from prior Cody evidence formula
- `expected Genesis CRAM equivalent`: local xBGR-555 → Genesis conversion (`main.c:1013-1017`)

| input raw | 0x59AD4 output | MAME-decoded RGB | project CLCS Genesis output | expected Genesis CRAM equivalent |
|---|---:|---|---:|---:|
| `0x0000` | `0x0000` | `(0,0,0)` | `0x0000` | `0x0000` |
| `0x0FFF` | `0x7BDE` | `(30,30,30)` | `0x00EE` | `0x0EEE` |
| `0x0FF8` | `0x43DE` | `(30,30,16)` | `0x00EC` | `0x08EE` |
| `0x0EC0` | `0x031C` | `(28,24,0)` | `0x00A0` | `0x00CE` |
| `0x0C90` | `0x0258` | `(24,18,0)` | `0x0028` | `0x008C` |
| `0x0A70` | `0x01D4` | `(20,14,0)` | `0x0088` | `0x006A` |
| `0x0850` | `0x0150` | `(16,10,0)` | `0x0008` | `0x0048` |
| `0x0530` | `0x00CA` | `(10,6,0)` | `0x0048` | `0x0024` |

UNKNOWN cells:
- None.

## §1.4 Andy Readiness (Mechanical)

Readiness: **READY**

Reason:
- Local MAME Rastan snapshot provides palette address map (`0x200000..0x200fff`) and palette format binding (`xBGR_555`).
- Local project code provides explicit xBGR-555 bit extraction and xBGR-555 → Genesis conversion implementation.
- Required 8-row comparison table populated from local-file evidence.

No conversion-path recommendation is made in this document.

## Phase 2 Integrity

- §1.1 local reference material inventory completed: YES
- §1.1 relevant reference material found: YES
- §1.2 palette device path identified: YES
- §1.3 comparison table populated: COMPLETE
- §1.4 Andy readiness: READY
- All findings cited from local files: YES
- Design recommendations performed: NONE
- Hypotheses generated: NONE
- Internet sources consulted: NONE
- Local files only: YES
- All cells populated or UNKNOWN-explained: YES
- No source/spec/tool modifications: YES
