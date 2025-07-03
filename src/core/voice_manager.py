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
        
        # Voice mapping for each personality - using your provided voice IDs
        self.personality_voices = {
            "networkchuck": "OuJq1nTHrT0iME3eqD5N",
            "bloomy": "IixZCtIbiujuj9uoKF2C",
            "ethicalhacker": "7ceZgj78jCCeAW93ItNk",
            "patientteacher": "h2sm0NbeIZXHBzJOMYcQ",
            "startupfounder": "GzE4TcXfh9rYCU9gVgPp",
            "datascientist": "yj30vwTGJxSHezdAGsv9"
        }
        
        # Initialize ElevenLabs client
        if self.elevenlabs_api_key:
            self.client = ElevenLabs(api_key=self.elevenlabs_api_key)
        else:
            self.client = None
    
    def text_to_speech(self, text: str, personality: str) -> Optional[bytes]:
        """
        Convert text to speech using ElevenLabs SDK
        Returns audio bytes or None if failed
        """
        if not self.client:
            return None
            
        # Clean personality name (remove emoji)
        clean_personality = personality.split(' ', 1)[1] if ' ' in personality else personality
        clean_personality = clean_personality.lower()
        
        voice_id = self.personality_voices.get(clean_personality, self.personality_voices["networkchuck"])
        
        try:
            # Generate speech using official SDK
            audio = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_monolingual_v1"
            )
            
            # Convert iterator to bytes
            audio_bytes = b"".join(audio)
            return audio_bytes
                
        except Exception as e:
            return None


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
                # Fall through to Whisper fallback
                pass
        
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
            
            return response.strip()
            
        except Exception as whisper_error:
            return "Speech recognition failed"
        
    except Exception as e:
        return "Speech recognition failed"


# Simple TTS function for use in app.py
def text_to_speech_simple(text: str, personality: str) -> Optional[bytes]:
    """Simple wrapper for TTS functionality"""
    voice_manager = VoiceManager()
    return voice_manager.text_to_speech(text, personality)