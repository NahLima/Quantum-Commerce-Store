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
import time

import httpx

DEFAULT_MODEL = "gemini-3.8-flash"
TIMEOUT_S = 120.0
# 429 (limite de requisições) e 503 (sobrecarga) são transitórios: vale
# uma segunda tentativa depois de uma espera. O free tier do Gemini
# limita requisições por minuto — sem isso, o aquecimento (50 produtos
# em sequência) esbarra no 429 e nenhum resumo é gerado.
RETRYABLE_STATUS = frozenset({429, 503})
RETRY_WAIT_S = 60.0


class GeminiClient:
    """Uma chamada `generateContent`; devolve o texto ou None (falha).

    A falha nunca é silenciosa: `last_error` guarda o motivo (status HTTP
    ou tipo do erro de rede), para o script de aquecimento — e quem roda
    ele — saber se a chave está errada, o modelo sobrecarregado ou a rede
    caiu, em vez de só "falhou".
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        transport: httpx.BaseTransport | None = None,
        retry_wait_s: float = RETRY_WAIT_S,
    ) -> None:
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self._model = model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
        self._transport = transport
        self._retry_wait_s = retry_wait_s
        self.last_error: str | None = None

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    @property
    def model(self) -> str:
        return self._model

    def generate(self, prompt: str) -> str | None:
        self.last_error = None
        if not self.available:
            self.last_error = "sem chave (GEMINI_API_KEY não definida)"
            return None
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:generateContent"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 300},
        }
        for attempt in (1, 2):
            try:
                with httpx.Client(
                    timeout=TIMEOUT_S, transport=self._transport, trust_env=False
                ) as client:
                    response = client.post(
                        url, headers={"x-goog-api-key": self._api_key}, json=payload
                    )
            except Exception as exc:  # timeout, DNS, conexão recusada...
                self.last_error = type(exc).__name__
                return None
            if response.status_code == 200:
                candidates = response.json().get("candidates") or []
                if not candidates:
                    self.last_error = "resposta sem candidatos"
                    return None
                parts = candidates[0].get("content", {}).get("parts") or []
                text = "".join(part.get("text", "") for part in parts).strip()
                if not text:
                    self.last_error = "resposta vazia"
                    return None
                self.last_error = None  # o retry deu certo: não há erro
                return text
            self.last_error = f"HTTP {response.status_code}"
            if response.status_code in RETRYABLE_STATUS and attempt == 1:
                time.sleep(self._retry_wait_s)
                continue
            return None
        return None
