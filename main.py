import os, uuid
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any, List
from vertexai import init as vae_init, agent_engines
from google.adk.sessions import VertexAiSessionService
import urllib
import asyncio
import uvicorn
from google import auth as google_auth
from google.auth.transport import requests as google_requests
from google.oauth2 import service_account
from google.cloud import secretmanager
import json
from vertexai.preview import reasoning_engines
import requests

PROJECT_ID = "agentcore-465415"
#PROJECT_NUMBER = os.getenv("GOOGLE_CLOUD_PROJECT_NUMBER")
LOCATION  = "us-central1"
STAGING_BUCKET = "gs://vertexai-storage-bucket"

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
    token:      Optional[str] = None
    session_id: Optional[str] = None
    user_id:    Optional[str] = None
    agent_id: str
    
class ChatResponse(BaseModel):
    session_id: str
    response:   Any

class LoginRequest(BaseModel):
    scope: Any
    auth_server: str
    return_window: str

#vae_init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

SESSION_SERVICE = VertexAiSessionService(project=PROJECT_ID, location=LOCATION)


@app.get("/login")
def login(req: LoginRequest = Depends()):
    
    params = {
        "scopes": req.scope,
        "return_url": req.return_window
    }
    qs = urllib.parse.urlencode(params)
    return RedirectResponse(
        f"{req.auth_server}/login?{qs}"
    )

@app.post("/chat")
def chat(req: ChatRequest):
    app_name=req.agent_id
    print("APPNAME:", app_name)

    remote_app = agent_engines.get(app_name)
    print("Calling engine under:", remote_app.resource_name)
    user_id = req.user_id
    if not req.session_id:
        session = asyncio.run(SESSION_SERVICE.create_session(app_name=app_name, user_id=user_id))
        session_id = session.id
    else:
        session_id = req.session_id
    
    print("SESSION_ID:",session_id)
    print("REMOTE_APP:", remote_app.project, remote_app.to_dict())
    payload = (
        f"OAuth token: {req.token}\n\n"
        f"{req.prompt}"
    )

    reply = remote_app.query(input=payload,
        config={
            "configurable": {"session_id": session_id}
        }
    )

    
    
    return ChatResponse(session_id=session_id, response=reply)

if __name__ == "__main__":
    #port = int(os.getenv("PORT", "8000"))

    vae_init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)
    from google.cloud.aiplatform import initializer
    print(vars(initializer.global_config))
    def get_identity_token():
        credentials, _ = google_auth.default()
        auth_request = google_requests.Request()
        credentials.refresh(auth_request)
        return credentials.token
    
    reasoning_engine_list = reasoning_engines.ReasoningEngine.list()
    print(reasoning_engine_list)
    response = requests.get(
    "https://us-central1-aiplatform.googleapis.com/v1/projects/agentcore-465415/locations/us-central1/reasoningEngines/4868980535419994112",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {get_identity_token()}",
        },
    )
    response.raise_for_status()
    print(json.loads(response.content).get("spec").get("classMethods"))

    resp = requests.post(
        f"https://us-central1-aiplatform.googleapis.com/v1/projects/agentcore-465415/locations/us-central1/reasoningEngines/4868980535419994112:query",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {get_identity_token()}",
        },
        data=json.dumps({
            "class_method": "query",
            "input": {
                "input": "Give me 5 Radiohead recommendations."
            }
        })
    )

    resp.raise_for_status()
    print(json.loads(resp.content))

    #agent = agent_engines.get("projects/agentcore-465415/locations/us-central1/reasoningEngines/4868980535419994112")
    #print(agent.operation_schemas())

    #agent.query(input="Give me 5 Radiohead recommendations")

    #uvicorn.run("main:app", host="0.0.0.0", port=port)
