# Docs

Project documentation is organized into:

- `reverse-engineering/` for ROM/disassembly tracing notes
- top-level files in this folder for project structure, validation references,
  staging strategy, and source provenance

Current key docs:

- [repo_structure_proposal.md](/home/tighe/projects/rastan-genesis/docs/project/repo_structure_proposal.md)
- [translation_plan.md](/home/tighe/projects/rastan-genesis/docs/project/translation_plan.md)
- [staging_strategy.md](/home/tighe/projects/rastan-genesis/docs/project/staging_strategy.md)
- [board_video_reference.md](/home/tighe/projects/rastan-genesis/docs/reference/board_video_reference.md)
- [rom_source_reference.md](/home/tighe/projects/rastan-genesis/docs/project/rom_source_reference.md)


## Hardware & Memory Architecture
This project may in the future utilize the EverDrive EX-SSF mapper to unlock true 16-bit writable RAM in the `$200000` cartridge space, bypassing standard Genesis SRAM limitations. 
* [Mega EverDrive EX-SSF Mapper Documentation](docs/everdrive_ex_ssf_mapper.md)