from fastapi import FastAPI, Request, Response
import httpx
import os

app = FastAPI(redirect_slashes=False)

AUTH_URL   = os.environ["AUTH_SERVICE_URL"]
PLAYER_URL = os.environ["PLAYER_SERVICE_URL"]
GAME_URL   = os.environ["GAME_SERVICE_URL"]

CA_CERT = "/certs/ca.crt"

client = httpx.AsyncClient(
    verify=CA_CERT,
    timeout=10.0
)

async def proxy(request: Request, target_url: str, path: str):
    url = f"{target_url}/{path}"
    if request.url.query:
        url += f"?{request.url.query}"

    body = await request.body()

    headers = dict(request.headers)
    headers.pop("host", None)

    resp = await client.request(
        method=request.method,
        url=url,
        headers=headers,
        content=body
    )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=dict(resp.headers)
    )

@app.api_route("/auth/{path:path}", methods=["GET","POST","PUT","DELETE"])
async def auth_proxy(request: Request, path: str):
    return await proxy(request, AUTH_URL, path)

@app.api_route("/player/{path:path}", methods=["GET","POST","PUT","DELETE"])
async def player_proxy(request: Request, path: str):
    return await proxy(request, PLAYER_URL, path)

@app.api_route("/game/{path:path}", methods=["GET","POST","PUT","DELETE"])
async def game_proxy(request: Request, path: str):
    return await proxy(request, GAME_URL, path)
