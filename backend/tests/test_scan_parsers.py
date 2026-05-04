import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.scan_parser import (parse_httpx_enrich_output,
                                      parse_nuclei_output)


class ScanParserTests(unittest.TestCase):
    def test_parse_httpx_enrich_output_extracts_core_fields(self):
        stdout = (
            '{"input":"api.example.com","tech":["cloudflare","nginx"],'
            '"cdn":{"name":"cloudflare"},"cname":"foo.azurewebsites.net","a":["1.2.3.4"]}\n'
        )
        parsed = parse_httpx_enrich_output(stdout)
        self.assertEqual(parsed["api.example.com"]["ip"], "1.2.3.4")
        self.assertEqual(parsed["api.example.com"]["cdn"], "cloudflare")
        self.assertEqual(parsed["api.example.com"]["cname"], "foo.azurewebsites.net")
        self.assertEqual(parsed["api.example.com"]["cdn_waf"], "cloudflare")

    def test_parse_nuclei_output_adds_source_and_confidence(self):
        stdout = (
            '{"template-id":"test-template","info":{"severity":"high","description":"desc"},'
            '"host":"https://api.example.com","matched-at":"https://api.example.com/admin"}\n'
        )
        findings = parse_nuclei_output(stdout)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["source"], "nuclei")
        self.assertGreater(findings[0]["confidence"], 0.9)
        self.assertEqual(findings[0]["matched_url"], "https://api.example.com/admin")


if __name__ == "__main__":
    unittest.main()
