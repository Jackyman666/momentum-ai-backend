import anthropic
from typing import Optional

from app.config import settings


class MiniMaxClient:
    """Client for MiniMax LLM API using Anthropic SDK - handles only API communication"""
    
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(
            api_key=settings.minimax_api_key,
            base_url=settings.minimax_api_url
        )
        self.model = settings.minimax_model_M25
    
    async def generate_completion(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000
    ) -> str:
        """
        Generate a completion from MiniMax LLM using Anthropic SDK
        
        Args:
            prompt: User prompt/message
            system_prompt: Optional system message to set context
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Raw text response from the LLM (combines all text blocks)
            
        Raises:
            Exception: If API call fails
        """
        try:
            # Build messages in Anthropic format
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
            
            # Call MiniMax via Anthropic SDK (async)
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt if system_prompt else "You are a helpful assistant.",
                messages=messages
            )
            
            # Extract text content from response blocks
            text_content = []
            thinking_content = []
            
            for block in message.content:
                if block.type == "thinking":
                    thinking_content.append(block.thinking)
                elif block.type == "text":
                    text_content.append(block.text)
            
            # Combine all text blocks
            result = "\n".join(text_content)
            
            if not result:
                raise ValueError("Empty response from LLM")
            
            return result
            
        except anthropic.APIError as e:
            raise Exception(f"MiniMax API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to generate completion: {str(e)}")


# Global instance
minimax_client = MiniMaxClient()
