"""OpenRouter LLM integration for patient persona conversations."""
import json
from typing import List, Dict, Any, Optional
import requests

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class OpenRouterClient:
    """Client for interacting with OpenRouter LLM API."""
    
    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    def __init__(self, api_key: str, model: str = "anthropic/claude-3.5-sonnet", temperature: float = 0.8):
        """Initialize OpenRouter client.
        
        Args:
            api_key: OpenRouter API key
            model: Model to use for generation
            temperature: Sampling temperature
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/voice-bot-tester",
            "X-Title": "Voice Bot Tester"
        }
        logger.info(f"OpenRouter client initialized with model {model}")
    
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 300,
        temperature: Optional[float] = None
    ) -> Optional[str]:
        """Generate a response from the LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Override default temperature
            
        Returns:
            Generated text or None if failed
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature if temperature is not None else self.temperature,
            }
            
            response = requests.post(
                self.BASE_URL,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API error: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            return None
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing OpenRouter response: {e}")
            return None
    
    def simulate_conversation(
        self,
        system_prompt: str,
        conversation_history: List[Dict[str, str]],
        max_turns: int = 10
    ) -> str:
        """Simulate a conversation turn.
        
        Args:
            system_prompt: System prompt defining the persona
            conversation_history: List of previous messages
            max_turns: Maximum conversation turns
            
        Returns:
            Patient's response
        """
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        
        response = self.generate_response(messages, max_tokens=250)
        return response if response else "Um... can you repeat that?"
