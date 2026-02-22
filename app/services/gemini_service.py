import google.generativeai as genai
from typing import AsyncGenerator
from tenacity import retry, stop_after_attempt, wait_exponential
from google.api_core.exceptions import ResourceExhausted
from app.config import Settings
import logging

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self, settings: Settings):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Stream tokens from Gemini."""
        response = await self.model.generate_content_async(
            prompt,
            stream=True,
        )
        async for chunk in response:
            if chunk.text:
                yield chunk.text

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def stream_with_retry(self, prompt: str) -> AsyncGenerator[str, None]:
        try:
            async for token in self.stream(prompt):
                yield token
        except ResourceExhausted:
            logger.warning("Gemini rate limit hit, retrying...")
            raise

    async def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe audio using Gemini multimodal."""
        # Gemini expects mime_type for blob
        response = await self.model.generate_content_async([
            {"mime_type": "audio/webm", "data": audio_bytes},
            "Transcribe this audio to text completely.",
        ])
        return response.text

    async def analyze_sentiment(self, text: str) -> tuple[str, float]:
        """Analyze sentiment of text using Gemini."""
        prompt = f"""
        Analyze the sentiment of the following text from a study session.
        Classify it into one of these labels: 'focused', 'confused', 'frustrated', 'confident', 'neutral'.
        Return ONLY a JSON object with 'label' and 'confidence' (0.0 to 1.0).
        
        Text: "{text}"
        """
        try:
            response = await self.model.generate_content_async(prompt)
            import json
            # Clean up potential markdown code blocks
            content = response.text.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            data = json.loads(content.strip())
            return data.get("label", "neutral"), float(data.get("confidence", 0.0))
        except Exception as e:
            logger.error(f"Gemini sentiment analysis failed: {e}")
            return "neutral", 0.0
