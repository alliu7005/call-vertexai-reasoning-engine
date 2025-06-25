import os, uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any, List
from vertexai import init as vae_init, agent_engines
from google.adk.sessions import VertexAiSessionService
import urllib
import asyncio
import uvicorn

PROJECT   = os.getenv("PROJECT")
LOCATION  = os.getenv("LOCATION","us-central1")

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
  expose_headers=["Location"],
)


class ChatRequest(BaseModel):
    prompt:     str
    token:      Optional[str]
    session_id: Optional[str]
    user_id:    Optional[str]
    agent_id: str
    
class ChatResponse(BaseModel):
    session_id: str
    response:   str

class LoginRequest(BaseModel):
    scope: Any
    auth_server: str
    user_id: str

vae_init(project=PROJECT, location=LOCATION)

SESSION_SERVICE = VertexAiSessionService(project=PROJECT, location=LOCATION)


@app.post("/login")
def login(req: LoginRequest):
    
    params = {
        "scopes": req.scope,
    }
    qs = urllib.parse.urlencode(params)
    return RedirectResponse(
        f"{req.auth_server}/login?{qs}"
    )

@app.post("/chat")
def chat(req: ChatRequest):
    app_name=f"projects/{PROJECT}/locations/{LOCATION}/reasoningEngines/{req.agent_id}"
    remote_app = agent_engines.get(app_name)
    user_id = req.user_id
    if not req.session_id:
        session = asyncio.run(SESSION_SERVICE.create_session(app_name=app_name, user_id=user_id))
        session_id = session.id
    else:
        session_id = req.session_id
    
    print(session_id)
    reply = remote_app.query(input=req.prompt,
        config={
            "metadata": {"spotify_token": req.token},
            "configurable": {"session_id": session_id}
        }
    )
    
    return ChatResponse(session_id=session_id, response=reply)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)