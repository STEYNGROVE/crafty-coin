import json
import hashlib
import subprocess
import sys
import re
from pathlib import Path
from decimal import Decimal

ROOT=Path(__file__).resolve().parents[1]
checks=[]

def check(name,condition):
    if not condition:
        raise RuntimeError("FAIL: "+name)

    checks.append(name)
    print("PASS:",name)

def load(name):
    return json.loads(
        (ROOT/name).read_text()
    )

security=load("config/security.json")
economics=load("config/economics.json")

locks=[
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

for lock in locks:
    check(
        lock+" disabled",
        security.get(lock) is False
    )

check(
    "All boolean security flags disabled",
    all(
        v is False
        for v in security.values()
        if type(v)==bool
    )
)

check(
    "Simulation mode",
    economics["mode"]=="SIMULATION_ONLY"
)

check(
    "Maximum supply",
    economics["maximumSupply"]==1000000
)

check(
    "Allocation conservation",
    sum(economics["allocations"].values())
    ==economics["maximumSupply"]
)

check(
    "Token precision",
    economics["decimals"]==9
)

check(
    "Presale funding cap",
    economics["allocations"]["presale"]*
    economics["presalePriceZAR"]
    ==economics["fundraisingTargetZAR"]
    ==2000000
)

check(
    "Mining reserve",
    economics["allocations"]["mining"]==350000
)

check(
    "Burn reserve",
    economics["allocations"]["burn"]==150000
)

check(
    "Eight-year halving",
    economics["halvingYears"]==8
)

check(
    "Founder vesting",
    economics["founderVestingYears"]==5
)

check(
    "Adult-only policy",
    economics["minimumAge"]==18
)

check(
    "Multisignature policy",
    security["treasurySignersRequired"]==2
    and security["treasuryTotalSigners"]==3
)

check(
    "Reserve burn policy",
    Decimal(str(economics["annualReserveBurnRate"]))
    ==Decimal("0.05")
)

check(
    "Commercial burn policy",
    Decimal(str(economics["commercialBurnRate"]))
    ==Decimal("0.02")
)

check(
    "Profit buyback ceiling",
    Decimal(str(economics["maximumProfitBurnRate"]))
    ==Decimal("0.05")
)

# Execute every existing test suite.

suites=[
    ("presale.py",9),
    ("treasury.py",13),
    ("mining.py",17),
    ("scarcity.py",20),
    ("customers.py",17),
    ("commerce.py",20),
    ("marketing.py",20)
]

total=0

for name,expected in suites:
    result=subprocess.run(
        [sys.executable,
         "-W","error::ResourceWarning",
         str(ROOT/"engine"/name)],
        capture_output=True,
        text=True
    )

    output=result.stdout+result.stderr

    match=re.search(r"Ran (\d+) tests?",output)

    check(
        name+" regression suite",
        result.returncode==0
        and match is not None
        and int(match.group(1))==expected
        and "ResourceWarning" not in output
    )

    total+=int(match.group(1))

check("Total regression tests",total==116)

# Validate existing simulation reports.

reports=[
    "simulation",
    "treasury",
    "mining",
    "scarcity",
    "customers",
    "commerce",
    "marketing"
]

for name in reports:
    report=load("reports/"+name+".json")

    check(
        name+" simulation mode",
        report.get("mode")=="SIMULATION_ONLY"
    )

treasury=load("reports/treasury.json")

check(
    "Treasury debit-credit reconciliation",
    treasury["ledgerDebitCents"]==
    treasury["ledgerCreditCents"]
)

check(
    "Escrow and refund liability",
    treasury["simulatedEscrowCents"]==
    treasury["refundLiabilityCents"]
)

check(
    "Treasury cash conservation",
    treasury["simulatedDepositsCents"]-
    treasury["simulatedRefundsCents"]==
    treasury["simulatedEscrowCents"]
)

check(
    "No actual funds",
    treasury["realFundsCollectedCents"]==0
)

check(
    "No authorized expenditure",
    treasury["authorizedSpendingCents"]==0
)

customers=load("reports/customers.json")

check(
    "No actual customer records",
    customers["realCustomers"]==0
)

check(
    "No reserved customer tokens",
    customers["reservedTokens"]==0
)

mining=load("reports/mining.json")

check(
    "Mining horizon",
    len(mining["years"])==100
)

check(
    "Mining budget conservation",
    sum(
        r["annualBudgetRaw"]
        for r in mining["years"]
    )<=350000*10**9
)

scarcity=load("reports/scarcity.json")

for scenario in scarcity["scenarios"]:
    previous=1000000*10**9

    for row in scenario["years"]:
        assert (
            row["totalSupplyRaw"]+
            row["destroyedRaw"]==
            1000000*10**9
        )

        assert row["totalSupplyRaw"]<=previous
        previous=row["totalSupplyRaw"]

check("400 scarcity scenario-years",True)

commerce=load("reports/commerce.json")

for row in commerce["scenarios"]:
    assert row["actualRevenueCents"]==0
    assert row["authorizedBuybackCents"]==0
    assert row["actualTokensBurned"]==0

check("Commercial financial isolation",True)

marketing=load("reports/marketing.json")

check(
    "Marketing remains unpublished",
    marketing["statistics"]["publishedCampaigns"]==0
)

check(
    "No advertising expenditure",
    marketing["statistics"]["advertisingSpendZAR"]==0
)

# Screen project files for common secret patterns.
# This is not a comprehensive secret scanner.

patterns=[
    r"ghp_[A-Za-z0-9]{30,}",
    r"github_pat_[A-Za-z0-9_]{30,}",
    r"gsk_[A-Za-z0-9]{30,}",
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    r"postgres(?:ql)?://[^/\s]+:[^@\s]+@"
]

manifest={}

for p in sorted(ROOT.rglob("*")):
    if p.is_symlink():
        raise RuntimeError("Unexpected symbolic link")

    if not p.is_file():
        continue

    if "__pycache__" in p.parts:
        continue

    if p.name==".gitignore":
        continue

    if p.parent==ROOT/"security":
        continue

    if p.name=="security.json" and \
       p.parent==ROOT/"reports":
        continue

    if p.name.startswith(".env") or \
       p.suffix in (".db",".key",".pem",".enc") or \
       any(x in p.name.lower() for x in
           ("keypair","wallet","secret")):
        raise RuntimeError(
            "Sensitive filename: "+p.name
        )

    data=p.read_bytes()

    if len(data)>20*1024*1024:
        raise RuntimeError("Unexpected large file")

    text=data.decode("utf-8",errors="ignore")

    if any(re.search(pattern,text)
           for pattern in patterns):
        raise RuntimeError(
            "Possible credential in "+p.name
        )

    manifest[str(p.relative_to(ROOT))]=\
        hashlib.sha256(data).hexdigest()

check("Basic sensitive file screening",True)

(ROOT/"security/manifest.json").write_text(
    json.dumps(manifest,indent=2)
)

check("SHA-256 manifest generated",bool(manifest))

report={
    "mode":"SIMULATION_ONLY",
    "localAudit":"PASS",
    "regressionTestsPassed":total,
    "checksPassed":len(checks),
    "checks":checks,
    "manifestFiles":len(manifest),
    "actualFundsCollectedZAR":0,
    "authorizedExpenditureZAR":0,
    "productionReadiness":"NO_GO",
    "independentSecurityAudit":"NOT_COMPLETED",
    "mainnetEnabled":False,
    "realPaymentsEnabled":False
}

(ROOT/"reports/security.json").write_text(
    json.dumps(report,indent=2)
)

print(json.dumps(report,indent=2))
