import streamlit as st
from elevenlabs_integration import (
    speech_to_text_from_bytes,
    text_to_speech
)

from openai_integration.agent import AppointmentAgent

# Page config
st.set_page_config(
    page_title="Voice Assistant",
    page_icon="🎙️",
    layout="centered"
)

# Initialize agent
if "agent" not in st.session_state:
    st.session_state.agent = AppointmentAgent()

# Title
st.title("🎙️ Voice Assistant")

# Record audio
audio_bytes = st.audio_input("Record your message")

if audio_bytes:
    if st.button("▶️ Send", use_container_width=True):
        
        with st.spinner("Processing..."):
            # Speech to Text
            stt_result = speech_to_text_from_bytes(
                audio_bytes.getvalue(),
                filename="audio.wav",
                language_code="en"
            )
            
            if stt_result["status"] == "success":
                user_text = stt_result["text"]
                st.info(f"You said: {user_text}")
                
                # Process with Agent
                agent_response = st.session_state.agent.process_message(user_text)
                st.success(f"Assistant: {agent_response}")
                
                # Text to Speech
                response_audio = text_to_speech(agent_response)
                
                # Play response
                st.audio(response_audio, format="audio/mp3", autoplay=True)
                
            else:
                st.error(f"Error: {stt_result['message']}")
