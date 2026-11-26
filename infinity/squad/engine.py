import json
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

CHALLENGES=json.loads(
    (ROOT/"squad/challenges.json").read_text()
)

INDEX={c["id"]:c for c in CHALLENGES}

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

def available(age):
    locks()

    if type(age)!=int or not 4<=age<=17:
        raise ValueError("Invalid age")

    return [
        c for c in CHALLENGES
        if c["minimumAge"]<=age<=c["maximumAge"]
    ]

class Squad:

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

        CREATE TABLE IF NOT EXISTS achievements(
            learner TEXT NOT NULL
                REFERENCES learners(id)
                ON DELETE CASCADE,
            challenge TEXT NOT NULL,
            difficulty INTEGER NOT NULL
                CHECK(difficulty BETWEEN 1 AND 3),
            PRIMARY KEY(learner,challenge,difficulty)
        );
        """)

    def close(self):
        self.db.close()

    def register(self,learner,age):
        available(age)

        if not isinstance(learner,str) or \
           not learner.startswith("SIM-") or \
           not 5<=len(learner)<=64:
            raise ValueError("Synthetic learner required")

        with self.db:
            self.db.execute(
                "INSERT INTO learners VALUES(?,?)",
                (learner,age)
            )

    def age(self,learner):
        row=self.db.execute(
            "SELECT age FROM learners WHERE id=?",
            (learner,)
        ).fetchone()

        if row is None:
            raise PermissionError("Unknown learner")

        return row[0]

    def complete(self,learner,challenge,difficulty=1):
        locks()

        age=self.age(learner)

        if challenge not in INDEX:
            raise ValueError("Unknown challenge")

        if challenge not in {
            c["id"] for c in available(age)
        }:
            raise PermissionError("Age mismatch")

        if type(difficulty)!=int or \
           difficulty not in (1,2,3):
            raise ValueError("Invalid difficulty")

        if difficulty>1:
            previous=self.db.execute(
                """
                SELECT 1 FROM achievements
                WHERE learner=? AND challenge=?
                AND difficulty=?
                """,
                (learner,challenge,difficulty-1)
            ).fetchone()

            if previous is None:
                raise PermissionError(
                    "Previous level not recorded"
                )

        with self.db:
            self.db.execute(
                "INSERT INTO achievements VALUES(?,?,?)",
                (learner,challenge,difficulty)
            )

    def progress(self,learner):
        age=self.age(learner)

        rows=self.db.execute(
            """
            SELECT challenge,MAX(difficulty)
            FROM achievements WHERE learner=?
            GROUP BY challenge
            """,(learner,)
        ).fetchall()

        return {
            "leader":"Crafty",
            "completedChallenges":len(rows),
            "availableChallenges":len(available(age)),
            "achievements":[
                {
                    "hero":INDEX[c]["hero"],
                    "challenge":c,
                    "difficulty":d
                }
                for c,d in rows
            ],
            "cashRewards":0,
            "cryptoRewards":0
        }

    def delete(self,learner):
        with self.db:
            self.db.execute(
                "DELETE FROM learners WHERE id=?",
                (learner,)
            )

    def financial_reward(self,*args):
        raise PermissionError(
            "Financial rewards prohibited"
        )
