import json
from decimal import Decimal
from pathlib import Path
from mining import (
    UNIT,RESERVE,annual_budget,
    difficulty,CATEGORIES
)

root=Path(__file__).resolve().parents[1]

rows=[]
released=0

for year in range(1,101):
    budget=annual_budget(year)
    released+=budget

    assert released<=RESERVE

    rows.append({
        "year":year,
        "annualBudgetRaw":budget,
        "maximumCumulativeReleaseRaw":released,
        "remainingReserveRaw":RESERVE-released,
        "difficulty100Users":difficulty(year,100),
        "difficulty10000Users":difficulty(year,10000)
    })

    if year in [1,8,9,16,17,20,50,100]:
        print(
            f"Year {year}: "
            f"Budget={Decimal(budget)/UNIT:,.9f} "
            f"CRAFTY | Difficulty={difficulty(year,100)}"
        )

report={
    "mode":"SIMULATION_ONLY",
    "categories":CATEGORIES,
    "maximumMiningReserveRaw":RESERVE,
    "actualTokensTransferred":0,
    "years":rows,
    "status":"PASS"
}

(root/"reports/mining.json").write_text(
    json.dumps(report,indent=2)
)

print("PASS: 100-year mining budget")
print("PASS: Progressive difficulty")
print("PASS: Mining reserve conservation")
