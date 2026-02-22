from pydantic import BaseModel

class VoiceTranscriptionRequest(BaseModel):
    # We might receive base64 encoded audio or just metadata if sending file via multipart
    # For JSON request, base64 is common
    audio_data: str # Base64 encoded
    format: str = "webm" 

class VoiceTranscriptionResponse(BaseModel):
    text: str
