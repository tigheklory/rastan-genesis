# Board Video Reference

This note tracks video references captured from original arcade hardware so
they can be used to validate behavior without relying on memory.

## Current board capture

Preferred local mirror in this repo:

- [video/actual_arcade_gameplay.mp4](/home/tighe/projects/rastan-genesis/video/actual_arcade_gameplay.mp4)

Public share link:

- `https://photos.app.goo.gl/xPJ7VGipgTGUkmEFA`

What it is:

- capture from the user's actual `Rastan` arcade board
- credit switch is wired to player 2 button for adding credits
- audio is not a reliable reference because `Galaga '88` is audible from a
  nearby cabinet

Observed accessible metadata from the public page on `2026-03-13`:

- title shown by Google Photos: `New video · Friday, Mar 13`
- media type: `video/mp4`
- preview resolution reported by the page: `1920x1080`

Observed local file metadata on `2026-03-13`:

- duration: `00:01:20.76`
- video: `1920x1080`, `29.99 fps`, H.264
- audio: AAC stereo

Derived local reference artifacts:

- metadata: [metadata.txt](/home/tighe/projects/rastan-genesis/docs/reference/media/actual_arcade_gameplay_reference/metadata.txt)
- contact sheet: [contact_sheet.png](/home/tighe/projects/rastan-genesis/docs/reference/media/actual_arcade_gameplay_reference/contact_sheet.png)
- extracted frames: [frames](/home/tighe/projects/rastan-genesis/docs/reference/media/actual_arcade_gameplay_reference/frames)

## How to use this reference

Use this capture for:

- startup timing and normal boot flow
- basic system-test behavior that runs every boot
- attract/title/story progression
- credit insertion behavior
- story page order, timing, and scrolling behavior

Do not use this capture as a primary reference for:

- audio timing or music/SFX correctness
- any behavior obscured by the cabinet environment or recording UI

## Provenance rule

This is a behavioral reference only.

It does **not** replace:

- original ROMs as source of truth for code/data
- machine-readable build specs under `specs/`

The local repo copy should be treated as the working reference for this
project. The public link remains useful as provenance and an external backup.
