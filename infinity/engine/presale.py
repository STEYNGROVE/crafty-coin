import sqlite3
import unittest
import uuid

PRICE=1000
LIMIT=200000

class Presale:
    def __init__(self):
        self.db=sqlite3.connect(":memory:")
        self.db.executescript("""
        CREATE TABLE orders(
            reference TEXT PRIMARY KEY,
            buyer TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity>0),
            amount INTEGER NOT NULL,
            status TEXT NOT NULL
        );
        CREATE TABLE payments(
            evidence TEXT PRIMARY KEY,
            reference TEXT UNIQUE NOT NULL,
            amount INTEGER NOT NULL,
            method TEXT NOT NULL
        );
        """)

    def order(self,buyer,age,quantity):
        if type(age)!=int or age<18:
            raise ValueError("Adult simulation only")
        if not buyer or type(quantity)!=int or quantity<10:
            raise ValueError("Invalid order")

        with self.db:
            allocated=self.db.execute(
                "SELECT COALESCE(SUM(quantity),0) FROM orders"
            ).fetchone()[0]

            if allocated+quantity>LIMIT:
                raise ValueError("Allocation exhausted")

            ref="SIM-"+uuid.uuid4().hex
            self.db.execute(
                "INSERT INTO orders VALUES(?,?,?,?,?)",
                (ref,buyer,quantity,quantity*PRICE,"PENDING")
            )
        return ref

    def payment(self,ref,evidence,amount,method):
        if method not in ("SIM_EFT","SIM_USDC"):
            raise ValueError("Real payments prohibited")

        if not evidence or type(amount)!=int:
            raise ValueError("Invalid evidence")

        with self.db:
            order=self.db.execute(
                "SELECT amount,status FROM orders WHERE reference=?",
                (ref,)
            ).fetchone()

            if not order or order!=(amount,"PENDING"):
                raise ValueError("Payment mismatch")

            self.db.execute(
                "INSERT INTO payments VALUES(?,?,?,?)",
                (evidence,ref,amount,method)
            )

            self.db.execute(
                "UPDATE orders SET status='SIM_ALLOCATED' "
                "WHERE reference=?",(ref,)
            )

class Tests(unittest.TestCase):
    def setUp(self):
        self.p=Presale()

    def tearDown(self):
        self.p.db.close()

    def test_eft(self):
        r=self.p.order("TEST",30,100)
        self.p.payment(r,"E1",100000,"SIM_EFT")

    def test_usdc(self):
        r=self.p.order("TEST",30,10)
        self.p.payment(r,"U1",10000,"SIM_USDC")

    def test_minor(self):
        with self.assertRaises(ValueError):
            self.p.order("TEST",17,100)

    def test_overallocation(self):
        with self.assertRaises(ValueError):
            self.p.order("TEST",30,200001)

    def test_wrong_amount(self):
        r=self.p.order("TEST",30,10)
        with self.assertRaises(ValueError):
            self.p.payment(r,"E2",1,"SIM_EFT")

    def test_duplicate(self):
        r=self.p.order("TEST",30,10)
        self.p.payment(r,"E3",10000,"SIM_EFT")
        with self.assertRaises(ValueError):
            self.p.payment(r,"E3",10000,"SIM_EFT")

    def test_duplicate_evidence(self):
        a=self.p.order("A",30,10)
        b=self.p.order("B",30,10)
        self.p.payment(a,"E4",10000,"SIM_EFT")
        with self.assertRaises(sqlite3.IntegrityError):
            self.p.payment(b,"E4",10000,"SIM_EFT")

    def test_live_blocked(self):
        r=self.p.order("TEST",30,10)
        with self.assertRaises(ValueError):
            self.p.payment(r,"LIVE",10000,"EFT")

    def test_invalid_quantity(self):
        with self.assertRaises(ValueError):
            self.p.order("TEST",30,-100)

if __name__=="__main__":
    unittest.main(verbosity=2)
