import json
import urllib.request
import urllib.error
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

KEY_PATH=(
    Path.home()
    /".config/crafty-infinity/groq.key"
)

MODELS_URL="https://api.groq.com/openai/v1/models"

class NoRedirect(urllib.request.HTTPRedirectHandler):

    def redirect_request(self,*args,**kwargs):
        raise PermissionError("Redirect blocked")

def verify_locks():

    security=json.loads(
        (ROOT/"config/security.json").read_text()
    )

    for flag in (
        "mainnetEnabled",
        "realPaymentsEnabled",
        "presaleEnabled",
        "withdrawalsEnabled",
        "paidInfrastructureEnabled",
        "paidAdvertisingEnabled"
    ):
        if security.get(flag) is not False:
            raise PermissionError(flag)

    policy=json.loads(
        (ROOT/"ai/policy.json").read_text()
    )

    for flag in (
        "liveRequestsEnabled",
        "childLiveAIEnabled",
        "automaticFinancialActions",
        "automaticPublishing",
        "persistentConversationStorage"
    ):
        if policy.get(flag) is not False:
            raise PermissionError(flag)

def read_key():

    if not KEY_PATH.is_file():
        raise FileNotFoundError(
            "Private Groq credential unavailable"
        )

    if KEY_PATH.stat().st_mode & 0o077:
        raise PermissionError(
            "Credential permissions must be 600"
        )

    key=KEY_PATH.read_text().strip()

    if not key.startswith("gsk_"):
        raise ValueError("Invalid credential format")

    return key

def models():

    verify_locks()

    request=urllib.request.Request(
        MODELS_URL,
        headers={
            "Authorization":"Bearer "+read_key(),
            "Accept":"application/json",
            "User-Agent":"Crafty-Infinity/1.0"
        },
        method="GET"
    )

    opener=urllib.request.build_opener(
        NoRedirect()
    )

    with opener.open(request,timeout=20) as response:

        raw=response.read(2_000_001)

        if len(raw)>2_000_000:
            raise ValueError("Response too large")

        data=json.loads(raw)

    return sorted({
        item["id"]
        for item in data["data"]
        if isinstance(item.get("id"),str)
        and item.get("active",True)
    })

def generate(*args,**kwargs):
    raise PermissionError(
        "Live AI generation remains disabled"
    )

if __name__=="__main__":

    report={
        "phase":35,
        "provider":"GROQ",
        "operation":"READ_ONLY_MODEL_DISCOVERY",
        "liveGenerationEnabled":False,
        "childLiveAIEnabled":False,
        "learnerDataSubmitted":False,
        "financialOperationsEnabled":False,
        "generationRequests":0,
        "productionReadiness":"NO_GO"
    }

    try:

        available=models()

        report.update({
            "status":"PASS" if available else "FAIL",
            "providerAuthenticated":True,
            "availableModels":available,
            "modelCount":len(available)
        })

    except urllib.error.HTTPError as exc:

        report.update({
            "status":"FAIL",
            "httpStatus":exc.code,
            "providerAuthenticated":False
        })

    except Exception as exc:

        report.update({
            "status":"FAIL",
            "errorType":type(exc).__name__,
            "providerAuthenticated":False
        })

    path=ROOT/"reports/groq-provider.json"

    path.write_text(
        json.dumps(report,indent=2)+"\n"
    )

    print(json.dumps(report,indent=2))

    if report["status"]!="PASS":
        raise SystemExit(1)
