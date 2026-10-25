import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prospect_lab.py"
spec = importlib.util.spec_from_file_location("prospect_lab", SCRIPT)
prospect_lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prospect_lab)

class ProspectLabTests(unittest.TestCase):
    def test_url_validation(self):
        self.assertTrue(prospect_lab.valid_http_url("https://example.com/about"))
        self.assertFalse(prospect_lab.valid_http_url("javascript:alert(1)"))
        self.assertFalse(prospect_lab.valid_http_url("not-a-url"))

    def test_score_is_transparent_and_bounded(self):
        row = {field: "" for field in prospect_lab.FIELDS}
        points, missing = prospect_lab.score(row, "not checked: missing/invalid URL")
        self.assertEqual(points, 0)
        self.assertEqual(len(missing), 7)
        complete = {
            "company": "Demo Co", "niche": "HVAC", "website": "https://example.com",
            "decision_maker": "Example Person", "role": "Owner",
            "linkedin_url": "https://www.linkedin.com/in/example",
            "source_url": "https://example.com/about",
            "observed_signal": "Specific publicly observed fact",
            "service_fit": "Website development (hypothesis)", "notes": "",
        }
        points, missing = prospect_lab.score(complete, "HTTP 200")
        self.assertEqual(points, 100)
        self.assertEqual(missing, [])

    def test_invalid_website_does_not_get_reachability_points(self):
        row = {field: "" for field in prospect_lab.FIELDS}
        row["website"] = "https://example.com"
        points, _ = prospect_lab.score(row, "not checked: host is not publicly reachable")
        self.assertEqual(points, 20)

if __name__ == "__main__":
    unittest.main()
