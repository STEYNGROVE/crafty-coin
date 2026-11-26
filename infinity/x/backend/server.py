import json
import secrets
import os
from pathlib import Path
from http.server import HTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlparse,parse_qs

from engine import Learning,verify_locks

os.umask(0o077)

HOST="127.0.0.1"
PORT=8096
ORIGIN=f"http://{HOST}:{PORT}"

ROOT=Path(__file__).resolve().parent.parent

DATABASE=(
    Path.home()/".local/share/crafty-infinity/learning"
)

TOKEN=secrets.token_urlsafe(32)

app=Learning(DATABASE)

class Handler(SimpleHTTPRequestHandler):

    def __init__(self,*args,**kwargs):
        super().__init__(
            *args,
            directory=str(ROOT/"learning"),
            **kwargs
        )

    def end_headers(self):
        self.send_header(
            "X-Content-Type-Options","nosniff"
        )
        self.send_header(
            "Referrer-Policy","no-referrer"
        )
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; object-src 'none'; "
            "frame-ancestors 'none'; base-uri 'none'"
        )
        super().end_headers()

    def reply(self,data,status=200):
        payload=json.dumps(data).encode()
        self.send_response(status)
        self.send_header(
            "Content-Type","application/json"
        )
        self.send_header(
            "Cache-Control","no-store"
        )
        self.send_header(
            "Content-Length",str(len(payload))
        )
        self.end_headers()
        self.wfile.write(payload)

    def valid_host(self):
        return self.headers.get("Host")==f"{HOST}:{PORT}"

    def do_GET(self):

        if not self.valid_host():
            self.reply({"error":"Host denied"},403)
            return

        url=urlparse(self.path)

        if not url.path.startswith("/api/"):
            return super().do_GET()

        try:
            verify_locks()

            if url.path=="/api/session":
                return self.reply({
                    "token":TOKEN,
                    "mode":"LOCAL_SYNTHETIC"
                })

            if url.path=="/api/health":
                return self.reply({
                    "status":"OK",
                    "connectedEngines":3,
                    "financialOperations":False
                })

            if url.path=="/api/progress":

                if self.headers.get("X-Crafty-Session")!=TOKEN:
                    return self.reply({"error":"Denied"},403)

                pathway=parse_qs(url.query).get(
                    "pathway",["DISCOVER"]
                )[0]

                return self.reply(
                    app.progress(pathway)
                )

            self.reply({"error":"Unknown route"},404)

        except (ValueError,PermissionError):
            self.reply({"error":"Request denied"},400)

    def do_POST(self):

        if (
            not self.valid_host()
            or self.headers.get("Origin")!=ORIGIN
            or self.headers.get("X-Crafty-Session")!=TOKEN
        ):
            return self.reply({"error":"Denied"},403)

        if self.headers.get("Content-Type")!="application/json":
            return self.reply({"error":"JSON required"},415)

        try:
            size=int(
                self.headers.get("Content-Length","0")
            )

            if not 0<size<=4096:
                return self.reply(
                    {"error":"Invalid request size"},400
                )

            body=json.loads(self.rfile.read(size))

            if not isinstance(body,dict):
                raise ValueError("Invalid body")

            pathway=body["pathway"]

            if self.path=="/api/complete":
                result=app.complete(
                    pathway,
                    body["mission"],
                    body.get("difficulty",1)
                )

            elif self.path=="/api/decide":
                result=app.decide(
                    pathway,body["action"]
                )

            elif self.path=="/api/reset":
                result=app.reset(pathway)

            else:
                return self.reply(
                    {"error":"Unknown route"},404
                )

            self.reply(result)

        except (
            ValueError,KeyError,TypeError,
            PermissionError
        ):
            self.reply({"error":"Request denied"},400)

        except Exception:
            self.reply({"error":"Local operation failed"},500)

if __name__=="__main__":

    print("CRAFTY LOCAL LEARNING SERVER")
    print(ORIGIN)
    print("Synthetic profiles only")
    print("Financial operations locked")

    server=HTTPServer((HOST,PORT),Handler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        app.close()
