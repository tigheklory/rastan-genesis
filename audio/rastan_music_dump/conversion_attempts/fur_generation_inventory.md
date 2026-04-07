# FUR Generation Inventory

| Artifact | Path | Why It Is Useful |
| --- | --- | --- |
| Rastan source dumps | `audio/rastan_music_dump/*.vgz` | Primary source material for conversion pipeline input. |
| Decompressed VGM files | `audio/rastan_music_dump/converted_vgm/*.vgm` | Direct chip-command timeline input for event extraction. |
| Prior vgm2fur outputs | `audio/rastan_music_dump/converted_fur/*.fur` | Baseline artifacts for structure comparison and sanity checking. |
| vgm2fur repository | `audio/rastan_music_dump/tools/vgm2fur/` | Local source for Furnace writer implementation and module structure evidence. |
| Furnace module serializer source | `audio/rastan_music_dump/tools/vgm2fur/vgm2fur/furnace/module.py` | Defines binary `.fur` module container and chunk layout generation. |
| Furnace instrument serializer source | `audio/rastan_music_dump/tools/vgm2fur/vgm2fur/furnace/instruments.py` | Defines placeholder FM/PSG instrument payload serialization. |
| Furnace note constants | `audio/rastan_music_dump/tools/vgm2fur/vgm2fur/furnace/notes.py` | Defines note encoding domain and OFF note code. |
| Previous event extraction artifacts | `audio/rastan_music_dump/conversion_attempts/*_events.csv` and `*_ym2151_writes.csv` | Existing intermediate evidence for timing and register-write parsing. |
| Direct generation summary | `audio/rastan_music_dump/conversion_attempts/direct_fur_generation_summary.json` | Machine-readable status for generated `.fur` and per-track validation. |
