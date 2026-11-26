import unittest
import sqlite3
import tempfile
from pathlib import Path

from engine import (
    VirtualLife,available,MISSIONS,
    ACTIONS,RESOURCES,locks
)

class Tests(unittest.TestCase):

    def setUp(self):
        self.v=VirtualLife(":memory:")
        self.v.register("SIM-PLAYER",10)

    def tearDown(self):
        self.v.close()

    def test_worlds(self):
        self.assertEqual(
            len({m["world"] for m in MISSIONS}),12)

    def test_missions(self):
        self.assertEqual(len(MISSIONS),36)

    def test_unique_missions(self):
        self.assertEqual(
            len({m["id"] for m in MISSIONS}),36)

    def test_all_ages(self):
        for age in range(4,18):
            self.assertEqual(len(available(age)),12)

    def test_adult_block(self):
        with self.assertRaises(ValueError):
            available(18)

    def test_invalid_age(self):
        with self.assertRaises(ValueError):
            available(3)

    def test_invalid_type(self):
        with self.assertRaises(ValueError):
            available("10")

    def test_real_identity(self):
        with self.assertRaises(ValueError):
            self.v.register("REAL-USER",10)

    def test_start(self):
        self.assertEqual(
            self.v.state("SIM-PLAYER")["energy"],80)

    def test_garden(self):
        s=self.v.decide(
            "SIM-PLAYER","GARDEN","SIM-1")
        self.assertEqual(s["environment"],85)
        self.assertEqual(s["resources"],50)

    def test_rest(self):
        s=self.v.decide(
            "SIM-PLAYER","REST","SIM-1")
        self.assertEqual(s["energy"],100)

    def test_ceiling(self):
        for n in range(20):
            s=self.v.decide(
                "SIM-PLAYER","REST",f"SIM-{n}")
        self.assertEqual(s["energy"],100)

    def test_insufficient(self):
        for n in range(4):
            self.v.decide(
                "SIM-PLAYER","LEARNING_CENTRE",
                f"SIM-{n}")

        before=self.v.state("SIM-PLAYER")

        with self.assertRaises(ValueError):
            self.v.decide(
                "SIM-PLAYER","LEARNING_CENTRE",
                "SIM-FAIL")

        self.assertEqual(
            before,self.v.state("SIM-PLAYER"))

    def test_duplicate(self):
        self.v.decide(
            "SIM-PLAYER","GARDEN","SIM-1")

        before=self.v.state("SIM-PLAYER")

        with self.assertRaises(sqlite3.IntegrityError):
            self.v.decide(
                "SIM-PLAYER","GARDEN","SIM-1")

        self.assertEqual(
            before,self.v.state("SIM-PLAYER"))

    def test_unknown_action(self):
        with self.assertRaises(ValueError):
            self.v.decide(
                "SIM-PLAYER","UNKNOWN","SIM-1")

    def test_unknown_player(self):
        with self.assertRaises(PermissionError):
            self.v.state("SIM-UNKNOWN")

    def test_real_reference(self):
        with self.assertRaises(ValueError):
            self.v.decide(
                "SIM-PLAYER","REST","REAL-1")

    def test_completion(self):
        self.v.complete(
            "SIM-PLAYER",available(10)[0]["id"])

        self.assertEqual(
            self.v.progress("SIM-PLAYER")
            ["completed"],1)

    def test_wrong_pathway(self):
        with self.assertRaises(PermissionError):
            self.v.complete(
                "SIM-PLAYER",available(5)[0]["id"])

    def test_duplicate_mission(self):
        m=available(10)[0]["id"]
        self.v.complete("SIM-PLAYER",m)

        with self.assertRaises(sqlite3.IntegrityError):
            self.v.complete("SIM-PLAYER",m)

    def test_deletion(self):
        self.v.decide(
            "SIM-PLAYER","REST","SIM-1")
        self.v.complete(
            "SIM-PLAYER",available(10)[0]["id"])

        self.v.delete("SIM-PLAYER")

        for table in ["players","decisions","missions"]:
            self.assertEqual(
                self.v.db.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0],0)

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"life.db"
            v=VirtualLife(p)
            v.register("SIM-PERSIST",15)
            v.decide("SIM-PERSIST","REST","SIM-1")
            v.close()

            v=VirtualLife(p)
            try:
                self.assertEqual(
                    v.state("SIM-PERSIST")["energy"],100)
            finally:
                v.close()

    def test_crafty(self):
        self.assertTrue(all(
            m["guide"]=="Crafty" for m in MISSIONS))

    def test_no_real_money(self):
        self.assertTrue(all(
            m["realMoney"] is False for m in MISSIONS))

    def test_no_crypto(self):
        self.assertTrue(all(
            m["crypto"] is False for m in MISSIONS))

    def test_no_live_ai(self):
        self.assertTrue(all(
            m["liveAI"] is False for m in MISSIONS))

    def test_withdrawal(self):
        with self.assertRaises(PermissionError):
            self.v.withdraw()

    def test_locks(self):
        locks()

if __name__=="__main__":
    unittest.main(verbosity=2)
