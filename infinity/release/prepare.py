import json
import shutil
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

security=json.loads(
    (ROOT/"config/security.json").read_text()
)

audit=json.loads(
    (ROOT/"reports/security.json").read_text()
)

assert all(
    v is False
    for v in security.values()
    if type(v)==bool
)

assert audit["localAudit"]=="PASS"
assert audit["regressionTestsPassed"]==116

destination=ROOT/"release/staging"

destination.mkdir(
    parents=True,exist_ok=True
)

# Explicit public-safe file allowlist.
# Internal marketing and treasury reports excluded.

allowed=[
    "index.html",
    "whitepaper.txt",
    "simulation.json",
    "mining.json",
    "scarcity.json",
    "community.html",
    "customers.json",
    "ecosystem.html",
    "commerce.json",
    "robots.txt"
]

for name in allowed:
    source=ROOT/"web"/name

    assert source.is_file(),name
    assert not source.is_symlink(),name

    shutil.copy2(
        source,destination/name
    )

p=destination/"index.html"
s=p.read_text()

# Disable links to internal-only reports.

import re

for name in [
    "treasury.html",
    "treasury.json",
    "marketing.html",
    "marketing.json"
]:
    s=re.sub(
        r'<a\b[^>]*href=["\']'+
        re.escape(name)+
        r'["\'][^>]*>.*?</a>',
        '',
        s,
        flags=re.I|re.S
    )

banner="""
<div style="padding:16px;background:#302818;
color:#ffe5a3;text-align:center">
<strong>DEVELOPMENT PREVIEW</strong><br>
No token sale is open. No deposits accepted.
All economic and customer figures are simulations.
Adults only. Cryptocurrency involves risk.
</div>
"""

s=re.sub(
    r"(<body[^>]*>)",
    lambda m:m.group(1)+banner,
    s,count=1,flags=re.I
)

p.write_text(s)

(destination/"robots.txt").write_text(
    "User-agent: *\nDisallow: /\n"
)

(destination/".nojekyll").touch()

report={
    "project":"CRAFTY INFINITY",
    "mode":"SIMULATION_ONLY",
    "prototypePhasesPrepared":12,
    "regressionTestsPassed":116,
    "localSecurityAudit":"PASS",
    "sourceRecovery":"OWNER_REPORTED_PASS",
    "stagingPackage":"PREPARED",
    "publicDeployment":"NOT_EXECUTED",
    "productionRelease":"NO_GO",
    "proposedMainnetSupply":1000000,
    "proposedPresalePriceZAR":10,
    "proposedFundingTargetZAR":2000000,
    "actualFundsCollectedZAR":0,
    "actualRevenueZAR":0,
    "authorizedExpenditureZAR":0,
    "mainnetEnabled":False,
    "realPaymentsEnabled":False,
    "outstandingGates":[
        "Independent legal review",
        "Issuing entity approval",
        "Bank commercial-use verification",
        "Independent escrow",
        "Payment provider approval",
        "Independent security audit",
        "Cross-engine transactional integration",
        "Production authentication",
        "Verified adult eligibility",
        "Multisignature treasury setup",
        "Verified customer demand",
        "Separate mainnet authorization",
        "Separate real-payment authorization"
    ]
}

(ROOT/"release/readiness.json").write_text(
    json.dumps(report,indent=2)
)

(destination/"readiness.json").write_text(
    json.dumps(report,indent=2)
)

manifest={}

for p in sorted(destination.iterdir()):
    if p.is_file():
        manifest[p.name]=hashlib.sha256(
            p.read_bytes()
        ).hexdigest()

(ROOT/"release/staging-manifest.json").write_text(
    json.dumps(manifest,indent=2)
)

print(json.dumps(report,indent=2))
print("PASS: Staging package prepared")
print("PASS: Financial activation disabled")
