import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from safety_net_cli import main


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dd = ["--data-dir", self.tmp.name]

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            main(self.dd + argv)
        return buf.getvalue()

    def test_benefits_flow(self):
        out = self._run(["benefits", "enroll", "--id", "BEN-1",
                         "--program", "retirement", "--amount", "1200",
                         "--schedule", "monthly"])
        rec = json.loads(out)
        self.assertEqual(rec["id"], "BEN-1")
        out = self._run(["benefits", "beneficiaries"])
        self.assertEqual(len(json.loads(out)), 1)
        out = self._run(["benefits", "summary"])
        self.assertEqual(json.loads(out)["beneficiaries"], 1)

    def test_benefits_bad_choice_rejected(self):
        with self.assertRaises(SystemExit):
            self._run(["benefits", "enroll", "--id", "BEN-1",
                       "--program", "lottery", "--amount", "100",
                       "--schedule", "monthly"])

    def test_disaster_flow(self):
        self._run(["disaster", "stock", "--depot", "north",
                   "--resource", "water", "--quantity", "10000"])
        self._run(["disaster", "stock", "--depot", "north",
                   "--resource", "food", "--quantity", "10000"])
        out = self._run(["disaster", "report", "--type", "flood",
                         "--locality", "Riverside", "--severity", "1"])
        rec = json.loads(out)
        self.assertEqual(rec["id"], "INC-0001")
        out = self._run(["disaster", "dispatch", "--incident", "INC-0001"])
        self.assertIn("dispatched to INC-0001", out)
        out = self._run(["disaster", "unmet", "--incident", "INC-0001"])
        self.assertEqual(json.loads(out), {})

    def test_disaster_incidents_list(self):
        self._run(["disaster", "report", "--type", "fire",
                   "--locality", "Drytown", "--severity", "2"])
        out = self._run(["disaster", "incidents", "--status", "open"])
        self.assertEqual(len(json.loads(out)), 1)

    def test_diplomacy_flow(self):
        out = self._run(["diplomacy", "log", "--counterparty", "Atlantis",
                         "--type", "treaty", "--date", "2026-01-15",
                         "--summary", "trade"])
        self.assertEqual(json.loads(out)["id"], "DIP-0001")
        out = self._run(["diplomacy", "obligations"])
        self.assertIn("obligation(s)", out)
        out = self._run(["diplomacy", "summary"])
        self.assertEqual(json.loads(out)["entries"], 1)

    def test_diplomacy_set_status(self):
        self._run(["diplomacy", "log", "--counterparty", "Atlantis",
                   "--type", "notice", "--date", "2026-01-15",
                   "--summary", "heads up"])
        out = self._run(["diplomacy", "set-status", "--id", "DIP-0001",
                         "--status", "expired"])
        self.assertEqual(json.loads(out)["status"], "expired")


if __name__ == "__main__":
    unittest.main()
