# Rastan

Known-good SGDK text-mode sanity build for the `Rastan` startup configuration screen.
This is the current baseline app for the project.

## Build

```bash
source ../../tools/setup_env.sh
make
```

Output ROM:

```bash
out/rom.bin
```

Named release copy:

```bash
../../dist/Rastan_<build_number>_<timestamp>.bin
```

## Controls

- Up / Down: move selection
- Left / Right / A: change selected setting
- B: undo last change
- C: factory reset
- Start: launch stub
