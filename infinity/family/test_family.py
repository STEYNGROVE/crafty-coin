import unittest
import sqlite3
from engine import Family,verify_locks

class Tests(unittest.TestCase):

    def setUp(self):

        self.f=Family()

        self.f.adult("SIM-PARENT","PARENT")
        self.f.adult("SIM-OTHER","PARENT")
        self.f.adult("SIM-TEACHER","TEACHER")

        self.f.learner(
            "SIM-CHILD",10,"SIM-PARENT"
        )

    def tearDown(self):
        self.f.close()

    def test_01_locks(self):
        verify_locks()

    def test_02_parent_report(self):
        self.assertEqual(
            self.f.report(
                "SIM-PARENT","SIM-CHILD"
            )["completedActivities"],0
        )

    def test_03_other_parent_denied(self):
        with self.assertRaises(PermissionError):
            self.f.report("SIM-OTHER","SIM-CHILD")

    def test_04_teacher_denied(self):
        with self.assertRaises(PermissionError):
            self.f.report("SIM-TEACHER","SIM-CHILD")

    def test_05_teacher_grant(self):
        self.f.grant(
            "SIM-PARENT","SIM-CHILD","SIM-TEACHER"
        )
        self.f.report("SIM-TEACHER","SIM-CHILD")

    def test_06_teacher_revoke(self):
        self.f.grant(
            "SIM-PARENT","SIM-CHILD","SIM-TEACHER"
        )
        self.f.revoke(
            "SIM-PARENT","SIM-CHILD","SIM-TEACHER"
        )
        with self.assertRaises(PermissionError):
            self.f.report("SIM-TEACHER","SIM-CHILD")

    def test_07_wrong_parent_grant(self):
        with self.assertRaises(PermissionError):
            self.f.grant(
                "SIM-OTHER","SIM-CHILD","SIM-TEACHER"
            )

    def test_08_wrong_parent_revoke(self):
        with self.assertRaises(PermissionError):
            self.f.revoke(
                "SIM-OTHER","SIM-CHILD","SIM-TEACHER"
            )

    def test_09_invalid_teacher(self):
        with self.assertRaises(PermissionError):
            self.f.grant(
                "SIM-PARENT","SIM-CHILD","SIM-OTHER"
            )

    def test_10_invalid_age(self):
        with self.assertRaises(ValueError):
            self.f.learner(
                "SIM-NEW",18,"SIM-PARENT"
            )

    def test_11_minimum_age(self):
        self.f.learner("SIM-NEW",4,"SIM-PARENT")

    def test_12_maximum_age(self):
        self.f.learner("SIM-NEW",17,"SIM-PARENT")

    def test_13_boolean_age(self):
        with self.assertRaises(ValueError):
            self.f.learner(
                "SIM-NEW",True,"SIM-PARENT"
            )

    def test_14_teacher_not_parent(self):
        with self.assertRaises(PermissionError):
            self.f.learner(
                "SIM-NEW",10,"SIM-TEACHER"
            )

    def test_15_real_alias_denied(self):
        with self.assertRaises(ValueError):
            self.f.adult("REAL-USER","PARENT")

    def test_16_invalid_role(self):
        with self.assertRaises(ValueError):
            self.f.adult("SIM-NEW","ADMIN")

    def test_17_duplicate_adult(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.f.adult("SIM-PARENT","PARENT")

    def test_18_duplicate_learner(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.f.learner(
                "SIM-CHILD",10,"SIM-PARENT"
            )

    def test_19_progress(self):
        self.f.record(
            "SIM-PARENT","SIM-CHILD","SIM-ACTIVITY"
        )
        self.assertEqual(
            self.f.report(
                "SIM-PARENT","SIM-CHILD"
            )["completedActivities"],1
        )

    def test_20_duplicate_progress(self):
        args=("SIM-PARENT","SIM-CHILD","SIM-ACTIVITY")
        self.f.record(*args)
        with self.assertRaises(sqlite3.IntegrityError):
            self.f.record(*args)

    def test_21_unauthorized_progress(self):
        with self.assertRaises(PermissionError):
            self.f.record(
                "SIM-OTHER","SIM-CHILD","SIM-ACTIVITY"
            )

    def test_22_invalid_activity(self):
        with self.assertRaises(ValueError):
            self.f.record(
                "SIM-PARENT","SIM-CHILD","INVALID"
            )

    def test_23_pathway(self):
        self.assertEqual(
            self.f.report(
                "SIM-PARENT","SIM-CHILD"
            )["pathway"],"EXPLORER"
        )

    def test_24_delete(self):
        self.f.delete("SIM-PARENT","SIM-CHILD")
        with self.assertRaises(PermissionError):
            self.f.report("SIM-PARENT","SIM-CHILD")

    def test_25_unauthorized_delete(self):
        with self.assertRaises(PermissionError):
            self.f.delete("SIM-OTHER","SIM-CHILD")

    def test_26_cascade(self):
        self.f.grant(
            "SIM-PARENT","SIM-CHILD","SIM-TEACHER"
        )
        self.f.record(
            "SIM-PARENT","SIM-CHILD","SIM-ACTIVITY"
        )
        self.f.delete("SIM-PARENT","SIM-CHILD")
        for table in ("consent","progress"):
            self.assertEqual(
                self.f.db.execute(
                    "SELECT COUNT(*) FROM "+table
                ).fetchone()[0],0
            )

    def test_27_no_finance(self):
        with self.assertRaises(PermissionError):
            self.f.financial_reward()

    def test_28_no_external_export(self):
        with self.assertRaises(PermissionError):
            self.f.export_external()

    def test_29_no_diagnosis(self):
        self.assertIsNone(
            self.f.report(
                "SIM-PARENT","SIM-CHILD"
            )["diagnosis"]
        )

    def test_30_no_crypto(self):
        self.assertEqual(
            self.f.report(
                "SIM-PARENT","SIM-CHILD"
            )["cryptoRewards"],0
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
