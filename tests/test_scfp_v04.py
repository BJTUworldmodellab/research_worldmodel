import json
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from scripts.compute_gated_floorprior import summarize
from scripts.run_cwgcp_pilot import _collision_gated_floor_prior
from src.cwgcp import CWGCPConfig, LayoutObject, RelationProposal
from src.cwgcp.constraints import (
    proposal_relation_metrics,
    relation_metrics,
)
from src.cwgcp.geometry import (
    exact_overlap_metrics,
    movement_metrics,
)
from src.cwgcp.repairer import repair_layout_cwgcp
from src.cwgcp.solver import _selection_key


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
        outer_iterations=1,
        solver_max_iterations=1,
        initial_trust_radius=0.8,
        max_trust_radius=1.2,
        per_object_budget=2.5,
        total_movement_budget=3.0,
        max_edited_objects=2,
        seed=11,
    )
    values.update(overrides)
    return CWGCPConfig(**values)


def _candidate_by_source(result, source):
    candidates = result.certificate["solver"]["candidate_metrics"]
    return next(
        candidate
        for candidate in candidates
        if candidate["candidate_source"] == source
    )


class SCFPV04ContractTests(unittest.TestCase):
    def assert_scfp_identity(self, result):
        self.assertEqual(result.certificate["algorithm"], "SCFP")
        self.assertEqual(
            result.certificate["algorithm_version"],
            "0.4.0-safety-certified-feasible-projection",
        )

    def assert_constraint_certificate(self, certificate, *, passed):
        self.assertIsInstance(certificate, dict)
        self.assertIs(certificate["feasible"], passed)
        self.assertIsInstance(certificate["violations"], list)
        self.assertIsInstance(certificate["constraints"], dict)
        self.assertTrue(certificate["constraints"])
        if passed:
            self.assertEqual(certificate["violations"], [])
        else:
            self.assertTrue(certificate["violations"])

    def test_scfp_selects_anchor_with_a_complete_auditable_certificate(self):
        objects = [_object(0, 1, 0.5, 0.0), _object(1, 2, 0.0, 0.0)]
        anchor = np.array([[-0.5, 0.0], [0.0, 0.0]], dtype=np.float64)
        result = repair_layout_cwgcp(
            objects,
            [RelationProposal(1, "left of", 2)],
            config=_config(
                certified_feasible_projection=True,
                coverage_first_selection=True,
                require_coverage_gain=True,
            ),
            anchor_centers=anchor,
        )

        np.testing.assert_array_equal(result.centers_xz, anchor)
        self.assertFalse(result.accepted)
        self.assertEqual(
            result.certificate["rollback_reason"],
            "anchor_already_full_coverage",
        )
        self.assert_scfp_identity(result)

        solver = result.certificate["solver"]
        selected = solver["selected_solution"]
        self.assertIsInstance(selected, dict)
        self.assertIn(
            selected["source"],
            {"anchor", "anchor_rollback"},
        )
        self.assertEqual(
            selected["source"],
            solver["selected_metrics"]["candidate_source"],
        )
        self.assertEqual(
            selected["role"],
            "anchor_identity_projection",
        )
        self.assertEqual(
            solver["projection_status"],
            "anchor_identity_selected",
        )
        self.assertIs(solver["projection_succeeded"], True)
        self.assertIs(solver["layout_modified"], False)
        self.assertIs(selected["feasible"], True)
        self.assertIsInstance(selected["dominates_anchor"], bool)
        self.assertIsInstance(solver["proof_obligations"], dict)
        self.assertTrue(solver["proof_obligations"])
        self.assertIn(
            "external_safety_score",
            solver["objective_terms"],
        )
        self.assertIn(
            "boundary_penalty",
            solver["objective_terms"],
        )
        self.assert_constraint_certificate(
            solver["constraint_certificate"],
            passed=True,
        )
        self.assertEqual(
            solver["constraint_certificate"]["feasible"],
            selected["feasible"],
        )

    def test_scfp_rejects_collision_pair_swap_hidden_by_aggregate_obb_metrics(self):
        # Baseline overlap: (0, 1), area 0.2. Candidate overlap: (1, 2),
        # also area 0.2. Aggregate-only gates therefore cannot detect the
        # newly introduced contact.
        objects = [
            _object(0, 10, 0.0, 0.0, 0.5, 0.5),
            _object(1, 1, 0.8, 0.0, 0.5, 0.5),
            _object(2, 2, 3.0, 0.0, 0.5, 0.5),
        ]
        anchor = np.array(
            [[0.0, 0.0], [0.8, 0.0], [3.0, 0.0]],
            dtype=np.float64,
        )
        pair_swap = np.array(
            [[0.0, 0.0], [2.2, 0.0], [3.0, 0.0]],
            dtype=np.float64,
        )
        result = repair_layout_cwgcp(
            objects,
            [RelationProposal(1, "right of", 2)],
            config=_config(
                certified_feasible_projection=True,
                per_object_budget=2.0,
                total_movement_budget=2.0,
                max_edited_objects=1,
            ),
            anchor_centers=anchor,
            warm_start_centers=[pair_swap],
        )

        warm = _candidate_by_source(result, "warm_start")
        anchor_metrics = result.certificate["solver"]["anchor_metrics"]
        self.assertEqual(
            warm["exact_obb_collision_pairs"],
            anchor_metrics["exact_obb_collision_pairs"],
        )
        self.assertAlmostEqual(
            warm["exact_obb_overlap_area"],
            anchor_metrics["exact_obb_overlap_area"],
            places=12,
        )
        self.assertIsInstance(
            warm["exact_obb_pair_overlaps"],
            dict,
        )
        self.assertIsInstance(
            anchor_metrics["exact_obb_pair_overlaps"],
            dict,
        )
        self.assertNotEqual(
            set(warm["exact_obb_pair_overlaps"]),
            set(anchor_metrics["exact_obb_pair_overlaps"]),
        )
        self.assertEqual(len(warm["exact_obb_pair_overlaps"]), 1)
        self.assertEqual(len(anchor_metrics["exact_obb_pair_overlaps"]), 1)
        self.assertLess(
            warm["proposal_weighted_relation_violation"],
            anchor_metrics["proposal_weighted_relation_violation"],
        )
        self.assertIs(warm["feasible"], False)
        self.assertIsInstance(warm["dominates_anchor"], bool)
        self.assert_constraint_certificate(
            warm["constraint_certificate"],
            passed=False,
        )
        self.assertIn(
            "exact_obb_new_collision_pair",
            warm["constraint_certificate"]["violations"],
        )

    def test_scfp_rejects_one_pair_worsening_hidden_by_total_overlap(self):
        # The pair identities stay fixed and the aggregate overlap stays 0.5:
        # (0, 1) grows 0.2 -> 0.3 while (2, 3) shrinks 0.3 -> 0.2.
        # A total-area-only gate would incorrectly accept this redistribution.
        objects = [
            _object(0, 10, 0.0, 0.0, 0.5, 0.5),
            _object(1, 1, 0.8, 0.0, 0.5, 0.5),
            _object(2, 20, 3.0, 0.0, 0.5, 0.5),
            _object(3, 2, 3.7, 0.0, 0.5, 0.5),
        ]
        anchor = np.array(
            [[0.0, 0.0], [0.8, 0.0], [3.0, 0.0], [3.7, 0.0]],
            dtype=np.float64,
        )
        redistributed = np.array(
            [[0.0, 0.0], [0.7, 0.0], [3.0, 0.0], [3.8, 0.0]],
            dtype=np.float64,
        )
        result = repair_layout_cwgcp(
            objects,
            [RelationProposal(1, "far", 2)],
            config=_config(
                certified_feasible_projection=True,
                far_distance=4.0,
                per_object_budget=0.2,
                total_movement_budget=0.2,
                max_edited_objects=2,
            ),
            anchor_centers=anchor,
            warm_start_centers=[redistributed],
        )

        candidate = _candidate_by_source(result, "warm_start")
        anchor_metrics = result.certificate["solver"]["anchor_metrics"]
        anchor_pairs = anchor_metrics["exact_obb_pair_overlaps"]
        candidate_pairs = candidate["exact_obb_pair_overlaps"]

        self.assertEqual(
            candidate["exact_obb_collision_pairs"],
            anchor_metrics["exact_obb_collision_pairs"],
        )
        self.assertAlmostEqual(
            candidate["exact_obb_overlap_area"],
            anchor_metrics["exact_obb_overlap_area"],
            places=12,
        )
        self.assertEqual(set(candidate_pairs), set(anchor_pairs))
        increased_pairs = [
            pair_id
            for pair_id in anchor_pairs
            if candidate_pairs[pair_id] > anchor_pairs[pair_id] + 1e-12
        ]
        decreased_pairs = [
            pair_id
            for pair_id in anchor_pairs
            if candidate_pairs[pair_id] < anchor_pairs[pair_id] - 1e-12
        ]
        self.assertEqual(len(increased_pairs), 1)
        self.assertEqual(len(decreased_pairs), 1)
        self.assertLess(
            candidate["proposal_weighted_relation_violation"],
            anchor_metrics["proposal_weighted_relation_violation"],
        )
        self.assertIs(candidate["feasible"], False)
        self.assert_constraint_certificate(
            candidate["constraint_certificate"],
            passed=False,
        )
        self.assertIn(
            "exact_obb_pair_overlap_increase",
            candidate["constraint_certificate"]["violations"],
        )

    def test_scfp_external_safety_failure_is_fail_closed(self):
        objects = [_object(0, 1, 0.5, 0.0), _object(1, 2, 0.0, 0.0)]
        anchor = np.array([[0.5, 0.0], [0.0, 0.0]], dtype=np.float64)
        warm = np.array([[-0.5, 0.0], [0.0, 0.0]], dtype=np.float64)

        def flaky_fcl(centers):
            if np.array_equal(centers, anchor):
                return {"mesh_collision_pairs": 0.0}
            raise RuntimeError("FCL unavailable for candidate")

        result = repair_layout_cwgcp(
            objects,
            [RelationProposal(1, "left of", 2)],
            config=_config(certified_feasible_projection=True),
            external_safety_fn=flaky_fcl,
            anchor_centers=anchor,
            warm_start_centers=[warm],
        )

        np.testing.assert_array_equal(result.centers_xz, anchor)
        self.assertFalse(result.accepted)
        self.assert_scfp_identity(result)
        candidate = _candidate_by_source(result, "warm_start")
        self.assertIs(candidate["feasible"], False)
        self.assert_constraint_certificate(
            candidate["constraint_certificate"],
            passed=False,
        )
        self.assertIn(
            "external_safety_unavailable",
            candidate["constraint_certificate"]["violations"],
        )
        self.assertEqual(
            result.certificate["solver"]["selected_solution"][
                "source"
            ],
            "anchor_rollback",
        )

    def test_scfp_honors_strict_coverage_gain_when_requested(self):
        objects = [_object(0, 1, 0.5, 0.0), _object(1, 2, 0.0, 0.0)]
        anchor = np.array([[0.5, 0.0], [0.0, 0.0]], dtype=np.float64)
        partial = np.array([[0.4, 0.0], [0.0, 0.0]], dtype=np.float64)
        result = repair_layout_cwgcp(
            objects,
            [RelationProposal(1, "left of", 2)],
            config=_config(
                certified_feasible_projection=True,
                coverage_first_selection=True,
                require_coverage_gain=True,
            ),
            anchor_centers=anchor,
            warm_start_centers=[partial],
        )

        warm = _candidate_by_source(result, "warm_start")
        self.assertLess(
            warm["proposal_weighted_relation_violation"],
            result.certificate["solver"]["anchor_metrics"][
                "proposal_weighted_relation_violation"
            ],
        )
        self.assertEqual(
            warm["proposal_satisfied_relations"],
            result.certificate["solver"]["anchor_metrics"][
                "proposal_satisfied_relations"
            ],
        )
        self.assertIs(warm["dominates_anchor"], False)
        self.assertIs(warm["gate_passed"], False)
        self.assertIn(
            "proposal_coverage_gain_required",
            warm["rejection_reasons"],
        )

    def test_scfp_requires_strict_improvement_when_epsilon_is_zero(self):
        objects = [_object(0, 1, 0.5, 0.0), _object(1, 2, 0.0, 0.0)]
        anchor = np.array([[0.5, 0.0], [0.0, 0.0]], dtype=np.float64)
        result = repair_layout_cwgcp(
            objects,
            [RelationProposal(1, "left of", 2)],
            config=_config(
                certified_feasible_projection=True,
                improvement_epsilon=0.0,
                max_edited_objects=0,
            ),
            anchor_centers=anchor,
            warm_start_centers=[anchor.copy()],
        )

        warm = _candidate_by_source(result, "warm_start")
        np.testing.assert_array_equal(result.centers_xz, anchor)
        self.assertFalse(result.accepted)
        self.assertIs(warm["dominates_anchor"], False)
        self.assertIs(warm["gate_passed"], False)
        self.assertEqual(
            result.certificate["solver"]["projection_status"],
            "anchor_identity_selected",
        )
        self.assertIs(
            result.certificate["solver"]["layout_modified"],
            False,
        )

    def test_scfp_uses_boundary_penalty_before_movement_as_a_tiebreak(self):
        common = {
            "proposal_satisfied_relations": 1,
            "proposal_weighted_relation_violation": 0.0,
            "exact_obb_collision_pairs": 0,
            "exact_obb_overlap_area": 0.0,
            "boundary_violations": 1,
            "external_safety_available": False,
            "edited_object_count": 1,
        }
        lower_boundary_penalty = {
            **common,
            "boundary_penalty": 0.1,
            "total_movement": 2.0,
        }
        lower_movement = {
            **common,
            "boundary_penalty": 0.2,
            "total_movement": 1.0,
        }
        config = _config(
            certified_feasible_projection=True,
            coverage_first_selection=True,
        )

        self.assertLess(
            _selection_key(lower_boundary_penalty, config),
            _selection_key(lower_movement, config),
        )

    def test_certified_flag_off_preserves_the_frozen_fapsp_v03_behavior(self):
        objects = [
            _object(0, 1, 0.02, 0.0, 0.005, 0.005),
            _object(1, 2, 0.0, 0.0, 0.005, 0.005),
        ]
        relations = [RelationProposal(1, "left of", 2)]
        anchor = np.array([[0.02, 0.0], [0.0, 0.0]], dtype=np.float64)
        common = dict(
            relation_margin=0.02,
            total_movement_budget=0.1,
            max_edited_objects=1,
            coverage_first_selection=True,
            require_coverage_gain=True,
            enable_proposal_nudge=True,
        )
        implicit_legacy = repair_layout_cwgcp(
            objects,
            relations,
            config=_config(**common),
            anchor_centers=anchor,
        )
        explicit_legacy = repair_layout_cwgcp(
            objects,
            relations,
            config=_config(
                certified_feasible_projection=False,
                **common,
            ),
            anchor_centers=anchor,
        )

        expected = np.array(
            [[-0.020010000000000003, 0.0], [0.0, 0.0]],
            dtype=np.float64,
        )
        np.testing.assert_array_equal(implicit_legacy.centers_xz, expected)
        np.testing.assert_array_equal(
            explicit_legacy.centers_xz,
            implicit_legacy.centers_xz,
        )
        self.assertTrue(explicit_legacy.accepted)
        self.assertEqual(explicit_legacy.certificate["algorithm"], "FA-PSP")
        self.assertEqual(
            explicit_legacy.certificate["algorithm_version"],
            "0.3.0-fa-psp",
        )
        self.assertEqual(
            explicit_legacy.certificate["layout_relation_hash"],
            "7d84fc7545c9ac34a86cc2bd9ffa2dda8c43bd01da04a10986f3ddd8cd113c1b",
        )
        self.assertEqual(
            explicit_legacy.certificate["input_hash"],
            implicit_legacy.certificate["input_hash"],
        )
        self.assertEqual(
            explicit_legacy.certificate["solver"],
            implicit_legacy.certificate["solver"],
        )
        self.assertNotIn(
            "proof_obligations",
            explicit_legacy.certificate["solver"],
        )

    def test_scfp_requires_an_anchor(self):
        objects = [_object(0, 1, 0.5, 0.0), _object(1, 2, 0.0, 0.0)]
        with self.assertRaisesRegex(ValueError, "requires anchor_centers"):
            repair_layout_cwgcp(
                objects,
                [RelationProposal(1, "left of", 2)],
                config=_config(certified_feasible_projection=True),
            )

    def test_scfp_certificate_hashes_and_selected_metrics_match_the_returned_layout(
        self,
    ):
        objects = [_object(0, 1, 0.5, 0.0), _object(1, 2, 0.0, 0.0)]
        relations = [RelationProposal(1, "left of", 2)]
        anchor = np.array([[0.5, 0.0], [0.0, 0.0]], dtype=np.float64)
        warm = np.array([[-0.5, 0.0], [0.0, 0.0]], dtype=np.float64)
        config = _config(certified_feasible_projection=True)
        kwargs = dict(
            config=config,
            anchor_centers=anchor,
            warm_start_centers=[warm],
            provenance={"scene_uid": "scfp-contract-scene"},
        )

        first = repair_layout_cwgcp(objects, relations, **kwargs)
        repeated = repair_layout_cwgcp(objects, relations, **kwargs)
        changed_anchor = repair_layout_cwgcp(
            objects,
            relations,
            config=config,
            anchor_centers=np.array(
                [[0.49, 0.0], [0.0, 0.0]],
                dtype=np.float64,
            ),
            warm_start_centers=[warm],
            provenance={"scene_uid": "scfp-contract-scene"},
        )

        self.assertTrue(first.accepted)
        self.assert_scfp_identity(first)
        selected = first.certificate["solver"]["selected_metrics"]
        selected_solution = first.certificate["solver"]["selected_solution"]
        self.assertEqual(
            selected_solution["source"],
            selected["candidate_source"],
        )
        self.assertEqual(
            selected_solution["role"],
            "dominating_feasible_candidate",
        )
        self.assertEqual(
            first.certificate["solver"]["projection_status"],
            "dominating_candidate_selected",
        )
        self.assertIs(
            first.certificate["solver"]["projection_succeeded"],
            True,
        )
        self.assertIs(first.certificate["solver"]["layout_modified"], True)
        self.assertIs(selected_solution["feasible"], True)
        self.assertIsInstance(selected_solution["dominates_anchor"], bool)

        expected_relation = relation_metrics(
            first.centers_xz,
            objects,
            first.resolved_relations,
            config,
        )
        expected_proposal = proposal_relation_metrics(
            first.centers_xz,
            objects,
            relations,
            config,
        )
        expected_overlap = exact_overlap_metrics(first.centers_xz, objects)
        original = np.stack([obj.center_xz for obj in objects], axis=0)
        expected_movement = movement_metrics(
            original,
            first.centers_xz,
            config.edit_threshold,
        )
        for expected in (
            expected_relation,
            expected_proposal,
            expected_overlap,
            expected_movement,
        ):
            for key, value in expected.items():
                if isinstance(value, float):
                    self.assertAlmostEqual(selected[key], value, places=12)
                else:
                    self.assertEqual(selected[key], value)

        self.assert_constraint_certificate(
            first.certificate["solver"]["constraint_certificate"],
            passed=True,
        )
        constraints = first.certificate["solver"][
            "constraint_certificate"
        ]["constraints"]
        for name in (
            "per_object_movement_budget",
            "total_movement_budget",
        ):
            self.assertEqual(constraints[name]["tolerance"], 1e-6)
            self.assertEqual(
                constraints[name]["effective_limit"],
                constraints[name]["limit"] + constraints[name]["tolerance"],
            )
        for candidate in first.certificate["solver"]["candidate_metrics"]:
            self.assertIn("feasible", candidate)
            self.assertIn("dominates_anchor", candidate)
            self.assertIn("constraint_certificate", candidate)

        for key in ("input_hash", "layout_relation_hash", "config_hash"):
            self.assertEqual(
                first.certificate[key],
                repeated.certificate[key],
            )
        self.assertNotEqual(
            first.certificate["input_hash"],
            changed_anchor.certificate["input_hash"],
        )
        self.assertEqual(
            first.certificate["layout_relation_hash"],
            changed_anchor.certificate["layout_relation_hash"],
        )
        self.assertEqual(
            first.certificate["config_hash"],
            changed_anchor.certificate["config_hash"],
        )
        self.assertTrue(math.isfinite(first.certificate["runtime_seconds"]))
        json.dumps(
            first.certificate,
            sort_keys=True,
            allow_nan=False,
        )


class CollisionGatedFloorPriorFailClosedTests(unittest.TestCase):
    def test_runner_cached_mesh_gate_falls_back_if_either_side_is_unavailable(
        self,
    ):
        layout_boxes = [
            {
                "index": 0,
                "translation": [0.0, 0.5, 0.0],
                "size": [0.2, 0.2, 0.2],
                "angle": 0.0,
            }
        ]
        repair_boxes = [
            {
                "index": 0,
                "translation": [1.0, 0.5, 0.0],
                "size": [0.2, 0.2, 0.2],
                "angle": 0.0,
            }
        ]
        available = {"available": True, "collision_pairs": 0}
        unavailable = {"available": False, "collision_pairs": 0}
        mesh_cases = (
            (unavailable, available),
            (available, unavailable),
        )

        for layout_mesh, repair_mesh in mesh_cases:
            with self.subTest(
                layout_available=layout_mesh["available"],
                repair_available=repair_mesh["available"],
            ):
                selected, gate = _collision_gated_floor_prior(
                    {
                        "layout_boxes": layout_boxes,
                        "repair_boxes": repair_boxes,
                        "layout_mesh_collision": layout_mesh,
                        "repair_mesh_collision": repair_mesh,
                    }
                )

                self.assertEqual(selected, layout_boxes)
                self.assertIsNot(selected, layout_boxes)
                self.assertFalse(gate["mesh_gate_available"])
                self.assertFalse(gate["repair_accepted"])
                self.assertEqual(
                    gate["gate_policy_version"],
                    "collision-gated-floor-prior-v2-fail-closed",
                )
                self.assertEqual(
                    gate["fail_closed_reason"],
                    "mesh_unavailable",
                )

    def test_fcl_unavailable_uses_baseline_instead_of_unverified_repair(self):
        scene_template = {
            "selected_relations": [[1, "left of", 2]],
            "layout_relations": [],
            "repair_relations": [[1, "left of", 2]],
        }
        availability_cases = (
            (False, False),
            (True, False),
            (False, True),
        )

        with tempfile.TemporaryDirectory() as directory:
            path = (
                Path(directory)
                / "bedroom_relation_aware_parsed_floor_prior_mesh_eval_cfg1.0_1.0.json"
            )
            for layout_available, repair_available in availability_cases:
                with self.subTest(
                    layout_available=layout_available,
                    repair_available=repair_available,
                ):
                    scene = dict(scene_template)
                    scene["layout_mesh_collision"] = {
                        "available": layout_available,
                        "collision_pairs": 2,
                        "total_pairs": 3,
                    }
                    scene["repair_mesh_collision"] = {
                        "available": repair_available,
                        "collision_pairs": 1,
                        "total_pairs": 3,
                    }
                    path.write_text(
                        json.dumps({"per_scene": [scene]}),
                        encoding="utf-8",
                    )

                    summary = summarize(path)

                    self.assertEqual(
                        summary["gate_policy_version"],
                        "collision-gated-floor-prior-v2-fail-closed",
                    )
                    self.assertEqual(summary["baseline_acc"], 0.0)
                    self.assertEqual(summary["repair_acc"], 1.0)
                    self.assertEqual(summary["gated_acc"], 0.0)
                    self.assertEqual(summary["gated_gain"], 0.0)
                    self.assertEqual(summary["fallback_scenes"], 1)
                    self.assertEqual(summary["mesh_scenes_evaluated"], 0)
                    self.assertAlmostEqual(
                        summary["gated_mesh_pair_rate"],
                        summary["baseline_mesh_pair_rate"],
                        places=12,
                    )


if __name__ == "__main__":
    unittest.main()
