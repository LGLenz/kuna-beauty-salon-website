import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import yaml

from scripts import check_dns


class CompareTests(unittest.TestCase):
    def test_cname_trailing_dot_is_optional_on_either_side(self):
        for live, expected in (
            (["pages.example.com."], ["pages.example.com"]),
            (["pages.example.com"], ["pages.example.com."]),
        ):
            with self.subTest(live=live, expected=expected):
                self.assertTrue(check_dns.compare(live, expected))

    def test_extra_live_records_and_order_do_not_cause_drift(self):
        self.assertTrue(
            check_dns.compare(
                ["192.0.2.3", "192.0.2.2", "192.0.2.1"],
                ["192.0.2.1", "192.0.2.2"],
            )
        )

    def test_missing_expected_record_causes_drift(self):
        for live in ([], ["192.0.2.1"]):
            with self.subTest(live=live):
                self.assertFalse(
                    check_dns.compare(live, ["192.0.2.1", "192.0.2.2"])
                )


class MainTests(unittest.TestCase):
    def run_check(self, record, live):
        with tempfile.TemporaryDirectory() as directory:
            spec_path = Path(directory) / "records.yaml"
            spec_path.write_text(
                yaml.safe_dump({"domain": "example.com", "records": [record]}),
                encoding="utf-8",
            )
            output = io.StringIO()
            with (
                patch.object(check_dns.sys, "argv", ["check_dns.py", str(spec_path)]),
                patch.object(check_dns, "dig", return_value=live) as dig_mock,
                redirect_stdout(output),
            ):
                status = check_dns.main()
            dig_mock.assert_called_once_with("salon.example.com", record["type"])
            return status, output.getvalue()

    def test_cname_normalisation_returns_success(self):
        status, output = self.run_check(
            {
                "name": "salon",
                "type": "CNAME",
                "expected": ["  PAGES.EXAMPLE.COM.  "],
            },
            ["pages.example.com"],
        )
        self.assertEqual(status, 0)
        self.assertIn("DNS OK: all expected records match.", output)

    def test_missing_address_returns_drift_not_success(self):
        record = {
            "name": "salon",
            "type": "A",
            "expected": ["192.0.2.1", "192.0.2.2"],
        }
        for live in ([], ["192.0.2.1"]):
            with self.subTest(live=live):
                status, output = self.run_check(record, live)
                self.assertEqual(status, 1)
                self.assertIn("DNS DRIFT: 1 record group(s)", output)
                self.assertNotIn("DNS OK:", output)

    def test_txt_requires_every_substring_but_allows_separate_values(self):
        record = {
            "name": "salon",
            "type": "TXT",
            "expected_contains": ["V=SPF1", "verification=salon"],
        }
        for live, expected_status in (
            (["v=spf1 include:example.com", "verification=salon"], 0),
            (["v=spf1 include:example.com"], 1),
            ([], 1),
        ):
            with self.subTest(live=live):
                status, output = self.run_check(record, live)
                self.assertEqual(status, expected_status)
                if expected_status:
                    self.assertIn("missing substrings:", output)
                    self.assertIn("verification=salon", output)
                else:
                    self.assertIn("DNS OK:", output)


if __name__ == "__main__":
    unittest.main()
