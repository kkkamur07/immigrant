"""
ElevenLabs Voice Service
Handles both text-to-speech and speech-to-text using ElevenLabs API
"""

import os
from typing import Optional, Dict, Any
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
    
    model = model or ELEVENLABS_STT_MODEL
    url = f"{ELEVENLABS_API_URL}/speech-to-text"
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    # Fix: Use 'file' instead of 'audio'
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
