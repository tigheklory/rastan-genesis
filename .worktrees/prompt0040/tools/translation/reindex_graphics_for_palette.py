#!/usr/bin/env python3
"""Reusable OFFLINE dry-run graphics reindexer for palette consolidation (ANALYSIS ONLY).

Given a set of 4bpp 8x8 patterns whose pixel indices point at a *source* palette, and a *target*
consolidated Genesis palette, produce the remapped patterns + an old->new index table and verify the
result is EXACT (every source pixel's arcade color is present at its new index in the target line).

NOT wired into production. General by round/phase/owner via an explicit policy config; the caller
supplies source patterns, the source palette (16 arcade colors), and the target line (up to 16 colors).
A physical *variant* is required only when the same physical art is used under two source palettes that
demand conflicting index maps into the same target line.

Usage (library): reindex(patterns, source_palette, target_line) -> ReindexResult
CLI: python3 reindex_graphics_for_palette.py --config <policy.json>  (dry-run report to stdout)
"""
from __future__ import annotations
import argparse, json, hashlib
from dataclasses import dataclass, field


def _hash(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()[:12]


def _pixels(tile32: bytes):
    """32-byte Genesis 4bpp 8x8 -> list of 64 pixel indices (row-major)."""
    return [(tile32[r * 4 + c // 2] >> 4) if c % 2 == 0 else (tile32[r * 4 + c // 2] & 0xF)
            for r in range(8) for c in range(8)]


def _pack(px):
    """64 indices -> 32-byte 4bpp tile."""
    out = bytearray(32)
    for i in range(0, 64, 2):
        out[i // 2] = ((px[i] & 0xF) << 4) | (px[i + 1] & 0xF)
    return bytes(out)


@dataclass
class ReindexResult:
    ok: bool
    index_map: dict            # source_index -> target_index
    unmapped_colors: list      # arcade colors present in art but absent from target line
    remapped: dict             # source_hash -> remapped 32-byte tile (hex)
    variant_required: bool
    notes: list = field(default_factory=list)


def build_index_map(source_palette, target_line, used_indices):
    """Map each USED source index to the target-line index holding the exact same arcade color."""
    tgt = {tuple(c): i for i, c in enumerate(target_line)}
    imap, missing = {}, []
    for si in used_indices:
        col = tuple(source_palette[si])
        if col in tgt:
            imap[si] = tgt[col]
        else:
            missing.append((si, col))
    return imap, missing


def reindex(patterns, source_palette, target_line):
    """patterns: list of 32-byte tiles. source_palette/target_line: list of (R,G,B). EXACT only."""
    used = set()
    for t in patterns:
        used.update(_pixels(t))
    imap, missing = build_index_map(source_palette, target_line, used)
    remapped = {}
    ok = not missing
    for t in patterns:
        if ok:
            px = _pixels(t)
            rp = _pack([imap[i] for i in px])
            # exact-color verification
            assert all(target_line[imap[i]] == source_palette[i] for i in set(px))
            remapped[_hash(t)] = rp.hex()
    return ReindexResult(ok=ok, index_map=imap,
                         unmapped_colors=[{"src_index": si, "arcade_rgb": list(c)} for si, c in missing],
                         remapped=remapped, variant_required=False,
                         notes=["EXACT reindex" if ok else "target line missing colors -> not exact; "
                                "consolidation or a physical variant needed"])


def _load_patterns(rom_path, codes):
    rom = open(rom_path, "rb").read()
    return [rom[c * 32:(c + 1) * 32] for c in codes]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="policy JSON: round/phase/owner/source rom+codes/"
                    "source_palette/target_line")
    args = ap.parse_args()
    cfg = json.load(open(args.config))
    pats = _load_patterns(cfg["pattern_rom"], cfg["codes"])
    r = reindex(pats, cfg["source_palette"], cfg["target_line"])
    print(json.dumps({
        "round": cfg.get("round"), "phase": cfg.get("phase"), "owner": cfg.get("owner"),
        "exact": r.ok, "index_map": {str(k): v for k, v in r.index_map.items()},
        "unmapped_colors": r.unmapped_colors, "variant_required": r.variant_required,
        "patterns": len(pats), "notes": r.notes,
        "dry_run": True, "production_integration": False,
    }, indent=1))


if __name__ == "__main__":
    main()
