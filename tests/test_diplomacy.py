import datetime
import os
import tempfile
import unittest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from diplomacy import Diplomacy, ENTRY_TYPES, ENTRY_STATUSES


def _date(days_from_today):
    return (datetime.datetime.now(datetime.timezone.utc).date()
            + datetime.timedelta(days=days_from_today)).isoformat()


class TestDiplomacy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Diplomacy(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_log_valid(self):
        e = self.d.log("Atlantis", "treaty", "2026-01-15",
                       "Mutual recognition and trade",
                       review_date="2027-01-15")
        self.assertEqual(e["id"], "DIP-0001")
        self.assertEqual(e["status"], "active")
        self.assertEqual(e["source"], "nation diplomacy log")

    def test_log_rejects_bad_type(self):
        with self.assertRaises(ValueError):
            self.d.log("Atlantis", "ultimatum", "2026-01-15", "x")

    def test_log_rejects_bad_date(self):
        with self.assertRaises(ValueError):
            self.d.log("Atlantis", "treaty", "15-01-2026", "x")

    def test_log_rejects_bad_review_date(self):
        with self.assertRaises(ValueError):
            self.d.log("Atlantis", "treaty", "2026-01-15", "x",
                       review_date="soon")

    def test_entries_filter(self):
        self.d.log("Atlantis", "treaty", "2026-01-15", "trade")
        self.d.log("Pacifica", "summit", "2026-03-01", "climate")
        self.assertEqual(len(self.d.entries(counterparty="Atlantis")), 1)
        self.assertEqual(len(self.d.entries(etype="summit")), 1)
        self.assertEqual(len(self.d.entries()), 2)

    def test_set_status(self):
        self.d.log("Atlantis", "treaty", "2026-01-15", "trade")
        e = self.d.set_status("DIP-0001", "expired")
        self.assertEqual(e["status"], "expired")

    def test_set_status_unknown_raises(self):
        with self.assertRaises(ValueError):
            self.d.set_status("DIP-9999", "expired")

    def test_obligations_within_window(self):
        self.d.log("Atlantis", "treaty", "2025-01-15", "trade",
                   review_date=_date(30))
        self.d.log("Pacifica", "treaty", "2025-06-01", "fisheries",
                   review_date=_date(200))
        ob = self.d.obligations(within_days=90)
        self.assertEqual(len(ob), 1)
        self.assertEqual(ob[0]["counterparty"], "Atlantis")
        self.assertFalse(ob[0]["overdue"])

    def test_obligations_include_overdue_flagged(self):
        self.d.log("Atlantis", "treaty", "2024-01-15", "trade",
                   review_date=_date(-10))
        ob = self.d.obligations(within_days=90)
        self.assertEqual(len(ob), 1)
        self.assertTrue(ob[0]["overdue"])
        self.assertEqual(ob[0]["days_until_review"], -10)

    def test_obligations_skip_inactive(self):
        self.d.log("Atlantis", "treaty", "2024-01-15", "trade",
                   status="withdrawn", review_date=_date(10))
        self.assertEqual(self.d.obligations(within_days=90), [])

    def test_obligations_skip_no_review_date(self):
        self.d.log("Atlantis", "notice", "2026-01-15", "heads up")
        self.assertEqual(self.d.obligations(within_days=90), [])

    def test_summary(self):
        self.d.log("Atlantis", "treaty", "2026-01-15", "trade",
                   review_date=_date(30))
        self.d.log("Pacifica", "summit", "2026-03-01", "climate")
        s = self.d.summary()
        self.assertEqual(s["entries"], 2)
        self.assertEqual(s["by_type"]["treaty"], 1)
        self.assertIn("Atlantis", s["counterparties"])
        self.assertEqual(s["upcoming_obligations_90d"], 1)

    def test_persistence(self):
        self.d.log("Atlantis", "treaty", "2026-01-15", "trade")
        d2 = Diplomacy(self.tmp.name)
        self.assertEqual(len(d2.entries()), 1)

    def test_entry_types_known(self):
        self.assertIn("treaty", ENTRY_TYPES)
        self.assertIn("active", ENTRY_STATUSES)


if __name__ == "__main__":
    unittest.main()
