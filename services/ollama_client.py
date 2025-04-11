import requests
import json
import logging
import os
import time

logger = logging.getLogger(__name__)

class OllamaClient:
    """
    Client for interacting with the Ollama API to analyze notebooks.
    """
    
    def __init__(self):
        """Initialize the Ollama client with default settings."""
        self.base_url = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
        self.model = os.environ.get("OLLAMA_MODEL", "llama2")
        self.max_retries = 3
        self.retry_delay = 2  # seconds
    
    def generate_feedback(self, prompt, temperature=0.7, max_tokens=2048):
        """
        Generate feedback for a notebook using Ollama.
        
        Args:
            prompt (str): The prompt to send to Ollama.
            temperature (float): Controls randomness in generation (0.0-1.0).
            max_tokens (int): Maximum number of tokens to generate.
            
        Returns:
            str: Generated feedback text.
            
        Raises:
            Exception: If there's an error communicating with Ollama.
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        # Try with retries
        for attempt in range(self.max_retries):
            try:
                response = requests.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                return result.get('response', '')
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    error_msg = f"Failed to generate feedback after {self.max_retries} attempts: {str(e)}"
                    logger.error(error_msg)
                    
                    # Return a fallback message if Ollama is not available
                    return (
                        "Error: Unable to generate automated feedback due to Ollama service unavailability. "
                        "Please check that Ollama is running locally or provide the correct OLLAMA_API_URL "
                        "environment variable."
                    )
    
    def is_available(self):
        """
        Check if the Ollama service is available.
        
        Returns:
            bool: True if Ollama is available, False otherwise.
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except:
            return False
