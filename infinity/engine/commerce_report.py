import json
import tempfile
from pathlib import Path
from commerce import Commerce,UNIT

ROOT=Path(__file__).resolve().parents[1]

# Hypothetical monthly business assumptions.
# Service, sales volume, price ZAR, direct cost ZAR.

ASSUMPTIONS=[
    ("PIXELPUNK",20,3500,1200),
    ("GPU_COMPUTE",50,800,550),
    ("GHOSTMEDIA",30,1000,400),
    ("MARKETPLACE",100,250,150),
    ("ACADEMY",100,200,60),
    ("MERCHANT",50,300,120)
]

results=[]

for name,volume in [
    ("Zero demand",0),
    ("Low adoption",25),
    ("Moderate adoption",50),
    ("Target adoption",100),
    ("High adoption",200)
]:
    with tempfile.TemporaryDirectory() as tmp:
        c=Commerce(Path(tmp)/"commerce.db")

        for service,count,price,cost in ASSUMPTIONS:
            for n in range(count*volume//100):
                c.sale(
                    f"SIM-{service}-{n}",
                    f"SIM-CUSTOMER-{n}",
                    30,
                    service,
                    price*100,
                    cost*100,
                    0
                )

        report=c.report(overhead=3500000)
        report["scenario"]=name
        report["volumePercent"]=volume

        assert report["actualRevenueCents"]==0
        assert report["authorizedBuybackCents"]==0

        results.append(report)
        c.db.close()

        print(
            name,
            "| Revenue R",
            report["revenueCents"]/100,
            "| Operating profit R",
            report["preTaxOperatingProfitCents"]/100
        )

report={
    "mode":"SIMULATION_ONLY",
    "status":"PASS",
    "monthlyOverheadAssumptionZAR":35000,
    "assumptions":ASSUMPTIONS,
    "scenarios":results
}

(ROOT/"reports/commerce.json").write_text(
    json.dumps(report,indent=2)
)

print("PASS: Six commercial service models")
print("PASS: Five demand scenarios")
print("PASS: No actual commercial transactions")
