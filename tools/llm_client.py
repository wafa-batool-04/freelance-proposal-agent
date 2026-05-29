from __future__ import annotations

import os
from enum import Enum
from typing import Any

import anthropic
import groq
from dotenv import load_dotenv

load_dotenv()


class Provider(str, Enum):
    ANTHROPIC = "anthropic"
    GROQ = "groq"


class ModelConfig:
    ANTHROPIC_DEFAULT = "claude-sonnet-4-6"
    ANTHROPIC_POWERFUL = "claude-opus-4-7"
    GROQ_DEFAULT = "llama-3.3-70b-versatile"
    GROQ_FAST = "llama-3.1-8b-instant"


class LLMClient:
    def __init__(self, provider: Provider = Provider.ANTHROPIC):
        self.provider = provider
        self._anthropic: anthropic.Anthropic | None = None
        self._groq: groq.Groq | None = None

    @property
    def anthropic(self) -> anthropic.Anthropic:
        if self._anthropic is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set in environment")
            self._anthropic = anthropic.Anthropic(api_key=api_key)
        return self._anthropic

    @property
    def groq_client(self) -> groq.Groq:
        if self._groq is None:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not set in environment")
            self._groq = groq.Groq(api_key=api_key)
        return self._groq

    def complete(
        self,
        prompt: str,
        system: str = "",
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        use_cache: bool = True,
    ) -> str:
        if self.provider == Provider.ANTHROPIC:
            return self._complete_anthropic(
                prompt=prompt,
                system=system,
                model=model or ModelConfig.ANTHROPIC_DEFAULT,
                max_tokens=max_tokens,
                temperature=temperature,
                use_cache=use_cache,
            )
        return self._complete_groq(
            prompt=prompt,
            system=system,
            model=model or ModelConfig.GROQ_DEFAULT,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def _complete_anthropic(
        self,
        prompt: str,
        system: str,
        model: str,
        max_tokens: int,
        temperature: float,
        use_cache: bool,
    ) -> str:
        system_content: list[dict[str, Any]] = []
        if system:
            block: dict[str, Any] = {"type": "text", "text": system}
            if use_cache:
                block["cache_control"] = {"type": "ephemeral"}
            system_content.append(block)

        response = self.anthropic.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_content if system_content else anthropic.NOT_GIVEN,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def _complete_groq(
        self,
        prompt: str,
        system: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self.groq_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    def stream(
        self,
        prompt: str,
        system: str = "",
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ):
        """Yields text chunks as they stream from the provider."""
        if self.provider == Provider.ANTHROPIC:
            yield from self._stream_anthropic(
                prompt=prompt,
                system=system,
                model=model or ModelConfig.ANTHROPIC_DEFAULT,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        else:
            yield from self._stream_groq(
                prompt=prompt,
                system=system,
                model=model or ModelConfig.GROQ_DEFAULT,
                max_tokens=max_tokens,
                temperature=temperature,
            )

    def _stream_anthropic(
        self,
        prompt: str,
        system: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ):
        system_content: list[dict[str, Any]] = []
        if system:
            system_content.append(
                {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
            )

        with self.anthropic.messages.stream(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_content if system_content else anthropic.NOT_GIVEN,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                yield text

    def _stream_groq(
        self,
        prompt: str,
        system: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ):
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        stream = self.groq_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


def get_client(provider: str = "anthropic") -> LLMClient:
    return LLMClient(provider=Provider(provider.lower()))
