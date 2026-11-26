import json
import unittest
from pathlib import Path
from treasury import verify_locks
from mining import annual_budget

ROOT=Path(__file__).resolve().parents[1]
C=json.loads(
    (ROOT/"config/economics.json").read_text()
)

U=10**C["decimals"]
MAX=C["maximumSupply"]*U

class Supply:
    def __init__(self):
        verify_locks()

        self.balances={
            k:v*U
            for k,v in C["allocations"].items()
        }

        self.balances["circulating"]=0
        self.destroyed=0
        self.year=0
        self.events=set()
        self.history=[]
        self.verify()

    def verify(self):
        assert all(
            v>=0 for v in self.balances.values()
        )
        assert self.destroyed>=0
        assert sum(self.balances.values())+\
            self.destroyed==MAX

    def event(self,ref):
        verify_locks()

        if not isinstance(ref,str) or \
           not ref.startswith("SIM-"):
            raise ValueError("Simulation reference required")

        if ref in self.events:
            raise ValueError("Duplicate event")

    def transfer(self,source,amount,ref):
        self.event(ref)

        if source not in (
            "presale","liquidity","ecosystem",
            "partnerships"
        ):
            raise ValueError("Restricted allocation")

        if type(amount)!=int or amount<=0:
            raise ValueError("Invalid amount")

        if amount>self.balances[source]:
            raise ValueError("Insufficient allocation")

        self.balances[source]-=amount
        self.balances["circulating"]+=amount
        self.events.add(ref)
        self.verify()

    def burn(self,source,amount,ref):
        self.event(ref)

        if source!="circulating":
            raise ValueError("Restricted burn source")

        if type(amount)!=int or amount<=0:
            raise ValueError("Invalid burn amount")

        if amount>self.balances[source]:
            raise ValueError("Insufficient balance")

        self.balances[source]-=amount
        self.destroyed+=amount
        self.events.add(ref)
        self.verify()

    def commercial_burn(self,receipts,ref):
        self.event(ref)

        if type(receipts)!=int or receipts<=0:
            raise ValueError("Invalid receipts")

        if receipts>self.balances["circulating"]:
            raise ValueError("Receipts exceed balance")

        amount=receipts*2//100

        if amount<=0:
            raise ValueError("Below minimum burn")

        self.burn("circulating",amount,ref)
        return amount

    def advance_year(self,release_mining=True):
        verify_locks()

        if self.year>=100:
            raise ValueError("Simulation horizon reached")

        if type(release_mining)!=bool:
            raise ValueError("Invalid release setting")

        self.year+=1

        reserve_burn=self.balances["burn"]*5//100
        self.balances["burn"]-=reserve_burn
        self.destroyed+=reserve_burn

        vest=min(
            self.balances["founder"],
            C["allocations"]["founder"]*U//
            C["founderVestingYears"]
        )

        reward=0

        if release_mining:
            reward=min(
                self.balances["mining"],
                annual_budget(self.year)
            )

        self.balances["founder"]-=vest
        self.balances["mining"]-=reward
        self.balances["circulating"]+=vest+reward

        self.verify()

        row=self.snapshot()
        row.update({
            "annualReserveBurnRaw":reserve_burn,
            "annualFounderReleaseRaw":vest,
            "annualMiningReleaseRaw":reward
        })

        self.history.append(row)
        return row

    def snapshot(self):
        return {
            "mode":"SIMULATION_ONLY",
            "year":self.year,
            "maximumSupplyRaw":MAX,
            "totalSupplyRaw":MAX-self.destroyed,
            "circulatingRaw":
                self.balances["circulating"],
            "destroyedRaw":self.destroyed,
            "balances":dict(self.balances),
            "actualTokensBurned":0,
            "actualTokensTransferred":0
        }

class Tests(unittest.TestCase):
    def setUp(self):
        self.s=Supply()

    def test_genesis(self):
        self.assertEqual(
            sum(self.s.balances.values()),MAX
        )

    def test_presale_release(self):
        self.s.transfer("presale",100*U,"SIM-1")
        self.assertEqual(
            self.s.balances["circulating"],100*U
        )

    def test_duplicate_event(self):
        self.s.transfer("presale",U,"SIM-2")
        with self.assertRaises(ValueError):
            self.s.transfer("presale",U,"SIM-2")

    def test_overallocation(self):
        with self.assertRaises(ValueError):
            self.s.transfer(
                "presale",200001*U,"SIM-3"
            )

    def test_founder_lock(self):
        with self.assertRaises(ValueError):
            self.s.transfer("founder",U,"SIM-4")

    def test_mining_lock(self):
        with self.assertRaises(ValueError):
            self.s.transfer("mining",U,"SIM-5")

    def test_burn_reserve_lock(self):
        with self.assertRaises(ValueError):
            self.s.transfer("burn",U,"SIM-6")

    def test_first_year_burn(self):
        self.s.advance_year()
        self.assertEqual(self.s.destroyed,7500*U)

    def test_founder_vesting(self):
        for _ in range(5):
            self.s.advance_year()
        self.assertEqual(
            self.s.balances["founder"],0
        )

    def test_commercial_burn(self):
        self.s.transfer("presale",100*U,"SIM-7")
        amount=self.s.commercial_burn(
            100*U,"SIM-8"
        )
        self.assertEqual(amount,2*U)

    def test_burn_reduces_supply(self):
        self.s.transfer("presale",100*U,"SIM-9")
        self.s.burn("circulating",U,"SIM-10")
        self.assertEqual(
            self.s.snapshot()["totalSupplyRaw"],
            MAX-U
        )

    def test_excess_burn(self):
        with self.assertRaises(ValueError):
            self.s.burn("circulating",U,"SIM-11")

    def test_negative_amount(self):
        with self.assertRaises(ValueError):
            self.s.transfer("presale",-U,"SIM-12")

    def test_real_event_blocked(self):
        with self.assertRaises(ValueError):
            self.s.transfer("presale",U,"REAL-1")

    def test_reserve_not_circulating(self):
        self.s.advance_year(False)
        self.assertEqual(
            self.s.balances["circulating"],
            10000*U
        )

    def test_no_mining_release(self):
        before=self.s.balances["mining"]
        self.s.advance_year(False)
        self.assertEqual(
            before,self.s.balances["mining"]
        )

    def test_100_year_conservation(self):
        for _ in range(100):
            self.s.advance_year()
            self.s.verify()

    def test_supply_monotonic(self):
        previous=MAX
        for _ in range(100):
            row=self.s.advance_year()
            self.assertLessEqual(
                row["totalSupplyRaw"],previous
            )
            previous=row["totalSupplyRaw"]

    def test_horizon(self):
        for _ in range(100):
            self.s.advance_year()
        with self.assertRaises(ValueError):
            self.s.advance_year()

    def test_no_real_burns(self):
        self.s.advance_year()
        self.assertEqual(
            self.s.snapshot()["actualTokensBurned"],0
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
