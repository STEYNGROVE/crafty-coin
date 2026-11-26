import json
import hashlib
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent

def read(path):
    return json.loads(
        (ROOT/path).read_text()
    )

def require(condition,message):
    if not condition:
        raise RuntimeError(message)
    print("PASS:",message)

security=read("config/security.json")

required=[
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
]

for key in required:
    require(
        security.get(key) is False,
        key+" remains disabled"
    )

regression=read("reports/full-regression.json")

require(
    regression["status"]=="PASS",
    "Consolidated regression"
)

require(
    regression["testsPassed"]==486,
    "486 regression tests"
)

economics=read("config/economics.json")

require(
    economics["maximumSupply"]==1000000,
    "Proposed maximum supply"
)

require(
    sum(economics["allocations"].values())
    ==1000000,
    "Allocation conservation"
)

require(
    economics["decimals"]==9,
    "Token precision"
)

vision=read("core/vision.json")

require(
    len(vision["academies"])==22,
    "22 academies"
)

require(
    len(vision["superheroes"])==12,
    "12 superheroes"
)

require(
    len(vision["applications"])==11,
    "11 application profiles"
)

reports=[
    "core",
    "brand",
    "ai",
    "education",
    "squad",
    "virtual-life",
    "language",
    "family",
    "integrations",
    "marketplace",
    "privacy",
    "platform",
    "finance"
]

for name in reports:

    report=read("reports/"+name+".json")

    require(
        report.get("status")=="PASS",
        name+" local report"
    )

    require(
        report.get("actualExpenditureZAR",0)==0,
        name+" reported expenditure zero"
    )

finance=read("reports/finance.json")

require(
    finance["productionReadiness"]=="NO_GO",
    "Financial production lock"
)

require(
    finance["actualFundsCollectedZAR"]==0,
    "No collected funds reported"
)

platform=read("reports/platform.json")

require(
    platform["connectedLocalEngines"]==4,
    "Four locally connected engines"
)

require(
    platform["externalServiceConnections"]==0,
    "External integrations remain disabled"
)

ai=read("reports/ai.json")

require(
    ai["childLiveAIEnabled"] is False,
    "Child live AI disabled"
)

require(
    ai["liveRequestsExecuted"]==0,
    "No live AI requests reported"
)

tracked=subprocess.check_output(
    ["git","ls-files"],
    cwd=ROOT.parent,
    text=True
).splitlines()

dangerous=[]

for filename in tracked:

    p=Path(filename)
    name=p.name.lower()

    if (
        name==".env"
        or name.endswith(".key")
        or name.endswith(".pem")
        or name.endswith(".db")
        or name.endswith(".sqlite")
        or name.endswith(".sqlite3")
        or name.endswith(".enc")
        or "keypair" in name
        or name=="wallet.json"
    ):
        dangerous.append(filename)

require(
    not dangerous,
    "Tracked sensitive filename screening"
)

report={
    "project":"CRAFTY INFINITY",
    "phase":27,
    "mode":"SIMULATION_ONLY",
    "localVerification":"PASS",
    "regressionTestsPassed":486,
    "academies":22,
    "superheroes":12,
    "applicationProfiles":11,
    "connectedLocalEngines":4,
    "verifiedModuleReports":len(reports),
    "actualFundsCollectedZAR":0,
    "actualExpenditureZAR":0,
    "productionReadiness":"NO_GO",
    "independentAudit":"NOT_COMPLETED",
    "mainnetEnabled":False,
    "realPaymentsEnabled":False,
    "childLiveAIEnabled":False,
    "remainingBlockers":[
        "Production authentication and MFA",
        "Verified age and parental consent",
        "Persistent production data architecture",
        "Complete cross-engine integration",
        "Production API and application interfaces",
        "Original Crafty master artwork",
        "Native-speaker curriculum and audio review",
        "Sesotho and isiZulu bundled audio",
        "Live external service verification",
        "POPIA and consumer protection review",
        "Financial and token legal classification",
        "Banking and escrow approval",
        "Independent custody verification",
        "Independent security audit",
        "Off-device recovery verification",
        "Separate live activation authorization"
    ]
}

(ROOT/"reports/master-verification.json").write_text(
    json.dumps(report,indent=2)
)

print(json.dumps(report,indent=2))
