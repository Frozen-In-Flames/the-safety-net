import datetime
import os
import tempfile
import unittest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benefits import Benefits, PROGRAMS, SCHEDULES


def _iso(dt):
    return dt.isoformat()


class TestBenefits(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.b = Benefits(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_enroll_valid(self):
        rec = self.b.enroll("BEN-001", "retirement", 1200.0, "monthly")
        self.assertEqual(rec["id"], "BEN-001")
        self.assertEqual(rec["amount"], 1200.0)
        self.assertEqual(rec["source"], "nation benefits ledger")

    def test_enroll_rejects_bad_program(self):
        with self.assertRaises(ValueError):
            self.b.enroll("BEN-001", "lottery", 100.0, "monthly")

    def test_enroll_rejects_bad_schedule(self):
        with self.assertRaises(ValueError):
            self.b.enroll("BEN-001", "retirement", 100.0, "yearly")

    def test_enroll_rejects_nonpositive_amount(self):
        with self.assertRaises(ValueError):
            self.b.enroll("BEN-001", "retirement", 0, "monthly")

    def test_enroll_rejects_duplicate(self):
        self.b.enroll("BEN-001", "retirement", 100.0, "monthly")
        with self.assertRaises(ValueError):
            self.b.enroll("BEN-001", "disability", 200.0, "weekly")

    def test_run_payments_pays_due(self):
        # Enrolled 40 days ago on a monthly schedule: one payment due.
        past = datetime.datetime.now(datetime.timezone.utc) \
            - datetime.timedelta(days=31)
        rec = self.b.enroll("BEN-001", "retirement", 1200.0, "monthly")
        rec["enrolled_at"] = _iso(past)
        self.b._save()
        pays = self.b.run_payments()
        self.assertEqual(len(pays), 1)
        self.assertEqual(pays[0]["beneficiary"], "BEN-001")
        self.assertEqual(pays[0]["status"], "paid")
        self.assertTrue(pays[0]["on_time"])

    def test_nothing_due_when_recently_paid(self):
        self.b.enroll("BEN-001", "retirement", 1200.0, "monthly")
        self.b.run_payments()  # nothing due yet
        pays = self.b.run_payments()
        self.assertEqual(pays, [])

    def test_late_payment_flagged(self):
        past = datetime.datetime.now(datetime.timezone.utc) \
            - datetime.timedelta(days=60)
        rec = self.b.enroll("BEN-001", "disability", 900.0, "monthly")
        rec["enrolled_at"] = _iso(past)
        self.b._save()
        pays = self.b.run_payments()
        self.assertEqual(len(pays), 1)
        # Due 30 days after enrollment, paid 60 days after: 30 days late.
        self.assertFalse(pays[0]["on_time"])
        self.assertGreater(pays[0]["late_days"], 3)

    def test_on_time_rate(self):
        past = datetime.datetime.now(datetime.timezone.utc) \
            - datetime.timedelta(days=31)
        for bid in ("BEN-001", "BEN-002"):
            rec = self.b.enroll(bid, "retirement", 1000.0, "monthly")
            rec["enrolled_at"] = _iso(past)
        self.b._save()
        self.b.run_payments()
        rate, due_n, on_n = self.b.on_time_rate(days=90)
        self.assertEqual(due_n, 2)
        self.assertEqual(on_n, 2)
        self.assertAlmostEqual(rate, 1.0)

    def test_on_time_rate_empty_window(self):
        rate, due_n, on_n = self.b.on_time_rate(days=90)
        self.assertIsNone(rate)
        self.assertEqual(due_n, 0)

    def test_summary_counts(self):
        self.b.enroll("BEN-001", "retirement", 1200.0, "monthly")
        self.b.enroll("BEN-002", "survivor", 800.0, "monthly")
        s = self.b.summary()
        self.assertEqual(s["beneficiaries"], 2)
        self.assertEqual(s["by_program"]["retirement"], 1)
        self.assertEqual(s["by_program"]["survivor"], 1)

    def test_persistence(self):
        self.b.enroll("BEN-001", "retirement", 1200.0, "monthly")
        b2 = Benefits(self.tmp.name)
        self.assertIsNotNone(b2.beneficiary("BEN-001"))

    def test_programs_and_schedules_known(self):
        self.assertIn("retirement", PROGRAMS)
        self.assertIn("monthly", SCHEDULES)


if __name__ == "__main__":
    unittest.main()
