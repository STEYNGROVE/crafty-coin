import json
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parent

POLICY=json.loads(
    (ROOT/"policy.json").read_text()
)

SECURITY=json.loads(
    (ROOT.parent/"config/security.json").read_text()
)

def verify_locks():

    required=[
        "mainnetEnabled",
        "realPaymentsEnabled",
        "presaleEnabled",
        "withdrawalsEnabled",
        "liveBurnsEnabled",
        "liveBuybacksEnabled"
    ]

    for key in required:
        if SECURITY.get(key) is not False:
            raise PermissionError(key)

    if POLICY.get("realAccountsEnabled") is not False:
        raise PermissionError("Live accounts disabled")

def alias(value):

    if not isinstance(value,str):
        raise ValueError("Invalid alias")

    if not value.startswith("SIM-"):
        raise ValueError("Synthetic aliases only")

    if not 5<=len(value)<=64:
        raise ValueError("Invalid alias length")

    return value

class Family:

    def __init__(self,path=":memory:"):

        verify_locks()

        self.db=sqlite3.connect(path)

        self.db.execute("PRAGMA foreign_keys=ON")

        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS adults(
            id TEXT PRIMARY KEY,
            role TEXT NOT NULL
            CHECK(role IN ('PARENT','TEACHER'))
        );

        CREATE TABLE IF NOT EXISTS learners(
            id TEXT PRIMARY KEY,
            age INTEGER NOT NULL
            CHECK(age BETWEEN 4 AND 17),
            parent TEXT NOT NULL
            REFERENCES adults(id)
        );

        CREATE TABLE IF NOT EXISTS consent(
            learner TEXT REFERENCES learners(id)
            ON DELETE CASCADE,
            teacher TEXT REFERENCES adults(id),
            PRIMARY KEY(learner,teacher)
        );

        CREATE TABLE IF NOT EXISTS progress(
            learner TEXT REFERENCES learners(id)
            ON DELETE CASCADE,
            activity TEXT NOT NULL,
            PRIMARY KEY(learner,activity)
        );
        """)

    def adult(self,identifier,role):

        alias(identifier)

        if role not in ("PARENT","TEACHER"):
            raise ValueError("Invalid role")

        with self.db:
            self.db.execute(
                "INSERT INTO adults VALUES(?,?)",
                (identifier,role)
            )

    def learner(self,identifier,age,parent):

        alias(identifier)

        if type(age) is not int or not 4<=age<=17:
            raise ValueError("Invalid age")

        row=self.db.execute(
            "SELECT role FROM adults WHERE id=?",
            (parent,)
        ).fetchone()

        if row!=("PARENT",):
            raise PermissionError("Parent required")

        with self.db:
            self.db.execute(
                "INSERT INTO learners VALUES(?,?,?)",
                (identifier,age,parent)
            )

    def owner(self,parent,learner):

        row=self.db.execute(
            "SELECT parent FROM learners WHERE id=?",
            (learner,)
        ).fetchone()

        if row!=(parent,):
            raise PermissionError("Access denied")

    def grant(self,parent,learner,teacher):

        self.owner(parent,learner)

        row=self.db.execute(
            "SELECT role FROM adults WHERE id=?",
            (teacher,)
        ).fetchone()

        if row!=("TEACHER",):
            raise PermissionError("Teacher required")

        with self.db:
            self.db.execute(
                "INSERT INTO consent VALUES(?,?)",
                (learner,teacher)
            )

    def revoke(self,parent,learner,teacher):

        self.owner(parent,learner)

        with self.db:
            self.db.execute(
                "DELETE FROM consent WHERE learner=? AND teacher=?",
                (learner,teacher)
            )

    def record(self,parent,learner,activity):

        self.owner(parent,learner)

        if not isinstance(activity,str):
            raise ValueError("Invalid activity")

        if not activity.startswith("SIM-"):
            raise ValueError("Synthetic activity required")

        if len(activity)>80:
            raise ValueError("Activity too long")

        with self.db:
            self.db.execute(
                "INSERT INTO progress VALUES(?,?)",
                (learner,activity)
            )

    def report(self,requester,learner):

        row=self.db.execute(
            "SELECT age,parent FROM learners WHERE id=?",
            (learner,)
        ).fetchone()

        if row is None:
            raise PermissionError("Access denied")

        age,parent=row

        permitted=requester==parent

        if not permitted:

            permitted=self.db.execute(
                "SELECT 1 FROM consent WHERE learner=? AND teacher=?",
                (learner,requester)
            ).fetchone() is not None

        if not permitted:
            raise PermissionError("Access denied")

        completed=self.db.execute(
            "SELECT COUNT(*) FROM progress WHERE learner=?",
            (learner,)
        ).fetchone()[0]

        pathway=(
            "DISCOVER" if age<=7 else
            "EXPLORER" if age<=12 else
            "FUTURE"
        )

        return {
            "guide":"Crafty",
            "pathway":pathway,
            "completedActivities":completed,
            "recommendation":
                "Choose an age-appropriate activity or take a break.",
            "financialRewards":0,
            "cryptoRewards":0,
            "diagnosis":None,
            "simulationOnly":True
        }

    def delete(self,parent,learner):

        self.owner(parent,learner)

        with self.db:
            self.db.execute(
                "DELETE FROM learners WHERE id=?",
                (learner,)
            )

    def financial_reward(self,*args):
        raise PermissionError("Financial rewards disabled")

    def export_external(self,*args):
        raise PermissionError("External sharing disabled")

    def close(self):
        self.db.close()
