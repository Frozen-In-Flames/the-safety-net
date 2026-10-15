import os
import tempfile
import unittest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from disaster import Disaster, SEVERITY_NEED


class TestDisaster(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Disaster(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_stock_and_inventory(self):
        self.d.stock("depot-north", "water", 5000)
        self.d.stock("depot-north", "water", 1000)
        inv = self.d.inventory(depot="depot-north")
        self.assertEqual(len(inv), 1)
        self.assertEqual(inv[0]["quantity"], 6000)

    def test_stock_rejects_bad_resource(self):
        with self.assertRaises(ValueError):
            self.d.stock("depot-north", "caviar", 10)

    def test_stock_rejects_nonpositive(self):
        with self.assertRaises(ValueError):
            self.d.stock("depot-north", "water", 0)

    def test_report_incident(self):
        rec = self.d.report_incident("flood", "Riverside", 3)
        self.assertEqual(rec["id"], "INC-0001")
        self.assertEqual(rec["status"], "open")
        self.assertEqual(rec["source"], "nation disaster registry")

    def test_report_rejects_bad_severity(self):
        with self.assertRaises(ValueError):
            self.d.report_incident("flood", "Riverside", 9)

    def test_report_rejects_bad_type(self):
        with self.assertRaises(ValueError):
            self.d.report_incident("volcano", "Riverside", 2)

    def test_need_comes_from_severity_table(self):
        rec = self.d.report_incident("storm", "Coastville", 2)
        need = self.d.need(rec["id"])
        self.assertEqual(need, SEVERITY_NEED[2])

    def test_dispatch_allocates_and_decrements(self):
        self.d.stock("depot-north", "water", 10000)
        self.d.stock("depot-north", "food", 10000)
        self.d.stock("depot-north", "blankets", 10000)
        rec = self.d.report_incident("storm", "Coastville", 2)
        disp = self.d.dispatch(rec["id"])
        self.assertEqual(disp["allocations"]["water"], 500)
        self.assertEqual(disp["allocations"]["food"], 500)
        self.assertEqual(disp["allocations"]["blankets"], 200)
        self.assertEqual(disp["unmet"], {})
        inv = {i["resource"]: i["quantity"]
               for i in self.d.inventory(depot="depot-north")}
        self.assertEqual(inv["water"], 9500)
        self.assertEqual(self.d.incident(rec["id"])["status"], "responding")

    def test_dispatch_reports_unmet_need(self):
        self.d.stock("depot-north", "water", 100)  # far short of sev-3 need
        rec = self.d.report_incident("fire", "Drytown", 3)
        disp = self.d.dispatch(rec["id"])
        self.assertEqual(disp["allocations"]["water"], 100)
        self.assertIn("food", disp["unmet"])
        self.assertGreater(disp["unmet"]["food"], 0)

    def test_unmet_need_empty_when_fully_supplied(self):
        self.d.stock("depot-north", "water", 10000)
        self.d.stock("depot-north", "food", 10000)
        rec = self.d.report_incident("flood", "Riverside", 1)
        self.d.dispatch(rec["id"])
        self.assertEqual(self.d.unmet_need(rec["id"]), {})

    def test_second_dispatch_covers_remainder(self):
        self.d.stock("depot-north", "water", 100)
        rec = self.d.report_incident("fire", "Drytown", 3)
        self.d.dispatch(rec["id"])
        self.assertIn("food", self.d.unmet_need(rec["id"]))
        self.d.stock("depot-south", "food", 50000)
        self.d.stock("depot-south", "water", 50000)
        self.d.stock("depot-south", "shelter_kits", 50000)
        self.d.stock("depot-south", "medical", 50000)
        self.d.stock("depot-south", "blankets", 50000)
        disp2 = self.d.dispatch(rec["id"])
        self.assertEqual(self.d.unmet_need(rec["id"]), {})
        self.assertGreater(len(disp2["allocations"]), 0)

    def test_resolve(self):
        rec = self.d.report_incident("flood", "Riverside", 1)
        self.d.resolve(rec["id"])
        self.assertEqual(self.d.incident(rec["id"])["status"], "resolved")

    def test_dispatch_resolved_raises(self):
        rec = self.d.report_incident("flood", "Riverside", 1)
        self.d.resolve(rec["id"])
        with self.assertRaises(ValueError):
            self.d.dispatch(rec["id"])

    def test_incidents_filter_by_status(self):
        self.d.report_incident("flood", "Riverside", 1)
        r2 = self.d.report_incident("fire", "Drytown", 2)
        self.d.resolve(r2["id"])
        self.assertEqual(len(self.d.incidents(status="open")), 1)
        self.assertEqual(len(self.d.incidents(status="resolved")), 1)

    def test_persistence(self):
        self.d.stock("depot-north", "water", 500)
        d2 = Disaster(self.tmp.name)
        inv = d2.inventory(depot="depot-north")
        self.assertEqual(inv[0]["quantity"], 500)


if __name__ == "__main__":
    unittest.main()
