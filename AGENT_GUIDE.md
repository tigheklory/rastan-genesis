# AGENT_GUIDE.md

## Rules for Agents (Andy / Cody)

### DO

- Follow strict scope
- Produce exact outputs
- Avoid speculation

### DO NOT

- Redesign system unless asked
- Add extra features
- Drift from prompt
- Emulate PC080SN/PC090OJ hardware or introduce/retain software chip devices, virtual chip
  RAM, C-window/name-RAM shadows, object-RAM mirrors, generic chip-address translation, or
  full-map projection as the final architecture

---

## PC080SN / PC090OJ work

Before proposing or implementing any tilemap (PC080SN) or sprite (PC090OJ) work, read
`docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md` (and `RULES.md` §11). Cut at the
arcade **semantic** boundary and produce final Genesis VDP/SAT output directly. In your
response, state the semantic cut and the chip-specific tail being removed.

---

## Workflow

1. Andy plans (strict, minimal)
2. Cody implements (exact)
3. Validate with evidence

---

## Philosophy

- Build real systems, not scaffolding
- Debug only after architecture is in place
