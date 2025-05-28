from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from gemini_agent import GeminiAgent
from db import Database
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Financial Assistant API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize components
agent = GeminiAgent()
db = Database()


class ChatMessage(BaseModel):
    message: str
    user_id: int


class CreateUserRequest(BaseModel):
    name: str


@app.get("/", response_class=HTMLResponse)
async def get_home():
    with open("templates/index.html") as f:
        return f.read()


@app.post("/api/chat")
async def chat(message: ChatMessage):
    try:
        response = agent.process_message(message.message, message.user_id)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/create_user")
async def create_user(request: CreateUserRequest):
    try:
        user_id = db.add_user(request.name)
        return {"user_id": user_id, "name": request.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
