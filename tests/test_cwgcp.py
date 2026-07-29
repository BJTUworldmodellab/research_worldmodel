import unittest

import numpy as np

from src.cwgcp import (
    CWGCPConfig,
    LayoutObject,
    RelationProposal,
    repair_layout_cwgcp,
)
from src.cwgcp.adapters import apply_centers_to_exported_boxes
from src.cwgcp.assignment import resolve_relations
from src.cwgcp.geometry import collision_metrics, exact_overlap_metrics
from src.cwgcp.constraints import relation_violation
from src.cwgcp.types import ResolvedRelation
from scripts.run_cwgcp_pilot import (
    _bootstrap_delta,
    _method_budget,
    _split_for_scene,
)


def _object(index, class_id, x, z, half_x=0.2, half_z=0.2):
    return LayoutObject(
        index=index,
        class_id=class_id,
        class_name=f"class_{class_id}",
        center_xz=np.array([x, z], dtype=np.float64),
        half_size_xz=np.array([half_x, half_z], dtype=np.float64),
    )


def _config(**overrides):
    values = dict(
        restarts=2,
        outer_iterations=2,
        solver_max_iterations=80,
        initial_trust_radius=0.8,
        max_trust_radius=1.2,
        per_object_budget=1.2,
        total_movement_budget=1.2,
        max_edited_objects=2,
        seed=7,
    )
    values.update(overrides)
    return CWGCPConfig(**values)


class CWGCPTests(unittest.TestCase):
    def test_anchor_residual_budget_contains_anchor_and_bounds_extra_movement(self):
        floor_movement = {"total": 0.4, "edited": 1}
        self.assertEqual(
            _method_budget(
                floor_movement,
                "anchor_plus_residual",
                total_movement_cap=3.6,
                edit_cap=3,
                anchor_residual_cap=0.25,
            ),
            (0.65, 3),
        )
        self.assertEqual(
            _method_budget(
                {"total": 3.5, "edited": 2},
                "anchor_plus_residual",
                total_movement_cap=3.6,
                edit_cap=3,
                anchor_residual_cap=0.25,
            ),
            (3.6, 3),
        )

    def test_method_budget_rejects_cap_smaller_than_anchor(self):
        with self.assertRaises(ValueError):
            _method_budget(
                {"total": 1.0, "edited": 2},
                "anchor_plus_residual",
                total_movement_cap=0.9,
                edit_cap=3,
                anchor_residual_cap=0.25,
            )
        with self.assertRaises(ValueError):
            _method_budget(
                {"total": 1.0, "edited": 2},
                "fixed_cap",
                total_movement_cap=3.6,
                edit_cap=1,
                anchor_residual_cap=0.25,
            )

    def test_source_scene_split_is_deterministic_and_cluster_safe(self):
        first = _split_for_scene("shared-scene", "frozen-salt", 0.4)
        second = _split_for_scene("shared-scene", "frozen-salt", 0.4)
        self.assertEqual(first, second)
        self.assertIn(first, {"dev", "validation"})

    def test_bootstrap_clusters_records_by_source_scene(self):
        rows = [
            {
                "scene_uid": "shared",
                "lhs_satisfied": 1,
                "lhs_total": 1,
                "rhs_satisfied": 0,
                "rhs_total": 1,
            },
            {
                "scene_uid": "shared",
                "lhs_satisfied": 0,
                "lhs_total": 1,
                "rhs_satisfied": 1,
                "rhs_total": 1,
            },
            {
                "scene_uid": "unique",
                "lhs_satisfied": 1,
                "lhs_total": 1,
                "rhs_satisfied": 0,
                "rhs_total": 1,
            },
        ]
        interval = _bootstrap_delta(rows, "lhs", "rhs", 100, 7)
        self.assertEqual(interval["scene_count"], 3)
        self.assertEqual(interval["cluster_count"], 2)

    def test_unique_assignment_keeps_full_confidence(self):
        objects = [_object(0, 1, 0, 0), _object(1, 2, 1, 0)]
        proposal = RelationProposal(1, "left of", 2)
        resolved, unresolved = resolve_relations(objects, [proposal], _config())
        self.assertEqual(unresolved, [])
        self.assertEqual(len(resolved), 1)
        self.assertEqual((resolved[0].subject_index, resolved[0].object_index), (0, 1))
        self.assertEqual(resolved[0].confidence, 1.0)

    def test_ambiguous_assignment_lowers_confidence(self):
        objects = [
            _object(0, 1, 0.0, 0.0),
            _object(1, 1, 0.02, 0.0),
            _object(2, 2, 1.0, 0.0),
        ]
        proposal = RelationProposal(1, "left of", 2)
        resolved, _ = resolve_relations(objects, [proposal], _config())
        self.assertGreater(resolved[0].confidence, 0.0)
        self.assertLess(resolved[0].confidence, 0.2)

    def test_vertical_relation_is_explicitly_unresolved(self):
        objects = [_object(0, 1, 0, 0), _object(1, 2, 1, 0)]
        proposal = RelationProposal(1, "above", 2)
        resolved, unresolved = resolve_relations(objects, [proposal], _config())
        self.assertEqual(resolved, [])
        self.assertEqual(unresolved[0]["reason"], "unsupported_non_xz_relation")

    def test_front_and_behind_use_positive_and_negative_z(self):
        objects = [_object(0, 1, 0, 1), _object(1, 2, 0, 0)]
        centers = np.stack([obj.center_xz for obj in objects])
        front = ResolvedRelation(0, "in front of", 1, 1.0, 0, 1.0)
        behind = ResolvedRelation(0, "behind", 1, 1.0, 0, 1.0)
        self.assertEqual(
            relation_violation(centers, objects, front, _config()), 0.0
        )
        self.assertGreater(
            relation_violation(centers, objects, behind, _config()), 0.0
        )

    def test_zero_budget_returns_bitwise_identity(self):
        objects = [_object(0, 1, 1, 0), _object(1, 2, 0, 0)]
        result = repair_layout_cwgcp(
            objects,
            [RelationProposal(1, "left of", 2)],
            config=_config(total_movement_budget=0.0),
        )
        np.testing.assert_array_equal(
            result.centers_xz,
            np.stack([obj.center_xz for obj in objects]),
        )
        self.assertFalse(result.accepted)
        self.assertEqual(result.certificate["rollback_reason"], "zero_budget")

    def test_solver_is_deterministic_for_fixed_seed(self):
        objects = [_object(0, 1, 1, 0), _object(1, 2, 0, 0)]
        relations = [RelationProposal(1, "left of", 2)]
        first = repair_layout_cwgcp(objects, relations, config=_config())
        second = repair_layout_cwgcp(objects, relations, config=_config())
        np.testing.assert_allclose(first.centers_xz, second.centers_xz, atol=1e-10)
        self.assertEqual(first.accepted, second.accepted)

    def test_movement_and_edit_budgets_are_enforced(self):
        objects = [
            _object(0, 1, 1.0, 0.0),
            _object(1, 2, 0.0, 0.0),
            _object(2, 3, 0.0, -1.0),
        ]
        relations = [
            RelationProposal(1, "left of", 2),
            RelationProposal(3, "in front of", 2),
        ]
        config = _config(
            per_object_budget=0.35,
            total_movement_budget=0.5,
            max_edited_objects=2,
        )
        result = repair_layout_cwgcp(objects, relations, config=config)
        movement = np.linalg.norm(
            result.centers_xz - np.stack([obj.center_xz for obj in objects]),
            axis=1,
        )
        self.assertLessEqual(float(movement.max()), 0.350001)
        self.assertLessEqual(float(movement.sum()), 0.500001)
        self.assertLessEqual(int(np.count_nonzero(movement > 1e-3)), 2)

    def test_accepted_solution_does_not_increase_obb_collisions(self):
        objects = [
            _object(0, 1, 1.0, 0.0),
            _object(1, 2, 0.0, 0.0),
            _object(2, 3, 2.0, 2.0),
        ]
        baseline = collision_metrics(
            np.stack([obj.center_xz for obj in objects]), objects
        )
        result = repair_layout_cwgcp(
            objects,
            [RelationProposal(1, "left of", 2)],
            config=_config(),
        )
        repaired = collision_metrics(result.centers_xz, objects)
        baseline_exact = exact_overlap_metrics(
            np.stack([obj.center_xz for obj in objects]), objects
        )
        repaired_exact = exact_overlap_metrics(result.centers_xz, objects)
        self.assertLessEqual(
            repaired["collision_pairs"], baseline["collision_pairs"]
        )
        self.assertLessEqual(
            repaired["collision_penalty"],
            baseline["collision_penalty"] + 1e-7,
        )
        self.assertLessEqual(
            repaired_exact["exact_obb_overlap_area"],
            baseline_exact["exact_obb_overlap_area"] + 1e-7,
        )

    def test_export_adapter_changes_only_x_and_z(self):
        boxes = [
            {
                "index": 0,
                "class_id": 1,
                "class_name": "chair",
                "translation": [0.0, 0.7, 0.0],
                "size": [0.2, 0.4, 0.2],
                "angle": 0.3,
            }
        ]
        repaired = apply_centers_to_exported_boxes(
            boxes, np.array([[1.0, -2.0]])
        )
        self.assertEqual(repaired[0]["translation"], [1.0, 0.7, -2.0])
        self.assertEqual(repaired[0]["size"], boxes[0]["size"])
        self.assertEqual(repaired[0]["angle"], boxes[0]["angle"])
        self.assertEqual(boxes[0]["translation"], [0.0, 0.7, 0.0])

    def test_external_safety_callback_can_force_rollback(self):
        objects = [_object(0, 1, 1, 0), _object(1, 2, 0, 0)]

        def safety(centers):
            moved = float(
                np.linalg.norm(
                    centers - np.stack([obj.center_xz for obj in objects])
                )
            )
            return {"mesh_collision_pairs": 0.0 if moved == 0 else 1.0}

        result = repair_layout_cwgcp(
            objects,
            [RelationProposal(1, "left of", 2)],
            config=_config(),
            external_safety_fn=safety,
        )
        self.assertFalse(result.accepted)
        self.assertEqual(
            result.certificate["rollback_reason"],
            "no_candidate_passed_gate",
        )

    def test_invalid_external_safety_cannot_bypass_obb_gate(self):
        objects = [_object(0, 1, 0.5, 0), _object(1, 2, 0, 0)]
        colliding_warm = np.array([[0.1, 0.0], [0.0, 0.0]])
        for invalid_result in ({}, {"mesh_collision_pairs": float("nan")}):
            result = repair_layout_cwgcp(
                objects,
                [RelationProposal(1, "left of", 2)],
                config=_config(total_movement_budget=1.0),
                external_safety_fn=lambda _centers, value=invalid_result: value,
                warm_start_centers=[colliding_warm],
            )
            self.assertFalse(result.accepted)

    def test_non_finite_budgets_are_rejected(self):
        for field in ("per_object_budget", "total_movement_budget"):
            with self.assertRaises(ValueError):
                _config(**{field: float("nan")})
            with self.assertRaises(ValueError):
                _config(**{field: float("inf")})

    def test_candidate_cannot_break_previously_satisfied_relation(self):
        objects = [
            _object(0, 1, -1.0, 0.0),
            _object(1, 2, 0.0, 0.0),
            _object(2, 3, 0.0, -1.0),
        ]
        result = repair_layout_cwgcp(
            objects,
            [
                RelationProposal(1, "left of", 2),
                RelationProposal(3, "in front of", 2),
            ],
            config=_config(total_movement_budget=0.4, max_edited_objects=1),
        )
        if result.accepted:
            baseline = result.certificate["solver"]["baseline_metrics"][
                "relation_violations"
            ]
            selected = result.certificate["solver"]["selected_metrics"][
                "relation_violations"
            ]
            for before, after in zip(baseline, selected):
                if before <= 1e-6:
                    self.assertLessEqual(after, 1e-6)

    def test_safe_warm_start_is_considered_as_candidate(self):
        objects = [_object(0, 1, 0.5, 0), _object(1, 2, 0, 0)]
        warm = np.array([[-0.5, 0.0], [0.0, 0.0]])
        result = repair_layout_cwgcp(
            objects,
            [RelationProposal(1, "left of", 2)],
            config=_config(total_movement_budget=1.5),
            warm_start_centers=[warm],
        )
        self.assertTrue(result.accepted)
        self.assertGreaterEqual(result.certificate["warm_start_count"], 1)
        self.assertLessEqual(
            result.certificate["solver"]["selected_metrics"][
                "weighted_relation_violation"
            ],
            result.certificate["solver"]["baseline_metrics"][
                "weighted_relation_violation"
            ],
        )

    def test_certificate_hash_covers_warm_start_and_provenance(self):
        objects = [_object(0, 1, 0.5, 0), _object(1, 2, 0, 0)]
        relations = [RelationProposal(1, "left of", 2)]
        first = repair_layout_cwgcp(
            objects,
            relations,
            config=_config(),
            warm_start_centers=[np.array([[-0.5, 0.0], [0.0, 0.0]])],
            provenance={"scene_uid": "scene-a"},
        )
        second = repair_layout_cwgcp(
            objects,
            relations,
            config=_config(),
            warm_start_centers=[np.array([[-0.4, 0.0], [0.0, 0.0]])],
            provenance={"scene_uid": "scene-a"},
        )
        third = repair_layout_cwgcp(
            objects,
            relations,
            config=_config(),
            warm_start_centers=[np.array([[-0.5, 0.0], [0.0, 0.0]])],
            provenance={"scene_uid": "scene-b"},
        )
        self.assertNotEqual(
            first.certificate["input_hash"],
            second.certificate["input_hash"],
        )
        self.assertNotEqual(
            first.certificate["input_hash"],
            third.certificate["input_hash"],
        )
        self.assertEqual(
            first.certificate["layout_relation_hash"],
            second.certificate["layout_relation_hash"],
        )


if __name__ == "__main__":
    unittest.main()
