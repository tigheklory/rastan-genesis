#!/usr/bin/env python3
"""Deterministic checks for the offline palette residency analyzer."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_palette_residency as analyzer


class PaletteResidencyAnalyzerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args = analyzer.build_parser().parse_args([])
        cls.result = analyzer.analyze(cls.args)

    def test_effect_membership_and_no_sprites(self):
        effect = self.result["effect"]
        self.assertEqual(effect["members"], list(analyzer.FIRE_USAGES))
        self.assertEqual(effect["sprite_members"], [])
        self.assertEqual(effect["sprite_hypothesis"], "DISPROVEN_FOR_R1S2")
        self.assertEqual(effect["records"], [18])

    def test_bank_and_all_source_indices(self):
        self.assertEqual(self.result["inputs"]["source_palette_bank"], "0x014")
        self.assertEqual(self.result["effect"]["source_indices_used"], list(range(1, 16)))
        self.assertTrue(self.result["effect"]["all_nontransparent_source_indices_used"])

    def test_genesis_quantization_and_color_count_resolution(self):
        fire = self.result["fire_animation"]
        self.assertEqual(fire["initial_unique_count"], 9)
        self.assertEqual(fire["animated_phase_unique_counts"], [9, 8, 8])
        self.assertEqual(fire["lifecycle_unique_count"], 9)
        self.assertEqual(fire["maximum_simultaneously_required"], 9)
        self.assertEqual(fire["quantization_only_merges"], 6)
        self.assertIn("0x08EE", fire["lifecycle_unique_colors"])
        self.assertNotIn("0x08CE", fire["lifecycle_unique_colors"])

    def test_mode8_phase_reconstruction_and_keep(self):
        states = self.result["fire_animation"]["states"]
        self.assertEqual([s["name"] for s in states],
                         ["initial_bank_014", "mode8_phase_0", "mode8_phase_1", "mode8_phase_2"])
        self.assertEqual(states[1]["raw_arcade_words"][0], "0xFFFF")
        self.assertEqual(states[1]["raw_arcade_words"][5], "0xFFFF")
        self.assertEqual(states[1]["cram_words"][0], states[0]["cram_words"][0])
        self.assertEqual(states[1]["cram_words"][5], states[0]["cram_words"][5])
        self.assertEqual(states[3]["cram_words"][5], states[2]["cram_words"][5])
        self.assertEqual(states[3]["cram_words"][6], states[2]["cram_words"][6])

    def test_viewport_and_reverse_window(self):
        vis = self.result["visibility"]
        self.assertEqual(vis["viewport"], {
            "height_cells": 28,
            "source": ("tilemap_hooks.s .Lplane_a_visible_top_from_scroll_d0 semantics; "
                       "Genesis H40 320x224 = 40x28 cells"),
            "top_logical_row": 1,
            "width_cells": 40,
        })
        self.assertEqual(vis["effect_cell_bounds"]["global_x"], [1160, 1207])
        self.assertEqual(vis["effect_cell_bounds"]["global_x_pixels"], [9280, 9663])
        self.assertEqual(vis["candidate_camera_left_global_cells"], [1121, 1207])
        self.assertEqual(vis["candidate_camera_left_pixels_exact"], [8961, 9663])
        self.assertEqual(vis["critical_viewport_count"], 87)
        self.assertTrue(vis["reverse_supported"])

    def test_host_demand_and_line3_capacity(self):
        q = self.result["line3_question"]
        self.assertEqual(q["maximum_simultaneous_nonfire_castle_colors"], 13)
        self.assertEqual(q["fire_lifecycle_colors"], 9)
        self.assertEqual(q["exact_overlap"], 0)
        self.assertEqual(q["combined"], 22)
        self.assertEqual(q["over_capacity"], 7)
        self.assertEqual(self.result["candidate_lines"]["3"]["result"],
                         "REQUIRES_ARTISTIC_MERGES")
        self.assertGreater(len(q["affected_usage_ids"]), 0)
        self.assertGreater(len(q["affected_tile_codes"]), 0)

    def test_line1_free_slot_lease_is_proven(self):
        candidate = self.result["candidate_lines"]["1"]
        self.assertEqual(candidate["result"], "LOSSLESS_FREE_SLOT_LEASE")
        self.assertEqual(candidate["host_required_indices"], [])
        self.assertEqual(candidate["combined_lossless_requirement"], 9)
        slots = self.result["slot_classifications"]["1"]
        self.assertEqual(slots[0]["classification"], "USED_STATIC")
        for index in range(1, 16):
            self.assertEqual(slots[index]["classification"], "UNUSED_STABLE")

    def test_line1_roster_mapping_and_writer_proof(self):
        proof = self.result["line1_question"]
        self.assertEqual(proof["status"], "LOSSLESS_FREE_SLOT_LEASE")
        self.assertEqual(proof["possible_consumers"], [])
        self.assertEqual(proof["unresolved_consumers"], [])
        self.assertEqual(len(proof["excluded_consumers"]), 7)
        self.assertEqual(proof["unused_stable_indices"], list(range(1, 16)))
        self.assertEqual(proof["exact_overlap_count"], 0)
        self.assertFalse(proof["writer_proof"]["arbitrary_runtime_translation_required"])

    def test_line1_independent_regional_composite(self):
        regional = self.result["line1_question"]["regional_composite"]
        self.assertEqual(regional["result"], "LOSSLESS_REGIONAL_COMPOSITE")
        self.assertEqual(regional["lossless_union_size"], 9)
        self.assertEqual(regional["over_capacity"], 0)
        self.assertEqual(regional["artistic_merges_required"], 0)
        self.assertEqual(regional["sprite_usages_requiring_reindex"], [])
        self.assertEqual(regional["maximum_pattern_variant_cost_bytes"], 512)

    def test_reward_authored_rows_are_not_production_line1_consumers(self):
        excluded = {row["usage"]: row for row in self.result["line1_question"]["excluded_consumers"]}
        for uid in ("object:item.reward.kind01", "object:item.reward.kind11"):
            self.assertEqual(excluded[uid]["status"], "PROVEN_EXCLUDED")
            self.assertIn("embedded Line 0", excluded[uid]["evidence"])

    def test_line2_writer_blocks_lease(self):
        candidate = self.result["candidate_lines"]["2"]
        self.assertEqual(candidate["result"], "UNSAFE_DYNAMIC_WRITER")
        self.assertEqual(self.result["line_demand"]["plane_b"],
                         "INSUFFICIENT_Y_ENVELOPE_PROOF")
        slots = self.result["slot_classifications"]["2"]
        self.assertEqual(slots[0]["classification"], "USED_STATIC")
        self.assertTrue(all(slot["classification"] == "USED_DYNAMIC" for slot in slots[1:]))

    def test_slot_writer_classification(self):
        valid = {"USED_DYNAMIC", "USED_STATIC", "UNUSED_DYNAMIC", "UNUSED_STABLE", "UNKNOWN"}
        for slots in self.result["slot_classifications"].values():
            self.assertEqual(len(slots), 16)
            self.assertTrue(all(slot["classification"] in valid for slot in slots))

    def test_identical_runs_are_byte_identical(self):
        first = json.dumps(analyzer.analyze(self.args), indent=2, sort_keys=True) + "\n"
        second = json.dumps(analyzer.analyze(self.args), indent=2, sort_keys=True) + "\n"
        self.assertEqual(first, second)
        self.assertEqual(hashlib.sha256(first.encode()).hexdigest(),
                         hashlib.sha256(second.encode()).hexdigest())
        with tempfile.TemporaryDirectory() as td:
            a = Path(td) / "a.json"
            b = Path(td) / "b.json"
            a.write_text(first)
            b.write_text(second)
            self.assertEqual(a.read_bytes(), b.read_bytes())


if __name__ == "__main__":
    unittest.main()
