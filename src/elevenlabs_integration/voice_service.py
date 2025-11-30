import os
import asyncio
import websockets
import json
import base64
from typing import Optional, Dict, Any, AsyncIterator, Callable
import requests
from dotenv import load_dotenv

load_dotenv()

# ElevenLabs Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")
ELEVENLABS_STT_MODEL = os.getenv("ELEVENLABS_STT_MODEL", "scribe_v1")

# API Endpoints
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"


def text_to_speech(
    text: str,
    voice_id: Optional[str] = None,
    model: Optional[str] = None,
    stability: float = 0.5,
    similarity_boost: float = 0.75
) -> bytes:

    voice_id = voice_id or ELEVENLABS_VOICE_ID
    model = model or ELEVENLABS_MODEL
    
    url = f"{ELEVENLABS_API_URL}/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    data = {
        "text": text,
        "model_id": model,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] ElevenLabs TTS error: {e}")
        raise


def speech_to_text_from_bytes(
    audio_data,
    filename: str = "audio.mp3",
    model: Optional[str] = None,
    language_code: Optional[str] = None,
) -> Dict[str, Any]:
    """Original STT - kept for compatibility"""
    model = model or ELEVENLABS_STT_MODEL
    url = f"{ELEVENLABS_API_URL}/speech-to-text"
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    files = {
        "file": (filename, audio_data, "audio/mpeg")
    }
    
    data = {
        "model_id": model
    }
    
    if language_code:
        data["language_code"] = language_code
    
    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        result = response.json()
        
        return {
            "status": "success",
            "text": result.get("text", ""),
            "language": result.get("language", ""),
            "duration": result.get("duration"),
            "full_response": result
        }
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] ElevenLabs STT error: {e}")
        
        if hasattr(e, 'response') and e.response is not None:
            print(f"[ERROR] Response: {e.response.text}")
        return {
            "status": "error",
            "message": str(e),
            "text": ""
        }


async def text_chunker(chunks: AsyncIterator[str]) -> AsyncIterator[str]:

    splitters = (".", ",", "?", "!", ";", ":", "—", "-", "(", ")", "[", "]", "}", " ")
    buffer = ""
    
    async for text in chunks:
        if not text:
            continue
            
        if buffer.endswith(splitters):
            yield buffer + " "
            buffer = text
        elif text.startswith(splitters):
            output = buffer + text[0] + " "
            yield output
            buffer = text[1:]
        else:
            buffer += text
    
    if buffer:
        yield buffer + " "


async def stream_tts_websocket(
    text_iterator: AsyncIterator[str],
    audio_callback: Callable[[bytes], None],
    voice_id: Optional[str] = None,
    stability: float = 0.5,
    similarity_boost: float = 0.8,
    model: str = "eleven_turbo_v2"
):

    voice_id = voice_id or ELEVENLABS_VOICE_ID
    uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input?model_id={model}"
    
    print(f"[INFO] Connecting to ElevenLabs WebSocket...")
    
    try:
        async with websockets.connect(uri) as websocket:
            # Send initial configuration
            initial_message = {
                "text": " ",
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost
                },
                "xi_api_key": ELEVENLABS_API_KEY,
            }
            
            await websocket.send(json.dumps(initial_message))
            print("[INFO] WebSocket connected and initialized")
            
            async def receive_audio():
                try:
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        
                        if data.get("audio"):
                            audio_chunk = base64.b64decode(data["audio"])
                            if asyncio.iscoroutinefunction(audio_callback):
                                await audio_callback(audio_chunk)
                            else:
                                audio_callback(audio_chunk)
                            print(f"[DEBUG] Received audio chunk: {len(audio_chunk)} bytes")
                        
                        if data.get("isFinal"):
                            print("[INFO] Final audio chunk received")
                            break
                            
                except websockets.exceptions.ConnectionClosed:
                    print("[INFO] Audio reception completed")
            
            receive_task = asyncio.create_task(receive_audio())
            
            chunk_count = 0
            async for text_chunk in text_chunker(text_iterator):
                chunk_count += 1
                message = {
                    "text": text_chunk,
                    "try_trigger_generation": True
                }
                await websocket.send(json.dumps(message))
                print(f"[DEBUG] Sent text chunk {chunk_count}: {text_chunk[:50]}...")
            
            await websocket.send(json.dumps({"text": ""}))
            print("[INFO] End-of-stream signal sent")
            
            await receive_task
            print("[INFO] Streaming completed successfully")
            
    except Exception as e:
        print(f"[ERROR] WebSocket streaming error: {e}")
        raise



async def test_streaming():
    """Test the streaming functionality"""
    
    async def mock_text_generator():
        """Simulate OpenAI streaming response"""
        sentences = [
            "Hello! ",
            "I can help you ",
            "schedule an appointment ",
            "at the KVR office. ",
            "What would you like to do today?"
        ]
        for sentence in sentences:
            await asyncio.sleep(0.3) 
            yield sentence
    
    audio_chunks = []
    
    async def audio_handler(chunk: bytes):
        audio_chunks.append(chunk)
        print(f"[TEST] Received {len(chunk)} bytes of audio")
    
    print("[TEST] Starting streaming test...")
    await stream_tts_websocket(mock_text_generator(), audio_handler)
    
    # Save combined audio
    if audio_chunks:
        with open("test_output.mp3", "wb") as f:
            f.write(b"".join(audio_chunks))
        print(f"[TEST] Saved {len(audio_chunks)} chunks to test_output.mp3")


if __name__ == "__main__":
    asyncio.run(test_streaming())
