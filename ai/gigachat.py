from typing import Optional
from langchain_gigachat.chat_models import GigaChat

from config import settings


class GigaChatGenerator:
    def __init__(self):
        self.llm = GigaChat(
            credentials=settings.gigachat_credentials,
            verify_ssl_certs=False,
        )

    def generate(self, rating: int, review_text: str, category: Optional[str] = None) -> str:
        tone = "благодарным и дружелюбным" if rating >= 4 else "внимательным и извиняющимся"
        cat_hint = f" Товар из категории: {category}." if category else ""

        prompt = (
            f"Ты — менеджер по работе с клиентами маркетплейса Ozon.{cat_hint}\n"
            f"Клиент оставил отзыв с оценкой {rating} из 5 звёзд.\n"
            f'Текст отзыва: "{review_text}"\n\n'
            f"Напиши короткий (2-3 предложения), {tone} ответ на русском языке. "
            f"Ответ должен звучать естественно и персонализированно.\nОтвет:"
        )
        return self.llm.invoke(prompt).content.strip()
