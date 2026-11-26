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
RESERVE=CONFIG["allocations"]["mining"]*UNIT
HALVING=CONFIG["halvingYears"]

CATEGORIES={
    "COMPUTE":100,
    "CREATION":100,
    "KNOWLEDGE":100,
    "DEVELOPMENT":150,
    "SECURITY":150,
    "COMMERCE":100,
    "INNOVATION":150
}

def annual_budget(year):
    if type(year)!=int or not 1<=year<=100:
        raise ValueError("Invalid simulation year")

    epoch=(year-1)//HALVING
    return RESERVE//(HALVING*2**(epoch+1))

def difficulty(year,participants):
    annual_budget(year)

    if type(participants)!=int or participants<1:
        raise ValueError("Invalid participant count")

    epoch=(year-1)//HALVING

    time_factor=100+5*(year-1)
    demand_factor=max(100,participants//10)

    return (
        time_factor*demand_factor*2**epoch
    )//100

class Mining:
    def __init__(self,path):
        verify_locks()

        self.db=sqlite3.connect(path,timeout=10)

        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS rewards(
            evidence TEXT PRIMARY KEY,
            participant TEXT NOT NULL,
            category TEXT NOT NULL,
            year INTEGER NOT NULL,
            score INTEGER NOT NULL,
            reward INTEGER NOT NULL CHECK(reward>0)
        );

        CREATE TRIGGER IF NOT EXISTS rewards_no_update
        BEFORE UPDATE ON rewards
        BEGIN
            SELECT RAISE(ABORT,'Immutable rewards');
        END;

        CREATE TRIGGER IF NOT EXISTS rewards_no_delete
        BEFORE DELETE ON rewards
        BEGIN
            SELECT RAISE(ABORT,'Immutable rewards');
        END;
        """)

    def reward(self,participant,age,category,
               evidence,score,year,participants,
               verified=False):

        verify_locks()

        if type(age)!=int or age<18:
            raise ValueError("Adults only")

        if not isinstance(participant,str) or \
           not participant.startswith("SIM-"):
            raise ValueError("Simulation identity required")

        if not isinstance(evidence,str) or \
           not evidence.startswith("SIM-"):
            raise ValueError("Simulation evidence required")

        if category not in CATEGORIES:
            raise ValueError("Unknown contribution category")

        if verified is not True:
            raise ValueError("Unverified contribution")

        if type(score)!=int or not 0<=score<=100:
            raise ValueError("Invalid contribution score")

        threshold=min(95,60+(year-1)//2)

        if score<threshold:
            raise ValueError("Contribution below threshold")

        budget=annual_budget(year)
        d=difficulty(year,participants)

        amount=(
            UNIT*score*CATEGORIES[category]
        )//(100*d)

        if amount<=0:
            raise ValueError("Reward below minimum unit")

        self.db.execute("BEGIN IMMEDIATE")

        try:
            total=self.db.execute(
                "SELECT COALESCE(SUM(reward),0) FROM rewards"
            ).fetchone()[0]

            used=self.db.execute(
                "SELECT COALESCE(SUM(reward),0) "
                "FROM rewards WHERE year=?",(year,)
            ).fetchone()[0]

            amount=min(
                amount,
                budget-used,
                RESERVE-total
            )

            if amount<=0:
                raise ValueError("Reward budget exhausted")

            self.db.execute(
                "INSERT INTO rewards VALUES(?,?,?,?,?,?)",
                (evidence,participant,category,
                 year,score,amount)
            )

            self.db.commit()
            return amount

        except Exception:
            self.db.rollback()
            raise

    def report(self):
        count,total=self.db.execute(
            "SELECT COUNT(*),COALESCE(SUM(reward),0) "
            "FROM rewards"
        ).fetchone()

        assert 0<=total<=RESERVE

        return {
            "mode":"SIMULATION_ONLY",
            "contributions":count,
            "distributedRaw":total,
            "remainingReserveRaw":RESERVE-total,
            "actualTokensTransferred":0
        }

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.m=Mining(
            Path(self.tmp.name)/"mining.db"
        )

    def tearDown(self):
        self.m.db.close()
        self.tmp.cleanup()

    def claim(self,**changes):
        args={
            "participant":"SIM-USER",
            "age":30,
            "category":"COMPUTE",
            "evidence":"SIM-EVIDENCE",
            "score":90,
            "year":1,
            "participants":100,
            "verified":True
        }
        args.update(changes)
        return self.m.reward(**args)

    def test_reward(self):
        self.assertGreater(self.claim(),0)

    def test_minor(self):
        with self.assertRaises(ValueError):
            self.claim(age=17)

    def test_unverified(self):
        with self.assertRaises(ValueError):
            self.claim(verified=False)

    def test_duplicate(self):
        self.claim()
        with self.assertRaises(sqlite3.IntegrityError):
            self.claim()

    def test_low_quality(self):
        with self.assertRaises(ValueError):
            self.claim(score=10)

    def test_invalid_category(self):
        with self.assertRaises(ValueError):
            self.claim(category="UNKNOWN")

    def test_invalid_score(self):
        with self.assertRaises(ValueError):
            self.claim(score=101)

    def test_real_identity_blocked(self):
        with self.assertRaises(ValueError):
            self.claim(participant="REAL-USER")

    def test_real_evidence_blocked(self):
        with self.assertRaises(ValueError):
            self.claim(evidence="REAL-EVIDENCE")

    def test_halving(self):
        self.assertEqual(
            annual_budget(9),
            annual_budget(1)//2
        )

    def test_time_difficulty(self):
        self.assertGreater(
            difficulty(20,100),
            difficulty(1,100)
        )

    def test_demand_difficulty(self):
        self.assertGreater(
            difficulty(1,10000),
            difficulty(1,100)
        )

    def test_reward_decline(self):
        a=self.claim()
        b=self.claim(
            evidence="SIM-E2",year=20
        )
        self.assertLess(b,a)

    def test_reserve_conservation(self):
        amount=self.claim()
        r=self.m.report()
        self.assertEqual(
            r["remainingReserveRaw"]+amount,
            RESERVE
        )

    def test_100_year_cap(self):
        self.assertLessEqual(
            sum(annual_budget(y)
                for y in range(1,101)),
            RESERVE
        )

    def test_immutable(self):
        self.claim()
        with self.assertRaises(sqlite3.IntegrityError):
            self.m.db.execute(
                "DELETE FROM rewards"
            )

    def test_no_real_transfers(self):
        self.claim()
        self.assertEqual(
            self.m.report()["actualTokensTransferred"],0
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
