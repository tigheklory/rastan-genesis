# ChatGPT prompt — generating aligned Rastana frames

## PART A — Master setup (send ONCE, attach your approved Rastana render + one reg_*.png template)

> I'm producing an animation frame set for **Rastana**, a female barbarian — Rastan's sister. Keep her
> EXACTLY the character in the attached reference: heavily muscled but attractive and believable
> (think Tyris Flare from Golden Axe, more muscle-bound), long flowing dark-auburn hair, fur/hide
> bikini-armour top and loincloth, gold arm-bands and belt, and knee-high **red** boots. Hand-drawn
> vintage-arcade cutscene style with painted cel shading, bold ink outlines, warm skin tones — the
> same rendering as the reference. She must look like the SAME person in every frame.
>
> I will send you one **registration template** per frame. The template is a GUIDE ONLY — never draw
> the grey shape, the grid, or the coloured markers. Read them as hard alignment rules:
>
> - **Grey silhouette** = the exact envelope Rastana must fill. Her pose, limb angles, height and width
>   must stay inside it so she matches the game's hit-boxes. She can be more feminine (narrower waist,
>   bust, longer hair) but must not exceed the silhouette.
> - **Cyan horizontal line = the fixed WAIST seam.** Her body above the line is one sprite, below it is
>   another, and they must meet exactly on this line. Her torso must bottom-out on the cyan line and her
>   hips/legs begin right at it. Across walk frames the upper body stays put — only the legs change.
> - **Magenta cross = her sword HAND.** Place the grip of her hand precisely on the cross.
> - **Yellow outline = where the game's sword will be drawn.** Leave that area EMPTY — do not draw a
>   blade there; just have her hand grip as if holding it. (Frames with no cross/yellow carry no weapon.)
> - **Blue vertical line = centre axis** for left/right balance.
>
> Output each frame as a **PNG on a fully transparent background**, cropped to the template's exact pixel
> dimensions, no text, no markers, no grid — only Rastana. Confirm you understand and I'll send frame 1.

## PART B — Per-frame message (send with each reg_*.png)

> Frame: **{LABEL}**. Match this template exactly — silhouette, waist on the cyan line, sword hand on the
> magenta cross, blade area (yellow) left empty, transparent background, same Rastana. {SEMANTIC NOTE}

Fill `{LABEL}` from the file name and `{SEMANTIC NOTE}` only for the special cases below (leave blank
for ordinary idle/walk/attack/jump/crouch frames):

- **climb / rope (u15–18):** "She is CLIMBING A ROPE — one/both arms reaching overhead gripping a rope on
  the centre axis, torso stretched upward, legs tucked and pulling; her weight hangs from her arms. Not a
  jump, not a victory pose."
- **death: dissolve (u40–42, and later 56–61):** "This is a DEATH frame — she is DISINTEGRATING into rising
  points of light. Her body is breaking apart into scattered sparkle-particles, silhouette dissolving,
  arms failing. Progressively less solid figure, more scattered light. Read as death/destruction, NOT a
  dramatic pose."
- **death: burn (u70–76):** "This is a DEATH frame — she is being CONSUMED BY FLAME, fire rising over her
  legs and body, collapsing in pain. A burning death, not a stance."
- **up-thrust (u12–13):** "She thrusts straight UP — sword arm extended overhead, hand on the cross, blade
  pointing up out of frame (leave the yellow empty)."
- **weapon swing (u43–54):** "Mid sword-swing — arm driving across; keep the hand on the cross and the
  yellow blade zone empty."

## Tips
- Do frames in small batches so the style stays consistent; re-attach the master reference if she drifts.
- If a frame comes back misaligned, resend it with: "Her waist isn't on the cyan line / her hand isn't on
  the magenta cross — nudge her so it matches, keep everything else."
- Return frames at the template's native size; that keeps them sliceable back onto the 16×16 cell grid.
