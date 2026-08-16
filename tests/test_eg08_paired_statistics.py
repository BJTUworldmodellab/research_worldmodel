import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "compute_eg08_paired_statistics.py"
spec = importlib.util.spec_from_file_location("compute_eg08_paired_statistics", SCRIPT)
stats = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = stats
spec.loader.exec_module(stats)


def scene(scene_id, room, n_relations, baseline, main, generic, randoms):
    satisfied = {
        stats.BASELINE: baseline,
        stats.MAIN: main,
        stats.GENERIC: generic,
        **{variant: value for variant, value in zip(stats.RANDOMS, randoms)},
    }
    return stats.SceneRecord(scene_id, room, n_relations, satisfied)


class Eg08PairedStatisticsTest(unittest.TestCase):
    def test_ratio_of_sums_point_estimate(self):
        records = [
            scene("a", "bedroom", 1, 0, 1, 0, (0, 0, 0)),
            scene("b", "bedroom", 3, 3, 3, 3, (3, 3, 3)),
        ]
        main, baseline, gain, denominator = stats.point_estimate(records, stats.BASELINE)
        self.assertEqual(denominator, 4)
        self.assertAlmostEqual(main, 1.0)
        self.assertAlmostEqual(baseline, 0.75)
        self.assertAlmostEqual(gain, 0.25)

    def test_random_mean_uses_three_paired_seeds(self):
        records = [scene("a", "bedroom", 3, 0, 3, 0, (0, 1, 2))]
        main, control, gain, _ = stats.point_estimate(records, "random_seed_mean")
        self.assertAlmostEqual(main, 1.0)
        self.assertAlmostEqual(control, 1.0 / 3.0)
        self.assertAlmostEqual(gain, 2.0 / 3.0)

    def test_bootstrap_is_deterministic_and_paired(self):
        records = [
            scene(f"s{i}", "bedroom", 1, 0, 1, 0, (0, 0, 0))
            for i in range(8)
        ]
        first = stats._bootstrap_scope(records, 100, 17, False, 25)
        second = stats._bootstrap_scope(records, 100, 17, False, 25)
        self.assertTrue((first["main_vs_baseline"] == second["main_vs_baseline"]).all())
        self.assertTrue((first["main_vs_baseline"] == 1.0).all())

    def test_interval_classification(self):
        self.assertEqual(stats.classify_interval(0.01, 0.2), "MAIN_HIGHER")
        self.assertEqual(stats.classify_interval(-0.2, -0.01), "MAIN_LOWER")
        self.assertEqual(stats.classify_interval(-0.1, 0.1), "INCONCLUSIVE")


if __name__ == "__main__":
    unittest.main()
