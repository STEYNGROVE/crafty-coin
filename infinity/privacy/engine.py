import json
import hashlib
import hmac
import secrets
import sqlite3
import time

from pathlib import Path

ROOT=Path(__file__).resolve().parent

POLICY=json.loads(
    (ROOT/"policy.json").read_text()
)

ROLES={
    "PARENT":"EDUCATION",
    "TEACHER":"EDUCATION",
    "LEARNER":"EDUCATION",
    "CUSTOMER":"ADULT",
    "MERCHANT":"ADULT",
    "OPERATOR":"ADULT"
}

def locks():

    security=json.loads(
        (ROOT.parent/"config/security.json").read_text()
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
        if security.get(key) is not False:
            raise PermissionError(key)

    for key in (
        "realAccountsEnabled",
        "childFinancialAccess",
        "crossDomainDataSharing",
        "externalDataSharing",
        "biometricCollection",
        "behaviouralAdvertising",
        "financialActivation"
    ):
        if POLICY.get(key) is not False:
            raise PermissionError(key)

def password_hash(password,salt):

    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        POLICY["passwordIterations"]
    )

def digest(value):

    return hashlib.sha256(
        value.encode()
    ).hexdigest()

class Security:

    def __init__(self,path=":memory:",clock=None):

        locks()

        self.clock=clock or time.time

        self.db=sqlite3.connect(path)

        self.db.execute("PRAGMA foreign_keys=ON")

        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id TEXT PRIMARY KEY,
            role TEXT NOT NULL,
            domain TEXT NOT NULL,
            salt BLOB NOT NULL,
            password BLOB NOT NULL,
            failures INTEGER NOT NULL DEFAULT 0,
            locked_until INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS sessions(
            token_hash TEXT PRIMARY KEY,
            user TEXT NOT NULL REFERENCES users(id)
            ON DELETE CASCADE,
            expires INTEGER NOT NULL,
            revoked INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS events(
            sequence INTEGER PRIMARY KEY,
            event TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            previous TEXT NOT NULL,
            checksum TEXT NOT NULL
        );
        """)

    def now(self):
        return int(self.clock())

    def event(self,name):

        if name not in {
            "REGISTER",
            "LOGIN_SUCCESS",
            "LOGIN_FAILURE",
            "LOGIN_LOCKED",
            "SESSION_REVOKED",
            "ACCOUNT_DELETED",
            "ACCESS_DENIED"
        }:
            raise ValueError("Unknown event")

        row=self.db.execute(
            """SELECT sequence,checksum
            FROM events
            ORDER BY sequence DESC LIMIT 1"""
        ).fetchone()

        sequence=row[0]+1 if row else 1
        previous=row[1] if row else "GENESIS"
        timestamp=self.now()

        checksum=digest(json.dumps(
            [sequence,name,timestamp,previous],
            separators=(",",":")
        ))

        self.db.execute(
            "INSERT INTO events VALUES(?,?,?,?,?)",
            (
                sequence,name,timestamp,
                previous,checksum
            )
        )

    def register(self,user,role,password):

        locks()

        if not isinstance(user,str):
            raise ValueError("Invalid alias")

        if not user.startswith("SIM-"):
            raise ValueError("Synthetic accounts only")

        if not 5<=len(user)<=64:
            raise ValueError("Invalid alias length")

        if role not in ROLES:
            raise ValueError("Invalid role")

        if not isinstance(password,str):
            raise ValueError("Invalid password")

        if not 12<=len(password)<=256:
            raise ValueError("Invalid password length")

        salt=secrets.token_bytes(32)
        hashed=password_hash(password,salt)

        with self.db:

            self.db.execute(
                """INSERT INTO users
                (id,role,domain,salt,password)
                VALUES(?,?,?,?,?)""",
                (
                    user,role,ROLES[role],
                    salt,hashed
                )
            )

            self.event("REGISTER")

    def login(self,user,password):

        locks()

        if not isinstance(password,str):
            raise PermissionError("Login denied")

        if len(password)>256:
            raise PermissionError("Login denied")

        row=self.db.execute(
            """SELECT salt,password,failures,
            locked_until FROM users WHERE id=?""",
            (user,)
        ).fetchone()

        if row is None:

            password_hash(password,b"\0"*32)

            with self.db:
                self.event("LOGIN_FAILURE")

            raise PermissionError("Login denied")

        salt,hashed,failures,locked=row

        if locked>self.now():

            with self.db:
                self.event("LOGIN_LOCKED")

            raise PermissionError("Login denied")

        if locked and locked<=self.now():
            failures=0

        candidate=password_hash(password,salt)

        if not hmac.compare_digest(candidate,hashed):

            failures+=1

            until=(
                self.now()+POLICY["lockoutSeconds"]
                if failures>=POLICY["maximumFailedAttempts"]
                else 0
            )

            with self.db:

                self.db.execute(
                    """UPDATE users
                    SET failures=?,locked_until=?
                    WHERE id=?""",
                    (failures,until,user)
                )

                self.event("LOGIN_FAILURE")

            raise PermissionError("Login denied")

        token=secrets.token_urlsafe(32)

        with self.db:

            self.db.execute(
                """UPDATE users
                SET failures=0,locked_until=0
                WHERE id=?""",
                (user,)
            )

            self.db.execute(
                "INSERT INTO sessions VALUES(?,?,?,0)",
                (
                    digest(token),
                    user,
                    self.now()+POLICY[
                        "sessionLifetimeSeconds"
                    ]
                )
            )

            self.event("LOGIN_SUCCESS")

        return token

    def authorize(self,token,domain,roles=None):

        locks()

        if not isinstance(token,str):
            raise PermissionError("Access denied")

        row=self.db.execute(
            """SELECT u.id,u.role,u.domain
            FROM sessions s JOIN users u
            ON s.user=u.id
            WHERE s.token_hash=?
            AND s.revoked=0
            AND s.expires>?""",
            (digest(token),self.now())
        ).fetchone()

        if (
            row is None
            or row[2]!=domain
            or (roles is not None and row[1] not in roles)
        ):

            with self.db:
                self.event("ACCESS_DENIED")

            raise PermissionError("Access denied")

        return {
            "id":row[0],
            "role":row[1],
            "domain":row[2],
            "simulationOnly":True
        }

    def revoke(self,token):

        with self.db:

            result=self.db.execute(
                """UPDATE sessions SET revoked=1
                WHERE token_hash=? AND revoked=0""",
                (digest(token),)
            )

            if result.rowcount!=1:
                raise PermissionError("Revocation denied")

            self.event("SESSION_REVOKED")

    def delete(self,token,domain):

        identity=self.authorize(token,domain)

        with self.db:

            self.db.execute(
                "DELETE FROM users WHERE id=?",
                (identity["id"],)
            )

            self.event("ACCOUNT_DELETED")

    def verify_events(self):

        previous="GENESIS"
        expected=1

        for row in self.db.execute(
            "SELECT * FROM events ORDER BY sequence"
        ):

            sequence,event,timestamp,prior,checksum=row

            calculated=digest(json.dumps(
                [sequence,event,timestamp,prior],
                separators=(",",":")
            ))

            if (
                sequence!=expected
                or prior!=previous
                or not hmac.compare_digest(
                    calculated,checksum
                )
            ):
                return False

            previous=checksum
            expected+=1

        return True

    def activate_finance(self,*args):
        raise PermissionError("Financial activation locked")

    def share_external(self,*args):
        raise PermissionError("External sharing disabled")

    def close(self):
        self.db.close()
