import unittest
import sqlite3
import tempfile
from pathlib import Path

from engine import (
    Squad,CHALLENGES,available,locks
)

class Tests(unittest.TestCase):

    def setUp(self):
        self.s=Squad(":memory:")
        self.s.register("SIM-PLAYER",10)
        self.challenge=available(10)[0]["id"]

    def tearDown(self):
        self.s.close()

    def test_challenge_count(self):
        self.assertEqual(len(CHALLENGES),36)

    def test_unique_challenges(self):
        self.assertEqual(
            len({c["id"] for c in CHALLENGES}),36
        )

    def test_heroes(self):
        self.assertEqual(
            len({c["hero"] for c in CHALLENGES}),12
        )

    def test_crafty_leader(self):
        self.assertTrue(all(
            c["leader"]=="Crafty"
            for c in CHALLENGES
        ))

    def test_all_ages(self):
        for age in range(4,18):
            self.assertEqual(len(available(age)),12)

    def test_adult_block(self):
        with self.assertRaises(ValueError):
            available(18)

    def test_invalid_age(self):
        with self.assertRaises(ValueError):
            available(3)

    def test_invalid_age_type(self):
        with self.assertRaises(ValueError):
            available("10")

    def test_real_identity_block(self):
        with self.assertRaises(ValueError):
            self.s.register("REAL-USER",10)

    def test_completion(self):
        self.s.complete("SIM-PLAYER",self.challenge)
        self.assertEqual(
            self.s.progress("SIM-PLAYER")
            ["completedChallenges"],1
        )

    def test_duplicate(self):
        self.s.complete("SIM-PLAYER",self.challenge)

        with self.assertRaises(sqlite3.IntegrityError):
            self.s.complete("SIM-PLAYER",self.challenge)

    def test_wrong_age(self):
        with self.assertRaises(PermissionError):
            self.s.complete(
                "SIM-PLAYER",available(5)[0]["id"]
            )

    def test_unknown_learner(self):
        with self.assertRaises(PermissionError):
            self.s.complete(
                "SIM-UNKNOWN",self.challenge
            )

    def test_unknown_challenge(self):
        with self.assertRaises(ValueError):
            self.s.complete("SIM-PLAYER","UNKNOWN")

    def test_invalid_difficulty(self):
        with self.assertRaises(ValueError):
            self.s.complete(
                "SIM-PLAYER",self.challenge,4
            )

    def test_skip_level(self):
        with self.assertRaises(PermissionError):
            self.s.complete(
                "SIM-PLAYER",self.challenge,3
            )

    def test_progression(self):
        for level in (1,2,3):
            self.s.complete(
                "SIM-PLAYER",self.challenge,level
            )

        p=self.s.progress("SIM-PLAYER")

        self.assertEqual(p["completedChallenges"],1)
        self.assertEqual(
            p["achievements"][0]["difficulty"],3
        )

    def test_deletion(self):
        self.s.complete("SIM-PLAYER",self.challenge)
        self.s.delete("SIM-PLAYER")

        self.assertEqual(
            self.s.db.execute(
                "SELECT COUNT(*) FROM achievements"
            ).fetchone()[0],0
        )

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"test.db"

            s=Squad(path)
            s.register("SIM-PERSIST",10)
            s.complete("SIM-PERSIST",self.challenge)
            s.close()

            s=Squad(path)

            try:
                self.assertEqual(
                    s.progress("SIM-PERSIST")
                    ["completedChallenges"],1
                )
            finally:
                s.close()

    def test_offline(self):
        self.assertTrue(all(
            c["offlineAvailable"]
            for c in CHALLENGES
        ))

    def test_optional(self):
        self.assertTrue(all(
            c["optional"] for c in CHALLENGES
        ))

    def test_no_live_ai(self):
        self.assertTrue(all(
            c["liveAIRequired"] is False
            for c in CHALLENGES
        ))

    def test_no_crypto(self):
        self.assertTrue(all(
            c["cryptoReward"] is False
            for c in CHALLENGES
        ))

    def test_no_cash(self):
        self.assertEqual(
            self.s.progress("SIM-PLAYER")
            ["cashRewards"],0
        )

    def test_financial_reward_block(self):
        with self.assertRaises(PermissionError):
            self.s.financial_reward()

    def test_financial_locks(self):
        locks()

if __name__=="__main__":
    unittest.main(verbosity=2)
