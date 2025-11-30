"""
FastAPI WebSocket Server for Real-time Voice Assistant
Minimal async - only what's required by FastAPI
"""

import sys
import os
import hmac
import hashlib

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException, Request
from fastapi.responses import FileResponse
from typing import Dict
from dotenv import load_dotenv
import json

from elevenlabs_integration.voice_service import stream_tts_websocket
from openai_integration.agent import AppointmentAgent

load_dotenv()

app = FastAPI(title="Voice Assistant WebSocket Server")

active_agents: Dict[int, AppointmentAgent] = {}

ELEVENLABS_WEBHOOK_SECRET = os.getenv("ELEVENLABS_WEBHOOK_SECRET")


def verify_elevenlabs_signature(payload: bytes, signature: str) -> bool:
    """Sync function - no async needed"""
    if not ELEVENLABS_WEBHOOK_SECRET:
        return True 
    
    expected_signature = hmac.new(
        ELEVENLABS_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)


@app.get("/")
async def get_homepage():
    """MUST be async - FastAPI requirement"""
    html_path = os.path.join(os.path.dirname(__file__), "voice.html")
    return FileResponse(html_path)


@app.websocket("/websocket")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    session_id = id(websocket)
    agent = AppointmentAgent()
    active_agents[session_id] = agent
    
    print(f"[INFO] New WebSocket connection: {session_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "user_message":
                user_text = message.get("text", "")
                print(f"[INFO] User said: {user_text}")
                
                await websocket.send_text(json.dumps({
                    "type": "status",
                    "message": "Processing your request..."
                }))
                
                full_response = await agent.process_message(user_text)
                
                print(f"[INFO] OpenAI response: {full_response[:100]}...")
                
                await websocket.send_text(json.dumps({
                    "type": "assistant_message",
                    "text": full_response
                }))
                
                async def audio_callback(audio_chunk: bytes):
                    await websocket.send_bytes(audio_chunk)
                
                async def text_generator():
                    yield full_response
                
                # Stream TTS - MUST await
                await stream_tts_websocket(text_generator(), audio_callback)
                
                print(f"[INFO] Audio streaming complete")
                
    except WebSocketDisconnect:
        print(f"[INFO] WebSocket disconnected: {session_id}")
    except Exception as e:
        print(f"[ERROR] WebSocket error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup - sync operation
        if session_id in active_agents:
            del active_agents[session_id]
        print(f"[INFO] Cleaned up session: {session_id}")


@app.post("/webhook")
async def elevenlabs_webhook(
    request: Request,
    x_elevenlabs_signature: str = Header(None)
):
    body = await request.body()
    
    if x_elevenlabs_signature:
        if not verify_elevenlabs_signature(body, x_elevenlabs_signature):
            print("[ERROR] Invalid webhook signature!")
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    data = json.loads(body)
    print(f"[WEBHOOK] Received: {json.dumps(data, indent=2)}")
    
    event_type = data.get("type")
    
    if event_type == "tool_call":
        tool_name = data.get("tool_name")
        parameters = data.get("parameters", {})
        
        from tools import execute_function_call
        # If this is sync, no await needed
        result = execute_function_call(tool_name, parameters)
        
        return {"success": True, "result": result}
    
    return {"success": True}


@app.get("/health")
async def health_check():
    
    return {
        "status": "healthy",
        "active_connections": len(active_agents)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
