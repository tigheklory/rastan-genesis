# Player-Tied Candidate Gallery

These images are ROM-derived sprite candidates tied to the confirmed player world coordinates by code path.

They are not all the confirmed player body.
They are grouped by routines that directly copy or closely slave display coordinates to `a5+0x10be / a5+0x10c0`.

Confirmed coordinate-copy anchors:

- `0x428b2`: copies player X/Y into the `0x0508` actor cluster
- `0x447b6`: copies player X/Y into `0x02c8` actors of class `10/11/18`
- `0x45c0c`: copies player X/Y-16 into helper-strip actors

## 0x0508 state 8 direct-copy candidate

- source: `0x45342 seeds state 8 and 0x428b2 copies player X/Y into this actor family`
- state: `0x08`

### default table

- tile_base: `0x004b`
- frame_code: `0x17`
- anim_len: `0x01`

- family `0`: [0508_state8_default_family0.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0508_state8_default_family0.png) `32x48`
- family `1`: [0508_state8_default_family1.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0508_state8_default_family1.png) `16x16`
- family `2`: [0508_state8_default_family2.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0508_state8_default_family2.png) `16x16`
- family `3`: [0508_state8_default_family3.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0508_state8_default_family3.png) `250x254`
- family `4`: [0508_state8_default_family4.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0508_state8_default_family4.png) `250x254`

### alt table

- tile_base: `0x004b`
- frame_code: `0x17`
- anim_len: `0x01`

- family `0`: [0508_state8_alt_family0.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0508_state8_alt_family0.png) `32x48`
- family `1`: [0508_state8_alt_family1.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0508_state8_alt_family1.png) `16x16`
- family `2`: [0508_state8_alt_family2.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0508_state8_alt_family2.png) `16x16`
- family `3`: [0508_state8_alt_family3.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0508_state8_alt_family3.png) `250x254`
- family `4`: [0508_state8_alt_family4.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0508_state8_alt_family4.png) `250x254`

## 0x0508 state 9 direct-copy candidate

- source: `0x45342 seeds state 9 and 0x428b2 copies player X/Y into this actor family`
- state: `0x09`

### default table

- tile_base: `0x00d0`
- frame_code: `0x23`
- anim_len: `0x01`

- family `0`: [0508_state9_default_family0.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0508_state9_default_family0.png) `32x64`
- family `1`: [0508_state9_default_family1.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0508_state9_default_family1.png) `16x16`
- family `2`: [0508_state9_default_family2.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0508_state9_default_family2.png) `16x16`
- family `3`: [0508_state9_default_family3.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0508_state9_default_family3.png) `32x64`
- family `4`: [0508_state9_default_family4.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0508_state9_default_family4.png) `32x64`

### alt table

- tile_base: `0x00d0`
- frame_code: `0x23`
- anim_len: `0x01`

- family `0`: [0508_state9_alt_family0.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0508_state9_alt_family0.png) `32x64`
- family `1`: [0508_state9_alt_family1.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0508_state9_alt_family1.png) `16x16`
- family `2`: [0508_state9_alt_family2.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0508_state9_alt_family2.png) `16x16`
- family `3`: [0508_state9_alt_family3.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0508_state9_alt_family3.png) `32x64`
- family `4`: [0508_state9_alt_family4.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0508_state9_alt_family4.png) `32x64`

## 0x0748 class-11 helper-strip candidate

- source: `0x45642 builds class 11 helpers and 0x45c0c copies player X/Y-16 into their display coordinates`
- state: `0x0b`

### default table

- tile_base: `0x02e8`
- frame_code: `0x5f`
- anim_len: `0x01`

- family `0`: [0748_state11_default_family0.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0748_state11_default_family0.png) `48x51`
- family `1`: [0748_state11_default_family1.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0748_state11_default_family1.png) `40x48`
- family `2`: [0748_state11_default_family2.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0748_state11_default_family2.png) `32x32`
- family `3`: [0748_state11_default_family3.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0748_state11_default_family3.png) `250x254`
- family `4`: [0748_state11_default_family4.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0748_state11_default_family4.png) `250x254`

### alt table

- tile_base: `0x02e8`
- frame_code: `0x5f`
- anim_len: `0x01`

- family `0`: [0748_state11_alt_family0.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0748_state11_alt_family0.png) `48x51`
- family `1`: [0748_state11_alt_family1.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0748_state11_alt_family1.png) `40x48`
- family `2`: [0748_state11_alt_family2.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0748_state11_alt_family2.png) `32x32`
- family `3`: [0748_state11_alt_family3.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0748_state11_alt_family3.png) `250x254`
- family `4`: [0748_state11_alt_family4.png](/home/tighe/projects/rastan-genesis/build/player_tied_candidates/0748_state11_alt_family4.png) `250x254`

