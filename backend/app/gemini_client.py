"""Cliente mínimo do Gemini (REST `generateContent`) para o resumo de avaliações.

Lê `GEMINI_API_KEY` e `GEMINI_MODEL` do ambiente. Sem chave, o cliente
fica indisponível e o resumo cai para a versão determinística — a API
nunca quebra por falta de chave. A chave vive no `backend/.env` (nunca
no repo; ver `backend/.env.example`).

Modelo padrão: `gemini-3.8-flash`, verificado com a chave dela em
31/out/2026 (`gemini-2.5-flash` dá 404 para chaves novas).
"""

from __future__ import annotations

import os

import httpx

DEFAULT_MODEL = "gemini-3.8-flash"
TIMEOUT_S = 120.0


class GeminiClient:
    """Uma chamada `generateContent`; devolve o texto ou None (falha)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self._model = model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
        self._transport = transport

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    @property
    def model(self) -> str:
        return self._model

    def generate(self, prompt: str) -> str | None:
        if not self.available:
            return None
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:generateContent"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 300},
        }
        try:
            with httpx.Client(
                timeout=TIMEOUT_S, transport=self._transport, trust_env=False
            ) as client:
                response = client.post(
                    url, headers={"x-goog-api-key": self._api_key}, json=payload
                )
            if response.status_code != 200:
                return None
            parts = response.json()["candidates"][0]["content"]["parts"]
            text = "".join(part.get("text", "") for part in parts).strip()
            return text or None
        except Exception:
            return None
