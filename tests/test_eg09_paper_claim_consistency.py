import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_eg09_paper_claim_consistency.py"
spec = importlib.util.spec_from_file_location("check_eg09_paper_claim_consistency", SCRIPT)
checker = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)


class Eg09PaperClaimConsistencyTest(unittest.TestCase):
    def test_repository_surfaces_match_formal_evidence(self):
        payload = checker.validate(ROOT)
        self.assertEqual(payload["status"], "EG09_CLAIMS_FROZEN")
        self.assertEqual(payload["errors"], [])

    def test_stale_number_in_paper_is_rejected(self):
        main = " ".join(checker.REQUIRED_MAIN_TOKENS + checker.REQUIRED_BOUNDARY_TOKENS)
        main += " 0.8449"
        claim = "EG09_CLAIMS_FROZEN\n## Historical-number boundary\n0.8449"
        errors = checker.check_text_surfaces(main, claim)
        self.assertIn("paper contains stale development token: 0.8449", errors)

    def test_historical_numbers_are_allowed_only_after_boundary(self):
        main = " ".join(checker.REQUIRED_MAIN_TOKENS + checker.REQUIRED_BOUNDARY_TOKENS)
        clean_claim = "EG09_CLAIMS_FROZEN\n## Historical-number boundary\n0.8449 +8.2"
        self.assertEqual(checker.check_text_surfaces(main, clean_claim), [])

        dirty_claim = "EG09_CLAIMS_FROZEN 0.8449\n## Historical-number boundary\n"
        errors = checker.check_text_surfaces(main, dirty_claim)
        self.assertIn("active claim map contains stale development token: 0.8449", errors)

    def test_missing_claim_boundary_is_rejected(self):
        main = " ".join(checker.REQUIRED_MAIN_TOKENS)
        claim = "EG09_CLAIMS_FROZEN\n## Historical-number boundary\n"
        errors = checker.check_text_surfaces(main, claim)
        self.assertTrue(any("paper lacks required claim boundary" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
