import json
import tempfile
from pathlib import Path
from marketing import Marketing,CHANNELS,funnel

ROOT=Path(__file__).resolve().parents[1]

TOPICS=[
    "Project introduction",
    "Development transparency",
    "Commercial utility research",
    "Fixed supply mathematics",
    "Mining reward simulation",
    "Treasury safeguards",
    "Founder vesting",
    "Risk education",
    "Merchant opportunities",
    "Creator ecosystem",
    "Security progress",
    "Development milestones"
]

calendar=[]

with tempfile.TemporaryDirectory() as tmp:
    m=Marketing(Path(tmp)/"marketing.db")

    for day in range(1,91):
        channel=list(CHANNELS)[
            (day-1)%len(CHANNELS)
        ]

        topic=TOPICS[
            ((day-1)//len(CHANNELS)+day-1)
            %len(TOPICS)
        ]

        content=(
            f"CRAFTY INFINITY development update: "
            f"{topic}. Adult-only project research. "
            "No token sale is open. "
            "No investment returns are promised."
        )

        ref=f"SIM-DAY-{day:03}"

        m.draft(
            ref,channel,"ADULT_ONLY",content
        )

        calendar.append({
            "day":day,
            "channel":channel,
            "topic":topic,
            "content":content,
            "status":"DRAFT",
            "budgetZAR":0
        })

    stats=m.report()
    m.db.close()

assert stats["draftCampaigns"]==90
assert stats["publishedCampaigns"]==0

scenarios=[]

for name,visitors,interest,buyers,average in [
    ("No demand",0,0,0,0),
    ("Early discovery",10000,500,500,500),
    ("Conservative",50000,1000,500,1000),
    ("Moderate",100000,1000,1000,1000),
    ("Target",200000,1000,1000,1000),
    ("High interest",500000,1500,1000,1000)
]:
    row=funnel(visitors,interest,buyers,average)
    row["scenario"]=name
    scenarios.append(row)

    print(
        name,
        "| Hypothetical demand R",
        row["hypotheticalDemandZAR"]
    )

report={
    "mode":"SIMULATION_ONLY",
    "status":"PASS",
    "statistics":stats,
    "channels":CHANNELS,
    "scenarios":scenarios,
    "calendar":calendar
}

(ROOT/"reports/marketing.json").write_text(
    json.dumps(report,indent=2)
)

(ROOT/"marketing/calendar.json").write_text(
    json.dumps(calendar,indent=2)
)

print("PASS: 90-day campaign calendar")
print("PASS: Twelve acquisition channels")
print("PASS: Six conversion scenarios")
print("PASS: No publishing or expenditure")
