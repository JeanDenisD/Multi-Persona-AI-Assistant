"""
Simple test to verify OpenAI Whisper STT works
"""

import os
import io
import wave
import numpy as np
from dotenv import load_dotenv

load_dotenv()

def test_whisper():
    """Test OpenAI Whisper with a simple audio file"""
    try:
        import openai
        
        # Check API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ No OPENAI_API_KEY found in .env")
            return False
            
        print(f"🔑 OpenAI API key found: {api_key[:8]}...")
        
        # Create simple test audio (1 second of silence)
        print("🎵 Creating test audio...")
        sample_rate = 16000
        duration = 1.0
        audio_array = np.zeros(int(sample_rate * duration), dtype=np.int16)
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_array.tobytes())
        
        wav_buffer.seek(0)
        wav_buffer.name = "test_audio.wav"
        
        print("🎤 Testing Whisper STT...")
        
        # Test Whisper API
        client = openai.OpenAI(api_key=api_key)
        
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=wav_buffer,
            response_format="text"
        )
        
        print(f"✅ Whisper response: '{response}'")
        print("🎉 Whisper STT is working!")
        return True
        
    except Exception as e:
        print(f"❌ Whisper test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing OpenAI Whisper STT\n")
    success = test_whisper()
    
    if success:
        print("\n✅ Whisper fallback will work when ElevenLabs is busy!")
    else:
        print("\n❌ Whisper fallback will NOT work - check your OpenAI API key")