"""Thin wrapper around the Groq API so every agent calls the LLM the same way."""
import os
from groq import Groq

_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY not set. Get a free key at https://console.groq.com/keys "
                "and set it as an environment variable (or Streamlit secret)."
            )
        _client = Groq(api_key=api_key)
    return _client


def chat(system: str, user: str, model: str = "openai/gpt-oss-120b", temperature: float = 0.2) -> str:
    """Single-turn chat call. Kept simple and stateless so each agent is independent."""
    client = get_client()
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content
