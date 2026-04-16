from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import google.generativeai as genai
import os
from datetime import datetime
import uuid

# إعداد Gemini
API_KEY = "AIzaSyBnUf97bdEt_WlLdC79LNX1lqRak1d5s_Y"
genai.configure(api_key=API_KEY)

app = FastAPI(title="Family History Chatbot")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = genai.GenerativeModel("gemini-1.5-flash")
chat_sessions = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str = None

@app.get("/")
def home():
    return {
        "message": "✅ Family History Chatbot شغال!",
        "status": "active",
        "endpoints": ["/test", "/sessions", "/chat", "/stats", "/helper.html"]
    }

@app.get("/test")
def test():
    return {
        "status": "ok",
        "message": "✅ Test ناجح!",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/sessions")
def get_sessions():
    return {
        "total": len(chat_sessions),
        "sessions": list(chat_sessions.keys())[:5]
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        if session_id not in chat_sessions:
            chat_sessions[session_id] = model.start_chat(history=[])
        
        response = chat_sessions[session_id].send_message(request.message)
        
        return {
            "reply": response.text,
            "session_id": session_id,
            "status": "success"
        }
    except Exception as e:
        return {
            "reply": f"خطأ: {str(e)}",
            "session_id": request.session_id,
            "status": "error"
        }

@app.get("/stats")
def get_stats():
    return {
        "total_sessions": len(chat_sessions),
        "total_messages": sum(1 for _ in chat_sessions.keys())
    }

@app.get("/helper.html", response_class=HTMLResponse)
async def get_helper():
    try:
        with open("helper.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except:
        return HTMLResponse(content="<h1>ملف helper.html مش موجود</h1>")

# ===== مهم: أضف السطرين دول =====
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)