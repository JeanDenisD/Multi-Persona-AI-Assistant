"""
Voice Manager - Text-to-Speech and Speech-to-Text Integration
Using ElevenLabs Python SDK (official API structure)
"""

import os
import base64
from typing import Dict, Optional
import gradio as gr

from elevenlabs.client import ElevenLabs


class VoiceManager:
    """
    Voice manager using ElevenLabs Python SDK
    """
    
    def __init__(self):
        self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        
        # Voice mapping for each personality - replace with your chosen voice IDs
        self.personality_voices = {
            "networkchuck": "21m00Tcm4TlvDq8ikWAM",  # Replace with your chosen voice IDs
            "bloomy": "AZnzlk1XvdvUeBnXmlld",       # Rachel
            "ethicalhacker": "EXAVITQu4vr4xnSDxMaL",  # Sarah
            "patientteacher": "ThT5KcBeYPX3keUQqHPh", # Dorothy
            "startupfounder": "29vD33N1CtxCmqQRPOHJ", # Drew
            "datascientist": "XB0fDUnXU5powFXDhCwa"   # Charlotte
        }
        
        # Initialize ElevenLabs client (using official API structure)
        if self.elevenlabs_api_key:
            self.client = ElevenLabs(api_key=self.elevenlabs_api_key)
            print("✅ Voice Manager ready with ElevenLabs SDK")
        else:
            self.client = None
            print("⚠️ ElevenLabs API key not found")
    
    def text_to_speech(self, text: str, personality: str) -> Optional[str]:
        """
        Convert text to speech using ElevenLabs SDK
        Returns base64 encoded audio or None if failed
        """
        if not self.client:
            return None
            
        # Clean personality name (remove emoji)
        clean_personality = personality.split(' ', 1)[1] if ' ' in personality else personality
        clean_personality = clean_personality.lower()
        
        voice_id = self.personality_voices.get(clean_personality, self.personality_voices["networkchuck"])
        
        try:
            # Generate speech using official SDK API structure
            audio = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_monolingual_v1",
                output_format="mp3_44100_128"
            )
            
            # Convert audio bytes directly
            audio_bytes = b"".join(audio)
            
            # Return base64 encoded audio
            audio_base64 = base64.b64encode(audio_bytes).decode()
            return f"data:audio/mpeg;base64,{audio_base64}"
                
        except Exception as e:
            print(f"❌ TTS Exception: {e}")
            return None
    
    def create_audio_player(self, audio_data: str) -> str:
        """
        Create HTML audio player for the generated speech
        """
        if not audio_data:
            return ""
        
        return f"""
        <audio controls autoplay style="width: 100%; margin: 10px 0;">
            <source src="{audio_data}" type="audio/mpeg">
            Your browser does not support audio playback.
        </audio>
        """


def create_voice_components():
    """
    Create Gradio components for voice functionality
    Returns tuple of (speech_input, tts_button, audio_output)
    """
    
    # Speech-to-Text input (using browser Web Speech API)
    speech_input = gr.Audio(
        sources=["microphone"],  # Updated for newer Gradio
        type="numpy", 
        label="🎤 Voice Input",
        visible=True
    )
    
    # Text-to-Speech button
    tts_button = gr.Button(
        "🔊 Generate Speech",
        variant="secondary",
        size="sm"
    )
    
    # Audio output for TTS
    audio_output = gr.HTML(
        label="🔊 AI Voice Response",
        visible=True
    )
    
    return speech_input, tts_button, audio_output


# Simple STT function using ElevenLabs Speech-to-Text API with fallback
def speech_to_text(audio_data) -> str:
    """
    Convert speech to text using ElevenLabs Speech-to-Text API with Whisper fallback
    """
    if audio_data is None:
        return ""
    
    try:
        import io
        import wave
        import numpy as np
        
        # Convert numpy array to WAV file
        sample_rate, audio_array = audio_data
        
        # Normalize audio
        if audio_array.dtype != np.int16:
            audio_array = (audio_array * 32767).astype(np.int16)
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_array.tobytes())
        
        wav_buffer.seek(0)
        
        # Try ElevenLabs Speech-to-Text API first
        elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        if elevenlabs_api_key:
            try:
                from elevenlabs.client import ElevenLabs
                client = ElevenLabs(api_key=elevenlabs_api_key)
                
                transcription = client.speech_to_text.convert(
                    file=wav_buffer,
                    model_id="scribe_v1",
                    language_code="eng"
                )
                
                # Extract text from the response object
                if hasattr(transcription, 'text'):
                    return transcription.text.strip()
                elif hasattr(transcription, 'transcript'):
                    return transcription.transcript.strip()
                else:
                    return str(transcription).strip()
                    
            except Exception as e:
                print(f"⚠️ ElevenLabs STT failed: {e}")
                print("🔄 Falling back to OpenAI Whisper...")
                # Fall through to Whisper fallback
        
        # Fallback to OpenAI Whisper
        try:
            import openai
            client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            wav_buffer.seek(0)  # Reset buffer position
            wav_buffer.name = "audio.wav"
            
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=wav_buffer,
                response_format="text"
            )
            
            print("✅ Used Whisper fallback successfully")
            return response.strip()
            
        except Exception as whisper_error:
            print(f"❌ Whisper fallback also failed: {whisper_error}")
            return "Speech recognition failed"
        
    except Exception as e:
        print(f"❌ STT Error: {e}")
        return "Speech recognition failed"


# Test function
def test_voice_integration():
    """Test voice manager functionality"""
    print("🧪 Testing Voice Integration...")
    
    # Load environment variables for testing
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        voice_manager = VoiceManager()
        
        # Test TTS
        test_text = "Hello! This is a test of the voice system."
        audio_data = voice_manager.text_to_speech(test_text, "networkchuck")
        
        if audio_data:
            print("✅ TTS test successful")
        else:
            print("⚠️ TTS test failed - check API key")
        
        # Test component creation
        components = create_voice_components()
        print(f"✅ Created {len(components)} voice components")
        
        return True
        
    except Exception as e:
        print(f"❌ Voice integration test failed: {e}")
        return False


if __name__ == "__main__":
    test_voice_integration()