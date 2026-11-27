import unittest
import sqlite3
import tempfile
from pathlib import Path
from engine import Subscriptions,PRODUCTS,locks

class Tests(unittest.TestCase):

    def setUp(self):
        self.s=Subscriptions()
        self.s.register("SIM-ADULT",30)
        self.s.register("SIM-OTHER",40)

    def tearDown(self):
        self.s.close()

    def create(self,period="MONTHLY"):
        return self.s.create(
            "SIM-SUB","SIM-ADULT",
            "BUSINESS_BASIC",period,0
        )

    def test_01_locks(self):
        locks()

    def test_02_catalogue(self):
        self.assertEqual(len(PRODUCTS),8)

    def test_03_minor(self):
        with self.assertRaises(PermissionError):
            self.s.register("SIM-CHILD",17)

    def test_04_real_identity(self):
        with self.assertRaises(PermissionError):
            self.s.register("REAL",30)

    def test_05_boolean_age(self):
        with self.assertRaises(PermissionError):
            self.s.register("SIM-INVALID",True)

    def test_06_monthly(self):
        self.assertEqual(self.create()["expires"],30)

    def test_07_annual(self):
        self.assertEqual(self.create("ANNUAL")["expires"],365)

    def test_08_trial(self):
        result=self.create("TRIAL")
        self.assertEqual(result["expires"],7)
        self.assertEqual(result["illustrativePriceCents"],0)

    def test_09_monthly_price(self):
        self.assertEqual(
            self.create()["illustrativePriceCents"],9900
        )

    def test_10_annual_price(self):
        self.assertEqual(
            self.create("ANNUAL")["illustrativePriceCents"],
            118800
        )

    def test_11_expiration(self):
        self.create()
        self.assertFalse(
            self.s.status("SIM-SUB","SIM-ADULT",30)["access"]
        )

    def test_12_active(self):
        self.create()
        self.assertTrue(
            self.s.status("SIM-SUB","SIM-ADULT",29)["access"]
        )

    def test_13_isolation(self):
        self.create()
        with self.assertRaises(PermissionError):
            self.s.status("SIM-SUB","SIM-OTHER",0)

    def test_14_duplicate(self):
        self.create()
        with self.assertRaises(sqlite3.IntegrityError):
            self.create()

    def test_15_renewal(self):
        self.create()
        result=self.s.simulate_renewal(
            "SIM-RENEW","SIM-SUB","SIM-ADULT",30
        )
        self.assertEqual(result["expires"],60)

    def test_16_duplicate_renewal(self):
        self.create()
        self.s.simulate_renewal(
            "SIM-RENEW","SIM-SUB","SIM-ADULT",30
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.s.simulate_renewal(
                "SIM-RENEW","SIM-SUB","SIM-ADULT",30
            )
        self.assertEqual(
            self.s.status("SIM-SUB","SIM-ADULT",30)["expires"],60
        )

    def test_17_trial_renewal(self):
        self.create("TRIAL")
        with self.assertRaises(PermissionError):
            self.s.simulate_renewal(
                "SIM-RENEW","SIM-SUB","SIM-ADULT",7
            )

    def test_18_cancel_immediate(self):
        self.create()
        result=self.s.cancel(
            "SIM-CANCEL","SIM-SUB","SIM-ADULT",5,True
        )
        self.assertFalse(result["access"])

    def test_19_cancel_end(self):
        self.create()
        result=self.s.cancel(
            "SIM-CANCEL","SIM-SUB","SIM-ADULT",5
        )
        self.assertTrue(result["access"])
        self.assertFalse(
            self.s.status("SIM-SUB","SIM-ADULT",30)["access"]
        )

    def test_20_cancelled_renewal(self):
        self.create()
        self.s.cancel(
            "SIM-CANCEL","SIM-SUB","SIM-ADULT",5
        )
        with self.assertRaises(PermissionError):
            self.s.simulate_renewal(
                "SIM-RENEW","SIM-SUB","SIM-ADULT",30
            )

    def test_21_perpetual_licence(self):
        result=self.s.create(
            "SIM-LIC","SIM-ADULT",
            "SOFTWARE_LICENSE","PERPETUAL",0
        )
        self.assertIsNone(result["expires"])

    def test_22_invalid_perpetual(self):
        with self.assertRaises(ValueError):
            self.create("PERPETUAL")

    def test_23_unknown_product(self):
        with self.assertRaises(ValueError):
            self.s.create(
                "SIM-SUB","SIM-ADULT","UNKNOWN","MONTHLY",0
            )

    def test_24_unknown_period(self):
        with self.assertRaises(ValueError):
            self.create("UNKNOWN")

    def test_25_invalid_day(self):
        self.create()
        with self.assertRaises(ValueError):
            self.s.status("SIM-SUB","SIM-ADULT",-1)

    def test_26_no_real_revenue(self):
        self.create()
        self.assertEqual(
            self.s.summary()["actualRevenueCents"],0
        )

    def test_27_no_charges(self):
        with self.assertRaises(PermissionError):
            self.s.charge()

    def test_28_no_live_renewals(self):
        with self.assertRaises(PermissionError):
            self.s.renew_live()

    def test_29_no_token_payment(self):
        with self.assertRaises(PermissionError):
            self.s.token_payment()

    def test_30_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"trial.db"
            s=Subscriptions(path)
            s.register("SIM-TEST",30)
            s.create(
                "SIM-ORDER","SIM-TEST",
                "BUSINESS_BASIC","MONTHLY",0
            )
            s.close()
            s=Subscriptions(path)
            self.assertTrue(
                s.status("SIM-ORDER","SIM-TEST",1)["access"]
            )
            s.close()

if __name__=="__main__":
    unittest.main(verbosity=2)
