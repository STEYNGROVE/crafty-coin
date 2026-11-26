import unittest
import sqlite3

from engine import Security,locks,digest

PASSWORD="Synthetic-Test-Password-2026"

class Tests(unittest.TestCase):

    def setUp(self):

        self.now=1000000

        self.s=Security(
            clock=lambda:self.now
        )

        self.s.register(
            "SIM-ADULT","CUSTOMER",PASSWORD
        )

    def tearDown(self):
        self.s.close()

    def login(self):
        return self.s.login(
            "SIM-ADULT",PASSWORD
        )

    def test_01_locks(self):
        locks()

    def test_02_login(self):
        self.assertTrue(self.login())

    def test_03_wrong_password(self):
        with self.assertRaises(PermissionError):
            self.s.login("SIM-ADULT","Wrong")

    def test_04_unknown_account(self):
        with self.assertRaises(PermissionError):
            self.s.login("SIM-MISSING",PASSWORD)

    def test_05_short_password(self):
        with self.assertRaises(ValueError):
            self.s.register(
                "SIM-NEW","CUSTOMER","short"
            )

    def test_06_real_alias(self):
        with self.assertRaises(ValueError):
            self.s.register(
                "REAL-USER","CUSTOMER",PASSWORD
            )

    def test_07_invalid_role(self):
        with self.assertRaises(ValueError):
            self.s.register(
                "SIM-NEW","ADMIN",PASSWORD
            )

    def test_08_duplicate_account(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.s.register(
                "SIM-ADULT","CUSTOMER",PASSWORD
            )

    def test_09_password_not_plaintext(self):
        row=self.s.db.execute(
            "SELECT password FROM users"
        ).fetchone()
        self.assertNotEqual(
            row[0],PASSWORD.encode()
        )

    def test_10_unique_salts(self):
        self.s.register(
            "SIM-OTHER","CUSTOMER",PASSWORD
        )
        rows=self.s.db.execute(
            "SELECT salt FROM users"
        ).fetchall()
        self.assertNotEqual(rows[0],rows[1])

    def test_11_token_not_plaintext(self):
        token=self.login()
        row=self.s.db.execute(
            "SELECT token_hash FROM sessions"
        ).fetchone()
        self.assertEqual(row[0],digest(token))
        self.assertNotEqual(row[0],token)

    def test_12_valid_session(self):
        identity=self.s.authorize(
            self.login(),"ADULT"
        )
        self.assertEqual(
            identity["id"],"SIM-ADULT"
        )

    def test_13_invalid_session(self):
        with self.assertRaises(PermissionError):
            self.s.authorize("INVALID","ADULT")

    def test_14_cross_domain(self):
        with self.assertRaises(PermissionError):
            self.s.authorize(
                self.login(),"EDUCATION"
            )

    def test_15_role_permission(self):
        self.s.authorize(
            self.login(),"ADULT",{"CUSTOMER"}
        )

    def test_16_wrong_role(self):
        with self.assertRaises(PermissionError):
            self.s.authorize(
                self.login(),"ADULT",{"OPERATOR"}
            )

    def test_17_expired_session(self):
        token=self.login()
        self.now+=1800
        with self.assertRaises(PermissionError):
            self.s.authorize(token,"ADULT")

    def test_18_revoked_session(self):
        token=self.login()
        self.s.revoke(token)
        with self.assertRaises(PermissionError):
            self.s.authorize(token,"ADULT")

    def test_19_duplicate_revocation(self):
        token=self.login()
        self.s.revoke(token)
        with self.assertRaises(PermissionError):
            self.s.revoke(token)

    def test_20_unique_sessions(self):
        self.assertNotEqual(
            self.login(),self.login()
        )

    def test_21_lockout(self):
        for _ in range(5):
            with self.assertRaises(PermissionError):
                self.s.login("SIM-ADULT","Wrong")
        with self.assertRaises(PermissionError):
            self.login()

    def test_22_lockout_expiry(self):
        for _ in range(5):
            with self.assertRaises(PermissionError):
                self.s.login("SIM-ADULT","Wrong")
        self.now+=301
        self.login()

    def test_23_failure_reset(self):
        with self.assertRaises(PermissionError):
            self.s.login("SIM-ADULT","Wrong")
        self.login()
        row=self.s.db.execute(
            "SELECT failures FROM users"
        ).fetchone()
        self.assertEqual(row[0],0)

    def test_24_education_account(self):
        self.s.register(
            "SIM-LEARNER","LEARNER",PASSWORD
        )
        token=self.s.login(
            "SIM-LEARNER",PASSWORD
        )
        self.s.authorize(token,"EDUCATION")

    def test_25_education_adult_denied(self):
        self.s.register(
            "SIM-LEARNER","LEARNER",PASSWORD
        )
        token=self.s.login(
            "SIM-LEARNER",PASSWORD
        )
        with self.assertRaises(PermissionError):
            self.s.authorize(token,"ADULT")

    def test_26_delete_account(self):
        token=self.login()
        self.s.delete(token,"ADULT")
        with self.assertRaises(PermissionError):
            self.s.authorize(token,"ADULT")

    def test_27_delete_sessions(self):
        token=self.login()
        self.login()
        self.s.delete(token,"ADULT")
        count=self.s.db.execute(
            "SELECT COUNT(*) FROM sessions"
        ).fetchone()[0]
        self.assertEqual(count,0)

    def test_28_event_integrity(self):
        self.login()
        self.assertTrue(self.s.verify_events())

    def test_29_event_tampering(self):
        self.login()
        self.s.db.execute(
            "UPDATE events SET event='ALTERED'"
        )
        self.assertFalse(self.s.verify_events())

    def test_30_event_gap(self):
        self.login()
        self.s.db.execute(
            "DELETE FROM events WHERE sequence=1"
        )
        self.assertFalse(self.s.verify_events())

    def test_31_no_financial_activation(self):
        with self.assertRaises(PermissionError):
            self.s.activate_finance()

    def test_32_no_external_sharing(self):
        with self.assertRaises(PermissionError):
            self.s.share_external()

    def test_33_unknown_event(self):
        with self.assertRaises(ValueError):
            self.s.event("INVALID")

    def test_34_no_credentials_in_events(self):
        token=self.login()
        rows=str(self.s.db.execute(
            "SELECT * FROM events"
        ).fetchall())
        self.assertNotIn(PASSWORD,rows)
        self.assertNotIn(token,rows)

    def test_35_wrong_domain_deletion(self):
        with self.assertRaises(PermissionError):
            self.s.delete(
                self.login(),"EDUCATION"
            )

    def test_36_session_survives_other_revocation(self):
        first=self.login()
        second=self.login()
        self.s.revoke(first)
        self.s.authorize(second,"ADULT")

if __name__=="__main__":
    unittest.main(verbosity=2)
