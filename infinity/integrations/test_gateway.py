import unittest
import sqlite3

from gateway import Gateway,SERVICES,locks

class Tests(unittest.TestCase):

    def setUp(self):
        self.g=Gateway()
        self.g.register("SIM-ADULT",30)
        self.g.register("SIM-OTHER",40)

    def tearDown(self):
        self.g.close()

    def draft(self):
        self.g.draft(
            "SIM-ORDER",
            "SIM-ADULT",
            "PIXELPUNK",
            100000
        )

    def test_01_locks(self):
        locks()

    def test_02_services(self):
        self.assertEqual(len(SERVICES),7)

    def test_03_adult_domains(self):
        self.assertTrue(
            all(
                s["domain"]=="ADULT"
                for s in SERVICES.values()
            )
        )

    def test_04_minor_denied(self):
        with self.assertRaises(PermissionError):
            self.g.register("SIM-CHILD",17)

    def test_05_boolean_age(self):
        with self.assertRaises(PermissionError):
            self.g.register("SIM-NEW",True)

    def test_06_minimum_age(self):
        self.g.register("SIM-NEW",18)

    def test_07_maximum_age(self):
        self.g.register("SIM-NEW",120)

    def test_08_invalid_age(self):
        with self.assertRaises(PermissionError):
            self.g.register("SIM-NEW",121)

    def test_09_real_account_denied(self):
        with self.assertRaises(ValueError):
            self.g.register("REAL-USER",30)

    def test_10_duplicate_account(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.g.register("SIM-ADULT",30)

    def test_11_draft(self):
        self.draft()
        self.assertEqual(
            self.g.summary("SIM-ADULT")["requests"][0][1],
            "DRAFT"
        )

    def test_12_all_services(self):
        for i,service in enumerate(SERVICES):
            self.g.draft(
                f"SIM-{i:03d}",
                "SIM-ADULT",
                service,
                10000
            )

    def test_13_unknown_service(self):
        with self.assertRaises(ValueError):
            self.g.draft(
                "SIM-ORDER","SIM-ADULT","INVALID",0
            )

    def test_14_negative_amount(self):
        with self.assertRaises(ValueError):
            self.g.draft(
                "SIM-ORDER","SIM-ADULT","PIXELPUNK",-1
            )

    def test_15_float_amount(self):
        with self.assertRaises(ValueError):
            self.g.draft(
                "SIM-ORDER","SIM-ADULT","PIXELPUNK",1.5
            )

    def test_16_boolean_amount(self):
        with self.assertRaises(ValueError):
            self.g.draft(
                "SIM-ORDER","SIM-ADULT","PIXELPUNK",True
            )

    def test_17_duplicate_reference(self):
        self.draft()
        with self.assertRaises(sqlite3.IntegrityError):
            self.draft()

    def test_18_unknown_account(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.g.draft(
                "SIM-ORDER","SIM-MISSING","PIXELPUNK",0
            )

    def test_19_review(self):
        self.draft()
        self.g.review("SIM-ORDER","SIM-ADULT")

    def test_20_wrong_reviewer(self):
        self.draft()
        with self.assertRaises(PermissionError):
            self.g.review("SIM-ORDER","SIM-OTHER")

    def test_21_duplicate_review(self):
        self.draft()
        self.g.review("SIM-ORDER","SIM-ADULT")
        with self.assertRaises(PermissionError):
            self.g.review("SIM-ORDER","SIM-ADULT")

    def test_22_cancel(self):
        self.draft()
        self.g.cancel("SIM-ORDER","SIM-ADULT")

    def test_23_cancel_reviewed(self):
        self.draft()
        self.g.review("SIM-ORDER","SIM-ADULT")
        self.g.cancel("SIM-ORDER","SIM-ADULT")

    def test_24_wrong_cancellation(self):
        self.draft()
        with self.assertRaises(PermissionError):
            self.g.cancel("SIM-ORDER","SIM-OTHER")

    def test_25_review_cancelled(self):
        self.draft()
        self.g.cancel("SIM-ORDER","SIM-ADULT")
        with self.assertRaises(PermissionError):
            self.g.review("SIM-ORDER","SIM-ADULT")

    def test_26_account_isolation(self):
        self.draft()
        self.assertEqual(
            self.g.summary("SIM-OTHER")["requests"],[]
        )

    def test_27_no_actual_revenue(self):
        self.draft()
        self.assertEqual(
            self.g.summary("SIM-ADULT")["actualRevenueZAR"],
            0
        )

    def test_28_no_purchases(self):
        with self.assertRaises(PermissionError):
            self.g.purchase()

    def test_29_no_settlement(self):
        with self.assertRaises(PermissionError):
            self.g.settle()

    def test_30_no_publishing(self):
        with self.assertRaises(PermissionError):
            self.g.publish()

    def test_31_no_child_data(self):
        with self.assertRaises(PermissionError):
            self.g.child_data()

    def test_32_no_live_connections(self):
        with self.assertRaises(PermissionError):
            self.g.connect_live()

if __name__=="__main__":
    unittest.main(verbosity=2)
