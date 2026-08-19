import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "evaluation" / "independent_relation_evaluator.py"
spec = importlib.util.spec_from_file_location("independent_relation_evaluator", SCRIPT)
evaluator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = evaluator
spec.loader.exec_module(evaluator)


def obj(index, category, center, yaw=0.0):
    return {
        "index": index,
        "category": category,
        "center": center,
        "size": [1.0, 1.0, 1.0],
        "yaw": yaw,
    }


class IndependentRelationEvaluatorTest(unittest.TestCase):
    def test_alias_matching_and_baseline_frozen_instance_pair(self):
        layouts = [
            {
                "scene_id": "s1",
                "room_type": "bedroom",
                "layout_variant": "baseline",
                "source_config_id": "fixture",
                "objects": [
                    obj(0, "bed", [0.0, 0.0, 0.0]),
                    obj(1, "night stand", [0.2, 0.0, 0.0]),
                    obj(2, "nightstand", [5.0, 0.0, 0.0]),
                ],
                "target_relations": [
                    {"relation_id": "r1", "subject_class": "nightstand", "predicate": "right", "object_class": "bed"}
                ],
            },
            {
                "scene_id": "s1",
                "room_type": "bedroom",
                "layout_variant": "collision_gated_floor_prior",
                "source_config_id": "fixture",
                "objects": [
                    obj(0, "bed", [0.0, 0.0, 0.0]),
                    obj(1, "night stand", [-0.2, 0.0, 0.0]),
                    obj(2, "nightstand", [8.0, 0.0, 0.0]),
                ],
                "target_relations": [],
            },
        ]
        per_relation, _, _, _ = evaluator.evaluate(layouts)
        baseline = [row for row in per_relation if row["layout_variant"] == "baseline"][0]
        repair = [row for row in per_relation if row["layout_variant"] == "collision_gated_floor_prior"][0]
        self.assertEqual(baseline["subject_index"], 1)
        self.assertEqual(repair["subject_index"], 1)
        self.assertEqual(baseline["is_satisfied"], 1)
        self.assertEqual(repair["is_satisfied"], 0)

    def test_thresholds_missing_unsupported_and_conflict_denominator(self):
        layouts = [
            {
                "scene_id": "s2",
                "room_type": "livingroom",
                "layout_variant": "baseline",
                "source_config_id": "fixture",
                "objects": [
                    obj(0, "sofa", [0.0, 0.0, 0.0], yaw=1.57),
                    obj(1, "coffee table", [0.04, 0.0, 0.0], yaw=0.5),
                ],
                "target_relations": [
                    {"relation_id": "left_boundary", "subject_class": "sofa", "predicate": "left", "object_class": "coffee table"},
                    {"relation_id": "right_conflict", "subject_class": "sofa", "predicate": "right", "object_class": "coffee table"},
                    {"relation_id": "missing", "subject_class": "lamp", "predicate": "near", "object_class": "sofa"},
                    {"relation_id": "unsupported", "subject_class": "sofa", "predicate": "touching", "object_class": "coffee table"},
                ],
            }
        ]
        per_relation, per_scene, summary, _ = evaluator.evaluate(layouts)
        by_id = {row["relation_id"]: row for row in per_relation}
        self.assertEqual(by_id["left_boundary"]["is_satisfied"], 0)
        self.assertEqual(by_id["missing"]["status"], "missing_subject")
        self.assertEqual(by_id["unsupported"]["status"], "unsupported_predicate")
        self.assertEqual(per_scene[0]["has_conflicting_targets"], 1)
        self.assertEqual(per_scene[0]["n_relations"], 4)
        self.assertEqual(per_scene[0]["n_evaluated"], 2)
        self.assertAlmostEqual(summary[0]["missing_rate"], 0.25)
        self.assertAlmostEqual(summary[0]["unsupported_rate"], 0.25)

    def test_front_behind_follow_eg02_annotation_coordinate_rule(self):
        layouts = [
            {
                "scene_id": "s_front",
                "room_type": "bedroom",
                "layout_variant": "baseline",
                "source_config_id": "fixture",
                "objects": [
                    obj(0, "chair", [0.0, 0.0, -0.2]),
                    obj(1, "table", [0.0, 0.0, 0.0]),
                    obj(2, "lamp", [0.0, 0.0, 0.2]),
                ],
                "target_relations": [
                    {"relation_id": "behind", "subject_class": "chair", "predicate": "behind", "object_class": "table"},
                    {"relation_id": "front", "subject_class": "lamp", "predicate": "in front of", "object_class": "table"},
                ],
            }
        ]
        per_relation, _, _, _ = evaluator.evaluate(layouts)
        by_id = {row["relation_id"]: row for row in per_relation}
        self.assertEqual(by_id["behind"]["is_satisfied"], 1)
        self.assertEqual(by_id["front"]["is_satisfied"], 1)

    def test_cli_writes_required_outputs(self):
        layouts = [
            {
                "scene_id": "s3",
                "room_type": "diningroom",
                "layout_variant": "baseline",
                "source_config_id": "fixture",
                "objects": [
                    obj(0, "dining table", [0.0, 0.0, 0.0]),
                    obj(1, "chair", [0.0, 0.0, 2.0]),
                ],
                "target_relations": [
                    {"relation_id": "behind", "subject_class": "chair", "predicate": "behind", "object_class": "dinner table"}
                ],
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "layouts.json"
            input_path.write_text(__import__("json").dumps({"layouts": layouts}), encoding="utf-8")
            out_dir = tmp_path / "out"
            evaluator.main.__globals__["argparse"].ArgumentParser
            import subprocess
            import sys

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(input_path), "--output-dir", str(out_dir), "--run-id", "fixture"],
                check=True,
                text=True,
                capture_output=True,
            )
            self.assertIn("wrote", result.stdout)
            for name in ["per_relation.csv", "per_scene.csv", "summary.csv", "audit.json"]:
                self.assertTrue((out_dir / name).exists())


if __name__ == "__main__":
    unittest.main()
