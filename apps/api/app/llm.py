from __future__ import annotations

import json

from openai import AsyncOpenAI

from app.config import Settings
from app.domain import NeedProfile


class QwenNeedInterpreter:
    """可选的结构化模型适配器；默认不调用外部服务。"""

    def __init__(self, settings: Settings) -> None:
        self.enabled = settings.llm_enabled and bool(settings.llm_api_key)
        self.model = settings.llm_model
        self.client = (
            AsyncOpenAI(api_key=settings.llm_api_key or "disabled", base_url=settings.llm_api_base)
            if self.enabled
            else None
        )

    async def extract(self, content: str, current: NeedProfile) -> NeedProfile | None:
        if not self.client:
            return None
        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "只提取装机需求 JSON。不要编造价格、配件或兼容性结论。",
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {"current": current.model_dump(), "message": content}, ensure_ascii=False
                    ),
                },
            ],
        )
        raw = response.choices[0].message.content or "{}"
        return NeedProfile.model_validate({**current.model_dump(), **json.loads(raw)})
