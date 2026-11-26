import importlib.util
import sqlite3
import json
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def load(name,path):
    spec=importlib.util.spec_from_file_location(
        name,ROOT/path
    )
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

education=load(
    "crafty_education","education/engine.py"
)

squad=load(
    "crafty_squad","squad/engine.py"
)

life=load(
    "crafty_life","virtual-life/engine.py"
)

PATHWAYS={
    "DISCOVER":6,
    "EXPLORER":10,
    "FUTURE":15
}

def verify_locks():
    life.locks()
    education.locks()
    squad.locks()

class Learning:

    def __init__(self,directory):
        verify_locks()

        self.directory=Path(directory)
        self.directory.mkdir(
            parents=True,exist_ok=True
        )
        self.directory.chmod(0o700)

        self.education=education.Education(
            self.directory/"education.db"
        )

        self.squad=squad.Squad(
            self.directory/"squad.db"
        )

        self.life=life.VirtualLife(
            self.directory/"life.db"
        )

        for p in self.directory.glob("*.db"):
            p.chmod(0o600)

        for pathway,age in PATHWAYS.items():

            learner=self.identity(pathway)

            for engine,table in (
                (self.education,"learners"),
                (self.squad,"learners"),
                (self.life,"players")
            ):
                row=engine.db.execute(
                    f"SELECT age FROM {table} WHERE id=?",
                    (learner,)
                ).fetchone()

                if row is None:
                    engine.register(learner,age)
                elif row[0]!=age:
                    raise ValueError("Pathway mismatch")

    def identity(self,pathway):

        if pathway not in PATHWAYS:
            raise ValueError("Unknown pathway")

        return "SIM-LOCAL-"+pathway

    def progress(self,pathway):

        verify_locks()
        learner=self.identity(pathway)

        academy_ids=[
            row[0]
            for row in self.education.db.execute(
                "SELECT mission FROM progress WHERE learner=?",
                (learner,)
            )
        ]

        heroes=self.squad.progress(learner)

        life_ids=[
            row[0]
            for row in self.life.db.execute(
                "SELECT mission FROM missions WHERE player=?",
                (learner,)
            )
        ]

        completed=academy_ids+life_ids+[
            item["challenge"]
            for item in heroes["achievements"]
        ]

        return {
            "pathway":pathway,
            "completed":completed,
            "count":len(completed),
            "available":46,
            "heroes":heroes["achievements"],
            "virtualLife":self.life.state(learner),
            "financialRewards":0,
            "cryptoRewards":0
        }

    def complete(self,pathway,mission,difficulty=1):

        verify_locks()
        learner=self.identity(pathway)

        if not isinstance(mission,str):
            raise ValueError("Invalid mission")

        if mission.startswith("ACA-"):

            if difficulty!=1:
                raise ValueError("Invalid difficulty")

            engine=self.education
            table="progress"
            field="mission"
            owner="learner"

        elif mission.startswith("LIFE-"):

            if difficulty!=1:
                raise ValueError("Invalid difficulty")

            engine=self.life
            table="missions"
            field="mission"
            owner="player"

        elif mission.startswith("SQUAD-"):

            if type(difficulty)!=int or difficulty not in (1,2,3):
                raise ValueError("Invalid difficulty")

            row=self.squad.db.execute(
                """SELECT 1 FROM achievements
                WHERE learner=? AND challenge=?
                AND difficulty=?""",
                (learner,mission,difficulty)
            ).fetchone()

            if row is None:
                self.squad.complete(
                    learner,mission,difficulty
                )

            return self.progress(pathway)

        else:
            raise ValueError("Unknown mission")

        row=engine.db.execute(
            f"SELECT 1 FROM {table} WHERE {owner}=? AND {field}=?",
            (learner,mission)
        ).fetchone()

        if row is None:
            engine.complete(learner,mission)

        return self.progress(pathway)

    def decide(self,pathway,action):

        verify_locks()

        return self.life.decide(
            self.identity(pathway),
            action,
            "SIM-"+uuid.uuid4().hex
        )

    def reset(self,pathway):

        verify_locks()

        learner=self.identity(pathway)
        age=PATHWAYS[pathway]

        for engine in (
            self.education,self.squad,self.life
        ):
            engine.delete(learner)
            engine.register(learner,age)

        return self.progress(pathway)

    def close(self):

        for engine in (
            self.education,self.squad,self.life
        ):
            engine.close()
