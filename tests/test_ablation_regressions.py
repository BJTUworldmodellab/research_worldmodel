import unittest

import numpy as np

from scripts.evaluate_semantic_relation_respace import PREDICATES, relation_holds
from src.ablation.evaluators import evaluate_bounds_proxy
from src.ablation.repairers import repair_overlap_with_sg_guard


class AblationRegressionTests(unittest.TestCase):
    def _overlapping_scene(self):
        object_types = ["chair", "table"]
        predicate_types = [
            "above",
            "left of",
            "in front of",
            "closely left of",
            "closely in front of",
            "below",
            "right of",
            "behind",
            "closely right of",
            "closely behind",
        ]
        cls_dim = len(object_types) + 1
        bbox = np.zeros((2, cls_dim + 7), dtype=np.float64)
        bbox[:, cls_dim + 3 : cls_dim + 6] = 0.5
        objs = np.array([0, 1], dtype=np.int64)
        edges = np.full((2, 2), len(predicate_types), dtype=np.int64)
        masks = np.ones(2, dtype=np.int64)
        return bbox, objs, edges, masks, object_types, predicate_types

    def test_zero_iterations_returns_baseline(self):
        args = self._overlapping_scene()
        repaired, log = repair_overlap_with_sg_guard(*args, max_iter=0)
        np.testing.assert_array_equal(repaired, args[0])
        self.assertEqual(log["iterations_run"], 0)

    def test_repair_seed_controls_tied_center_direction(self):
        args = self._overlapping_scene()
        repaired_a, _ = repair_overlap_with_sg_guard(*args, max_iter=1, seed=7)
        repaired_b, _ = repair_overlap_with_sg_guard(*args, max_iter=1, seed=7)
        np.testing.assert_array_equal(repaired_a, repaired_b)

    def test_bounds_proxy_uses_supplied_class_dimension(self):
        cls_dim = 3
        bbox = np.zeros((1, cls_dim + 7), dtype=np.float64)
        bbox[0, cls_dim] = 2.0
        bounds = {
            "translations": np.array([[-1.0, -1.0, -1.0], [1.0, 1.0, 1.0]])
        }
        result = evaluate_bounds_proxy(
            bbox,
            np.ones(1, dtype=np.int64),
            bounds,
            cls_dim,
        )
        self.assertEqual(result["proxy_n_translation_violations"], 1)

    def test_respace_close_predicates_match_canonical_order(self):
        self.assertEqual(PREDICATES[4], "close_front")
        self.assertEqual(PREDICATES[8], "close_right")
        self.assertEqual(PREDICATES[9], "close_behind")

        center = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.assertTrue(
            relation_holds(
                {"x": 0.0, "y": 0.0, "z": 0.5},
                4,
                center,
                close_threshold=0.75,
            )
        )
        self.assertTrue(
            relation_holds(
                {"x": 0.5, "y": 0.0, "z": 0.0},
                8,
                center,
                close_threshold=0.75,
            )
        )
        self.assertTrue(
            relation_holds(
                {"x": 0.0, "y": 0.0, "z": -0.5},
                9,
                center,
                close_threshold=0.75,
            )
        )


if __name__ == "__main__":
    unittest.main()
