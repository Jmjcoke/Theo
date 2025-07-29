"""
OpenAI client utility for PocketFlow integration.
Configured to use environment variables for API key management.
"""
import os
from openai import OpenAI
from typing import Optional

def get_openai_client() -> OpenAI:
    """
    Get configured OpenAI client using environment variable.
    
    Returns:
        OpenAI: Configured OpenAI client
        
    Raises:
        ValueError: If OPENAI_API_KEY environment variable is not set
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required. "
            "Please set it in your .env file or environment."
        )
    
    return OpenAI(api_key=api_key)

def call_llm(
    prompt: str, 
    model: str = "gpt-4o", 
    max_tokens: Optional[int] = None,
    temperature: float = 0.7
) -> str:
    """
    Call OpenAI LLM with the given prompt.
    
    Args:
        prompt: The prompt to send to the LLM
        model: The model to use (default: gpt-4o)
        max_tokens: Maximum tokens in response (optional)
        temperature: Sampling temperature (default: 0.7)
        
    Returns:
        str: The LLM response content
    """
    client = get_openai_client()
    
    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature
    }
    
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
    
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content

if __name__ == "__main__":
    # Test the utility
    try:
        result = call_llm("What is 2+2?")
        print(f"LLM Response: {result}")
    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"API Error: {e}")