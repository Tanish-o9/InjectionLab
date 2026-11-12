"""LLM backends for InjectionLab: mock (offline, deterministic), Ollama (local), OpenAI-compatible API.

Spec strings:
    mock:weak | mock:strong
    ollama:qwen2.5:3b-instruct          (needs `ollama serve`, env OLLAMA_HOST optional)
    openai:gpt-4o-mini                  (env OPENAI_API_KEY, optional OPENAI_BASE_URL)
"""
import os
import requests

import config


class OllamaLLM:
    def __init__(self, model):
        self.name = f"ollama:{model}"
        self.model = model
        self.host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    def chat(self, messages, trial=0):
        r = requests.post(
            f"{self.host}/api/chat",
            json={"model": self.model, "messages": messages, "stream": False,
                  "options": {"temperature": config.TEMPERATURE, "seed": config.SEED + trial}},
            timeout=300,
        )
        r.raise_for_status()
        return r.json()["message"]["content"]


class OpenAICompatLLM:
    def __init__(self, model):
        self.name = f"openai:{model}"
        self.model = model
        self.base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.key = os.environ.get("OPENAI_API_KEY", "")

    def chat(self, messages, trial=0):
        r = requests.post(
            f"{self.base}/chat/completions",
            headers={"Authorization": f"Bearer {self.key}"},
            json={"model": self.model, "messages": messages,
                  "temperature": config.TEMPERATURE, "seed": config.SEED + trial},
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


def get_llm(spec: str):
    kind, _, rest = spec.partition(":")
    if kind == "mock":
        from mock_llm import MockLLM
        return MockLLM(rest or "weak")
    if kind == "ollama":
        return OllamaLLM(rest)
    if kind == "openai":
        return OpenAICompatLLM(rest)
    raise ValueError(f"Unknown LLM spec: {spec}")
