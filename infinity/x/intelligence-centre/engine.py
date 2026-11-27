import json
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[2]

SOURCES={
    "PIXELPUNK":"pixelpunk.json",
    "GPU_COMPUTE":"gpu-connector.json",
    "GHOSTMEDIA":"ghostmedia-connector.json",
    "GROQ":"groq-provider.json",
    "SUBSCRIPTIONS":"subscriptions.json"
}

def locks():
    policy=json.loads(
        (ROOT/"config/security.json").read_text()
    )

    for flag in (
        "mainnetEnabled",
        "realPaymentsEnabled",
        "presaleEnabled",
        "withdrawalsEnabled",
        "liveBurnsEnabled",
        "liveBuybacksEnabled",
        "paidInfrastructureEnabled",
        "paidAdvertisingEnabled"
    ):
        if policy.get(flag) is not False:
            raise PermissionError(flag)

def read_report(name,directory=None):

    directory=Path(directory or ROOT/"reports")

    if name not in set(SOURCES.values())|{
        "full-regression.json"
    }:
        raise PermissionError("Report not allowlisted")

    try:

        path=directory/name

        if path.stat().st_size>1000000:
            return {}

        data=json.loads(path.read_text())

        return data if isinstance(data,dict) else {}

    except (OSError,ValueError):
        return {}

def aggregate(directory=None):

    locks()

    services=[]

    for name,filename in SOURCES.items():

        report=read_report(filename,directory)

        status=report.get("status","UNVERIFIED")

        if status not in ("PASS","PARTIAL","FAIL"):
            status="UNVERIFIED"

        services.append({
            "service":name,
            "checkpoint":status,
            "currentLiveHealthVerified":False,
            "source":filename
        })

    regression=read_report(
        "full-regression.json",directory
    )

    tests=regression.get("testsPassed",0)

    if type(tests) is not int or tests<0:
        tests=0

    return {
        "mode":"LOCAL_REPORT_AGGREGATION",
        "generatedAt":datetime.now(
            timezone.utc
        ).isoformat(),
        "services":services,
        "regressionTests":tests,
        "actualRevenueZAR":0,
        "actualExpenditureZAR":0,
        "financialOperationsEnabled":False,
        "liveMonitoringEnabled":False,
        "childDataIncluded":False,
        "productionReadiness":"NO_GO"
    }

def forecast(counts,overhead_cents=0):

    locks()

    products=json.loads(
        (ROOT/"marketplace/catalogue.json").read_text()
    )["products"]

    prices={
        p["id"]:p["priceCents"]
        for p in products
        if p["type"]=="SUBSCRIPTION"
    }

    if not isinstance(counts,dict):
        raise ValueError("Invalid forecast")

    if type(overhead_cents) is not int or overhead_cents<0:
        raise ValueError("Invalid overhead")

    monthly=0

    for product,count in counts.items():

        if product not in prices:
            raise ValueError("Unknown subscription")

        if type(count) is not int or not 0<=count<=1000000:
            raise ValueError("Invalid subscriber count")

        monthly+=prices[product]*count

    return {
        "mode":"ILLUSTRATIVE_ONLY",
        "monthlyGrossCents":monthly,
        "annualizedGrossCents":monthly*12,
        "monthlyOverheadCents":overhead_cents,
        "balanceBeforeOtherCostsCents":monthly-overhead_cents,
        "actualRevenueCents":0,
        "guaranteedReturns":False
    }

def activate_finance(*args,**kwargs):
    raise PermissionError("Financial activation disabled")

def export_child_data(*args,**kwargs):
    raise PermissionError("Child data export denied")

def modify_provider(*args,**kwargs):
    raise PermissionError("Independent provider protected")
