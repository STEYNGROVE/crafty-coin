import json
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

MISSIONS=json.loads(
    (ROOT/"education/curriculum.json").read_text()
)

INDEX={m["id"]:m for m in MISSIONS}

def locks():
    config=json.loads(
        (ROOT/"config/security.json").read_text()
    )

    if any(
        v is not False
        for v in config.values()
        if type(v)==bool
    ):
        raise PermissionError("Financial locks required")

def validate_age(age):
    if type(age)!=int or not 4<=age<=17:
        raise ValueError("Invalid learning age")

def available(age):
    locks()
    validate_age(age)

    return [
        m for m in MISSIONS
        if m["minimumAge"]<=age<=m["maximumAge"]
    ]

class Education:

    def __init__(self,path):
        locks()

        self.db=sqlite3.connect(path)

        self.db.execute("PRAGMA foreign_keys=ON")

        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS learners(
            id TEXT PRIMARY KEY,
            age INTEGER NOT NULL
                CHECK(age BETWEEN 4 AND 17)
        );

        CREATE TABLE IF NOT EXISTS progress(
            learner TEXT NOT NULL
                REFERENCES learners(id),
            mission TEXT NOT NULL,
            completed INTEGER NOT NULL
                CHECK(completed=1),
            PRIMARY KEY(learner,mission)
        );
        """)

    def close(self):
        self.db.close()

    def register(self,learner,age):
        locks()
        validate_age(age)

        if not isinstance(learner,str) or \
           not learner.startswith("SIM-") or \
           not 5<=len(learner)<=64:
            raise ValueError("Synthetic learner required")

        with self.db:
            self.db.execute(
                "INSERT INTO learners VALUES(?,?)",
                (learner,age)
            )

    def complete(self,learner,mission):
        locks()

        row=self.db.execute(
            "SELECT age FROM learners WHERE id=?",
            (learner,)
        ).fetchone()

        if row is None:
            raise PermissionError("Unknown learner")

        if mission not in INDEX:
            raise ValueError("Unknown mission")

        item=INDEX[mission]

        if not item["minimumAge"]<=row[0]<=item["maximumAge"]:
            raise PermissionError("Age pathway mismatch")

        with self.db:
            self.db.execute(
                "INSERT INTO progress VALUES(?,?,1)",
                (learner,mission)
            )

    def progress(self,learner):
        row=self.db.execute(
            "SELECT age FROM learners WHERE id=?",
            (learner,)
        ).fetchone()

        if row is None:
            raise PermissionError("Unknown learner")

        completed=self.db.execute(
            "SELECT COUNT(*) FROM progress WHERE learner=?",
            (learner,)
        ).fetchone()[0]

        return {
            "completed":completed,
            "available":len(available(row[0])),
            "financialRewards":0,
            "cryptoRewards":0
        }

    def delete(self,learner):
        with self.db:
            self.db.execute(
                "DELETE FROM progress WHERE learner=?",
                (learner,)
            )
            self.db.execute(
                "DELETE FROM learners WHERE id=?",
                (learner,)
            )

    def convert_achievement(self,*args):
        raise PermissionError(
            "Educational achievements have no cash value"
        )
