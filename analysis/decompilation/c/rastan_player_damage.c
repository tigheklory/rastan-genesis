/* rastan_player_damage.c — ENEMY-CONTACT -> RASTAN DAMAGE/HURT/KNOCKBACK/DEATH chain.
 * Semantic reconstruction of the arcade "enemy touches Rastan" path that the Build-0438 damage
 * audit (docs/design/Andy_build0438_player_damage_failure_audit.md) marked "not located". It is now
 * located and fully recovered. NOT original Taito source; byte-faithful control flow in
 * raw/000449b4.c (producer), raw/00054a40.c (consumer), raw/000551b0.c (handlers + 0x5560C).
 * The 68000 binary is final authority.
 *
 * This is DISTINCT from:
 *   - weapon->enemy  (rastan_actor_collision.c: 0x449B4/0x447CE one-hit enemy death), and
 *   - terrain/solid->player  (rastan_player_solid_object.c: 0x54BF8 push-out resolution).
 *
 * CHAIN (all PCs are ORIGINAL ARCADE; A5 base 0x10C000 -> Genesis WRAM 0xFF0000):
 *
 *   0x449B4 pass 1 (0x449E4): for each live enemy (mode +0x03==0), build its hurtbox index (0x446BC)
 *       and test it against the PLAYER BODY box (0x44930 dispatch -> 0x44CBA AABB). On overlap it
 *       records {active=1, type(=1), X=+0x16, Y=+0x1A} into the BODY-HIT LIST at A5+0x12A8,
 *       A5-relative (LEA %a5@(4776)) -- up to 4 entries. [producer, correct on Genesis]
 *
 *   0x54A40 consumer: LEA 0x0010D2A8,A0 (ABSOLUTE) and loops the 4 records; for a live record with
 *       type in range it dispatches a per-type handler via the jump table at 0x550A8. [KF-044 site]
 *
 *   0x551CC family (0x551CC/0x5520E/0x55250/0x55292/0x552D4/0x55316/0x55346/0x55376/0x553A6/...):
 *       (1) if A5+0x0040 != 0  -> return (DEBUG/benchmark invincibility; stock MAME cheat sets bit6);
 *       (2) A5+0x13C4 = 1 (hit seen);
 *       (3) if A5+0x1366 == 1 -> return (TEMPORARY POST-HIT INVULNERABILITY window still open);
 *       (4) if A5+0x12F0==1 or A5+0x130E==1 -> return (already hurt / in knockback);
 *       (5) A5+0x013A -= (type-specific amount: 512/1024/1536/2048/2560/3072/4096/5120/6144,
 *           i.e. -2..-24 energy cells)  <-- ENERGY IS THE HEALTH FIELD; enemy contact decrements it;
 *       (6) A5+0x12FC = 1 (damage taken); A5+0x1366 = 1 (start post-hit invuln); A5+0x1368 = 0;
 *       (7) 0x5560C hurt reaction: pose 0x0C via 0x3A0EC, knockback A5+0x130E=1 / A5+0x130C=16,
 *           hurt timer A5+0x12F2=12.
 *       Lethal/special arms (e.g. 0x553E6) set A5+0x10E8 = 8 (player death) directly.
 *
 *   DEATH: when A5+0x013A reaches 0, the player state logic (rastan_player_animation.c) enters
 *       death state 8. So repeated/strong enemy contact drains energy to death; a lethal-arm contact
 *       forces state 8 immediately.
 *
 * ENERGY QUESTION (explicit): YES. Ordinary enemy contact DOES decrement A5+0x013A (the same field
 * the HUD energy bar and the energy timer use), by a type-specific amount. It is not a separate HP
 * accumulator. The reduced Genesis HUD merely hides A5+0x013A; it does not change this semantics.
 *
 * POST-HIT INVULNERABILITY (explicit): A5+0x1366 latch + A5+0x1368 countdown, set on hit and
 * consulted at the top of every handler (step 3). It is DISTINCT from the A5+0x0040 debug gate.
 */
#include "rastan_arcade_types.h"

/* See raw/000551b0.c for the exact per-handler energy decrements and 0x5560C body. */
