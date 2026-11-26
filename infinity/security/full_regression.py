import json
import re
import sys
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

suites=[
    "engine/presale.py",
    "engine/treasury.py",
    "engine/mining.py",
    "engine/scarcity.py",
    "engine/customers.py",
    "engine/commerce.py",
    "engine/marketing.py",
    "core/test_core.py",
    "brand/test_brand.py",
    "ai/test_ai.py",
    "education/test_education.py",
    "squad/test_squad.py",
    "virtual-life/test_life.py",
    "language/test_language.py",
    "family/test_family.py",
    "integrations/test_gateway.py",
    "marketplace/test_marketplace.py"
]

results=[]
total=0

for suite in suites:

    path=ROOT/suite

    if not path.is_file():
        raise SystemExit(f"Missing suite: {suite}")

    p=subprocess.run(
        [sys.executable,str(path)],
        capture_output=True,
        text=True,
        timeout=120
    )

    output=p.stdout+"\n"+p.stderr

    match=re.search(
        r"Ran (\d+) tests?",output
    )

    if p.returncode!=0 or not match:
        print(output)
        raise SystemExit(f"FAIL: {suite}")

    count=int(match.group(1))

    if count<1:
        raise SystemExit("Empty test suite")

    total+=count

    results.append({
        "suite":suite,
        "tests":count,
        "status":"PASS"
    })

    print(f"PASS: {suite}: {count} tests")

assert total==390, f"Unexpected total: {total}"

report={
    "mode":"SIMULATION_ONLY",
    "status":"PASS",
    "suites":len(results),
    "testsPassed":total,
    "results":results,
    "productionReadiness":"NO_GO",
    "actualExpenditureZAR":0
}

(ROOT/"reports/full-regression.json").write_text(
    json.dumps(report,indent=2)+"\n"
)

print(json.dumps(report,indent=2))
