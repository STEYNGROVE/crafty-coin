import tempfile
import unittest
import sqlite3
from pathlib import Path
from core import Core,VISION,pathway,verify_locks

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.c=Core(self.tmp.name)

    def tearDown(self):
        self.c.close()
        self.tmp.cleanup()

    def child(self):
        return self.c.register("SIM-CHILD",10)

    def adult(self):
        return self.c.register("SIM-ADULT",25)

    def test_character(self):
        self.assertEqual(
            VISION["character"]["name"],"Crafty"
        )

    def test_academies(self):
        self.assertEqual(len(VISION["academies"]),22)
        self.assertEqual(
            len(set(VISION["academies"])),22
        )

    def test_superheroes(self):
        self.assertEqual(len(VISION["superheroes"]),12)

    def test_applications(self):
        self.assertEqual(len(VISION["applications"]),11)

    def test_languages(self):
        self.assertEqual(len(VISION["languages"]),4)

    def test_discover(self):
        self.assertEqual(pathway(4),"Discover")
        self.assertEqual(pathway(7),"Discover")

    def test_explorer(self):
        self.assertEqual(pathway(8),"Explorer")
        self.assertEqual(pathway(12),"Explorer")

    def test_future(self):
        self.assertEqual(pathway(13),"Future")
        self.assertEqual(pathway(17),"Future")

    def test_infinity(self):
        self.assertEqual(pathway(18),"Infinity")

    def test_invalid_age(self):
        with self.assertRaises(ValueError):
            pathway(3)

    def test_invalid_age_type(self):
        with self.assertRaises(ValueError):
            pathway("18")

    def test_child_domain(self):
        self.assertEqual(self.child()[1],"EDUCATION")

    def test_adult_domain(self):
        self.assertEqual(self.adult()[1],"ADULT")

    def test_child_isolation(self):
        identifier,_=self.child()

        with self.assertRaises(PermissionError):
            self.c.profile(identifier,"ADULT")

    def test_adult_isolation(self):
        identifier,_=self.adult()

        with self.assertRaises(PermissionError):
            self.c.profile(identifier,"EDUCATION")

    def test_child_application(self):
        identifier,domain=self.child()

        self.assertTrue(
            self.c.allowed_application(
                identifier,domain,"ColourCraft Kids"
            )
        )

    def test_child_financial_block(self):
        identifier,domain=self.child()

        self.assertFalse(
            self.c.allowed_application(
                identifier,domain,"Crafty Infinity"
            )
        )

    def test_adult_application(self):
        identifier,domain=self.adult()

        self.assertTrue(
            self.c.allowed_application(
                identifier,domain,"Crafty Infinity"
            )
        )

    def test_achievement(self):
        identifier,_=self.child()
        self.c.achievement(identifier,"BrainLab")

    def test_duplicate_achievement(self):
        identifier,_=self.child()
        self.c.achievement(identifier,"BrainLab")

        with self.assertRaises(sqlite3.IntegrityError):
            self.c.achievement(identifier,"BrainLab")

    def test_unknown_academy(self):
        identifier,_=self.child()

        with self.assertRaises(ValueError):
            self.c.achievement(identifier,"UNKNOWN")

    def test_real_identity_blocked(self):
        with self.assertRaises(ValueError):
            self.c.register("REAL-USER",25)

    def test_language_validation(self):
        with self.assertRaises(ValueError):
            self.c.register("SIM-USER",25,"unknown")

    def test_credit_conversion_blocked(self):
        with self.assertRaises(PermissionError):
            self.c.convert_credits()

    def test_automatic_migration_blocked(self):
        with self.assertRaises(PermissionError):
            self.c.transfer_to_adult()

    def test_database_separation(self):
        self.assertTrue(
            (Path(self.tmp.name)/"education.db").exists()
        )
        self.assertTrue(
            (Path(self.tmp.name)/"adult.db").exists()
        )

    def test_persistence(self):
        identifier,domain=self.child()
        self.c.close()
        self.c=Core(self.tmp.name)

        self.assertEqual(
            self.c.profile(identifier,domain)["age"],10
        )

    def test_financial_locks(self):
        verify_locks()

    def test_no_real_users(self):
        self.child()
        self.assertEqual(
            self.c.report()["realUsers"],0
        )

    def test_no_real_payments(self):
        self.adult()
        self.assertEqual(
            self.c.report()["realPayments"],0
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
