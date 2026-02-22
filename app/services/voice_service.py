from app.services.gemini_service import GeminiService
import base64
import logging

class VoiceService:
    def __init__(self, gemini: GeminiService):
        self.gemini = gemini

    async def transcribe_audio(self, audio_data_base64: str) -> str:
        try:
            # Decode base64
            # Handle potential header "data:audio/webm;base64,"
            if "," in audio_data_base64:
                audio_data_base64 = audio_data_base64.split(",")[1]
                
            audio_bytes = base64.b64decode(audio_data_base64)
            
            # Send to Gemini
            text = await self.gemini.transcribe(audio_bytes)
            return text
        except Exception as e:
            logging.error(f"Transcription failed: {str(e)}")
            raise e
