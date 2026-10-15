import os

import openai
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class LLMError(Exception):
    """Raised when a model call fails."""


def ask_ollama(system: str, user: str, temperature: float = 0.1) -> str:
    url = f"{os.getenv('OLLAMA_URL')}/api/chat"
    payload = {
        "model": os.getenv("OLLAMA_MODEL"),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {"temperature": temperature},
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        raise LLMError("Ollama is not running. Start it with `ollama serve`.") from e
    except requests.exceptions.Timeout as e:
        raise LLMError("Ollama took too long to respond.") from e
    except requests.exceptions.HTTPError as e:
        raise LLMError(f"Ollama returned an error: {e}") from e

    return response.json()["message"]["content"]


def ask_api(system: str, user: str, temperature: float = 0.1) -> str:
    client = OpenAI(
        api_key=os.getenv("API_KEY"),
        base_url=os.getenv("BASE_URL"),
        timeout=60,
    )
    model = os.getenv("MODEL")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
    except openai.APITimeoutError as e:
        raise LLMError(
            "API request timed out. Check your connection or try again."
        ) from e
    except openai.APIConnectionError as e:
        raise LLMError(
            "Could not reach the API. Check your internet/VPN and BASE_URL."
        ) from e
    except openai.AuthenticationError as e:
        raise LLMError("Invalid API key. Check API_KEY in your .env file.") from e
    except openai.NotFoundError as e:
        raise LLMError(
            f"Model '{model}' not found. Check MODEL in your .env file."
        ) from e
    except openai.RateLimitError as e:
        raise LLMError("Rate limit reached. Wait a moment and try again.") from e
    except openai.APIStatusError as e:
        raise LLMError(f"API error {e.status_code}: {e.message}") from e

    content = response.choices[0].message.content
    if not content:
        raise LLMError("API returned an empty response.")
    return content


def ask(provider: str, system: str, user: str, temperature: float = 0.1) -> str:
    if provider == "ollama":
        return ask_ollama(system, user, temperature)
    if provider == "api":
        return ask_api(system, user, temperature)
    raise ValueError(f"Unknown provider: {provider!r} (use 'ollama' or 'api')")


if __name__ == "__main__":
    system = "You are a concise assistant."
    user = "In one sentence: what is a log file?"
    for provider in ["ollama", "api"]:
        print(f"--- {provider} ---")
        print(ask(provider, system, user))
