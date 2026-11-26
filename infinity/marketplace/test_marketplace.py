import unittest
import sqlite3

from engine import Marketplace,PRODUCTS,locks

class Tests(unittest.TestCase):

    def setUp(self):
        self.m=Marketplace()
        self.m.register("SIM-ADULT",30)
        self.m.register("SIM-OTHER",40)

    def tearDown(self):
        self.m.close()

    def order(self):
        self.m.order(
            "SIM-ORDER",
            "SIM-ADULT",
            "BUSINESS_PRO"
        )

    def activate(self):
        self.order()
        self.m.simulate("SIM-ORDER","SIM-ADULT")

    def test_01_locks(self):
        locks()

    def test_02_products(self):
        self.assertEqual(len(PRODUCTS),12)

    def test_03_minor_denied(self):
        with self.assertRaises(PermissionError):
            self.m.register("SIM-CHILD",17)

    def test_04_boolean_age(self):
        with self.assertRaises(PermissionError):
            self.m.register("SIM-NEW",True)

    def test_05_minimum_age(self):
        self.m.register("SIM-NEW",18)

    def test_06_maximum_age(self):
        self.m.register("SIM-NEW",120)

    def test_07_invalid_age(self):
        with self.assertRaises(PermissionError):
            self.m.register("SIM-NEW",121)

    def test_08_real_customer_denied(self):
        with self.assertRaises(ValueError):
            self.m.register("REAL-CUSTOMER",30)

    def test_09_duplicate_customer(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.m.register("SIM-ADULT",30)

    def test_10_order(self):
        self.order()

    def test_11_unknown_product(self):
        with self.assertRaises(ValueError):
            self.m.order(
                "SIM-ORDER","SIM-ADULT","INVALID"
            )

    def test_12_unknown_customer(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.m.order(
                "SIM-ORDER","SIM-MISSING","BUSINESS_PRO"
            )

    def test_13_duplicate_order(self):
        self.order()
        with self.assertRaises(sqlite3.IntegrityError):
            self.order()

    def test_14_all_products(self):
        for i,product in enumerate(PRODUCTS):
            self.m.order(
                f"SIM-{i:03d}",
                "SIM-ADULT",
                product
            )

    def test_15_draft_no_access(self):
        self.order()
        self.assertFalse(
            self.m.access("SIM-ADULT","BUSINESS_PRO")
        )

    def test_16_simulated_access(self):
        self.activate()
        self.assertTrue(
            self.m.access("SIM-ADULT","BUSINESS_PRO")
        )

    def test_17_duplicate_activation(self):
        self.activate()
        with self.assertRaises(PermissionError):
            self.m.simulate("SIM-ORDER","SIM-ADULT")

    def test_18_wrong_customer_activation(self):
        self.order()
        with self.assertRaises(PermissionError):
            self.m.simulate("SIM-ORDER","SIM-OTHER")

    def test_19_missing_order(self):
        with self.assertRaises(PermissionError):
            self.m.simulate("SIM-MISSING","SIM-ADULT")

    def test_20_customer_isolation(self):
        self.activate()
        self.assertFalse(
            self.m.access("SIM-OTHER","BUSINESS_PRO")
        )

    def test_21_product_isolation(self):
        self.activate()
        self.assertFalse(
            self.m.access("SIM-ADULT","BUSINESS_BASIC")
        )

    def test_22_cancel_draft(self):
        self.order()
        self.m.cancel("SIM-ORDER","SIM-ADULT")

    def test_23_cancel_active(self):
        self.activate()
        self.m.cancel("SIM-ORDER","SIM-ADULT")
        self.assertFalse(
            self.m.access("SIM-ADULT","BUSINESS_PRO")
        )

    def test_24_wrong_customer_cancel(self):
        self.activate()
        with self.assertRaises(PermissionError):
            self.m.cancel("SIM-ORDER","SIM-OTHER")

    def test_25_cancelled_activation(self):
        self.order()
        self.m.cancel("SIM-ORDER","SIM-ADULT")
        with self.assertRaises(PermissionError):
            self.m.simulate("SIM-ORDER","SIM-ADULT")

    def test_26_duplicate_cancel(self):
        self.order()
        self.m.cancel("SIM-ORDER","SIM-ADULT")
        with self.assertRaises(PermissionError):
            self.m.cancel("SIM-ORDER","SIM-ADULT")

    def test_27_no_revenue(self):
        self.activate()
        self.assertEqual(
            self.m.summary("SIM-ADULT")["actualRevenueZAR"],
            0
        )

    def test_28_no_payment(self):
        with self.assertRaises(PermissionError):
            self.m.pay()

    def test_29_no_renewal(self):
        with self.assertRaises(PermissionError):
            self.m.renew()

    def test_30_no_settlement(self):
        with self.assertRaises(PermissionError):
            self.m.settle()

    def test_31_no_token_payment(self):
        with self.assertRaises(PermissionError):
            self.m.token_payment()

    def test_32_no_child_purchase(self):
        with self.assertRaises(PermissionError):
            self.m.child_purchase()

    def test_33_summary_isolation(self):
        self.activate()
        self.assertEqual(
            self.m.summary("SIM-OTHER")["orders"],
            []
        )

    def test_34_no_token_transfers(self):
        self.activate()
        self.assertEqual(
            self.m.summary("SIM-ADULT")[
                "actualTokenTransfers"
            ],0
        )

    def test_35_price_integrity(self):
        self.order()
        row=self.m.db.execute(
            "SELECT amount FROM orders"
        ).fetchone()
        self.assertEqual(
            row[0],
            PRODUCTS["BUSINESS_PRO"]["priceCents"]
        )

    def test_36_entitlement_integrity(self):
        self.activate()
        count=self.m.db.execute(
            "SELECT COUNT(*) FROM entitlements"
        ).fetchone()[0]
        self.assertEqual(count,1)

if __name__=="__main__":
    unittest.main(verbosity=2)
