import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from treasury import verify_locks

ROOT=Path(__file__).resolve().parents[1]

CHANNELS={
    "WEBSITE":"Official website and SEO",
    "X":"X organic content",
    "REDDIT":"Relevant adult communities",
    "DISCORD":"Adult community management",
    "TELEGRAM":"Adult community updates",
    "YOUTUBE":"Educational videos",
    "LINKEDIN":"Commercial partnerships",
    "FACEBOOK":"Adult business audiences",
    "INSTAGRAM":"Adult creator content",
    "NEWSLETTER":"Opt-in email newsletter",
    "GITHUB":"Open development transparency",
    "PARTNERS":"Verified commercial partners"
}

BLOCKED=[
    "guaranteed profit",
    "guaranteed returns",
    "risk free",
    "risk-free",
    "guaranteed income",
    "guaranteed price increase",
    "get rich quick",
    "100x guaranteed",
    "buy now before",
    "children can earn crypto"
]

def validate_content(text):
    if not isinstance(text,str) or not text.strip():
        raise ValueError("Content required")

    normalized=" ".join(text.lower().split())

    if any(term in normalized for term in BLOCKED):
        raise ValueError("Prohibited promotional claim")

    return True

def funnel(visitors,interest_bps,buyer_bps,average):
    values=(visitors,interest_bps,buyer_bps,average)

    if any(type(v)!=int or v<0 for v in values):
        raise ValueError("Invalid funnel input")

    if interest_bps>10000 or buyer_bps>10000:
        raise ValueError("Invalid conversion rate")

    interested=visitors*interest_bps//10000
    buyers=interested*buyer_bps//10000

    gross=buyers*average
    capped=min(gross,2000000)

    return {
        "visitors":visitors,
        "hypotheticalInterested":interested,
        "hypotheticalBuyers":buyers,
        "hypotheticalDemandZAR":gross,
        "cappedGrossFundingZAR":capped,
        "actualFundsCollectedZAR":0
    }

class Marketing:
    def __init__(self,path):
        verify_locks()

        self.db=sqlite3.connect(path,timeout=10)

        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS campaigns(
            reference TEXT PRIMARY KEY,
            channel TEXT NOT NULL,
            audience TEXT NOT NULL
            CHECK(audience='ADULT_ONLY'),
            content TEXT NOT NULL,
            status TEXT NOT NULL
            CHECK(status='DRAFT'),
            budget INTEGER NOT NULL CHECK(budget=0)
        );
        """)

    def draft(self,ref,channel,audience,content,budget=0):
        verify_locks()

        if not isinstance(ref,str) or \
           not ref.startswith("SIM-"):
            raise ValueError("Simulation reference required")

        if channel not in CHANNELS:
            raise ValueError("Unknown channel")

        if audience!="ADULT_ONLY":
            raise ValueError("Adults only")

        if type(budget)!=int or budget!=0:
            raise ValueError("Paid advertising prohibited")

        validate_content(content)

        with self.db:
            self.db.execute(
                "INSERT INTO campaigns VALUES(?,?,?,?,?,?)",
                (ref,channel,audience,content,"DRAFT",0)
            )

    def report(self):
        count=self.db.execute(
            "SELECT COUNT(*) FROM campaigns"
        ).fetchone()[0]

        return {
            "mode":"SIMULATION_ONLY",
            "draftCampaigns":count,
            "availableChannels":len(CHANNELS),
            "publishedCampaigns":0,
            "messagesSent":0,
            "advertisingSpendZAR":0,
            "actualFundsCollectedZAR":0
        }

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.m=Marketing(
            Path(self.tmp.name)/"marketing.db"
        )

    def tearDown(self):
        self.m.db.close()
        self.tmp.cleanup()

    def draft(self,**changes):
        args={
            "ref":"SIM-CAMPAIGN",
            "channel":"WEBSITE",
            "audience":"ADULT_ONLY",
            "content":"Explore our development research.",
            "budget":0
        }

        args.update(changes)
        self.m.draft(**args)

    def test_draft(self):
        self.draft()
        self.assertEqual(
            self.m.report()["draftCampaigns"],1
        )

    def test_duplicate(self):
        self.draft()
        with self.assertRaises(sqlite3.IntegrityError):
            self.draft()

    def test_unknown_channel(self):
        with self.assertRaises(ValueError):
            self.draft(channel="UNKNOWN")

    def test_minor_audience(self):
        with self.assertRaises(ValueError):
            self.draft(audience="CHILDREN")

    def test_paid_ads_blocked(self):
        with self.assertRaises(ValueError):
            self.draft(budget=100)

    def test_real_campaign_blocked(self):
        with self.assertRaises(ValueError):
            self.draft(ref="REAL-1")

    def test_guaranteed_profit(self):
        with self.assertRaises(ValueError):
            self.draft(content="Guaranteed profit")

    def test_guaranteed_returns(self):
        with self.assertRaises(ValueError):
            self.draft(content="Guaranteed returns")

    def test_risk_free(self):
        with self.assertRaises(ValueError):
            self.draft(content="Risk-free investment")

    def test_empty_content(self):
        with self.assertRaises(ValueError):
            self.draft(content="")

    def test_all_channels(self):
        for n,channel in enumerate(CHANNELS):
            self.draft(
                ref=f"SIM-{n}",
                channel=channel
            )

        self.assertEqual(
            self.m.report()["draftCampaigns"],12
        )

    def test_no_publication(self):
        self.draft()
        self.assertEqual(
            self.m.report()["publishedCampaigns"],0
        )

    def test_no_messages(self):
        self.assertEqual(
            self.m.report()["messagesSent"],0
        )

    def test_zero_spend(self):
        self.assertEqual(
            self.m.report()["advertisingSpendZAR"],0
        )

    def test_funnel(self):
        r=funnel(10000,1000,1000,1000)
        self.assertEqual(
            r["hypotheticalDemandZAR"],100000
        )

    def test_funding_cap(self):
        r=funnel(1000000,10000,10000,10000)
        self.assertEqual(
            r["cappedGrossFundingZAR"],2000000
        )

    def test_invalid_conversion(self):
        with self.assertRaises(ValueError):
            funnel(100,10001,1000,1000)

    def test_negative_visitors(self):
        with self.assertRaises(ValueError):
            funnel(-1,1000,1000,1000)

    def test_zero_demand(self):
        self.assertEqual(
            funnel(0,1000,1000,1000)
            ["hypotheticalDemandZAR"],0
        )

    def test_no_actual_funding(self):
        self.assertEqual(
            funnel(100000,1000,1000,1000)
            ["actualFundsCollectedZAR"],0
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
