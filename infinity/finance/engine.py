import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def read(name):
    return json.loads(
        (ROOT/name).read_text()
    )

def locks():

    security=read("../config/security.json")
    policy=read("policy.json")

    required=[
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

    for key in required:
        if security.get(key) is not False:
            raise PermissionError(key)

    if policy.get("mode")!="SIMULATION_ONLY":
        raise PermissionError("Invalid mode")

    for key in (
        "mainnetEnabled",
        "realPaymentsEnabled",
        "presaleEnabled",
        "withdrawalsEnabled",
        "tokenTransfersEnabled",
        "automaticBuybacksEnabled",
        "automaticBurnsEnabled",
        "childFinancialAccess",
        "guaranteedReturns"
    ):
        if policy.get(key) is not False:
            raise PermissionError(key)

def adult(age):

    if type(age) is not int or not 18<=age<=120:
        raise PermissionError("Adults only")

def integer(value):

    if type(value) is not int or value<0:
        raise ValueError("Nonnegative integer required")

    return value

def readiness():

    locks()

    policy=read("policy.json")

    return {
        "mode":"SIMULATION_ONLY",
        "productionReadiness":"NO_GO",
        "approvals":{
            key:"PENDING"
            for key in policy["requiredApprovals"]
        },
        "actualFundsZAR":0,
        "actualExpenditureZAR":0,
        "mainnetEnabled":False
    }

def economics():

    locks()

    e=read("../config/economics.json")

    supply=integer(e["maximumSupply"])
    allocations=e["allocations"]

    for amount in allocations.values():
        integer(amount)

    if sum(allocations.values())!=supply:
        raise ValueError("Supply mismatch")

    if supply!=1000000:
        raise ValueError("Unexpected supply")

    if e["decimals"]!=9:
        raise ValueError("Unexpected precision")

    return e

def presale_scenario(age,requested_tokens):

    locks()
    adult(age)

    quantity=integer(requested_tokens)
    e=economics()

    cap=e["allocations"]["presale"]

    if quantity>cap:
        raise ValueError("Presale cap exceeded")

    return {
        "mode":"SIMULATION_ONLY",
        "requestedTokens":quantity,
        "hypotheticalGrossZAR":
            quantity*e["presalePriceZAR"],
        "actualFundsZAR":0,
        "reservedTokens":0,
        "allocatedTokens":0,
        "guaranteedReturns":False
    }

def profit_scenario(
    revenue_cents,
    direct_costs_cents,
    overhead_cents,
    tax_reserve_cents
):

    locks()

    revenue=integer(revenue_cents)
    costs=integer(direct_costs_cents)
    overhead=integer(overhead_cents)
    tax=integer(tax_reserve_cents)

    net=revenue-costs-overhead-tax

    maximum_buyback=max(0,net)*5//100

    return {
        "mode":"SIMULATION_ONLY",
        "netProfitCents":net,
        "hypotheticalBuybackCeilingCents":
            maximum_buyback,
        "actualBuybacksCents":0,
        "actualBurnedTokens":0,
        "actualExpenditureCents":0
    }

def liquidity_stress(
    cash_cents,
    refund_liability_cents,
    operating_reserve_cents
):

    locks()

    cash=integer(cash_cents)
    refunds=integer(refund_liability_cents)
    reserve=integer(operating_reserve_cents)

    required=refunds+reserve

    return {
        "mode":"SIMULATION_ONLY",
        "cashCents":cash,
        "requiredCents":required,
        "shortfallCents":max(0,required-cash),
        "surplusCents":max(0,cash-required),
        "covered":cash>=required,
        "actualFundsCents":0
    }

def activate(*args,**kwargs):
    raise PermissionError("Live activation locked")

def collect_payment(*args,**kwargs):
    raise PermissionError("Payments locked")

def transfer_token(*args,**kwargs):
    raise PermissionError("Transfers locked")

def withdraw(*args,**kwargs):
    raise PermissionError("Withdrawals locked")

def buyback(*args,**kwargs):
    raise PermissionError("Buybacks locked")

def burn(*args,**kwargs):
    raise PermissionError("Burns locked")
