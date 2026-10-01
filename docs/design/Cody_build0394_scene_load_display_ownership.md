# Cody — Build 0394 scene-load display ownership

## Result

Build 0393 is rejected. Static code establishes that `load_scene_tiles` is a
resource/residency loader, not the owner of the completed initial gameplay
presentation. On the normal path it is called from
`genesistan_hook_itempage_strip_blit` (arcade producer `0x055C5E`, canonical
Genesis patched site `0x055CEE`, native helper `0x072614`). The call at
`0x072660 -> load_scene_tiles 0x074640` occurs during the first iteration of
the retained 64-iteration scene fill.

After that call returns, the current Plane-B strip finishes its 64 cells and
the outer arcade fill continues producing both Plane A and Plane B for all 64
iterations. The already-hooked return at arcade `0x050482` / Genesis
`0x050682` is therefore the first existing boundary after both initial native
maps are complete.

## Ownership correction

The retained scene-fill countdown `a5+0x10AA`, rather than a READY/round/scene
test, marks resource loading as part of initial-map replacement. On that path:

- `load_scene_tiles` still disables display and owns pattern residency, scene
  identity, palette selection, cache/package setup, and test-palette staging;
- its initial package install no longer publishes the pre-fill Plane A/B names
  or enables display;
- `load_scene_tiles` returns with display off;
- `fg_boundary_install_post_reseed`, already called at the completed-fill
  boundary, moves the two existing 2048-word initial Plane-B/Plane-A name DMAs
  there and then enables display.

The new canonical display-enable is in
`fg_boundary_install_post_reseed` at `0x0728DE` (helper entry `0x07286A`),
after publication at `0x072898` and `0x0728AC`. Build 0393's
`vdp_commit_bg_strips_if_dirty` call in `load_scene_tiles` was **reverted**:
it ran before the authoritative fill and therefore could not publish the
completed initial map.

Semantic cut: retained arcade scene-fill progression owns map completion;
native code realizes its completed Plane-A/Plane-B state directly in Genesis
VRAM. The retired PC080SN chip-write tail remains removed. No PC080SN shadow,
emulation, framebuffer, new clear, arbitrary delay, scene-1/READY special
case, or per-frame work was added.

## Build result

The first numbered attempt produced and preserved Build 0394 canonical and
`_d`, then `_s` crossed one wrapper alignment page and failed the strict
Build-0029 coverage invariant. Per the no-reuse rule, counter 394 was consumed.
The exact score-variant `+0x1000` coverage delta was recorded in the Makefile;
the complete release advanced to **Build 0395**.

| Build 0395 variant | Bytes | SHA-256 |
|---|---:|---|
| canonical | 1,744,568 | `77369949a85ca726072349db82839a10834a14841a2e2dc956b88e217fb61a64` |
| `_c` | 1,748,664 | `619ac56248540ac155f61c3b90437529b5fde18310f673ecee310ff0801a4476` |
| `_d` | 1,744,568 | `50f5c0fcd8e8e45e5ad02a9471282822b6ea7fe18f8338d8f16741055357304f` |
| `_do` | 1,744,568 | `5c0c645ba075e892d85256a71c0dd1bc93c0751837f55d66474bce9f05106734` |
| `_s` | 1,748,664 | `d1aa23c21a5b028d8d72e2cdd74a891f08f9811df2dc8e82762e0e4f773b02be` |

- Canonical gate: **PASS**.
- Gameplay-entry gate: **PASS**; gameplay reached, player control observed,
  no address/bus/illegal/crash-handler events.
- Transition-retention gate: **PASS**.
- Complete five-ROM variant gate: **PASS**.
- Phase-1 seven-epoch gate: **FAIL/WARNING**, pre-existing and non-blocking.
- Palette decisions, final Plane-A resolver, and collision: **unchanged**.
- Knowledge classification: **EXTENDING** existing scene-fill ownership;
  no KNOWN/OPEN/CLOSED issue status changed.
- Visual/gameplay acceptance: **TIGHE MUST VERIFY**.

