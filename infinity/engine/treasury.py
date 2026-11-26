import sqlite3
import json
import unittest
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def verify_locks():
    s = json.loads(
        (ROOT/"config/security.json").read_text()
    )

    required = [
        "mainnetEnabled",
        "realPaymentsEnabled",
        "presaleEnabled",
        "withdrawalsEnabled",
        "liveBurnsEnabled",
        "liveBuybacksEnabled"
    ]

    if any(s.get(k) is not False for k in required):
        raise RuntimeError("Financial safety lock failure")

class Treasury:
    def __init__(self,path):
        verify_locks()

        self.db=sqlite3.connect(path,timeout=10)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")

        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS deposits(
            reference TEXT PRIMARY KEY,
            amount INTEGER NOT NULL CHECK(amount>0),
            method TEXT NOT NULL
            CHECK(method IN ('SIM_EFT','SIM_USDC'))
        );

        CREATE TABLE IF NOT EXISTS refunds(
            reference TEXT PRIMARY KEY,
            deposit TEXT UNIQUE NOT NULL
            REFERENCES deposits(reference),
            amount INTEGER NOT NULL CHECK(amount>0)
        );

        CREATE TABLE IF NOT EXISTS ledger(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference TEXT NOT NULL,
            account TEXT NOT NULL,
            debit INTEGER NOT NULL CHECK(debit>=0),
            credit INTEGER NOT NULL CHECK(credit>=0),
            CHECK(
                (debit>0 AND credit=0)
                OR (credit>0 AND debit=0)
            )
        );

        CREATE TRIGGER IF NOT EXISTS ledger_no_update
        BEFORE UPDATE ON ledger
        BEGIN
            SELECT RAISE(ABORT,'Immutable ledger');
        END;

        CREATE TRIGGER IF NOT EXISTS ledger_no_delete
        BEFORE DELETE ON ledger
        BEGIN
            SELECT RAISE(ABORT,'Immutable ledger');
        END;
        """)

    def entry(self,ref,account,debit,credit):
        self.db.execute(
            """INSERT INTO ledger
            (reference,account,debit,credit)
            VALUES(?,?,?,?)""",
            (ref,account,debit,credit)
        )

    def deposit(self,ref,amount,method):
        verify_locks()

        if not isinstance(ref,str) or not ref.startswith("SIM-"):
            raise ValueError("Simulation reference required")

        if type(amount)!=int or amount<=0:
            raise ValueError("Positive integer cents required")

        if method not in ("SIM_EFT","SIM_USDC"):
            raise ValueError("Real payments prohibited")

        self.db.execute("BEGIN IMMEDIATE")

        try:
            self.db.execute(
                "INSERT INTO deposits VALUES(?,?,?)",
                (ref,amount,method)
            )

            self.entry(ref,"SIM_ESCROW",amount,0)
            self.entry(ref,"REFUND_LIABILITY",0,amount)

            self.reconcile()
            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

    def refund(self,ref,deposit):
        verify_locks()

        if not isinstance(ref,str) or not ref.startswith("SIM-"):
            raise ValueError("Simulation reference required")

        self.db.execute("BEGIN IMMEDIATE")

        try:
            row=self.db.execute(
                "SELECT amount FROM deposits WHERE reference=?",
                (deposit,)
            ).fetchone()

            if row is None:
                raise ValueError("Unknown deposit")

            amount=row[0]

            self.db.execute(
                "INSERT INTO refunds VALUES(?,?,?)",
                (ref,deposit,amount)
            )

            self.entry(ref,"REFUND_LIABILITY",amount,0)
            self.entry(ref,"SIM_ESCROW",0,amount)

            self.reconcile()
            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

    def reconcile(self):
        debit,credit=self.db.execute(
            """SELECT COALESCE(SUM(debit),0),
            COALESCE(SUM(credit),0) FROM ledger"""
        ).fetchone()

        if debit!=credit:
            raise RuntimeError("Unbalanced ledger")

        escrow=self.db.execute(
            """SELECT COALESCE(SUM(debit-credit),0)
            FROM ledger WHERE account='SIM_ESCROW'"""
        ).fetchone()[0]

        liability=self.db.execute(
            """SELECT COALESCE(SUM(credit-debit),0)
            FROM ledger WHERE account='REFUND_LIABILITY'"""
        ).fetchone()[0]

        deposits=self.db.execute(
            "SELECT COALESCE(SUM(amount),0) FROM deposits"
        ).fetchone()[0]

        refunds=self.db.execute(
            "SELECT COALESCE(SUM(amount),0) FROM refunds"
        ).fetchone()[0]

        if not escrow==liability==deposits-refunds:
            raise RuntimeError("Escrow mismatch")

        if escrow<0:
            raise RuntimeError("Negative escrow")

        return {
            "mode":"SIMULATION_ONLY",
            "simulatedDepositsCents":deposits,
            "simulatedRefundsCents":refunds,
            "simulatedEscrowCents":escrow,
            "refundLiabilityCents":liability,
            "ledgerDebitCents":debit,
            "ledgerCreditCents":credit,
            "realFundsCollectedCents":0,
            "authorizedSpendingCents":0,
            "mainnetEnabled":False,
            "realPaymentsEnabled":False,
            "reconciliation":"PASS"
        }

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"test.db"
        self.t=Treasury(self.path)

    def tearDown(self):
        self.t.db.close()
        self.tmp.cleanup()

    def test_deposit(self):
        self.t.deposit("SIM-1",100000,"SIM_EFT")
        self.assertEqual(
            self.t.reconcile()["simulatedEscrowCents"],
            100000
        )

    def test_usdc_simulation(self):
        self.t.deposit("SIM-2",50000,"SIM_USDC")

    def test_duplicate_deposit(self):
        self.t.deposit("SIM-3",1000,"SIM_EFT")
        with self.assertRaises(sqlite3.IntegrityError):
            self.t.deposit("SIM-3",1000,"SIM_EFT")

    def test_refund(self):
        self.t.deposit("SIM-4",1000,"SIM_EFT")
        self.t.refund("SIM-R4","SIM-4")
        self.assertEqual(
            self.t.reconcile()["simulatedEscrowCents"],0
        )

    def test_duplicate_refund(self):
        self.t.deposit("SIM-5",1000,"SIM_EFT")
        self.t.refund("SIM-R5","SIM-5")
        with self.assertRaises(sqlite3.IntegrityError):
            self.t.refund("SIM-R6","SIM-5")

    def test_unknown_refund(self):
        with self.assertRaises(ValueError):
            self.t.refund("SIM-R7","UNKNOWN")

    def test_live_payment_blocked(self):
        with self.assertRaises(ValueError):
            self.t.deposit("SIM-8",1000,"EFT")

    def test_negative_amount(self):
        with self.assertRaises(ValueError):
            self.t.deposit("SIM-9",-1000,"SIM_EFT")

    def test_invalid_reference(self):
        with self.assertRaises(ValueError):
            self.t.deposit("REAL-1",1000,"SIM_EFT")

    def test_immutable_update(self):
        self.t.deposit("SIM-10",1000,"SIM_EFT")
        with self.assertRaises(sqlite3.IntegrityError):
            self.t.db.execute(
                "UPDATE ledger SET debit=0"
            )

    def test_immutable_delete(self):
        self.t.deposit("SIM-11",1000,"SIM_EFT")
        with self.assertRaises(sqlite3.IntegrityError):
            self.t.db.execute("DELETE FROM ledger")

    def test_persistence(self):
        self.t.deposit("SIM-12",25000,"SIM_EFT")
        self.t.db.close()
        self.t=Treasury(self.path)

        self.assertEqual(
            self.t.reconcile()["simulatedEscrowCents"],
            25000
        )

    def test_spending_locked(self):
        self.assertEqual(
            self.t.reconcile()["authorizedSpendingCents"],
            0
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
