import json
import sqlite3
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

VISION=json.loads(
    (ROOT/"core/vision.json").read_text()
)

def verify_locks():
    config=json.loads(
        (ROOT/"config/security.json").read_text()
    )

    required=[
        "mainnetEnabled",
        "realPaymentsEnabled",
        "presaleEnabled",
        "withdrawalsEnabled",
        "liveBurnsEnabled",
        "liveBuybacksEnabled",
        "paidAdvertisingEnabled",
        "paidInfrastructureEnabled"
    ]

    for key in required:
        if config.get(key) is not False:
            raise RuntimeError("Unsafe configuration")

def pathway(age):
    if type(age)!=int or not 4<=age<=120:
        raise ValueError("Invalid age")

    for p in VISION["pathways"]:
        if p["min"]<=age<=p["max"]:
            return p["name"]

    raise ValueError("Invalid pathway")

class Core:
    def __init__(self,directory):
        verify_locks()

        self.directory=Path(directory)
        self.directory.mkdir(
            parents=True,exist_ok=True,mode=0o700
        )

        self.databases={}

        for domain in ("EDUCATION","ADULT"):
            path=self.directory/(domain.lower()+".db")

            db=sqlite3.connect(path,timeout=10)

            path.chmod(0o600)

            db.execute("PRAGMA foreign_keys=ON")

            db.executescript("""
            CREATE TABLE IF NOT EXISTS profiles(
                id TEXT PRIMARY KEY,
                alias TEXT UNIQUE NOT NULL,
                age INTEGER NOT NULL,
                language TEXT NOT NULL,
                pathway TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS achievements(
                id TEXT PRIMARY KEY,
                profile TEXT NOT NULL
                REFERENCES profiles(id),
                activity TEXT NOT NULL,
                UNIQUE(profile,activity)
            );
            """)

            self.databases[domain]=db

    def close(self):
        for db in self.databases.values():
            db.close()

    def register(self,alias,age,language="en"):
        verify_locks()

        if not isinstance(alias,str) or \
           not alias.startswith("SIM-") or \
           not 5<=len(alias)<=64:
            raise ValueError("Synthetic aliases only")

        route=pathway(age)

        if language not in VISION["languages"]:
            raise ValueError("Unsupported language")

        domain="EDUCATION" if age<18 else "ADULT"

        identifier="SIM-"+uuid.uuid4().hex

        db=self.databases[domain]

        with db:
            db.execute(
                "INSERT INTO profiles VALUES(?,?,?,?,?)",
                (identifier,alias,age,language,route)
            )

        return identifier,domain

    def profile(self,identifier,domain):
        if domain not in self.databases:
            raise ValueError("Invalid domain")

        row=self.databases[domain].execute(
            """
            SELECT id,alias,age,language,pathway
            FROM profiles WHERE id=?
            """,(identifier,)
        ).fetchone()

        if row is None:
            raise PermissionError("Profile unavailable")

        return dict(zip(
            ["id","alias","age","language","pathway"],
            row
        ))

    def achievement(self,identifier,academy):
        verify_locks()

        self.profile(identifier,"EDUCATION")

        if academy not in VISION["academies"]:
            raise ValueError("Unknown academy")

        db=self.databases["EDUCATION"]

        with db:
            db.execute(
                "INSERT INTO achievements VALUES(?,?,?)",
                ("SIM-"+uuid.uuid4().hex,
                 identifier,academy)
            )

    def allowed_application(self,identifier,domain,app):
        self.profile(identifier,domain)

        for item in VISION["applications"]:
            if item["name"]==app:
                return item["domain"]==domain

        return False

    def convert_credits(self,*args):
        raise PermissionError(
            "Learning credits cannot convert to crypto"
        )

    def transfer_to_adult(self,*args):
        raise PermissionError(
            "Automatic profile migration prohibited"
        )

    def report(self):
        verify_locks()

        counts={}

        for domain,db in self.databases.items():
            counts[domain]=db.execute(
                "SELECT COUNT(*) FROM profiles"
            ).fetchone()[0]

        return {
            "mode":"SIMULATION_ONLY",
            "character":VISION["character"]["name"],
            "academies":len(VISION["academies"]),
            "superheroes":len(VISION["superheroes"]),
            "applications":len(VISION["applications"]),
            "languages":VISION["languages"],
            "syntheticProfiles":counts,
            "realUsers":0,
            "realPayments":0,
            "mainnetEnabled":False,
            "creditConversionEnabled":False,
            "liveAIConnected":False
        }
