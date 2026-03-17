# Rastan

Known-good SGDK text-mode sanity build for the `Rastan` startup configuration screen.
This is the current baseline app for the project.

## Build

```bash
source ../../tools/setup_env.sh
make
```

No-hook payload build:

```bash
source ../../tools/setup_env.sh
make release-nohook
```

Output ROM:

```bash
out/rom.bin
```

Named release copy:

```bash
../../dist/Rastan_<build_number>_<timestamp>.bin
```

`release-nohook` keeps the launcher active, embeds the extracted `maincpu`,
`audiocpu`, `adpcm`, `pc080sn`, and `pc090oj` regions, and leaves the
`START RASTAN` action as a packed-payload stub so the launcher can be verified
without the startup hook.

## Controls

- Up / Down: move selection
- Left / Right / A: change selected setting
- B: undo last change
- C: factory reset
- Start: launch stub
