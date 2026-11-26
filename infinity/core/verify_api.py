import json
import threading
import urllib.request
import urllib.error
from api import create_server

server=create_server(0)

thread=threading.Thread(
    target=server.serve_forever,daemon=True
)

thread.start()

base=f"http://127.0.0.1:{server.server_port}"

try:
    expected={
        "/health":None,
        "/v1/character":None,
        "/v1/academies":22,
        "/v1/superheroes":12,
        "/v1/applications":11,
        "/v1/pathways":4,
        "/v1/languages":4
    }

    for route,count in expected.items():
        with urllib.request.urlopen(
            base+route,timeout=5
        ) as response:
            assert response.status==200
            data=json.load(response)

            if count is not None:
                assert len(data)==count

        print("PASS:",route)

    for route,method,status in [
        ("/v1/payments","GET",404),
        ("/v1/mainnet","GET",404),
        ("/v1/profiles","GET",404),
        ("/v1/character","POST",405)
    ]:
        request=urllib.request.Request(
            base+route,method=method
        )

        try:
            urllib.request.urlopen(
                request,timeout=5
            )
            raise AssertionError("Unsafe route")
        except urllib.error.HTTPError as e:
            assert e.code==status

        print("PASS: Blocked",method,route)

finally:
    server.shutdown()
    server.server_close()
    thread.join()

print("PASS: 11 API checks")
