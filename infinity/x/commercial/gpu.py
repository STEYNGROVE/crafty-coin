import json
import urllib.request
import urllib.error
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

BASE="https://gpu-compute-arbitrage-os-and-connect-it.onrender.com"

HEALTH_URL=BASE+"/api/health"

SERVICES={
    "GPU_RENTAL":"GPU compute rental",
    "AI_INFERENCE":"Managed AI inference",
    "AI_TRAINING":"AI training",
    "FINE_TUNING":"Model fine-tuning",
    "BATCH_PROCESSING":"Batch processing",
    "TRANSCRIPTION":"Audio transcription",
    "HPC":"High performance computing",
    "WORKLOAD_MATCHING":"Compute workload matching"
}

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None

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

def health():

    locks()

    request=urllib.request.Request(
        HEALTH_URL,
        headers={
            "User-Agent":"Crafty-Infinity/1.0",
            "Accept":"application/json"
        },
        method="GET"
    )

    opener=urllib.request.build_opener(NoRedirect())

    try:

        with opener.open(request,timeout=90) as response:

            raw=response.read(65537)

            if len(raw)>65536:
                raise ValueError("Response too large")

            data=json.loads(raw)

            if not isinstance(data,dict):
                raise ValueError("Invalid response")

            valid=(
                response.status==200
                and "status" in data
                and "check" in data
            )

            return {
                "reachable":True,
                "httpStatus":response.status,
                "healthSchemaVerified":valid,
                "reportedStatus":str(
                    data.get("status","unknown")
                )[:80],
                "productionReadinessVerified":False
            }

    except urllib.error.HTTPError as exc:

        return {
            "reachable":False,
            "httpStatus":exc.code,
            "healthSchemaVerified":False
        }

    except Exception as exc:

        return {
            "reachable":False,
            "errorType":type(exc).__name__,
            "healthSchemaVerified":False
        }

def draft(age,service,hours,budget_cents):

    locks()

    if type(age) is not int or not 18<=age<=120:
        raise PermissionError("Adult domain only")

    if service not in SERVICES:
        raise ValueError("Unknown service")

    if type(hours) is not int or not 1<=hours<=8760:
        raise ValueError("Invalid compute duration")

    if type(budget_cents) is not int or budget_cents<0:
        raise ValueError("Invalid budget")

    return {
        "provider":"GPU_COMPUTE_OS",
        "domain":"ADULT",
        "service":service,
        "requestedHours":hours,
        "illustrativeBudgetCents":budget_cents,
        "status":"LOCAL_DRAFT",
        "submitted":False,
        "bindingQuote":False,
        "gpuPurchased":False,
        "workloadStarted":False,
        "actualExpenditureZAR":0
    }

def purchase(*args,**kwargs):
    raise PermissionError("GPU purchase disabled")

def launch(*args,**kwargs):
    raise PermissionError("Workload launch disabled")

def submit(*args,**kwargs):
    raise PermissionError("External submission disabled")

def owner_access(*args,**kwargs):
    raise PermissionError("Owner access disabled")

def database_access(*args,**kwargs):
    raise PermissionError("Database access disabled")

def child_data(*args,**kwargs):
    raise PermissionError("Child data access denied")

def deployment_change(*args,**kwargs):
    raise PermissionError("Deployment changes disabled")

if __name__=="__main__":

    result=health()

    report={
        "phase":37,
        "provider":"GPU_COMPUTE_OS",
        "mode":"READ_ONLY_AND_LOCAL_DRAFT",
        "status":"PASS" if result.get(
            "healthSchemaVerified"
        ) else "PARTIAL",
        "deployment":BASE,
        "health":result,
        "proposedServices":len(SERVICES),
        "independentApplication":True,
        "ownerCredentialsRequired":False,
        "liveServiceFulfilmentVerified":False,
        "gpuPurchases":0,
        "workloadsStarted":0,
        "deploymentChanges":0,
        "actualExpenditureZAR":0,
        "productionReadiness":"NO_GO"
    }

    (ROOT/"reports/gpu-connector.json").write_text(
        json.dumps(report,indent=2)+chr(10)
    )

    print(json.dumps(report,indent=2))
