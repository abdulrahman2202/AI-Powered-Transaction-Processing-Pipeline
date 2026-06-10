import google.generativeai as genai
import time
from app.core.config import settings
from app.core.logging import logger

class GeminiClient:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self.configured = False
        
        if not self.api_key or "your_gemini_api_key_here" in self.api_key:
            logger.error("Gemini API key is not set or is still the default placeholder. AI services will fail.")
        else:
            try:
                genai.configure(api_key=self.api_key)
                self.configured = True
                logger.info("Google Generative AI successfully configured.")
            except Exception as e:
                logger.error(f"Failed to configure Google Generative AI: {e}")

    def generate_json_response(self, prompt: str, system_instruction: str = None) -> str:
        """Call Gemini to generate a response in JSON format.
        Includes error handling.
        """
        if not self.configured:
            raise ValueError("Gemini client is not configured. Please check GEMINI_API_KEY environment variable.")

        try:
            logger.info(f"Sending prompt to Gemini (Model: {self.model_name})...")
            
            # Setup generation configuration to return JSON
            generation_config = {
                "response_mime_type": "application/json",
                "temperature": 0.1,  # Low temperature for deterministic classification
            }

            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config,
                system_instruction=system_instruction
            )
            
            response = model.generate_content(prompt)
            
            if not response.text:
                raise ValueError("Received empty response from Gemini API.")
                
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini API request failed: {e}")
            raise

gemini_client = GeminiClient()
