import json
import time
import secrets
import hashlib
import threading
from pathlib import Path
from collections import deque

ROOT=Path(__file__).resolve().parents[2]
POLICY=Path(__file__).with_name("policy.json")

FLAGS=(
    "mainnetEnabled",
    "realPaymentsEnabled",
    "presaleEnabled",
    "withdrawalsEnabled",
    "liveBurnsEnabled",
    "liveBuybacksEnabled",
    "paidAdvertisingEnabled",
    "paidInfrastructureEnabled",
    "bankVerified",
    "legalApproved",
    "escrowVerified",
    "securityAuditApproved"
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
    data=json.loads(
        (ROOT/"config/security.json").read_text()
    )
    for flag in FLAGS:
        if data.get(flag) is not False:
            raise PermissionError(flag)

    p=json.loads(POLICY.read_text())

    if p.get("mode")!="LOCAL_SYNTHETIC":
        raise PermissionError("Invalid mode")

    for flag in (
        "realAccountsEnabled",
        "financialOperationsEnabled",
        "childDataExportEnabled",
        "crossDomainAccessEnabled"
    ):
        if p.get(flag) is not False:
            raise PermissionError(flag)

    providers=p.get("providers",{})
    if set(providers)!={
        "GROQ","PIXELPUNK",
        "GPU_COMPUTE","GHOSTMEDIA"
    }:
        raise PermissionError("Invalid providers")

    if any(v is not False for v in providers.values()):
        raise PermissionError("Provider activation denied")

    return p

class Guard:
    def __init__(self,clock=time.monotonic):
        locks()
        self.clock=clock
        self.sessions={}
        self.requests={}
        self.replays=set()
        self.mutex=threading.RLock()

    def issue(self,identity,age,role):
        locks()
        if not isinstance(identity,str):
            raise PermissionError("Invalid identity")
        if not identity.startswith("SIM-"):
            raise PermissionError("Synthetic only")
        if not 5<=len(identity)<=64:
            raise ValueError("Invalid identity")
        if role not in ROLES:
            raise PermissionError("Invalid role")
        if type(age) is not int or not 4<=age<=120:
            raise PermissionError("Invalid age")
        if (role=="LEARNER")!=(age<18):
            raise PermissionError("Age restriction")

        with self.mutex:
            now=self.clock()
            for key in list(self.sessions):
                if self.sessions[key]["expires"]<=now:
                    del self.sessions[key]
            if len(self.sessions)>=1000:
                raise PermissionError("Capacity")
            token=secrets.token_urlsafe(32)
            key=hashlib.sha256(token.encode()).hexdigest()
            self.sessions[key]={
                "identity":identity,
                "domain":ROLES[role],
                "role":role,
                "expires":now+1800
            }
            return token

    def authorize(self,token,domain,roles=None):
        locks()
        if not isinstance(token,str) or len(token)>128:
            raise PermissionError("Invalid token")
        key=hashlib.sha256(token.encode()).hexdigest()
        with self.mutex:
            s=self.sessions.get(key)
            if not s or s["expires"]<=self.clock():
                raise PermissionError("Session expired")
            if s["domain"]!=domain:
                raise PermissionError("Domain denied")
            if roles is not None and s["role"] not in roles:
                raise PermissionError("Role denied")
            return dict(s)

    def revoke(self,token):
        key=hashlib.sha256(token.encode()).hexdigest()
        with self.mutex:
            self.sessions.pop(key,None)

    def rate_limit(self,token,domain):
        with self.mutex:
            s=self.authorize(token,domain)
            now=self.clock()
            for key in list(self.requests):
                q=self.requests[key]
                while q and now-q[0]>=60:
                    q.popleft()
                if not q:
                    del self.requests[key]
            identity=s["identity"]
            if identity not in self.requests:
                if len(self.requests)>=1000:
                    raise PermissionError("Capacity")
            q=self.requests.setdefault(identity,deque())
            if len(q)>=60:
                raise PermissionError("Rate limited")
            q.append(now)

    def replay(self,reference):
        locks()
        if not isinstance(reference,str):
            raise ValueError("Invalid reference")
        if not reference.startswith("SIM-"):
            raise ValueError("Synthetic only")
        if not 5<=len(reference)<=128:
            raise ValueError("Invalid length")
        with self.mutex:
            if reference in self.replays:
                raise PermissionError("Duplicate")
            if len(self.replays)>=10000:
                raise PermissionError("Capacity")
            self.replays.add(reference)

    def provider(self,name):
        locks()
        raise PermissionError("Provider disabled")

    def financial_action(self,*args,**kwargs):
        raise PermissionError("Finance disabled")

    def child_export(self,*args,**kwargs):
        raise PermissionError("Export disabled")

def validate_request(raw,allowed,required):
    locks()
    if not isinstance(raw,bytes):
        raise ValueError("Bytes required")
    if not 1<=len(raw)<=4096:
        raise ValueError("Invalid size")

    def pairs(items):
        result={}
        for key,value in items:
            if key in result:
                raise ValueError("Duplicate key")
            result[key]=value
        return result

    def reject(value):
        raise ValueError("Invalid constant")

    data=json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=pairs,
        parse_constant=reject
    )
    if not isinstance(data,dict):
        raise ValueError("Object required")
    if not set(data)<=set(allowed):
        raise ValueError("Unknown field")
    if not set(required)<=set(data):
        raise ValueError("Missing field")
    return data
