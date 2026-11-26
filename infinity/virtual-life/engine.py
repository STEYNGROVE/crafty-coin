import json
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parent

MISSIONS=json.loads(
    (ROOT/"worlds.json").read_text()
)

RESOURCES=[
    "learning","energy","resources",
    "community","environment"
]

START=[50,80,60,50,70]

ACTIONS={
    "GARDEN":[5,-5,-10,10,15],
    "LEARNING_CENTRE":[15,-10,-15,10,0],
    "RECYCLE":[5,-5,15,5,10],
    "REST":[0,20,0,0,0],
    "INVENT":[10,-10,-5,5,0],
    "COMMUNITY_HELP":[5,-5,0,15,0],
    "CONSERVE":[5,0,5,0,10]
}

def locks():
    cfg=json.loads(
        (ROOT.parent/"config/security.json").read_text()
    )

    required=[
        "mainnetEnabled",
        "realPaymentsEnabled",
        "presaleEnabled",
        "withdrawalsEnabled",
        "liveBurnsEnabled",
        "liveBuybacksEnabled",
        "paidInfrastructureEnabled",
        "paidAdvertisingEnabled"
    ]

    if any(cfg.get(k) is not False for k in required):
        raise PermissionError("Financial locks required")

def available(age):
    locks()

    if type(age)!=int or not 4<=age<=17:
        raise ValueError("Invalid age")

    return [
        m for m in MISSIONS
        if m["minimumAge"]<=age<=m["maximumAge"]
    ]

class VirtualLife:

    def __init__(self,path):
        locks()
        self.db=sqlite3.connect(path,timeout=10)
        self.db.execute("PRAGMA foreign_keys=ON")

        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS players(
            id TEXT PRIMARY KEY,
            age INTEGER NOT NULL
                CHECK(age BETWEEN 4 AND 17),
            state TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS decisions(
            reference TEXT PRIMARY KEY,
            player TEXT NOT NULL
                REFERENCES players(id)
                ON DELETE CASCADE,
            action TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS missions(
            player TEXT NOT NULL
                REFERENCES players(id)
                ON DELETE CASCADE,
            mission TEXT NOT NULL,
            PRIMARY KEY(player,mission)
        );
        """)

    def close(self):
        self.db.close()

    def register(self,player,age):
        available(age)

        if not isinstance(player,str) or \
           not player.startswith("SIM-") or \
           not 5<=len(player)<=64:
            raise ValueError("Synthetic player required")

        with self.db:
            self.db.execute(
                "INSERT INTO players VALUES(?,?,?)",
                (player,age,json.dumps(START))
            )

    def state(self,player):
        row=self.db.execute(
            "SELECT age,state FROM players WHERE id=?",
            (player,)
        ).fetchone()

        if row is None:
            raise PermissionError("Unknown player")

        return {
            "age":row[0],
            **dict(zip(RESOURCES,json.loads(row[1]))),
            "guide":"Crafty",
            "cashValue":0,
            "cryptoValue":0
        }

    def decide(self,player,action,reference):
        locks()

        if action not in ACTIONS:
            raise ValueError("Unknown action")

        if not isinstance(reference,str) or \
           not reference.startswith("SIM-"):
            raise ValueError("Synthetic reference required")

        try:
            self.db.execute("BEGIN IMMEDIATE")

            state=self.state(player)

            values=[
                state[k]+d
                for k,d in zip(RESOURCES,ACTIONS[action])
            ]

            if any(v<0 for v in values):
                raise ValueError("Insufficient resources")

            values=[min(100,v) for v in values]

            self.db.execute(
                "INSERT INTO decisions VALUES(?,?,?)",
                (reference,player,action)
            )

            self.db.execute(
                "UPDATE players SET state=? WHERE id=?",
                (json.dumps(values),player)
            )

            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        return self.state(player)

    def complete(self,player,mission):
        age=self.state(player)["age"]

        if mission not in {
            m["id"] for m in available(age)
        }:
            raise PermissionError("Mission unavailable")

        with self.db:
            self.db.execute(
                "INSERT INTO missions VALUES(?,?)",
                (player,mission)
            )

    def progress(self,player):
        age=self.state(player)["age"]

        count=self.db.execute(
            "SELECT COUNT(*) FROM missions WHERE player=?",
            (player,)
        ).fetchone()[0]

        return {
            "completed":count,
            "available":len(available(age)),
            "financialRewards":0
        }

    def delete(self,player):
        with self.db:
            self.db.execute(
                "DELETE FROM players WHERE id=?",
                (player,)
            )

    def withdraw(self,*args):
        raise PermissionError("No monetary value")
