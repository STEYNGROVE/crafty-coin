import sqlite3
import json
import unittest
import tempfile
from pathlib import Path
from treasury import verify_locks

ROOT=Path(__file__).resolve().parents[1]

CONFIG=json.loads(
    (ROOT/"config/economics.json").read_text()
)

UNIT=10**CONFIG["decimals"]

SERVICES={
    "PIXELPUNK": "Website development",
    "GPU_COMPUTE": "AI computing",
    "GHOSTMEDIA": "Media production",
    "MARKETPLACE": "Digital products",
    "ACADEMY": "Adult professional education",
    "MERCHANT": "Merchant services"
}

class Commerce:
    def __init__(self,path):
        verify_locks()

        self.db=sqlite3.connect(path,timeout=10)
        self.db.execute("PRAGMA foreign_keys=ON")

        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS sales(
            reference TEXT PRIMARY KEY,
            customer TEXT NOT NULL,
            service TEXT NOT NULL,
            revenue INTEGER NOT NULL CHECK(revenue>0),
            cost INTEGER NOT NULL CHECK(cost>=0),
            token_receipts INTEGER NOT NULL
            CHECK(token_receipts>=0),
            burn INTEGER NOT NULL CHECK(burn>=0)
        );

        CREATE TRIGGER IF NOT EXISTS sales_no_update
        BEFORE UPDATE ON sales
        BEGIN
            SELECT RAISE(ABORT,'Immutable sale');
        END;

        CREATE TRIGGER IF NOT EXISTS sales_no_delete
        BEFORE DELETE ON sales
        BEGIN
            SELECT RAISE(ABORT,'Immutable sale');
        END;
        """)

    def sale(self,reference,customer,age,service,
             revenue,cost,token_receipts=0):

        verify_locks()

        if not isinstance(reference,str) or \
           not reference.startswith("SIM-"):
            raise ValueError("Simulation reference required")

        if not isinstance(customer,str) or \
           not customer.startswith("SIM-"):
            raise ValueError("Synthetic customer required")

        if type(age)!=int or age<18:
            raise ValueError("Adults only")

        if service not in SERVICES:
            raise ValueError("Unknown service")

        if type(revenue)!=int or revenue<=0:
            raise ValueError("Invalid revenue")

        if type(cost)!=int or cost<0:
            raise ValueError("Invalid cost")

        if type(token_receipts)!=int or token_receipts<0:
            raise ValueError("Invalid token receipts")

        # Hypothetical commercial burn obligation.
        # No blockchain transaction is created.
        burn=token_receipts*2//100

        with self.db:
            self.db.execute(
                "INSERT INTO sales VALUES(?,?,?,?,?,?,?)",
                (
                    reference,customer,service,
                    revenue,cost,token_receipts,burn
                )
            )

        return burn

    def report(self,overhead=0):
        verify_locks()

        if type(overhead)!=int or overhead<0:
            raise ValueError("Invalid overhead")

        count,revenue,cost,receipts,burn=self.db.execute(
            """
            SELECT COUNT(*),
            COALESCE(SUM(revenue),0),
            COALESCE(SUM(cost),0),
            COALESCE(SUM(token_receipts),0),
            COALESCE(SUM(burn),0)
            FROM sales
            """
        ).fetchone()

        gross_profit=revenue-cost
        operating_profit=gross_profit-overhead

        # Illustrative ceiling only.
        # Actual net profit requires verified expenses,
        # taxes, liabilities and accounting approval.
        buyback_ceiling=max(0,operating_profit)*5//100

        services=[]

        for key,name in SERVICES.items():
            n,r,c=self.db.execute(
                """
                SELECT COUNT(*),
                COALESCE(SUM(revenue),0),
                COALESCE(SUM(cost),0)
                FROM sales WHERE service=?
                """,(key,)
            ).fetchone()

            services.append({
                "service":key,
                "description":name,
                "simulatedSales":n,
                "revenueCents":r,
                "directCostCents":c,
                "grossProfitCents":r-c
            })

        return {
            "mode":"SIMULATION_ONLY",
            "simulatedSales":count,
            "revenueCents":revenue,
            "directCostCents":cost,
            "grossProfitCents":gross_profit,
            "overheadCents":overhead,
            "preTaxOperatingProfitCents":operating_profit,
            "simulatedTokenReceiptsRaw":receipts,
            "proposedBurnRaw":burn,
            "illustrativeBuybackCeilingCents":buyback_ceiling,
            "authorizedBuybackCents":0,
            "actualRevenueCents":0,
            "actualTokensBurned":0,
            "actualPayments":0,
            "services":services
        }

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.c=Commerce(
            Path(self.tmp.name)/"commerce.db"
        )

    def tearDown(self):
        self.c.db.close()
        self.tmp.cleanup()

    def sale(self,**changes):
        args={
            "reference":"SIM-SALE-1",
            "customer":"SIM-CUSTOMER",
            "age":30,
            "service":"PIXELPUNK",
            "revenue":100000,
            "cost":40000,
            "token_receipts":100*UNIT
        }
        args.update(changes)
        return self.c.sale(**args)

    def test_sale(self):
        self.sale()
        self.assertEqual(
            self.c.report()["simulatedSales"],1
        )

    def test_profit(self):
        self.sale()
        self.assertEqual(
            self.c.report()["grossProfitCents"],60000
        )

    def test_burn(self):
        self.assertEqual(self.sale(),2*UNIT)

    def test_overhead(self):
        self.sale()
        self.assertEqual(
            self.c.report(10000)
            ["preTaxOperatingProfitCents"],50000
        )

    def test_buyback_ceiling(self):
        self.sale()
        self.assertEqual(
            self.c.report()
            ["illustrativeBuybackCeilingCents"],3000
        )

    def test_loss(self):
        self.sale(cost=200000)
        self.assertEqual(
            self.c.report()
            ["illustrativeBuybackCeilingCents"],0
        )

    def test_duplicate(self):
        self.sale()
        with self.assertRaises(sqlite3.IntegrityError):
            self.sale()

    def test_minor(self):
        with self.assertRaises(ValueError):
            self.sale(age=17)

    def test_real_reference(self):
        with self.assertRaises(ValueError):
            self.sale(reference="REAL-1")

    def test_real_customer(self):
        with self.assertRaises(ValueError):
            self.sale(customer="REAL-CUSTOMER")

    def test_invalid_service(self):
        with self.assertRaises(ValueError):
            self.sale(service="UNKNOWN")

    def test_negative_revenue(self):
        with self.assertRaises(ValueError):
            self.sale(revenue=-100)

    def test_negative_cost(self):
        with self.assertRaises(ValueError):
            self.sale(cost=-100)

    def test_negative_receipts(self):
        with self.assertRaises(ValueError):
            self.sale(token_receipts=-100)

    def test_immutable_update(self):
        self.sale()
        with self.assertRaises(sqlite3.IntegrityError):
            self.c.db.execute(
                "UPDATE sales SET revenue=1"
            )

    def test_immutable_delete(self):
        self.sale()
        with self.assertRaises(sqlite3.IntegrityError):
            self.c.db.execute("DELETE FROM sales")

    def test_actual_revenue_zero(self):
        self.sale()
        self.assertEqual(
            self.c.report()["actualRevenueCents"],0
        )

    def test_no_actual_burn(self):
        self.sale()
        self.assertEqual(
            self.c.report()["actualTokensBurned"],0
        )

    def test_no_authorized_buyback(self):
        self.sale()
        self.assertEqual(
            self.c.report()["authorizedBuybackCents"],0
        )

    def test_all_services(self):
        for n,service in enumerate(SERVICES):
            self.sale(
                reference=f"SIM-ALL-{n}",
                service=service
            )

        self.assertEqual(
            self.c.report()["simulatedSales"],6
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
