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
        # Remove any whitespace from the URL in case there's a leading space in .env
        api_url = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
        self.base_url = api_url.strip()
        self.model = os.environ.get("OLLAMA_MODEL", "gemma3")
        self.max_retries = 3
        self.retry_delay = 2  # seconds

        # Log the API URL being used (without exposing sensitive information)
        logger.info(
            f"Ollama API configured with base URL: {self.base_url} and model: {self.model}"
        )

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
        logger.debug(f"Sending request to Ollama at {url}")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        logger.debug(f"Using model: {self.model}")

        # Try with retries
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Attempt {attempt + 1} to connect to Ollama")
                response = requests.post(url, json=payload)
                
                if response.status_code != 200:
                    logger.warning(f"Ollama returned status code {response.status_code}")
                    logger.warning(f"Response: {response.text[:200]}...")
                    
                response.raise_for_status()

                result = response.json()
                logger.debug("Successfully received response from Ollama")
                return result.get('response', '')
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    logger.debug(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    error_msg = f"Failed to generate feedback after {self.max_retries} attempts: {str(e)}"
                    logger.error(error_msg)

                    # Return a fallback message if Ollama is not available
                    return (
                        "Error: Unable to generate automated feedback due to Ollama service unavailability. "
                        "Please check that Ollama is running locally or provide the correct OLLAMA_API_URL "
                        "environment variable.")

    def is_available(self):
        """
        Check if the Ollama service is available.
        
        Returns:
            bool: True if Ollama is available, False otherwise.
        """
        try:
            # Try checking models API endpoint instead of tags
            logger.debug(f"Checking Ollama availability at {self.base_url}/api/models")
            response = requests.get(f"{self.base_url}/api/models")
            status_code = response.status_code
            logger.debug(f"Ollama API response status: {status_code}")
            
            if status_code != 200:
                # If models endpoint fails, try a simple generate request with a small prompt
                logger.debug("Models endpoint failed, trying simple generate request")
                generate_url = f"{self.base_url}/api/generate"
                test_payload = {
                    "model": self.model,
                    "prompt": "Hello",
                    "stream": False
                }
                
                generate_response = requests.post(generate_url, json=test_payload)
                status_code = generate_response.status_code
                logger.debug(f"Generate API response status: {status_code}")
                
                if status_code != 200:
                    logger.warning(f"Ollama API returned non-200 status: {status_code}")
                    if hasattr(generate_response, 'text'):
                        logger.warning(f"Response text: {generate_response.text[:200]}")
                
                return status_code == 200
            
            return True
        except Exception as e:
            logger.error(f"Error checking Ollama availability: {str(e)}")
            return False
