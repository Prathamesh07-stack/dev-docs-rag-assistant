"""
LLM client — free models only.

Two options, both 100% free:

  OPTION 1: Ollama (default) — runs locally on your machine
    - Free, private, no rate limits
    - Models: llama3.1:8b, mistral, gemma3, deepseek-r1
    - Requires: `ollama serve` + `ollama pull llama3.1:8b`
    - Best for: development, sensitive docs, offline

  OPTION 2: Groq — free cloud API
    - Free tier: 14,400 req/day, 6,000 tokens/min
    - Models: llama-3.3-70b-versatile (much smarter than 8B), gemma2-9b-it
    - Requires: free API key from https://console.groq.com
    - Best for: better answer quality without GPU

Switch via .env:
  LLM_PROVIDER=ollama   (default)
  LLM_PROVIDER=groq
"""

import os
import time
from typing import Optional

import httpx
import structlog

logger = structlog.get_logger()

# ── Config ────────────────────────────────────────────────────────────────────
LLM_PROVIDER    = os.getenv("LLM_PROVIDER",    "ollama")

# Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL",    "llama3.1:8b")

# Groq (free tier — https://console.groq.com)
GROQ_API_KEY    = os.getenv("GROQ_API_KEY",    "")
GROQ_MODEL      = os.getenv("GROQ_MODEL",      "llama-3.3-70b-versatile")
GROQ_BASE_URL   = "https://api.groq.com/openai"

LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_MAX_TOKENS  = int(os.getenv("LLM_MAX_TOKENS",   "1024"))
LLM_TIMEOUT     = float(os.getenv("LLM_TIMEOUT_S",  "60"))


class LLMClient:
    """
    Async LLM client supporting Ollama (local) and Groq (free cloud).
    Both use the OpenAI /v1/chat/completions message format.
    """

    def __init__(self):
        if LLM_PROVIDER == "groq":
            if not GROQ_API_KEY:
                raise ValueError(
                    "GROQ_API_KEY is not set. Get a free key at https://console.groq.com"
                )
            self.base_url = f"{GROQ_BASE_URL}/v1"
            self.model    = GROQ_MODEL
            self.headers  = {
                "Content-Type":  "application/json",
                "Authorization": f"Bearer {GROQ_API_KEY}",
            }
        else:
            # Default: Ollama local
            self.base_url = f"{OLLAMA_BASE_URL}/v1"
            self.model    = OLLAMA_MODEL
            self.headers  = {"Content-Type": "application/json"}

        logger.info(
            "llm_client.ready",
            provider=LLM_PROVIDER,
            model=self.model,
        )

    async def generate(self, messages: list[dict]) -> str:
        """
        Send messages to the LLM and return the assistant reply text.

        Raises RuntimeError with helpful message on failure.
        """
        payload = {
            "model":       self.model,
            "messages":    messages,
            "temperature": LLM_TEMPERATURE,
            "max_tokens":  LLM_MAX_TOKENS,
            "stream":      False,
        }

        t0 = time.time()

        try:
            async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=self.headers,
                )
                response.raise_for_status()

            data    = response.json()
            answer  = data["choices"][0]["message"]["content"].strip()
            elapsed = round((time.time() - t0) * 1000, 1)

            logger.info(
                "llm_client.generated",
                provider=LLM_PROVIDER,
                model=self.model,
                input_tokens=data.get("usage", {}).get("prompt_tokens"),
                output_tokens=data.get("usage", {}).get("completion_tokens"),
                elapsed_ms=elapsed,
            )
            return answer

        except httpx.ConnectError:
            if LLM_PROVIDER == "ollama":
                raise RuntimeError(
                    "Cannot connect to Ollama. Make sure it is running:\n"
                    "  1. `ollama serve`\n"
                    f"  2. `ollama pull {self.model}`"
                )
            raise RuntimeError(f"Cannot connect to Groq API. Check your network and GROQ_API_KEY.")

        except httpx.HTTPStatusError as e:
            logger.error("llm_client.http_error", status=e.response.status_code, body=e.response.text[:300])
            raise RuntimeError(f"LLM API error {e.response.status_code}: {e.response.text[:200]}")

        except Exception as e:
            logger.error("llm_client.error", error=str(e))
            raise RuntimeError(f"LLM call failed: {e}")


# ── Singleton ─────────────────────────────────────────────────────────────────
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """FastAPI dependency — returns the shared LLMClient instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
