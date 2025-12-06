"""
Token counting utilities for managing API context limits

This module provides functions for estimating token counts to ensure
requests stay within the Gemini API's context window limits.

Note: The estimation uses a simple character-to-token ratio which is
approximate. For production systems requiring precise token counts,
consider using the actual tokenizer for the specific model.
"""

# Default fallback for token limit (conservative estimate)
DEFAULT_CONTEXT_WINDOW = 200_000  # Conservative fallback for unknown models


def estimate_tokens(text: str, model_name: str = None) -> int:
    """
    Estimate token count using a character-based approximation or model-specific tokenizer.

    Tries to use tiktoken for accurate token counting if available. Falls back to
    a heuristic where 1 token ≈ 4 characters, which is reasonable for English text.

    Args:
        text: The text to estimate tokens for
        model_name: Optional model name to use for accurate token counting

    Returns:
        int: Estimated number of tokens
    """
    if not text:
        return 0
    
    # Try to use tiktoken for accurate token counting if available
    try:
        import tiktoken
        
        # Map model names to encoding names
        encoding_map = {
            # OpenAI models
            "gpt-4": "cl100k_base",
            "gpt-4-turbo": "cl100k_base",
            "gpt-3.5-turbo": "cl100k_base",
            "text-davinci-003": "p50k_base",
            "text-embedding-ada-002": "cl100k_base",
            
            # Gemini models
            "gemini-pro": "cl100k_base",
            "gemini-2.5-flash": "cl100k_base",
            "gemini-2.5-pro": "cl100k_base",
        }
        
        # Extract base model name if it contains suffixes like :free or :latest
        if model_name:
            base_model = model_name.split(":")[0]
        else:
            base_model = None
            
        # Fallback to cl100k_base if model not found
        encoding_name = encoding_map.get(base_model or model_name, "cl100k_base")
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except ImportError:
        # tiktoken not installed, use heuristic
        pass
    
    # Conservative estimate: 1 token per 4 characters
    return len(text) // 4


def check_token_limit(text: str, context_window: int = DEFAULT_CONTEXT_WINDOW, model_name: str = None) -> tuple[bool, int]:
    """
    Check if text exceeds the specified token limit.

    This function is used to validate that prepared prompts will fit
    within the model's context window, preventing API errors and ensuring
    reliable operation.

    Args:
        text: The text to check
        context_window: The model's context window size (defaults to conservative fallback)
        model_name: Optional model name to use for accurate token counting

    Returns:
        Tuple[bool, int]: (is_within_limit, estimated_tokens)
        - is_within_limit: True if the text fits within context_window
        - estimated_tokens: The estimated token count
    """
    estimated = estimate_tokens(text, model_name)
    return estimated <= context_window, estimated
