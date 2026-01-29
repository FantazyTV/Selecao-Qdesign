import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncIterator

from ..prompts.loader import load_prompt
from ..providers import factory


@dataclass
class AgentResult:
    name: str
    output: dict
    confidence: float
    timestamp: str


class BaseAgent:
    name = "base"

    async def run(self, state: dict) -> AgentResult:
        raise NotImplementedError

    async def _ask(self, prompt_name: str, state: dict) -> dict:
        provider = factory.get_provider()
        prompt = load_prompt(prompt_name)
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(state)},
        ]
        return await provider.generate(messages)
    
    async def _ask_stream(self, prompt_name: str, state: dict) -> AsyncIterator[str]:
        """Stream tokens from LLM in real-time."""
        provider = factory.get_provider()
        prompt = load_prompt(prompt_name)
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(state)},
        ]
        async for chunk in provider.stream(messages):
            yield chunk

    def _result(self, output: dict, confidence: float) -> AgentResult:
        ts = datetime.now(timezone.utc).isoformat()
        return AgentResult(self.name, output, confidence, ts)
