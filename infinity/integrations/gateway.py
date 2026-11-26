import json
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parent

CONFIG=json.loads(
    (ROOT/"services.json").read_text()
)

SERVICES={
    item["id"]:item
    for item in CONFIG["services"]
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
        "liveConnectionsEnabled",
        "automaticPurchases",
        "automaticPublishing",
        "realPayments",
        "childDataAccess",
        "tokenSettlement",
        "externalRequests"
    ):
        if CONFIG.get(key) is not False:
            raise PermissionError(key)

def synthetic(value):

    if not isinstance(value,str):
        raise ValueError("Invalid identifier")

    if not value.startswith("SIM-"):
        raise ValueError("Synthetic identifier required")

    if not 5<=len(value)<=80:
        raise ValueError("Invalid identifier length")

    return value

class Gateway:

    def __init__(self,path=":memory:"):

        locks()

        self.db=sqlite3.connect(path)

        self.db.execute("PRAGMA foreign_keys=ON")

        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS accounts(
            id TEXT PRIMARY KEY,
            age INTEGER NOT NULL
            CHECK(age BETWEEN 18 AND 120)
        );

        CREATE TABLE IF NOT EXISTS requests(
            reference TEXT PRIMARY KEY,
            account TEXT NOT NULL
            REFERENCES accounts(id),
            service TEXT NOT NULL,
            amount INTEGER NOT NULL
            CHECK(amount>=0),
            status TEXT NOT NULL
            CHECK(status IN (
                'DRAFT',
                'REVIEWED',
                'CANCELLED'
            ))
        );
        """)

    def register(self,account,age):

        locks()
        synthetic(account)

        if type(age) is not int or not 18<=age<=120:
            raise PermissionError("Adults only")

        with self.db:
            self.db.execute(
                "INSERT INTO accounts VALUES(?,?)",
                (account,age)
            )

    def draft(self,reference,account,service,amount):

        locks()

        synthetic(reference)
        synthetic(account)

        if service not in SERVICES:
            raise ValueError("Unknown service")

        if SERVICES[service]["domain"]!="ADULT":
            raise PermissionError("Invalid domain")

        if type(amount) is not int:
            raise ValueError("Integer cents required")

        if not 0<=amount<=100000000:
            raise ValueError("Invalid amount")

        with self.db:
            self.db.execute(
                "INSERT INTO requests VALUES(?,?,?,?,?)",
                (
                    reference,
                    account,
                    service,
                    amount,
                    "DRAFT"
                )
            )

    def review(self,reference,account):

        locks()

        with self.db:

            result=self.db.execute(
                """UPDATE requests
                SET status='REVIEWED'
                WHERE reference=?
                AND account=?
                AND status='DRAFT'""",
                (reference,account)
            )

            if result.rowcount!=1:
                raise PermissionError("Review denied")

    def cancel(self,reference,account):

        locks()

        with self.db:

            result=self.db.execute(
                """UPDATE requests
                SET status='CANCELLED'
                WHERE reference=?
                AND account=?
                AND status IN ('DRAFT','REVIEWED')""",
                (reference,account)
            )

            if result.rowcount!=1:
                raise PermissionError("Cancellation denied")

    def summary(self,account):

        rows=self.db.execute(
            """SELECT service,status,
            COUNT(*),SUM(amount)
            FROM requests
            WHERE account=?
            GROUP BY service,status""",
            (account,)
        ).fetchall()

        return {
            "mode":"SIMULATION_ONLY",
            "requests":rows,
            "actualRevenueZAR":0,
            "actualExpenditureZAR":0,
            "actualTokensTransferred":0
        }

    def purchase(self,*args):
        raise PermissionError("Purchases disabled")

    def settle(self,*args):
        raise PermissionError("Settlement disabled")

    def publish(self,*args):
        raise PermissionError("Publishing disabled")

    def child_data(self,*args):
        raise PermissionError("Child data isolated")

    def connect_live(self,*args):
        raise PermissionError("Live integration disabled")

    def close(self):
        self.db.close()
