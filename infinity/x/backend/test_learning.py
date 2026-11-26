import tempfile
import unittest
from engine import Learning

class Tests(unittest.TestCase):

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.app=Learning(self.tmp.name)

    def tearDown(self):
        self.app.close()
        self.tmp.cleanup()

    def test_01_initial(self):
        self.assertEqual(
            self.app.progress("DISCOVER")["count"],0
        )

    def test_02_academy(self):
        r=self.app.complete(
            "DISCOVER","ACA-01-DISCOVER"
        )
        self.assertEqual(r["count"],1)

    def test_03_duplicate(self):
        for _ in range(2):
            r=self.app.complete(
                "DISCOVER","ACA-01-DISCOVER"
            )
        self.assertEqual(r["count"],1)

    def test_04_wrong_pathway(self):
        with self.assertRaises(PermissionError):
            self.app.complete(
                "DISCOVER","ACA-01-FUTURE"
            )

    def test_05_hero(self):
        r=self.app.complete(
            "DISCOVER","SQUAD-01-DISCOVER",1
        )
        self.assertEqual(r["count"],1)

    def test_06_hero_progression(self):
        for level in (1,2,3):
            r=self.app.complete(
                "DISCOVER","SQUAD-01-DISCOVER",level
            )
        self.assertEqual(
            r["heroes"][0]["difficulty"],3
        )

    def test_07_skip_level(self):
        with self.assertRaises(PermissionError):
            self.app.complete(
                "DISCOVER","SQUAD-01-DISCOVER",3
            )

    def test_08_world(self):
        r=self.app.complete(
            "DISCOVER","LIFE-CITY-DISCOVER"
        )
        self.assertEqual(r["count"],1)

    def test_09_decision(self):
        r=self.app.decide("DISCOVER","GARDEN")
        self.assertEqual(r["learning"],55)

    def test_10_rest(self):
        r=self.app.decide("DISCOVER","REST")
        self.assertEqual(r["energy"],100)

    def test_11_unknown_action(self):
        with self.assertRaises(ValueError):
            self.app.decide("DISCOVER","UNKNOWN")

    def test_12_persistence(self):
        self.app.complete(
            "DISCOVER","ACA-01-DISCOVER"
        )
        self.app.close()
        self.app=Learning(self.tmp.name)

        self.assertEqual(
            self.app.progress("DISCOVER")["count"],1
        )

    def test_13_reset(self):
        self.app.complete(
            "DISCOVER","ACA-01-DISCOVER"
        )
        self.assertEqual(
            self.app.reset("DISCOVER")["count"],0
        )

    def test_14_isolation(self):
        self.app.complete(
            "DISCOVER","ACA-01-DISCOVER"
        )
        self.assertEqual(
            self.app.progress("FUTURE")["count"],0
        )

    def test_15_no_cash(self):
        self.assertEqual(
            self.app.progress("DISCOVER")[
                "financialRewards"
            ],0
        )

    def test_16_no_crypto(self):
        self.assertEqual(
            self.app.progress("DISCOVER")[
                "cryptoRewards"
            ],0
        )

    def test_17_invalid_pathway(self):
        with self.assertRaises(ValueError):
            self.app.progress("ADULT")

    def test_18_invalid_mission(self):
        with self.assertRaises(ValueError):
            self.app.complete(
                "DISCOVER","UNKNOWN"
            )

if __name__=="__main__":
    unittest.main(verbosity=2)
