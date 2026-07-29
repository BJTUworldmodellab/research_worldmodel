import unittest

import numpy as np

from src.cwgcp import CWGCPConfig, LayoutObject, RelationProposal
from src.cwgcp import solver as cwgcp_solver
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
            config=_config(max_edited_objects=1),
            anchor_centers=anchor,
        )
        self.assertFalse(result.accepted)
        np.testing.assert_allclose(result.centers_xz, anchor, atol=1e-10)
        selected = result.certificate["solver"]["selected_metrics"]
        self.assertEqual(selected["candidate_source"], "anchor_rollback")

    def test_anchor_outside_declared_budget_is_rejected(self):
        objects = [_object(0, 1, 1.0, 0.0), _object(1, 2, 0.0, 0.0)]
        anchor = np.array([[-0.5, 0.0], [0.0, 0.0]], dtype=np.float64)
        with self.assertRaisesRegex(ValueError, "anchor_centers exceed"):
            repair_layout_cwgcp(
                objects,
                [RelationProposal(1, "left of", 2)],
                config=_config(
                    per_object_budget=1.0,
                    total_movement_budget=1.0,
                    max_edited_objects=0,
                ),
                anchor_centers=anchor,
            )

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


class FAPSPV031CloseProjectionTests(unittest.TestCase):
    def _project(self, delta, predicate, config):
        helper = getattr(
            cwgcp_solver,
            "_project_close_directional_delta",
            None,
        )
        if helper is None:
            self.fail("solver._project_close_directional_delta is not implemented")
        projected = helper(np.asarray(delta, dtype=np.float64), predicate, config)
        self.assertIsNotNone(projected)
        return np.asarray(projected, dtype=np.float64)

    def _assert_close_directional_feasible(self, delta, predicate, config):
        if predicate == "closely left of":
            signed_axis = -float(delta[0])
            orthogonal = abs(float(delta[1]))
        elif predicate == "closely right of":
            signed_axis = float(delta[0])
            orthogonal = abs(float(delta[1]))
        elif predicate == "closely in front of":
            signed_axis = float(delta[1])
            orthogonal = abs(float(delta[0]))
        elif predicate == "closely behind":
            signed_axis = -float(delta[1])
            orthogonal = abs(float(delta[0]))
        else:
            raise AssertionError(f"unexpected predicate: {predicate}")

        self.assertGreaterEqual(
            signed_axis + 1e-10,
            orthogonal + config.relation_margin,
        )
        self.assertLessEqual(
            float(np.linalg.norm(delta)),
            config.close_distance + 1e-10,
        )

    def test_close_directional_projection_satisfies_all_four_cones(self):
        config = _config(close_distance=0.75, relation_margin=0.2)
        cases = {
            "closely left of": np.array([1.0, 0.6], dtype=np.float64),
            "closely right of": np.array([-1.0, 0.6], dtype=np.float64),
            "closely in front of": np.array([0.6, -1.0], dtype=np.float64),
            "closely behind": np.array([0.6, 1.0], dtype=np.float64),
        }

        for predicate, delta in cases.items():
            with self.subTest(predicate=predicate):
                projected = self._project(delta, predicate, config)
                self._assert_close_directional_feasible(
                    projected,
                    predicate,
                    config,
                )

    def test_projection_matches_closed_form_axis_and_interior_cases(self):
        config = _config(close_distance=0.75, relation_margin=0.2)
        interior = max(config.improvement_epsilon * 10.0, 1e-5)

        unchanged = self._project(
            [0.4, 0.1],
            "closely right of",
            config,
        )
        opposite = self._project(
            [-1.0, 0.0],
            "closely right of",
            config,
        )
        outside_ball = self._project(
            [2.0, 0.0],
            "closely right of",
            config,
        )

        np.testing.assert_allclose(unchanged, [0.4, 0.1], atol=1e-12)
        np.testing.assert_allclose(
            opposite,
            [config.relation_margin + interior, 0.0],
            atol=1e-12,
        )
        np.testing.assert_allclose(
            outside_ball,
            [config.close_distance - interior, 0.0],
            atol=1e-12,
        )

    def test_close_projection_regression_preserves_margin_after_ball_projection(self):
        config = _config(close_distance=0.75, relation_margin=0.2)
        delta = np.array([0.5, 0.8], dtype=np.float64)

        margin = config.relation_margin + max(config.improvement_epsilon * 10.0, 1e-5)
        legacy = delta.copy()
        required = abs(float(legacy[1])) + margin
        legacy[0] = -required
        distance = float(np.linalg.norm(legacy))
        legacy *= (config.close_distance - margin) / distance

        self.assertLess(
            -float(legacy[0]),
            abs(float(legacy[1])) + config.relation_margin,
        )

        projected = self._project(delta, "closely left of", config)
        self._assert_close_directional_feasible(
            projected,
            "closely left of",
            config,
        )

    def test_budget_step_preserves_anchor_instead_of_rescaling_it(self):
        config = _config(
            per_object_budget=0.2,
            total_movement_budget=0.13,
        )
        original = np.zeros((2, 2), dtype=np.float64)
        anchor = np.array([[0.08, 0.0], [0.02, 0.0]], dtype=np.float64)
        proposed = np.array([[0.14, 0.0], [0.02, 0.0]], dtype=np.float64)

        budgeted = cwgcp_solver._anchor_preserving_budget_step(
            original,
            anchor,
            proposed,
            config,
        )

        self.assertLessEqual(
            float(np.linalg.norm(budgeted - original, axis=1).sum()),
            config.total_movement_budget + 1e-10,
        )
        self.assertGreater(float(budgeted[0, 0]), float(anchor[0, 0]))
        self.assertAlmostEqual(float(budgeted[1, 0]), 0.02, places=12)

    def test_no_nudge_ablation_has_an_explicit_v031_variant_label(self):
        objects = [_object(0, 1, -0.5, 0.0), _object(1, 2, 0.0, 0.0)]
        anchor = np.array([[-0.5, 0.0], [0.0, 0.0]], dtype=np.float64)
        result = repair_layout_cwgcp(
            objects,
            [RelationProposal(1, "left of", 2)],
            config=_config(
                coverage_first_selection=True,
                require_coverage_gain=True,
                enable_proposal_nudge=False,
                enable_cone_ball_close_projection=True,
            ),
            anchor_centers=anchor,
        )
        self.assertEqual(
            result.certificate["algorithm_version"],
            "0.3.1-fa-psp-no-nudge",
        )

    def test_cone_ball_flag_activates_the_close_projection_end_to_end(self):
        objects = [
            _object(0, 1, 0.5, 0.8, half_x=0.005, half_z=0.005),
            _object(1, 2, 0.0, 0.0, half_x=0.005, half_z=0.005),
        ]
        anchor = np.array([[0.5, 0.8], [0.0, 0.0]], dtype=np.float64)
        common = dict(
            relation_margin=0.02,
            total_movement_budget=3.0,
            max_edited_objects=2,
            coverage_first_selection=True,
            require_coverage_gain=True,
            enable_proposal_nudge=True,
            restarts=1,
            outer_iterations=1,
            solver_max_iterations=1,
        )
        legacy = repair_layout_cwgcp(
            objects,
            [RelationProposal(1, "closely left of", 2)],
            config=_config(
                enable_cone_ball_close_projection=False,
                **common,
            ),
            anchor_centers=anchor,
        )
        projected = repair_layout_cwgcp(
            objects,
            [RelationProposal(1, "closely left of", 2)],
            config=_config(
                enable_cone_ball_close_projection=True,
                **common,
            ),
            anchor_centers=anchor,
        )
        budget_limited = repair_layout_cwgcp(
            objects,
            [RelationProposal(1, "closely left of", 2)],
            config=_config(
                enable_cone_ball_close_projection=True,
                **{**common, "total_movement_budget": 0.5},
            ),
            anchor_centers=anchor,
        )

        self.assertFalse(legacy.accepted)
        self.assertTrue(projected.accepted)
        self.assertFalse(budget_limited.accepted)
        self.assertFalse(
            any(
                metric.get("candidate_source") == "proposal_nudge"
                for metric in budget_limited.certificate["solver"][
                    "candidate_metrics"
                ]
            )
        )
        self.assertEqual(
            projected.certificate["solver"]["selected_metrics"][
                "candidate_source"
            ],
            "proposal_nudge",
        )
        self.assertEqual(
            projected.certificate["algorithm_version"],
            "0.3.1-fa-psp-cone-ball",
        )

    def test_cone_ball_profile_requires_an_anchor(self):
        objects = [_object(0, 1, 0.5, 0.8), _object(1, 2, 0.0, 0.0)]
        with self.assertRaisesRegex(ValueError, "requires anchor_centers"):
            repair_layout_cwgcp(
                objects,
                [RelationProposal(1, "closely left of", 2)],
                config=_config(
                    enable_proposal_nudge=True,
                    enable_cone_ball_close_projection=True,
                ),
            )


if __name__ == "__main__":
    unittest.main()
