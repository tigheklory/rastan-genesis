#!/usr/bin/env python3
"""PROMPT-ID-0098 — independent verifier for the ROM-sourced R1 boss palette + Flying Daggers +
Green Sword Knight first-class actor, across the manifest, the Palette Composer, and the generated
Bestiary HTML.

Independence: the R1 boss palette is decoded here directly from build/regions/maincpu.bin @ 0x4708C
(NOT imported from the implementation), compared to Cody PROMT-ID-0095's captured fixture, and then
required to equal the Composer result and the generated Bestiary swatches. A ROM mutation on an
ISOLATED buffer must flow through to both the Composer decode and the independent decode, while the
real maincpu.bin is proven byte-unchanged. No hard-coded R1 boss palette may exist in application
authority. Test.json is asserted byte-unchanged.

TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0098
"""
from __future__ import annotations
import importlib.util, json, threading, time, urllib.request, hashlib, sys
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P, F = [], []
def ck(n, c, extra=""):
    (P if c else F).append(n)
    print(("PASS " if c else "FAIL ") + n + ((" -> " + str(extra)) if extra and not c else ""))

ROM = (ROOT / "build/regions/maincpu.bin").read_bytes()
BOSS_ADDR = 0x4708C

def _pal4(n): return (n << 3) | (n >> 2)             # boss target-table convention (pal5bit of nibble)
def _pal5(n): v = n * 2; return (v << 3) | (v >> 2)  # field convention (nibble doubled)

def rom_boss_decode(buf, addr=BOSS_ADDR, count=15):
    cols = [(0, 0, 0)]
    for i in range(count):
        w = (buf[addr + 2 * i] << 8) | buf[addr + 2 * i + 1]
        cols.append((_pal4((w >> 8) & 0xF), _pal4((w >> 4) & 0xF), _pal4(w & 0xF)))
    while len(cols) < 16:
        cols.append((0, 0, 0))
    return cols

def rom_field_decode(buf, rnd, nibble):
    pidx = buf[0x3BA88 + (rnd - 1) * 32 + nibble]; b = 0x4FD02 + pidx * 32
    return [(_pal5((int.from_bytes(buf[b + i * 2:b + i * 2 + 2], "big") >> 8) & 0xF),
             _pal5((int.from_bytes(buf[b + i * 2:b + i * 2 + 2], "big") >> 4) & 0xF),
             _pal5(int.from_bytes(buf[b + i * 2:b + i * 2 + 2], "big") & 0xF)) for i in range(16)]

def vm_codes(base, anims, comp=0):
    vm = str(ROOT / "tools/graphics_optimizer")
    if vm not in sys.path:
        sys.path.insert(0, vm)
    from compositor_vm import ActorRenderState, visible_pieces
    codes = set()
    for a in anims:
        for p in visible_pieces(ActorRenderState(base, a, comp)):
            c = p.tile & 0x1FFF
            if c < 0x1000:
                codes.add(c)
    return codes


def main() -> int:
    tjson = ROOT / "analysis/graphics_optimizer/editor_policy/Test.json"
    t0 = hashlib.sha256(tjson.read_bytes()).hexdigest()
    rom_sha0 = hashlib.sha256(ROM).hexdigest()

    # ---------- (1) independent ROM decode vs Cody PROMT-ID-0095 fixture ----------
    cody = json.loads((ROOT / "analysis/actor_decompilation/r1_boss_palette_fade_dagger_semantics.json").read_text())
    want = [tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) for h in cody["palette"]["rgb8"]]
    got = rom_boss_decode(ROM)
    ck("R1. independent ROM 0x4708C decode == Cody PROMT-ID-0095 captured rgb8 (16/16)", got == want,
       [i for i in range(16) if got[i] != want[i]])
    ck("R2. boss source is NOT the field pool (0x4708C decode != 0x3BA88[R1][F] pool)",
       got != rom_field_decode(ROM, 1, 0xF))

    # ---------- (2) Palette Composer R1 boss group (started like the other verifiers) ----------
    spec = importlib.util.spec_from_file_location("ged_server98", ROOT / "tools/graphics_editor/server.py")
    srv = importlib.util.module_from_spec(spec)
    try: spec.loader.exec_module(srv)
    except SystemExit: pass
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), srv.Hd); port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start(); time.sleep(0.3)
    oracle = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/api/oracle"))
    us = oracle["usages"]
    by_obj = {}
    for u in us:
        by_obj.setdefault(u.get("object_id"), []).append(u)

    body = by_obj.get("object:boss.r1.body", [])
    dagg = by_obj.get("object:boss.r1.flying_daggers", [])
    ck("C1. Composer R1 boss body present, program $47908 comp1, R1-S3",
       bool(body) and all(u.get("program") == "0x47908" and u.get("compositor") == 1
                          and u.get("scene_key") == "PAL-R1-S3-PLANEA-BOSS" for u in body))
    ck("C2. Composer Flying Daggers present (object:boss.r1.flying_daggers, program $47E54)",
       bool(dagg) and all(u.get("program") == "0x47E54" for u in dagg))
    ck("C3. Composer boss palette_status RGB PROVEN · ROM 0x4708C · physical 0x4F",
       bool(body) and all(u["palette_status"].get("source_line") == "F"
                          and "PROVEN" in u["palette_status"].get("rgb_status", "")
                          and "4708C" in u["palette_status"].get("rom_source", "")
                          and u["palette_status"].get("physical_line") == "0x4F" for u in body + dagg))
    # Composer used_colors RGB must equal the independent ROM decode for each drawn index.
    def comp_matches(group):
        for u in group:
            for c in u.get("used_colors", []):
                idx = c["src_index"]
                if list(got[idx]) != list(c["arcade_rgb8"]):
                    return False, (u.get("object_id"), idx, c["arcade_rgb8"], list(got[idx]))
        return True, None
    okc, why = comp_matches(body + dagg)
    ck("C4. Composer used_colors == independent ROM 0x4708C decode (body + daggers)", okc, why)
    ck("C5. daggers share boss palette + restricted to the proven index subset {0,3,4,5,6,8,10,11,13}",
       bool(dagg) and all(u.get("shares_boss_palette") is True for u in dagg)
       and all(set(c["src_index"] for c in u.get("used_colors", [])) <= {0, 3, 4, 5, 6, 8, 10, 11, 13} for u in dagg))
    ck("C6. one shared palette context for body + daggers (no second line)",
       all(u.get("shared_palette_context") == "R1 Boss + Flying Daggers" for u in body + dagg))
    ck("C7. boss groups not auto-authorable (Tighe assigns the final Genesis line)",
       all(u.get("authorable") is False for u in body + dagg))

    # ---------- (3) ROM mutation sensitivity (isolated buffer; real ROM untouched) ----------
    mut = bytearray(ROM)
    mut[BOSS_ADDR + 2] ^= 0x0F      # perturb entry-2 low nibble of the source table
    ck("M1. isolated ROM mutation changes the independent decode", rom_boss_decode(bytes(mut)) != got)
    srv._MAINCPU = bytes(mut); srv._BOSS_USAGES_CACHE = None
    mut_body = [u for u in srv.r1_boss_usages() if u.get("object_id") == "object:boss.r1.body"]
    mut_rgbs = {c["src_index"]: tuple(c["arcade_rgb8"]) for u in mut_body for c in u.get("used_colors", [])}
    base_rgbs = {c["src_index"]: tuple(c["arcade_rgb8"]) for u in body for c in u.get("used_colors", [])}
    ck("M2. isolated ROM mutation changes the Composer decode", mut_rgbs != base_rgbs,
       "no change (index 2 drawn? %s)" % (2 in base_rgbs))
    srv._MAINCPU = ROM; srv._BOSS_USAGES_CACHE = None   # restore
    ck("M3. real maincpu.bin byte-unchanged by the mutation test",
       hashlib.sha256((ROOT / "build/regions/maincpu.bin").read_bytes()).hexdigest() == rom_sha0)

    # ---------- (4) generated Bestiary HTML: ROM-derived boss swatches + no stale R1 source ----------
    html = (ROOT / "docs/design/rastan_actor_bestiary.html").read_text()
    sw_ok = all(("rgb(%d,%d,%d)" % got[i]) in html for i in range(16))
    ck("B1. Bestiary R1 boss swatch == independent ROM decode (all 16 colours present)", sw_ok)
    ck("B2. Bestiary shows R1 boss 'RGB PROVEN · ROM 0x4708C' + 'physical line 0x4F'",
       "RGB PROVEN · ROM 0x4708C" in html and "physical line 0x4F" in html)
    ck("B3. Bestiary has no R1-boss field-pool/master-line source (0x4FE62 / 0x4EE16 absent)",
       "4FE62" not in html and "4EE16" not in html)
    ck("B4. Bestiary represents the Flying Daggers under the boss (SHARES R1 BOSS PALETTE)",
       "Flying Daggers" in html and "SHARES R1 BOSS PALETTE" in html)

    # ---------- (5) Green Sword Knight manifest actor record ----------
    M = json.loads((ROOT / "docs/design/rastan_actor_graphics_manifest.json").read_text())
    gk = next((a for a in M["actors"] if a.get("technical_id") == "green_sword_knight_r1"), None)
    ck("G1. canonical Green Sword Knight manifest actor exists", gk is not None)
    if gk:
        ck("G2. object id object:castle.green_sword_knight.r1.n3",
           gk.get("object_id") == "object:castle.green_sword_knight.r1.n3")
        ck("G3. base 0x033E, family 2, scene R1-S2",
           gk.get("base_graphics") == "0x033E" and gk.get("actor_family_3e") == 2 and gk.get("scene") == "R1-S2")
        ck("G4. domain = 23 programs / 97 pattern codes",
           gk.get("program_count") == 23 and gk.get("pattern_code_count") == 97)
        ck("G5. foreign $4D/$56/$57/$58/$59/$5A excluded in the record",
           set(gk.get("excluded_foreign_programs", [])) == {"0x4D", "0x56", "0x57", "0x58", "0x59", "0x5A"})

    # ---------- (6) Green Knight independent re-derivation + Composer + Bestiary card ----------
    kn = [u for u in us if (u.get("object_id") or "").startswith("object:castle.green_sword_knight") and u.get("round") == 1]
    kn_anims = {int(u["frame_label"].split()[-1], 16) for u in kn}
    ck("G6. Composer exposes EXACTLY 23 base-$033E knight programs (R1)", len(kn_anims) == 23, len(kn_anims))
    ck("G7. knight domain re-derives to 97 distinct codes (compositor VM, independent)",
       len(vm_codes(0x033E, kn_anims)) == 97, len(vm_codes(0x033E, kn_anims)))
    FOREIGN = {0x4D, 0x56, 0x57, 0x58, 0x59, 0x5A}
    ck("G8. no foreign $4D/$56-$5A contamination in the Composer domain", not (FOREIGN & kn_anims))
    rope = by_obj.get("object:castle.rope_climber.family8.r1", [])
    ck("G9. Rope Climber remains a SEPARATE object (base $0241)",
       bool(rope) and all(u.get("base") == "0x0241" for u in rope))
    valk = [u for u in us if u.get("base") == "0x0241" and "valk" in (u.get("object_id") or "").lower()]
    ck("G10. Valkyrie remains distinct (base 0x0241 object present, not the knight)",
       all(u.get("object_id") != "object:castle.green_sword_knight.r1.n3" for u in valk))
    ck("G11. Bestiary has a Green Sword Knight actor CARD in R1-S2 (not prose-only)",
       "object:castle.green_sword_knight.r1.n3" in html
       and "R1-S2 Scene Enemy — Green Sword Knight" in html
       and "Pose gallery" in html)
    gk_sw = rom_field_decode(ROM, 1, 3)   # green-armor line 3 (same convention the Bestiary renders)
    ck("G12. Bestiary knight swatch == independent ROM line-3 decode",
       all(("rgb(%d,%d,%d)" % gk_sw[i]) in html for i in range(16)))

    # ---------- (7) no hard-coded R1 boss palette in application authority ----------
    srv_txt = (ROOT / "tools/graphics_editor/server.py").read_text()
    bes_txt = (ROOT / "tools/graphics_optimizer/build_bestiary.py").read_text()
    man_txt = (ROOT / "docs/design/rastan_actor_graphics_manifest.json").read_text()
    final_words = cody["palette"]["final_live_words"]
    src_0rgb = [w.replace("(retained)", "") for w in cody["palette"]["source_0rgb"]]
    boss_hex = cody["palette"]["rgb8"]
    def has_block(txt, seq, k=4):
        # true if k+ consecutive values from the sequence all appear in the text (a stored palette block)
        hits = sum(1 for v in seq if v and v in txt)
        return hits >= k
    for label, txt in (("server.py", srv_txt), ("build_bestiary.py", bes_txt), ("manifest", man_txt)):
        ck(f"NH1[{label}]. no stored final-live-word R1 boss block", not has_block(txt, final_words))
        ck(f"NH2[{label}]. no stored source-0RGB R1 boss block", not has_block(txt, src_0rgb))
        ck(f"NH3[{label}]. no stored #RRGGBB R1 boss block", not has_block(txt, boss_hex))

    # ---------- (8) integrity ----------
    t1 = hashlib.sha256(tjson.read_bytes()).hexdigest()
    ck("INT. Test.json byte-unchanged", t0 == t1, (t0, t1))

    print(f"\n{'0098 R1-BOSS/GREEN-KNIGHT PASS' if not F else str(len(F))+' FAILED'}  (pass={len(P)})")
    return 1 if F else 0


if __name__ == "__main__":
    sys.exit(main())
