import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
import importlib.util
from pathlib import Path
from http.server import HTTPServer

ROOT=Path(__file__).resolve().parents[1]

sys.path.insert(0,str(ROOT/"backend"))

class Tests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.tmp=tempfile.TemporaryDirectory()

        original_home=os.environ.get("HOME")
        os.environ["HOME"]=cls.tmp.name

        try:
            spec=importlib.util.spec_from_file_location(
                "crafty_http",
                ROOT/"backend/server.py"
            )

            cls.module=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.module)

        finally:
            if original_home is None:
                os.environ.pop("HOME",None)
            else:
                os.environ["HOME"]=original_home

        cls.module.app.close()

        cls.server=HTTPServer(
            ("127.0.0.1",0),
            cls.module.Handler
        )

        port=cls.server.server_address[1]

        cls.module.PORT=port
        cls.module.ORIGIN=f"http://127.0.0.1:{port}"

        cls.origin=cls.module.ORIGIN

        cls.ready=threading.Event()
        cls.failure=None

        def serve():
            try:
                cls.module.app=cls.module.Learning(
                    Path(cls.tmp.name)/"http-test"
                )

                cls.ready.set()
                cls.server.serve_forever()

            except Exception as exc:
                cls.failure=exc
                cls.ready.set()

            finally:
                cls.module.app.close()

        cls.thread=threading.Thread(
            target=serve,daemon=True
        )

        cls.thread.start()

        if not cls.ready.wait(10):
            raise RuntimeError("Server startup timeout")

        if cls.failure:
            raise cls.failure

        status,data,_=cls.request("/api/session")

        assert status==200

        cls.token=data["token"]

    @classmethod
    def tearDownClass(cls):

        cls.server.shutdown()
        cls.thread.join(timeout=10)
        cls.server.server_close()
        cls.tmp.cleanup()

    @classmethod
    def request(
        cls,path,body=None,headers=None,
        raw=None,method=None
    ):

        h=dict(headers or {})

        if body is not None:
            raw=json.dumps(body).encode()
            h.setdefault(
                "Content-Type","application/json"
            )

        request=urllib.request.Request(
            cls.origin+path,
            data=raw,
            headers=h,
            method=method
        )

        try:
            response=urllib.request.urlopen(
                request,timeout=10
            )

        except urllib.error.HTTPError as exc:
            response=exc

        with response:

            payload=response.read()

            if "application/json" in response.headers.get(
                "Content-Type",""
            ):
                payload=json.loads(payload)

            return (
                response.status,
                payload,
                response.headers
            )

    def auth(self):
        return {
            "X-Crafty-Session":self.token,
            "Origin":self.origin
        }

    def post(self,path,body):
        return self.request(
            path,body,headers=self.auth()
        )

    def test_01_health(self):
        status,data,_=self.request("/api/health")
        self.assertEqual(status,200)
        self.assertEqual(data["connectedEngines"],3)

    def test_02_financial_lock(self):
        _,data,_=self.request("/api/health")
        self.assertFalse(data["financialOperations"])

    def test_03_session(self):
        status,data,headers=self.request("/api/session")
        self.assertEqual(status,200)
        self.assertGreater(len(data["token"]),30)
        self.assertEqual(headers["Cache-Control"],"no-store")

    def test_04_missing_token(self):
        status,_,_=self.request("/api/progress")
        self.assertEqual(status,403)

    def test_05_invalid_token(self):
        status,_,_=self.request(
            "/api/progress",
            headers={"X-Crafty-Session":"invalid"}
        )
        self.assertEqual(status,403)

    def test_06_progress(self):
        status,data,_=self.request(
            "/api/progress?pathway=DISCOVER",
            headers=self.auth()
        )
        self.assertEqual(status,200)
        self.assertEqual(data["available"],46)

    def test_07_invalid_pathway(self):
        status,_,_=self.request(
            "/api/progress?pathway=ADULT",
            headers=self.auth()
        )
        self.assertEqual(status,400)

    def test_08_missing_origin(self):
        status,_,_=self.request(
            "/api/reset",
            {"pathway":"DISCOVER"},
            headers={
                "X-Crafty-Session":self.token
            }
        )
        self.assertEqual(status,403)

    def test_09_wrong_origin(self):
        headers=self.auth()
        headers["Origin"]="https://example.invalid"

        status,_,_=self.request(
            "/api/reset",
            {"pathway":"DISCOVER"},
            headers=headers
        )
        self.assertEqual(status,403)

    def test_10_wrong_host(self):
        status,_,_=self.request(
            "/api/health",
            headers={"Host":"example.invalid"}
        )
        self.assertEqual(status,403)

    def test_11_academy_completion(self):
        status,data,_=self.post(
            "/api/complete",
            {
                "pathway":"DISCOVER",
                "mission":"ACA-01-DISCOVER"
            }
        )
        self.assertEqual(status,200)
        self.assertIn(
            "ACA-01-DISCOVER",data["completed"]
        )

    def test_12_wrong_age_mission(self):
        status,_,_=self.post(
            "/api/complete",
            {
                "pathway":"DISCOVER",
                "mission":"ACA-01-FUTURE"
            }
        )
        self.assertEqual(status,400)

    def test_13_virtual_decision(self):
        status,data,_=self.post(
            "/api/decide",
            {
                "pathway":"DISCOVER",
                "action":"GARDEN"
            }
        )
        self.assertEqual(status,200)
        self.assertEqual(data["cashValue"],0)

    def test_14_invalid_decision(self):
        status,_,_=self.post(
            "/api/decide",
            {
                "pathway":"DISCOVER",
                "action":"UNKNOWN"
            }
        )
        self.assertEqual(status,400)

    def test_15_malformed_json(self):
        headers=self.auth()
        headers["Content-Type"]="application/json"

        status,_,_=self.request(
            "/api/reset",
            raw=b"{invalid",
            headers=headers
        )
        self.assertEqual(status,400)

    def test_16_oversized_body(self):
        headers=self.auth()
        headers["Content-Type"]="application/json"

        status,_,_=self.request(
            "/api/reset",
            raw=b"x"*5000,
            headers=headers
        )
        self.assertEqual(status,400)

    def test_17_wrong_content_type(self):
        headers=self.auth()
        headers["Content-Type"]="text/plain"

        status,_,_=self.request(
            "/api/reset",
            raw=b"test",
            headers=headers
        )
        self.assertEqual(status,415)

    def test_18_unknown_route(self):
        status,_,_=self.request("/api/unknown")
        self.assertEqual(status,404)

    def test_19_financial_route_denied(self):
        status,_,_=self.post(
            "/api/payment",
            {"pathway":"DISCOVER"}
        )
        self.assertEqual(status,404)

    def test_20_static_application(self):
        status,data,_=self.request("/index.html")
        self.assertEqual(status,200)
        self.assertIn(b"University of Life",data)

    def test_21_original_artwork(self):
        status,data,_=self.request(
            "/assets/crafty-master.webp"
        )
        self.assertEqual(status,200)
        self.assertEqual(data[:4],b"RIFF")
        self.assertEqual(data[8:12],b"WEBP")

    def test_22_security_headers(self):
        _,_,headers=self.request("/index.html")
        self.assertEqual(
            headers["X-Content-Type-Options"],
            "nosniff"
        )
        self.assertIn(
            "frame-ancestors 'none'",
            headers["Content-Security-Policy"]
        )

    def test_23_reset(self):
        status,data,_=self.post(
            "/api/reset",
            {"pathway":"DISCOVER"}
        )
        self.assertEqual(status,200)
        self.assertEqual(data["count"],0)

    def test_24_pathway_isolation(self):
        status,data,_=self.request(
            "/api/progress?pathway=FUTURE",
            headers=self.auth()
        )
        self.assertEqual(status,200)
        self.assertEqual(data["count"],0)

if __name__=="__main__":
    unittest.main(verbosity=2)
