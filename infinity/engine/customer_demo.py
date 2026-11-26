import json
import tempfile
from pathlib import Path
from customers import Customers

root=Path(__file__).resolve().parents[1]

with tempfile.TemporaryDirectory() as tmp:
    c=Customers(Path(tmp)/"demo.db")

    founder,code=c.register("SIM-DEMO-001",30,True)
    c.interest(founder,1000)

    for n in range(2,101):
        cid,_=c.register(
            f"SIM-DEMO-{n:03}",
            30,True,
            referral=code if n<=31 else None
        )

        c.interest(cid,100*n)

    report=c.report()
    c.db.close()

assert report["syntheticCustomers"]==100
assert report["syntheticReferrals"]==30
assert report["realFundsCollectedZAR"]==0
assert report["reservedTokens"]==0

(root/"reports/customers.json").write_text(
    json.dumps(report,indent=2)
)

print(json.dumps(report,indent=2))
print("PASS: Customer acquisition simulation")
