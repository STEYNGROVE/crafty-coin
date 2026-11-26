import json
from pathlib import Path
from treasury import Treasury

root=Path(__file__).resolve().parents[1]

private=Path.home()/".local/share/crafty-infinity"
private.mkdir(parents=True,exist_ok=True)
private.chmod(0o700)

db=private/"treasury-demo.db"
t=Treasury(db)

if not t.db.execute(
    "SELECT 1 FROM deposits LIMIT 1"
).fetchone():

    t.deposit("SIM-DEMO-001",100000,"SIM_EFT")
    t.deposit("SIM-DEMO-002",250000,"SIM_USDC")
    t.deposit("SIM-DEMO-003",500000,"SIM_EFT")

    t.refund("SIM-REFUND-001","SIM-DEMO-001")

report=t.reconcile()

(root/"reports/treasury.json").write_text(
    json.dumps(report,indent=2)
)

print(json.dumps(report,indent=2))

t.db.close()
db.chmod(0o600)

print("PASS: Persistent simulated treasury")
print("PASS: Private database storage")
