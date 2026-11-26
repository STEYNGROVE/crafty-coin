import unittest
import sqlite3

from engine import (
    Education,MISSIONS,available,locks
)

class Tests(unittest.TestCase):

    def setUp(self):
        self.e=Education(":memory:")

    def tearDown(self):
        self.e.close()

    def test_missions(self):
        self.assertEqual(len(MISSIONS),66)

    def test_unique_missions(self):
        self.assertEqual(
            len({m["id"] for m in MISSIONS}),66
        )

    def test_academies(self):
        self.assertEqual(
            len({m["academy"] for m in MISSIONS}),22
        )

    def test_discover(self):
        self.assertEqual(len(available(4)),22)

    def test_explorer(self):
        self.assertEqual(len(available(10)),22)

    def test_future(self):
        self.assertEqual(len(available(17)),22)

    def test_all_ages(self):
        for age in range(4,18):
            self.assertEqual(len(available(age)),22)

    def test_invalid_age(self):
        with self.assertRaises(ValueError):
            available(3)

    def test_adult_isolation(self):
        with self.assertRaises(ValueError):
            available(18)

    def test_invalid_type(self):
        with self.assertRaises(ValueError):
            available("10")

    def test_registration(self):
        self.e.register("SIM-LEARNER",10)

    def test_real_identity_block(self):
        with self.assertRaises(ValueError):
            self.e.register("REAL-USER",10)

    def test_completion(self):
        self.e.register("SIM-LEARNER",10)
        self.e.complete(
            "SIM-LEARNER",available(10)[0]["id"]
        )
        self.assertEqual(
            self.e.progress("SIM-LEARNER")["completed"],1
        )

    def test_duplicate_completion(self):
        self.e.register("SIM-LEARNER",10)
        mission=available(10)[0]["id"]
        self.e.complete("SIM-LEARNER",mission)

        with self.assertRaises(sqlite3.IntegrityError):
            self.e.complete("SIM-LEARNER",mission)

    def test_wrong_pathway(self):
        self.e.register("SIM-LEARNER",10)

        with self.assertRaises(PermissionError):
            self.e.complete(
                "SIM-LEARNER",available(5)[0]["id"]
            )

    def test_unknown_mission(self):
        self.e.register("SIM-LEARNER",10)

        with self.assertRaises(ValueError):
            self.e.complete("SIM-LEARNER","UNKNOWN")

    def test_unknown_learner(self):
        with self.assertRaises(PermissionError):
            self.e.complete(
                "SIM-UNKNOWN",available(10)[0]["id"]
            )

    def test_deletion(self):
        self.e.register("SIM-LEARNER",10)
        self.e.complete(
            "SIM-LEARNER",available(10)[0]["id"]
        )
        self.e.delete("SIM-LEARNER")

        self.assertEqual(
            self.e.db.execute(
                "SELECT COUNT(*) FROM progress"
            ).fetchone()[0],0
        )

    def test_crafty_everywhere(self):
        self.assertTrue(all(
            m["character"]=="Crafty" for m in MISSIONS
        ))

    def test_offline(self):
        self.assertTrue(all(
            m["offlineAvailable"] for m in MISSIONS
        ))

    def test_live_ai_disabled(self):
        self.assertTrue(all(
            m["liveAIRequired"] is False for m in MISSIONS
        ))

    def test_crypto_disabled(self):
        self.assertTrue(all(
            m["cryptoEnabled"] is False for m in MISSIONS
        ))

    def test_financial_rewards_disabled(self):
        self.assertTrue(all(
            m["financialReward"] is False for m in MISSIONS
        ))

    def test_conversion_blocked(self):
        with self.assertRaises(PermissionError):
            self.e.convert_achievement()

    def test_financial_locks(self):
        locks()

if __name__=="__main__":
    unittest.main(verbosity=2)
