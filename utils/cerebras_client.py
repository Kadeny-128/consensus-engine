from __future__ import annotations

import asyncio
import json
import os
import re
import time

from dotenv import load_dotenv
from cerebras.cloud.sdk import AsyncCerebras

load_dotenv()


class CerebrasClient:
    def __init__(self, api_key: str | None = None):
        key = api_key or os.environ.get("CEREBRAS_API_KEY")
        if not key:
            try:
                import streamlit as st
                key = st.secrets.get("CEREBRAS_API_KEY")
            except Exception:
                pass
        if not key:
            raise ValueError("CEREBRAS_API_KEY not found in env, st.secrets, or argument")

        self.client = AsyncCerebras(api_key=key)
        self.semaphore = asyncio.Semaphore(10)

    @staticmethod
    def _clean_json(text: str) -> dict | str:
        """Strip markdown fences and parse JSON. Returns dict on success, raw string on failure."""
        cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return text

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "llama3.1-8b",
        json_mode: bool = False,
        max_tokens: int = 2048,
    ) -> dict:
        try:
            async with self.semaphore:
                start = time.perf_counter()
                response = await self.client.chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                latency = round((time.perf_counter() - start) * 1000, 1)

            raw = response.choices[0].message.content
            usage = response.usage
            content = self._clean_json(raw) if json_mode else raw

            return {
                "content": content,
                "latency": latency,
                "tokens": usage.total_tokens if usage else 0,
                "status": "success",
            }
        except Exception as e:
            return {
                "content": None,
                "latency": 0,
                "tokens": 0,
                "status": "error",
                "error_msg": str(e),
            }
