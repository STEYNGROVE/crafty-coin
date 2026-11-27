import json
import urllib.request
import urllib.error
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

BASE="https://ghostmedia-production-worker-r9va.onrender.com"

HEALTH_URL=BASE+"/health"

SERVICES={
    "FACELESS_VIDEO":"Faceless video production",
    "SHORTS":"Short-form video production",
    "AI_NARRATION":"AI narration",
    "CINEMATIC":"Cinematic production",
    "TREND_INTELLIGENCE":"Trend intelligence",
    "EDUCATIONAL_MEDIA":"Educational media",
    "BUSINESS_ADVERTISING":"Business advertising",
    "LOCALIZATION":"Content localization"
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
                and data.get("status")=="ok"
                and "persistence" in data
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

def draft(age,service,description,quantity=1):

    locks()

    if type(age) is not int or not 18<=age<=120:
        raise PermissionError("Adult domain only")

    if service not in SERVICES:
        raise ValueError("Unknown service")

    if not isinstance(description,str):
        raise ValueError("Invalid description")

    description=description.strip()

    if not 5<=len(description)<=1000:
        raise ValueError("Invalid description length")

    if type(quantity) is not int or not 1<=quantity<=100:
        raise ValueError("Invalid quantity")

    return {
        "provider":"GHOSTMEDIA",
        "domain":"ADULT",
        "service":service,
        "description":description,
        "quantity":quantity,
        "status":"LOCAL_DRAFT",
        "submitted":False,
        "bindingQuote":False,
        "generated":False,
        "published":False,
        "actualExpenditureZAR":0
    }

def generate(*args,**kwargs):
    raise PermissionError("Live generation disabled")

def publish(*args,**kwargs):
    raise PermissionError("Publishing disabled")

def submit(*args,**kwargs):
    raise PermissionError("External submission disabled")

def channel_access(*args,**kwargs):
    raise PermissionError("Channel access disabled")

def purchase(*args,**kwargs):
    raise PermissionError("Purchases disabled")

def child_data(*args,**kwargs):
    raise PermissionError("Child data access denied")

def deployment_change(*args,**kwargs):
    raise PermissionError("Deployment changes disabled")

if __name__=="__main__":

    result=health()

    report={
        "phase":38,
        "provider":"GHOSTMEDIA",
        "mode":"READ_ONLY_AND_LOCAL_DRAFT",
        "status":"PASS" if result.get(
            "healthSchemaVerified"
        ) else "PARTIAL",
        "deployment":BASE,
        "health":result,
        "proposedServices":len(SERVICES),
        "independentApplication":True,
        "liveMediaProductionVerified":False,
        "credentialsSubmitted":False,
        "videosGenerated":0,
        "videosPublished":0,
        "deploymentChanges":0,
        "actualExpenditureZAR":0,
        "productionReadiness":"NO_GO"
    }

    (ROOT/"reports/ghostmedia-connector.json").write_text(
        json.dumps(report,indent=2)+chr(10)
    )

    print(json.dumps(report,indent=2))
