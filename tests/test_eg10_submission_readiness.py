import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_eg10_submission_readiness.py"
spec = importlib.util.spec_from_file_location("check_eg10_submission_readiness", SCRIPT)
checker = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)


class Eg10SubmissionReadinessTest(unittest.TestCase):
    def test_current_repository_is_integrity_clean_but_submission_blocked(self):
        payload = checker.validate(ROOT)
        self.assertEqual(payload["integrity_status"], "PASS")
        self.assertEqual(payload["status"], "EG10_PRECHECK_BLOCKED")
        codes = {item["code"] for item in payload["hard_blockers"]}
        self.assertIn("PUBLIC_REPOSITORY_ANONYMITY_RISK", codes)
        self.assertNotIn("OFFICIAL_TEMPLATE_LOGIN_REQUIRED", codes)
        self.assertNotIn("SOURCE_NOT_MIGRATED", codes)
        self.assertNotIn("BIBLIOGRAPHY_STYLE_MISMATCH", codes)
        self.assertNotIn("CCS_CATEGORIES_MISSING", codes)
        self.assertIn("SUBMISSION_ID_PENDING", codes)
        self.assertNotIn("PDF_STALE", codes)
        self.assertNotIn("PDF_NOT_FRESH", codes)
        self.assertIn("AI_DISCLOSURE_AUTHOR_INPUT_NEEDED", codes)
        self.assertTrue(payload["checks"]["has_ccs_categories"])
        self.assertTrue(payload["checks"]["has_result_figure"])
        self.assertTrue(payload["checks"]["fresh_pdf_is_not_older_than_sources"])

    def test_citation_parser_handles_multiple_keys(self):
        tex = r"A \citep{alpha,beta} and B \cite{gamma}."
        self.assertEqual(checker.cited_keys(tex), {"alpha", "beta", "gamma"})

    def test_bibliography_parser_extracts_entry_keys(self):
        bib = "@article{alpha, title={A}}\n@misc{ beta, title={B}}"
        self.assertEqual(checker.bibliography_keys(bib), {"alpha", "beta"})

    def test_label_and_reference_parser(self):
        tex = r"\label{fig:a} See \ref{fig:a}, \autoref{tab:b}, and \eqref{eq:c}."
        labels, refs = checker.labels_and_refs(tex)
        self.assertEqual(labels, {"fig:a"})
        self.assertEqual(refs, {"fig:a", "tab:b", "eq:c"})


if __name__ == "__main__":
    unittest.main()
