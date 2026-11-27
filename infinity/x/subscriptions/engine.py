import json
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

PRODUCTS={
    p["id"]:p
    for p in json.loads(
        (ROOT/"marketplace/catalogue.json").read_text()
    )["products"]
    if p["type"] in ("SUBSCRIPTION","LICENSE")
}

PERIODS={
    "TRIAL":7,
    "MONTHLY":30,
    "ANNUAL":365,
    "PERPETUAL":None
}

def locks():
    policy=json.loads(
        (ROOT/"config/security.json").read_text()
    )

    for flag in (
        "mainnetEnabled",
        "realPaymentsEnabled",
        "presaleEnabled",
        "withdrawalsEnabled",
        "liveBurnsEnabled",
        "liveBuybacksEnabled",
        "paidInfrastructureEnabled",
        "paidAdvertisingEnabled"
    ):
        if policy.get(flag) is not False:
            raise PermissionError(flag)

def synthetic(value):
    if not isinstance(value,str):
        raise ValueError("Invalid identifier")
    if not value.startswith("SIM-"):
        raise PermissionError("Synthetic identities only")
    if not 5<=len(value)<=64:
        raise ValueError("Invalid identifier length")
    return value

def day(value):
    if type(value) is not int or not 0<=value<=1000000:
        raise ValueError("Invalid simulation day")
    return value

class Subscriptions:

    def __init__(self,path=":memory:"):
        locks()
        self.db=sqlite3.connect(path)
        self.db.execute("PRAGMA foreign_keys=ON")

        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS customers(
            id TEXT PRIMARY KEY,
            age INTEGER NOT NULL CHECK(age BETWEEN 18 AND 120)
        );

        CREATE TABLE IF NOT EXISTS subscriptions(
            id TEXT PRIMARY KEY,
            customer TEXT NOT NULL REFERENCES customers(id),
            product TEXT NOT NULL,
            period TEXT NOT NULL,
            started INTEGER NOT NULL,
            expires INTEGER,
            status TEXT NOT NULL,
            price INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS events(
            reference TEXT PRIMARY KEY,
            subscription TEXT NOT NULL REFERENCES subscriptions(id),
            action TEXT NOT NULL,
            day INTEGER NOT NULL,
            amount INTEGER NOT NULL
        );
        """)

    def register(self,customer,age):
        locks()
        synthetic(customer)

        if type(age) is not int or not 18<=age<=120:
            raise PermissionError("Adult domain only")

        with self.db:
            self.db.execute(
                "INSERT INTO customers VALUES (?,?)",
                (customer,age)
            )

    def create(self,reference,customer,product,period,now):
        locks()
        synthetic(reference)
        synthetic(customer)
        day(now)

        if product not in PRODUCTS:
            raise ValueError("Unknown product")

        if period not in PERIODS:
            raise ValueError("Unknown period")

        kind=PRODUCTS[product]["type"]

        if kind=="SUBSCRIPTION" and period=="PERPETUAL":
            raise ValueError("Invalid subscription period")

        if kind=="LICENSE" and period=="MONTHLY":
            raise ValueError("Invalid licence period")

        duration=PERIODS[period]

        expiry=None if duration is None else now+duration

        price=PRODUCTS[product]["priceCents"]

        if period=="TRIAL":
            price=0
        elif period=="ANNUAL" and kind=="SUBSCRIPTION":
            price*=12

        with self.db:

            self.db.execute(
                "INSERT INTO subscriptions VALUES (?,?,?,?,?,?,?,?)",
                (
                    reference,customer,product,period,
                    now,expiry,"ACTIVE",price
                )
            )

            self.db.execute(
                "INSERT INTO events VALUES (?,?,?,?,?)",
                (reference,reference,"CREATE",now,price)
            )

        return self.status(reference,customer,now)

    def record(self,reference,customer):

        row=self.db.execute(
            "SELECT * FROM subscriptions WHERE id=? AND customer=?",
            (reference,customer)
        ).fetchone()

        if row is None:
            raise PermissionError("Subscription unavailable")

        return row

    def status(self,reference,customer,now):
        locks()
        day(now)
        row=self.record(reference,customer)

        state=row[6]

        if state!="CANCELLED":

            if now<row[4]:
                state="NOT_STARTED"

            elif row[5] is not None and now>=row[5]:
                state="EXPIRED"

        return {
            "reference":reference,
            "customer":customer,
            "product":row[2],
            "period":row[3],
            "expires":row[5],
            "status":state,
            "access":state in ("ACTIVE","ENDING"),
            "illustrativePriceCents":row[7],
            "actualRevenueCents":0,
            "simulationOnly":True
        }

    def simulate_renewal(self,event,reference,customer,now):
        locks()
        synthetic(event)
        day(now)

        self.db.execute("BEGIN IMMEDIATE")

        try:

            row=self.record(reference,customer)

            if row[3] not in ("MONTHLY","ANNUAL"):
                raise PermissionError("Not renewable")

            if row[6]!="ACTIVE" or now<row[4]:
                raise PermissionError("Renewal unavailable")

            last=self.db.execute(
                "SELECT MAX(day) FROM events WHERE subscription=?",
                (reference,)
            ).fetchone()[0]

            if now<last:
                raise ValueError("Simulation time reversed")

            expiry=max(now,row[5])+PERIODS[row[3]]

            self.db.execute(
                "INSERT INTO events VALUES (?,?,?,?,?)",
                (event,reference,"RENEW",now,row[7])
            )

            self.db.execute(
                "UPDATE subscriptions SET expires=? WHERE id=?",
                (expiry,reference)
            )

            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        return self.status(reference,customer,now)

    def cancel(self,event,reference,customer,now,immediate=False):
        locks()
        synthetic(event)
        day(now)

        if type(immediate) is not bool:
            raise ValueError("Invalid cancellation mode")

        self.db.execute("BEGIN IMMEDIATE")

        try:

            row=self.record(reference,customer)

            last=self.db.execute(
                "SELECT MAX(day) FROM events WHERE subscription=?",
                (reference,)
            ).fetchone()[0]

            if now<last:
                raise ValueError("Simulation time reversed")

            if row[6]!="ACTIVE":
                raise PermissionError("Already cancelled")

            state="CANCELLED" if (
                immediate or row[5] is None
            ) else "ENDING"

            self.db.execute(
                "INSERT INTO events VALUES (?,?,?,?,?)",
                (event,reference,"CANCEL",now,0)
            )

            self.db.execute(
                "UPDATE subscriptions SET status=? WHERE id=?",
                (state,reference)
            )

            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        return self.status(reference,customer,now)

    def summary(self):
        locks()

        count,total=self.db.execute(
            "SELECT COUNT(*),COALESCE(SUM(amount),0) FROM events"
        ).fetchone()

        return {
            "events":count,
            "illustrativeRevenueCents":total,
            "actualRevenueCents":0,
            "actualExpenditureCents":0
        }

    def charge(self,*args,**kwargs):
        raise PermissionError("Real payments disabled")

    def renew_live(self,*args,**kwargs):
        raise PermissionError("Live renewals disabled")

    def token_payment(self,*args,**kwargs):
        raise PermissionError("Token settlement disabled")

    def close(self):
        self.db.close()
