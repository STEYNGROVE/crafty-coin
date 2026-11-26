import importlib.util
import json

from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent

def load(name,path):

    spec=importlib.util.spec_from_file_location(
        name,ROOT/path
    )

    module=importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module

privacy=load(
    "crafty_privacy","privacy/engine.py"
)

family=load(
    "crafty_family","family/engine.py"
)

marketplace=load(
    "crafty_marketplace","marketplace/engine.py"
)

gateway=load(
    "crafty_gateway","integrations/gateway.py"
)

class Platform:

    def __init__(self):

        privacy.locks()
        family.verify_locks()
        marketplace.locks()
        gateway.locks()

        self.auth=privacy.Security()
        self.family=family.Family()
        self.market=marketplace.Marketplace()
        self.gateway=gateway.Gateway()

    def bootstrap(self):

        # Fixed synthetic demonstration accounts.
        # Never use this password for real accounts.

        password="Synthetic-Platform-Demo-2026"

        accounts=[
            ("SIM-PARENT","PARENT"),
            ("SIM-TEACHER","TEACHER"),
            ("SIM-LEARNER","LEARNER"),
            ("SIM-CUSTOMER","CUSTOMER"),
            ("SIM-OTHER","CUSTOMER")
        ]

        for user,role in accounts:
            self.auth.register(user,role,password)

        self.family.adult("SIM-PARENT","PARENT")
        self.family.adult("SIM-TEACHER","TEACHER")

        self.family.learner(
            "SIM-LEARNER",10,"SIM-PARENT"
        )

        for user in ("SIM-CUSTOMER","SIM-OTHER"):
            self.market.register(user,30)
            self.gateway.register(user,30)

        return {
            user:self.auth.login(user,password)
            for user,role in accounts
        }

    def identity(self,token,domain,roles):

        return self.auth.authorize(
            token,domain,set(roles)
        )["id"]

    def parent_grant(self,token,learner,teacher):

        parent=self.identity(
            token,"EDUCATION",["PARENT"]
        )

        self.family.grant(parent,learner,teacher)

    def parent_revoke(self,token,learner,teacher):

        parent=self.identity(
            token,"EDUCATION",["PARENT"]
        )

        self.family.revoke(parent,learner,teacher)

    def learning_record(self,token,learner,activity):

        parent=self.identity(
            token,"EDUCATION",["PARENT"]
        )

        self.family.record(parent,learner,activity)

    def learning_report(self,token,learner):

        requester=self.identity(
            token,"EDUCATION",["PARENT","TEACHER"]
        )

        return self.family.report(requester,learner)

    def market_order(self,token,reference,product):

        customer=self.identity(
            token,"ADULT",["CUSTOMER"]
        )

        self.market.order(
            reference,customer,product
        )

    def market_activate(self,token,reference):

        customer=self.identity(
            token,"ADULT",["CUSTOMER"]
        )

        self.market.simulate(reference,customer)

    def market_cancel(self,token,reference):

        customer=self.identity(
            token,"ADULT",["CUSTOMER"]
        )

        self.market.cancel(reference,customer)

    def market_access(self,token,product):

        customer=self.identity(
            token,"ADULT",["CUSTOMER"]
        )

        return self.market.access(customer,product)

    def service_draft(
        self,token,reference,service,amount
    ):

        customer=self.identity(
            token,"ADULT",["CUSTOMER"]
        )

        self.gateway.draft(
            reference,customer,service,amount
        )

    def service_review(self,token,reference):

        customer=self.identity(
            token,"ADULT",["CUSTOMER"]
        )

        self.gateway.review(reference,customer)

    def dashboard(self,token,domain):

        if domain=="ADULT":

            customer=self.identity(
                token,"ADULT",["CUSTOMER"]
            )

            return {
                "mode":"SIMULATION_ONLY",
                "domain":"ADULT",
                "marketplace":self.market.summary(
                    customer
                ),
                "services":self.gateway.summary(
                    customer
                ),
                "actualRevenueZAR":0
            }

        if domain=="EDUCATION":

            self.identity(
                token,"EDUCATION",
                ["PARENT","TEACHER","LEARNER"]
            )

            return {
                "mode":"SIMULATION_ONLY",
                "domain":"EDUCATION",
                "guide":"Crafty",
                "financialRewards":0,
                "cryptoRewards":0
            }

        raise PermissionError("Unknown domain")

    def financial_activation(self,*args):

        raise PermissionError(
            "Financial activation locked"
        )

    def close(self):

        self.auth.close()
        self.family.close()
        self.market.close()
        self.gateway.close()
