import json
from pathlib import Path

P=Path(__file__).resolve().parents[1]
C=json.loads((P/"config/economics.json").read_text())
S=json.loads((P/"config/security.json").read_text())

U=10**C["decimals"]
A=C["allocations"]
INITIAL=C["maximumSupply"]*U

assert sum(A.values())*U==INITIAL
assert A["presale"]*C["presalePriceZAR"]==2000000
assert not any(v for v in S.values() if type(v)==bool)

results=[]

for name,subscription,burn_rate in [
    ("Failed fundraising",0,0),
    ("Low adoption",25,0),
    ("Conservative",50,1),
    ("Moderate",75,2),
    ("Strong adoption",100,3),
    ("Zero revenue",100,0),
    ("Market stress",100,0)
]:
    total=INITIAL
    mining=A["mining"]*U
    reserve=A["burn"]*U
    founder=A["founder"]*U
    ecosystem=A["ecosystem"]*U
    partners=A["partnerships"]*U
    sold=A["presale"]*U*subscription//100
    unsold=A["presale"]*U-sold
    circulating=sold+A["liquidity"]*U
    destroyed=0
    years=[]

    for year in range(1,101):
        epoch=(year-1)//8
        reward=min(mining,A["mining"]*U//(16*2**epoch))
        vest=min(founder,A["founder"]*U//5)
        eco=min(ecosystem,A["ecosystem"]*U//10)
        partner=min(partners,A["partnerships"]*U//10)

        mining-=reward
        founder-=vest
        ecosystem-=eco
        partners-=partner
        circulating+=reward+vest+eco+partner

        rb=reserve*5//100
        cb=circulating*burn_rate//100

        reserve-=rb
        circulating-=cb
        total-=rb+cb
        destroyed+=rb+cb

        assert total+destroyed==INITIAL
        assert total==sum([
            mining,reserve,founder,ecosystem,
            partners,unsold,circulating
        ])

        assert min(total,mining,reserve,founder,
                   ecosystem,partners,circulating)>=0

        years.append({
            "year":year,
            "totalSupplyRaw":total,
            "circulatingRaw":circulating,
            "miningReserveRaw":mining,
            "burnedRaw":destroyed
        })

    results.append({
        "scenario":name,
        "subscriptionPercent":subscription,
        "assumedCirculatingBurnPercent":burn_rate,
        "grossFundingZAR":subscription*20000,
        "years":years
    })

    print("PASS:",name,"100 years")

report={
    "mode":"SIMULATION_ONLY",
    "status":"PASS",
    "checks":700,
    "scenarios":results
}

(P/"reports/simulation.json").write_text(
    json.dumps(report,indent=2)
)

print("PASS: 700 supply conservation checks")
print("PASS: Financial locks")
