import json
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer
)
from core import VISION,verify_locks

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            verify_locks()

            routes={
                "/health":{
                    "status":"ok",
                    "mode":"SIMULATION_ONLY",
                    "payments":False,
                    "mainnet":False
                },
                "/v1/character":VISION["character"],
                "/v1/academies":VISION["academies"],
                "/v1/superheroes":VISION["superheroes"],
                "/v1/applications":VISION["applications"],
                "/v1/pathways":VISION["pathways"],
                "/v1/languages":VISION["languages"]
            }

            if self.path not in routes:
                self.send_error(404)
                return

            body=json.dumps(
                routes[self.path]
            ).encode()

            self.send_response(200)
            self.send_header(
                "Content-Type","application/json"
            )
            self.send_header(
                "Cache-Control","no-store"
            )
            self.send_header(
                "Content-Length",str(len(body))
            )
            self.end_headers()
            self.wfile.write(body)

        except Exception:
            self.send_error(503)

    def do_POST(self):
        self.send_error(405)

def create_server(port=8090):
    return ThreadingHTTPServer(
        ("127.0.0.1",port),Handler
    )

if __name__=="__main__":
    server=create_server()
    print("CRAFTY CORE: http://127.0.0.1:8090")
    server.serve_forever()
