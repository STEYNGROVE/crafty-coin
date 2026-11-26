import json
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parent

CONFIG=json.loads(
    (ROOT/"catalogue.json").read_text()
)

PRODUCTS={
    p["id"]:p
    for p in CONFIG["products"]
}

def locks():

    security=json.loads(
        (ROOT.parent/"config/security.json").read_text()
    )

    required=[
        "mainnetEnabled",
        "realPaymentsEnabled",
        "presaleEnabled",
        "withdrawalsEnabled",
        "liveBurnsEnabled",
        "liveBuybacksEnabled",
        "paidAdvertisingEnabled",
        "paidInfrastructureEnabled"
    ]

    for key in required:
        if security.get(key) is not False:
            raise PermissionError(key)

    for key in (
        "realPaymentsEnabled",
        "automaticRenewalsEnabled",
        "tokenPaymentsEnabled",
        "childPurchasesEnabled",
        "externalSettlementEnabled"
    ):
        if CONFIG.get(key) is not False:
            raise PermissionError(key)

def synthetic(value):

    if not isinstance(value,str):
        raise ValueError("Invalid identifier")

    if not value.startswith("SIM-"):
        raise ValueError("Synthetic identifiers only")

    if not 5<=len(value)<=80:
        raise ValueError("Invalid identifier length")

    return value

class Marketplace:

    def __init__(self,path=":memory:"):

        locks()

        self.db=sqlite3.connect(path)

        self.db.execute("PRAGMA foreign_keys=ON")

        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS customers(
            id TEXT PRIMARY KEY,
            age INTEGER NOT NULL
            CHECK(age BETWEEN 18 AND 120)
        );

        CREATE TABLE IF NOT EXISTS orders(
            reference TEXT PRIMARY KEY,
            customer TEXT NOT NULL
            REFERENCES customers(id),
            product TEXT NOT NULL,
            amount INTEGER NOT NULL
            CHECK(amount>=0),
            status TEXT NOT NULL
            CHECK(status IN (
                'DRAFT',
                'SIMULATED',
                'CANCELLED'
            ))
        );

        CREATE TABLE IF NOT EXISTS entitlements(
            reference TEXT PRIMARY KEY
            REFERENCES orders(reference),
            customer TEXT NOT NULL
            REFERENCES customers(id),
            product TEXT NOT NULL,
            active INTEGER NOT NULL
            CHECK(active IN (0,1))
        );
        """)

    def register(self,customer,age):

        locks()
        synthetic(customer)

        if type(age) is not int or not 18<=age<=120:
            raise PermissionError("Adults only")

        with self.db:
            self.db.execute(
                "INSERT INTO customers VALUES(?,?)",
                (customer,age)
            )

    def order(self,reference,customer,product):

        locks()
        synthetic(reference)
        synthetic(customer)

        if product not in PRODUCTS:
            raise ValueError("Unknown product")

        amount=PRODUCTS[product]["priceCents"]

        if type(amount) is not int or amount<0:
            raise ValueError("Invalid price")

        with self.db:
            self.db.execute(
                "INSERT INTO orders VALUES(?,?,?,?,?)",
                (
                    reference,
                    customer,
                    product,
                    amount,
                    "DRAFT"
                )
            )

    def simulate(self,reference,customer):

        locks()

        try:
            self.db.execute("BEGIN IMMEDIATE")

            row=self.db.execute(
                """SELECT product FROM orders
                WHERE reference=?
                AND customer=?
                AND status='DRAFT'""",
                (reference,customer)
            ).fetchone()

            if row is None:
                raise PermissionError("Simulation denied")

            self.db.execute(
                """UPDATE orders SET status='SIMULATED'
                WHERE reference=?""",
                (reference,)
            )

            self.db.execute(
                "INSERT INTO entitlements VALUES(?,?,?,1)",
                (reference,customer,row[0])
            )

            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

    def cancel(self,reference,customer):

        locks()

        with self.db:

            result=self.db.execute(
                """UPDATE orders SET status='CANCELLED'
                WHERE reference=? AND customer=?
                AND status IN ('DRAFT','SIMULATED')""",
                (reference,customer)
            )

            if result.rowcount!=1:
                raise PermissionError("Cancellation denied")

            self.db.execute(
                """UPDATE entitlements SET active=0
                WHERE reference=? AND customer=?""",
                (reference,customer)
            )

    def access(self,customer,product):

        return self.db.execute(
            """SELECT 1 FROM entitlements
            WHERE customer=? AND product=?
            AND active=1""",
            (customer,product)
        ).fetchone() is not None

    def summary(self,customer):

        rows=self.db.execute(
            """SELECT status,COUNT(*),SUM(amount)
            FROM orders WHERE customer=?
            GROUP BY status""",
            (customer,)
        ).fetchall()

        return {
            "mode":"SIMULATION_ONLY",
            "orders":rows,
            "actualRevenueZAR":0,
            "actualPayments":0,
            "actualTokenTransfers":0
        }

    def pay(self,*args):
        raise PermissionError("Payments disabled")

    def renew(self,*args):
        raise PermissionError("Automatic renewal disabled")

    def settle(self,*args):
        raise PermissionError("Settlement disabled")

    def token_payment(self,*args):
        raise PermissionError("Token payments disabled")

    def child_purchase(self,*args):
        raise PermissionError("Child purchases disabled")

    def close(self):
        self.db.close()
