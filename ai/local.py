from typing import Optional
import aiohttp
import logging

logger = logging.getLogger(__name__)


class LocalLLM:
    """Локальная LLM через Ollama API."""

    def __init__(self, model: str = "qwen2.5:7b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def generate(
        self, rating: int, review_text: str, category: Optional[str] = None
    ) -> str:
        tone = "благодарным и дружелюбным" if rating >= 4 else "внимательным и извиняющимся"
        cat_hint = f" Товар из категории: {category}." if category else ""

        prompt = (
            f"Ты — менеджер по работе с клиентами маркетплейса Ozon.{cat_hint}\n"
            f"Клиент оставил отзыв с оценкой {rating} из 5 звёзд.\n"
            f'Текст отзыва: "{review_text}"\n\n'
            f"Напиши короткий (2-3 предложения), {tone} ответ на русском языке. "
            f"Ответ должен звучать естественно и персонализированно.\nОтвет:"
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.7, "num_predict": 200},
                    },
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:
                    data = await resp.json()
                    return data["response"].strip()
        except Exception as e:
            logger.error(f"Local LLM error: {e}")
            raise

    def healthcheck(self) -> bool:
        """Проверка доступности Ollama сервера."""
        import requests

        try:
            requests.get(f"{self.base_url}/api/tags", timeout=5)
            return True
        except Exception:
            return False
