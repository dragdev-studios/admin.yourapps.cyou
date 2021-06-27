from fastapi import FastAPI, HTTPException, Depends
from fastapi import responses
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse
from httpx import get, post
from os import urandom, getenv, environ
from base64 import b64encode
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List

load_dotenv()
environ.setdefault("LOGS_USERNAME", "No-Username")
environ.setdefault("LOGS_PASSWORD", "No-Password")
environ.setdefault("ALLOW_USERNAME_CHANGES", "false")
environ.setdefault("ALLOW_PASSWORD_CHANGES", "false")
environ.setdefault("ADMIN_USERNAME", "admin")
environ.setdefault("ADMIN_PASSWORD", "0001")

from accounts import Account, AccessLevel, login


class ReloadModel(BaseModel):
    cogs: List[str]



app = FastAPI()


@app.get("/logs.txt")
def get_logs(mode: str = "error"):
    cachebuster = b64encode(urandom(64)).decode("utf-8")
    response = get(
        f"https://122.logs.clicksminuteper.net/yourapps-{mode}.log?cachebuster={cachebuster}",
        auth=(getenv("LOGS_USERNAME"), getenv("LOGS_PASSWORD"))
    )
    if response.status_code != 200:
        raise HTTPException(
            response.status_code,
            response.text,
            dict(response.headers)
        )
    else:
        return PlainTextResponse(response.text)


@app.post("/reload-cogs")
def reload_cogs(body: ReloadModel, authorization: Account = Depends(login("Safe", AccessLevel.MODERATOR))):
    response = post(
        "https://api.yourapps.cyou/admin/reload",
        json=body.json()
    )
    # return PlainTextResponse(response.text, response.status_code)
    return PlainTextResponse("OK", 200)


@app.post("/reboot")
def reload_cogs(authorization: Account = Depends(login("Unsafe", AccessLevel.ADMINISTRATOR))):
    response = post(
        "https://api.yourapps.cyou/admin/reload"
    )
    # return PlainTextResponse(response.text, response.status_code)
    return PlainTextResponse("OK", 200)



app.mount("/", StaticFiles(directory="./static", html=True))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port="8008", lifespan="on")
