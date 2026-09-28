# Rastana — Registration & Animation Brief

A spec for generating Rastana frames that drop into Rastan's arcade sprite engine **1:1**. Derived
from the static decompilation of the arcade program (torso table `0x5BD40`, leg table `0x5C466`,
weapon-overlay table `0x5CD8A`). Use the images in `registration/` as trace-over guides.

## The three hard registration rules (why free-hand art drifts)

The game does **not** draw a whole character — it composes three independent layers at fixed offsets.
Art that ignores these can't line up.

1. **The waist is a fixed seam.** Every frame is an upper **torso** sprite (cells at y −32 / −16) over a
   lower **legs** sprite (cells at y 0 / +16), composited at one shared origin. The **cyan line** in each
   template is y = 0, the seam. *Torso art must bottom-out exactly on that line; leg art must top-out on
   it; both centred on the vertical axis.* When she walks, the torso holds still and only the legs swap —
   so the torso's bottom edge must be identical across a walk cycle or the hips will jitter.

2. **The hand is where the weapon attaches.** The sword is a *separate* overlay, indexed by the same
   frame number as the body, drawn at a fixed offset (from `0x5CD8A`). The **magenta cross** marks that
   grip point and the **yellow outline** is the exact blade footprint. *Put her sword hand on the cross
   and leave the yellow area clear* — then the real in-game sword lands in her hand every frame. Frames
   with no yellow/cross carry no weapon (idle/among the death frames).

3. **Match the grey silhouette / cell grid.** The grey fill is Rastan's actual frame. Rastana can be
   more feminine (narrower waist, bust, longer hair) but her **overall envelope, limb angles and height
   must stay inside the same cells**, or she'll desync from hit-boxes and the weapon.

## Animation semantics ChatGPT got wrong

### Death is a DISSOLVE, not a pose
Rastan's death (player state 8) is a **disintegration**, driven through death-phase tables
`0x5BCC0 → 0x5BBC0 → 0x5BC40`:
- **Dissolve** (torso 40–42, legs 30–32): the body breaks into **rising sparkle/particles** — she is
  coming apart into points of light, arms falling, not striking a hero pose. Progressively more of the
  figure is replaced by scattered pixels until only sparkles remain (torso 56–61 / legs 46–51 are almost
  pure particles).
- **Burn variant** (torso 70–76, legs 41–45): an alternative death where she is **engulfed in flame** —
  lava/fire rising over the legs and body. Still a death, read as pain/collapse, not a stance.
So the brief for these frames is: *a warrior being destroyed and scattering into light (or burning),
losing her silhouette frame by frame* — sad/violent, not glamorous.

### Rope climb is a reach-and-pull, not a jump
Climb (player state 4) uses torso 15–18 with legs 13–16: **one or both arms reach up overhead gripping
a rope**, torso stretched, legs tucked/alternating as she pulls herself up a vertical rope. She is
*hanging and hauling*, weight on the arms — not leaping. The rope itself is background, so her hands
should close as if around a ~2px-wide rope on the centre axis.

## Frame map (label → torso/legs, see registration_data.json for hand points)
- idle 0/0 · walk 28/18, 29/19, 30/20
- climb 15/13, 16/14, 17/15, 18/16
- up-thrust 12/8, 13/8 · crouch 6/6 · jump 37/27 · overhead 38/28 · weapon swing 44/34
- death-dissolve 40/30, 41/31, 42/32 · death-burn 70/42, 72/44

## Suggested ChatGPT workflow
1. Feed the matching `registration/reg_*.png` as an image reference (or trace layer).
2. Prompt: keep her inside the grey silhouette, torso bottom on the cyan line, sword hand on the magenta
   cross, blade clear of the yellow zone; render in the hand-drawn arcade-cutscene style.
3. For death/rope frames, use the semantics above instead of a "cool pose".
4. Return each frame on transparent background at the template's pixel size so it slices back onto the
   16×16 cell grid cleanly.
