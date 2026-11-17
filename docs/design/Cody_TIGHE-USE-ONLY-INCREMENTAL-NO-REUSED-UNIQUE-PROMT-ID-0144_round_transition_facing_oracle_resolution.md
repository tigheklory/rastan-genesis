TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0144

# Round-transition facing oracle resolution

## Result

**CLOSED / NOT A BUG — arcade-accurate behavior.**

Original arcade Rastan preserves the player's final facing direction across R1-S3→R2-S1. Build 0573 does the same. The proposed new-round force-right reset is disproven, and no production correction is required.

## 1. Starting state

- Branch: `rastan-direct-proposal`.
- HEAD: `a823c07792d3f0c69cbcc6d9d653b1767787a5b2`.
- Makefile build counter: `573`.
- Build 0573: `dist/rastan-direct/rastan_direct_video_test_build_0573.bin`, 4,443,832 bytes, SHA-256 `1b396536f2a3543e42e6cab9b73e2f9bd67e40486ec3b070aa323223bc985b2f`.
- Existing 0142/0143 state: the Genesis completion gate extensions, assisted arcade launcher/observer, historical 0142 checkpoint report, OPEN-043, and 0143 log entry were present and preserved.
- Concurrent state preserved: dirty PROMT-ID-0135 `apps/rastan-direct/src/sound/sound_comm.s`; generated `apps/rastan-direct/out/*`, build maps/manifests/disassembly/trace/counter state; modified `tools/mame/cheat/output.json`; modified 0134 report; untracked 0135/0136, performance, and antigravity documents.
- No reset, clean, rebase, restore, rollback, push, or artifact deletion was performed.

## 2. Historical PROMT-ID-0142 blocker

PROMT-ID-0142 correctly stopped because the original arcade LEFT-finish behavior was unknown. Static evidence established authoritative facing state and its consumers, while automated Genesis routes reproduced the carry-over. It did not establish whether original arcade reset LEFT to RIGHT at new-round entry, so no fix was justified.

The original STOP remains preserved in the historical report. PROMT-ID-0144 adds a labeled post-checkpoint resolution rather than rewriting that history.

## 3. Assisted ORIGINAL ARCADE configuration

The retained human observer launches original `mame rastan` with:

- stock MAME starting selector `$F7` (`Round 1 Boss`, R1-S3);
- stock MAME `Invincibility` cheat, which uses the original `A5+$0040` debug gate;
- human-controlled input, boss fight, final blow, and finishing direction;
- no boss-health write, forced boss completion, forced transition, synthetic facing write, or facing input injection.

The selector and invincibility changed test convenience only. They did not manufacture the facing result or force the R1→R2 lifecycle being observed.

## 4. Human LEFT-facing result

Tighe finished original arcade R1-S3 facing LEFT and continued through the authentic boss completion into R2-S1.

`states/traces/promt0142_arcade_left_human/summary.txt` records:

- `result=PASS` / `reason=ROUND2_GAMEPLAY`;
- `assisted_start=R1-S3`, `start_selector=F7`, `invincibility=YES`;
- `final_round=02`, `final_record=0018`;
- `final_facing=0002`.

The event stream retains `$1114=$0002` through End-Round states 9, 11, 12, and 13, the Round-2 state change, and stable R2-S1 gameplay. Summary SHA-256: `0ad8e4470a4201ed3013493495a03db1e5a4ea0933c5952b7ad8068cc260bf8c`; event-stream SHA-256: `8a20f9f0b6f3347fb7fc4a58bdd4ed7741a87028130f0d20dc88bb545420da20`.

## 5. Human RIGHT-facing control

The RIGHT control was also run; it is not inferred or missing.

`states/traces/promt0142_arcade_right_human/summary.txt` records:

- `result=PASS` / `reason=ROUND2_GAMEPLAY`;
- `assisted_start=R1-S3`, `start_selector=F7`, `invincibility=YES`;
- `final_round=02`, `final_record=0018`;
- `final_facing=0003`.

The event stream retains `$1114=$0003` through the same transition and stable R2-S1 gameplay. Summary SHA-256: `83b31862ee9f5b0751f85093745b33027e158181b88d00eeb40a7ebe16d5d9e9`; event-stream SHA-256: `0ee66a9f8593c326ace26f900e804673afa591803b360033dce60f2c66cffcd3`.

## 6. Build-0573 Genesis comparison

The preserved Build-0573 Genesis routes already established the same behavior:

- LEFT-biased completion retained facing `2` through End-Round states 9–13 and first R2 gameplay;
- RIGHT completion retained facing `3` through End-Round states 9–13 and first R2 gameplay.

The original arcade controls now establish that this carry-over is correct. LEFT-facing R2-S1 entry is not a Build-0573 regression and no longer blocks Build 0573. This does not accept Build 0573 against unrelated issue conditions.

## 7. Authoritative state and native realization

Player facing is retained `A5+$1114`:

- original arcade address: `$0010D114`;
- Genesis WRAM address: `$00FF1114`;
- value `2`: LEFT;
- value `3`: RIGHT.

Original compositor `FUN_00054492` reads this word at `$0544AA/$0544E6/$054512`. Native `native_player_frame_try` and `native_player_secondary_frame` read `0x1114(%a5)` directly, select the generated orientation key, and emit the corresponding final piece attributes/SAT HFlip. No separate native facing cache was found.

The native path is therefore faithful by preserving and consuming the same retained gameplay state.

## 8. Disproven hypothesis and production disposition

Disproven: “new-round entry should force Rastan to face RIGHT.”

There is no missing reset to restore. Do not add:

- `move.w #3,A5+$1114` at player init, READY, scene load, spawn, or round entry;
- a Round-2 or R2-S1 special case;
- a native SAT/HFlip override;
- an independent Genesis facing cache.

Production source changed: **NONE**. Player gameplay, sprite HFlip, graphics, palettes, audio, Plane A/B, IRQ/performance scheduling, and build architecture are unchanged.

## 9. Documentation and ledger reconciliation

- Historical 0142 report amended with a labeled post-checkpoint resolution while preserving its original STOP.
- OPEN-043 moved to CLOSED-043 as **NOT A BUG — arcade-accurate behavior**.
- KF-097 added because this is a durable gameplay-lifecycle fact with a high risk of a future force-right “fix.”
- OPEN-040, OPEN-041, and OPEN-042 remain governed by their own acceptance conditions.

## 10. Trace-tool disposition

The useful tooling remains:

- `tools/mame/run_round_transition_facing_arcade.sh`;
- `tools/mame/scripts/round_transition_facing_arcade.lua`;
- `tools/mame/run_round1_completion_runtime_gate.sh`;
- `tools/mame/scripts/round1_completion_runtime_gate.lua`.

The arcade observer remains suitable for future facing/player-init comparisons. R1-S3 direct start and stock invincibility are explicit test conveniences. Facing, input, final blow, boss completion, and transition remain under human/original-game control.

Existing project tools reused: the PROMT-ID-0142/0143 ORIGINAL ARCADE observer and Build-0573 Genesis completion traces.

New tooling created: **NONE**.

Why new tooling was necessary: **not applicable**; existing traces answered the question.

## 11. ROM/build disposition

- ROM produced: **NONE**.
- Build number consumed: **NONE**.
- Counter remains `573`.
- Build 0573 artifact unchanged.
- No production commit or push was made.

## 12. Files changed by PROMT-ID-0144

- `docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0142_round_transition_player_facing_reset.md`;
- `docs/design/Cody_TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0144_round_transition_facing_oracle_resolution.md`;
- `OPEN_ISSUES.md`;
- `CLOSED_ISSUES.md`;
- `KNOWN_FINDINGS.md`;
- `AGENTS_LOG.md`.

Trace tools and captured trace outputs were reviewed and retained, not modified by PROMT-ID-0144.

## 13. Remaining unrelated Build-0573 items

This result closes only the player-facing question. It does not broaden Build-0573 acceptance. OPEN-040 still owns its progressed Record-29/later-progression condition; OPEN-041 retains its broader presentation lifecycle checks; OPEN-042 retains its complete first-visible scene set. Concurrent audio and other unrelated work are unchanged.

## Final conclusion

**Original arcade preserves final facing across R1-S3→R2-S1. Build 0573 matches. No production fix is required.**

TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0144
