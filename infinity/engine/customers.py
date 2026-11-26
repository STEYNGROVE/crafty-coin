import sqlite3
import json
import uuid
import unittest
import tempfile
from pathlib import Path
from datetime import datetime,timezone
from treasury import verify_locks

ROOT=Path(__file__).resolve().parents[1]

class Customers:
    def __init__(self,path):
        verify_locks()

        self.db=sqlite3.connect(path,timeout=10)
        self.db.execute("PRAGMA foreign_keys=ON")

        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS customers(
            id TEXT PRIMARY KEY,
            alias TEXT UNIQUE NOT NULL,
            age INTEGER NOT NULL CHECK(age>=18),
            referral TEXT UNIQUE NOT NULL,
            referred_by TEXT REFERENCES customers(id),
            consent INTEGER NOT NULL CHECK(consent IN (0,1)),
            created TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS interests(
            customer TEXT PRIMARY KEY
            REFERENCES customers(id) ON DELETE CASCADE,
            quantity INTEGER NOT NULL
            CHECK(quantity BETWEEN 10 AND 200000)
        );
        """)

    def register(self,alias,age,consent,referral=None):
        verify_locks()

        if not isinstance(alias,str) or \
           not alias.startswith("SIM-") or \
           not 5<=len(alias)<=64:
            raise ValueError("Synthetic identity required")

        if type(age)!=int or not 18<=age<=120:
            raise ValueError("Adult simulation only")

        if consent is not True:
            raise ValueError("Consent required")

        referrer=None

        with self.db:
            if referral is not None:
                row=self.db.execute(
                    "SELECT id FROM customers WHERE referral=?",
                    (referral,)
                ).fetchone()

                if row is None:
                    raise ValueError("Unknown referral")

                referrer=row[0]

            cid="SIM-"+uuid.uuid4().hex
            code="REF-"+uuid.uuid4().hex

            self.db.execute(
                "INSERT INTO customers VALUES(?,?,?,?,?,?,?)",
                (
                    cid,alias,age,code,referrer,1,
                    datetime.now(timezone.utc).isoformat()
                )
            )

        return cid,code

    def interest(self,cid,quantity):
        verify_locks()

        if type(quantity)!=int or \
           not 10<=quantity<=200000:
            raise ValueError("Invalid interest quantity")

        with self.db:
            row=self.db.execute(
                "SELECT consent FROM customers WHERE id=?",
                (cid,)
            ).fetchone()

            if row!=(1,):
                raise ValueError("Active consent required")

            self.db.execute("""
                INSERT INTO interests VALUES(?,?)
                ON CONFLICT(customer) DO UPDATE SET
                quantity=excluded.quantity
            """,(cid,quantity))

    def withdraw_consent(self,cid):
        with self.db:
            self.db.execute(
                "UPDATE customers SET consent=0 WHERE id=?",
                (cid,)
            )

            self.db.execute(
                "DELETE FROM interests WHERE customer=?",
                (cid,)
            )

    def delete(self,cid):
        with self.db:
            self.db.execute(
                "UPDATE customers SET referred_by=NULL "
                "WHERE referred_by=?",(cid,)
            )

            self.db.execute(
                "DELETE FROM customers WHERE id=?",(cid,)
            )

    def report(self):
        count=self.db.execute(
            "SELECT COUNT(*) FROM customers WHERE consent=1"
        ).fetchone()[0]

        referrals=self.db.execute(
            "SELECT COUNT(*) FROM customers "
            "WHERE referred_by IS NOT NULL AND consent=1"
        ).fetchone()[0]

        interested,quantity=self.db.execute(
            "SELECT COUNT(*),COALESCE(SUM(quantity),0) "
            "FROM interests"
        ).fetchone()

        return {
            "mode":"SIMULATION_ONLY",
            "syntheticCustomers":count,
            "syntheticReferrals":referrals,
            "interestedCustomers":interested,
            "nonbindingInterestTokens":quantity,
            "hypotheticalInterestZAR":quantity*10,
            "reservedTokens":0,
            "realCustomers":0,
            "realFundsCollectedZAR":0,
            "referralRewardsPaid":0
        }

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.c=Customers(
            Path(self.tmp.name)/"customers.db"
        )

    def tearDown(self):
        self.c.db.close()
        self.tmp.cleanup()

    def register(self,alias="SIM-USER",**changes):
        args={
            "alias":alias,
            "age":30,
            "consent":True
        }
        args.update(changes)
        return self.c.register(**args)

    def test_registration(self):
        self.register()
        self.assertEqual(
            self.c.report()["syntheticCustomers"],1
        )

    def test_minor(self):
        with self.assertRaises(ValueError):
            self.register(age=17)

    def test_consent(self):
        with self.assertRaises(ValueError):
            self.register(consent=False)

    def test_real_identity(self):
        with self.assertRaises(ValueError):
            self.register(alias="REAL-USER")

    def test_duplicate(self):
        self.register()
        with self.assertRaises(sqlite3.IntegrityError):
            self.register()

    def test_referral(self):
        _,code=self.register()
        self.register("SIM-SECOND",referral=code)

        self.assertEqual(
            self.c.report()["syntheticReferrals"],1
        )

    def test_invalid_referral(self):
        with self.assertRaises(ValueError):
            self.register(referral="INVALID")

    def test_interest(self):
        cid,_=self.register()
        self.c.interest(cid,100)

        self.assertEqual(
            self.c.report()["nonbindingInterestTokens"],100
        )

    def test_interest_update(self):
        cid,_=self.register()
        self.c.interest(cid,100)
        self.c.interest(cid,200)

        self.assertEqual(
            self.c.report()["nonbindingInterestTokens"],200
        )

    def test_invalid_interest(self):
        cid,_=self.register()

        with self.assertRaises(ValueError):
            self.c.interest(cid,-100)

    def test_unknown_customer(self):
        with self.assertRaises(ValueError):
            self.c.interest("UNKNOWN",100)

    def test_withdrawal(self):
        cid,_=self.register()
        self.c.interest(cid,100)
        self.c.withdraw_consent(cid)

        self.assertEqual(
            self.c.report()["nonbindingInterestTokens"],0
        )

        with self.assertRaises(ValueError):
            self.c.interest(cid,100)

    def test_deletion(self):
        cid,_=self.register()
        self.c.interest(cid,100)
        self.c.delete(cid)

        self.assertEqual(
            self.c.report()["syntheticCustomers"],0
        )

    def test_referrer_deletion(self):
        cid,code=self.register()
        self.register("SIM-SECOND",referral=code)
        self.c.delete(cid)

        self.assertEqual(
            self.c.report()["syntheticReferrals"],0
        )

    def test_no_reservation(self):
        cid,_=self.register()
        self.c.interest(cid,100)

        self.assertEqual(
            self.c.report()["reservedTokens"],0
        )

    def test_no_real_funds(self):
        self.assertEqual(
            self.c.report()["realFundsCollectedZAR"],0
        )

    def test_no_referral_rewards(self):
        self.assertEqual(
            self.c.report()["referralRewardsPaid"],0
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
