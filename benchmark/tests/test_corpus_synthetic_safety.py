"""Synthetic-only safety checks for the generated corpus and fixtures."""

from __future__ import annotations

import re
import unittest

from benchmark.corpus.generator import build_base_cases

# Secret-shaped strings that must never appear in synthetic corpus output.
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{18,}"),
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*[A-Za-z0-9_\-\.]{12,}"),
)

# Well-known real Korean service/telemarketing number prefixes that must not
# be accidentally generated as synthetic phone values.
SERVICE_PREFIXES = ("1566", "1577", "1588", "1600", "1644", "1666", "1677", "1688")


class SyntheticSafetyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = build_base_cases()

    def test_every_case_carries_synthetic_marker(self) -> None:
        for case in self.cases:
            self.assertTrue(case.synthetic, case.case_id)

    def test_no_secret_shaped_strings_in_corpus(self) -> None:
        for case in self.cases:
            for pattern in SECRET_PATTERNS:
                self.assertIsNone(
                    pattern.search(case.text),
                    f"secret-shaped string in {case.case_id}",
                )

    def test_no_real_service_number_prefixes(self) -> None:
        phone_pattern = re.compile(r"\b(\d{4})-\d{3,4}-\d{4}")
        for case in self.cases:
            for match in phone_pattern.finditer(case.text):
                prefix = match.group(1)
                self.assertNotIn(
                    prefix,
                    SERVICE_PREFIXES,
                    f"real service prefix in {case.case_id}: {match.group(0)}",
                )

    def test_email_domains_are_reserved_example_tld(self) -> None:
        email_pattern = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+)")
        for case in self.cases:
            for match in email_pattern.finditer(case.text):
                domain = match.group(1)
                self.assertTrue(
                    domain.endswith(".example"),
                    f"non-reserved email domain in {case.case_id}: {domain}",
                )


if __name__ == "__main__":
    unittest.main()
