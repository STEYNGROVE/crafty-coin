import json
import urllib.request
import urllib.error
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

SITES={
    "github_pages":
        "https://steyngrove.github.io/pixelpunk/",
    "cloudflare_pages":
        "https://pixelpunk.pages.dev/"
}

SERVICES={
    "WEBSITE_DESIGN":"Website design",
    "AI_WEBSITE":"AI website development",
    "ECOMMERCE":"E-commerce development",
    "SEO":"Search engine optimization",
    "MAINTENANCE":"Website maintenance",
    "AUTOMATION":"Business automation",
    "BRANDING":"Digital branding",
    "HOSTING_SETUP":"Hosting configuration"
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
        "paidAdvertisingEnabled",
        "paidInfrastructureEnabled"
    ):
        if policy.get(flag) is not False:
            raise PermissionError(flag)

def verify_sites():
    locks()
    results={}

    for name,url in SITES.items():
        try:
            request=urllib.request.Request(
                url,
                headers={
                    "User-Agent":"Crafty-Infinity/1.0"
                }
            )

            with urllib.request.urlopen(
                request,timeout=20
            ) as response:

                body=response.read(524288)

                results[name]={
                    "url":url,
                    "httpStatus":response.status,
                    "reachable":response.status==200,
                    "brandMarkerPresent":
                        b"pixelpunk" in body.lower()
                }

        except urllib.error.HTTPError as exc:
            results[name]={
                "url":url,
                "httpStatus":exc.code,
                "reachable":False
            }

        except Exception as exc:
            results[name]={
                "url":url,
                "reachable":False,
                "errorType":type(exc).__name__
            }

    return results

def draft(age,service,description):
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

    return {
        "provider":"PIXELPUNK",
        "service":service,
        "serviceName":SERVICES[service],
        "description":description,
        "domain":"ADULT",
        "status":"LOCAL_DRAFT",
        "submitted":False,
        "bindingQuote":False,
        "paymentRequired":False,
        "actualExpenditureZAR":0
    }

def submit(*args,**kwargs):
    raise PermissionError("Submission disabled")

def publish(*args,**kwargs):
    raise PermissionError("Publishing disabled")

def purchase(*args,**kwargs):
    raise PermissionError("Purchases disabled")

def child_data(*args,**kwargs):
    raise PermissionError("Child data access denied")

if __name__=="__main__":
    sites=verify_sites()

    verified=sum(
        item["reachable"] and
        item.get("brandMarkerPresent",False)
        for item in sites.values()
    )

    report={
        "phase":36,
        "provider":"PIXELPUNK",
        "mode":"READ_ONLY_AND_LOCAL_DRAFT",
        "status":"PASS" if verified==2 else "PARTIAL",
        "websites":sites,
        "verifiedWebsites":verified,
        "registeredServices":len(SERVICES),
        "liveCustomerSubmissions":0,
        "automaticPublishing":False,
        "childDataAccess":False,
        "realPaymentsEnabled":False,
        "actualExpenditureZAR":0,
        "productionReadiness":"NO_GO"
    }

    (ROOT/"reports/pixelpunk.json").write_text(
        json.dumps(report,indent=2)+chr(10)
    )

    print(json.dumps(report,indent=2))
