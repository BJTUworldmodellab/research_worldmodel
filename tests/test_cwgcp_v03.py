import unittest

import numpy as np

from src.cwgcp import CWGCPConfig, LayoutObject, RelationProposal
from src.cwgcp.repairer import repair_layout_cwgcp


def _object(index, class_id, x, z, half_x=0.05, half_z=0.05):
    return LayoutObject(
        index=index,
        class_id=class_id,
        class_name=f"class_{class_id}",
        center_xz=np.array([x, z], dtype=np.float64),
        half_size_xz=np.array([half_x, half_z], dtype=np.float64),
    )


def _config(**overrides):
    values = dict(
        restarts=1,
        outer_iterations=2,
        solver_max_iterations=80,
        initial_trust_radius=0.8,
        max_trust_radius=1.2,
        per_object_budget=2.5,
        total_movement_budget=3.0,
        max_edited_objects=2,
        seed=11,
    )
    values.update(overrides)
    return CWGCPConfig(**values)


class FAPSPV03Tests(unittest.TestCase):
    def test_full_coverage_anchor_skips_solver_when_strict_gain_is_required(self):
        objects = [_object(0, 1, -0.5, 0.0), _object(1, 2, 0.0, 0.0)]
        anchor = np.array([[-0.5, 0.0], [0.0, 0.0]], dtype=np.float64)
        result = repair_layout_cwgcp(
            objects,
            [RelationProposal(1, "left of", 2)],
            config=_config(
                coverage_first_selection=True,
                require_coverage_gain=True,
                enable_proposal_nudge=True,
            ),
            anchor_centers=anchor,
            warm_start_centers=[anchor],
        )
        self.assertFalse(result.accepted)
        self.assertEqual(
            result.certificate["rollback_reason"],
            "anchor_already_full_coverage",
        )
        self.assertEqual(result.certificate["solver"]["solver_runs"], [])
        np.testing.assert_allclose(result.centers_xz, anchor, atol=1e-10)

    def test_proposal_nudge_crosses_relation_boundary_under_all_gates(self):
        objects = [
            _object(0, 1, 0.02, 0.0, half_x=0.005, half_z=0.005),
            _object(1, 2, 0.0, 0.0, half_x=0.005, half_z=0.005),
        ]
        anchor = np.array([[0.02, 0.0], [0.0, 0.0]], dtype=np.float64)
        result = repair_layout_cwgcp(
            objects,
            [RelationProposal(1, "left of", 2)],
            config=_config(
                relation_margin=0.02,
                total_movement_budget=0.1,
                max_edited_objects=1,
                coverage_first_selection=True,
                require_coverage_gain=True,
                enable_proposal_nudge=True,
                restarts=1,
                outer_iterations=1,
                solver_max_iterations=1,
            ),
            anchor_centers=anchor,
        )
        self.assertTrue(result.accepted)
        self.assertEqual(result.certificate["algorithm"], "FA-PSP")
        self.assertEqual(
            result.certificate["algorithm_version"], "0.3.0-fa-psp"
        )
        selected = result.certificate["solver"]["selected_metrics"]
        self.assertEqual(selected["candidate_source"], "proposal_nudge")
        self.assertEqual(selected["proposal_satisfied_relations"], 1)
        self.assertLessEqual(selected["total_movement"], 0.1 + 1e-9)
        self.assertEqual(selected["exact_obb_collision_pairs"], 0)

    def test_anchor_is_returned_when_no_candidate_passes_gate(self):
        objects = [_object(0, 1, 1.0, 0.0), _object(1, 2, 0.0, 0.0)]
        anchor = np.array([[-0.5, 0.0], [0.0, 0.0]], dtype=np.float64)
        result = repair_layout_cwgcp(
            objects,
            [RelationProposal(1, "left of", 2)],
            config=_config(max_edited_objects=0),
            anchor_centers=anchor,
        )
        self.assertFalse(result.accepted)
        np.testing.assert_allclose(result.centers_xz, anchor, atol=1e-10)
        selected = result.certificate["solver"]["selected_metrics"]
        self.assertEqual(selected["candidate_source"], "anchor_rollback")

    def test_warm_start_refine_runs_from_warm_displacement(self):
        objects = [_object(0, 1, 0.6, 0.0), _object(1, 2, 0.0, 0.0)]
        warm = np.array([[0.1, 0.0], [0.0, 0.0]], dtype=np.float64)
        result = repair_layout_cwgcp(
            objects,
            [RelationProposal(1, "left of", 2)],
            config=_config(refine_warm_starts=True),
            warm_start_centers=[warm],
        )
        candidates = result.certificate["solver"]["candidate_metrics"]
        warm_metric = next(
            item for item in candidates if item["candidate_source"] == "warm_start"
        )
        refined_metric = next(
            item for item in candidates if item["candidate_source"] == "warm_refine"
        )
        self.assertTrue(
            any(
                run.get("source") == "warm_refine"
                for run in result.certificate["solver"]["solver_runs"]
            )
        )
        self.assertLess(
            refined_metric["proposal_weighted_relation_violation"],
            warm_metric["proposal_weighted_relation_violation"],
        )

    def test_coverage_first_rejects_lower_coverage_even_if_violation_improves(self):
        objects = [
            _object(0, 1, 0.0, 0.0),
            _object(1, 2, 0.0, 0.0),
            _object(2, 3, 0.0, 0.0),
        ]
        anchor = np.array([[-0.1, 0.0], [0.0, 0.0], [0.0, 0.0]])
        lower_violation_lower_coverage = np.array(
            [[0.1, 0.0], [0.0, 0.0], [1.55, 0.0]]
        )
        result = repair_layout_cwgcp(
            objects,
            [
                RelationProposal(1, "left of", 2),
                RelationProposal(3, "far", 2),
            ],
            config=_config(
                coverage_first_selection=True,
                restarts=1,
                outer_iterations=1,
                solver_max_iterations=1,
            ),
            anchor_centers=anchor,
            warm_start_centers=[lower_violation_lower_coverage],
        )
        np.testing.assert_allclose(result.centers_xz, anchor, atol=1e-10)
        rejected = [
            item
            for item in result.certificate["solver"]["candidate_metrics"]
            if item["candidate_source"] == "warm_start"
        ][0]
        self.assertIn("proposal_coverage_drop", rejected["rejection_reasons"])

    def test_require_coverage_gain_rejects_equal_coverage_violation_only_gain(self):
        objects = [
            _object(0, 1, 0.0, 0.0),
            _object(1, 2, 0.0, 0.0),
            _object(2, 3, 0.0, 0.0),
        ]
        anchor = np.array([[-0.1, 0.0], [0.0, 0.0], [0.0, 0.0]])
        same_coverage_better_violation = np.array(
            [[-0.1, 0.0], [0.0, 0.0], [1.55, 0.0]]
        )
        result = repair_layout_cwgcp(
            objects,
            [
                RelationProposal(1, "left of", 2),
                RelationProposal(3, "far", 2),
            ],
            config=_config(
                coverage_first_selection=True,
                require_coverage_gain=True,
                restarts=1,
                outer_iterations=1,
                solver_max_iterations=1,
            ),
            anchor_centers=anchor,
            warm_start_centers=[same_coverage_better_violation],
        )
        rejected = [
            item
            for item in result.certificate["solver"]["candidate_metrics"]
            if item["candidate_source"] == "warm_start"
        ][0]
        self.assertIn(
            "proposal_coverage_gain_required", rejected["rejection_reasons"]
        )


if __name__ == "__main__":
    unittest.main()
