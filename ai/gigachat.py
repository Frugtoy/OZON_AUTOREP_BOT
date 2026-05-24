from typing import Optional
from langchain_gigachat.chat_models import GigaChat

from config import settings


class GigaChatGenerator:
    def __init__(self):
        # verify_ssl_certs=False — MITM-риск. Используем только если
        # GigaChat API работает через сертификат, не принятый системой.
        # В .env можно установить GIGACHAT_VERIFY_SSL=false для отладки.
        verify_ssl = getattr(settings, "gigachat_verify_ssl", True)
        if not verify_ssl:
            import warnings
            warnings.warn(
                "GigaChat: verify_ssl_certs=False — трафик уязвим для MITM. "
                "Используйте только для отладки!",
                stacklevel=2,
            )

        self.llm = GigaChat(
            credentials=settings.gigachat_credentials,
            verify_ssl_certs=verify_ssl,
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
