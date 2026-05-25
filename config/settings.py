from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Ozon API
    api_token: str
    client_id: str

    # GigaChat
    gigachat_credentials: str
    gigachat_verify_ssl: bool = True  # false только для отладки MITM-риск!

    # Telegram Bot
    bot_token: str

    # Proxy (Telegram only)
    use_bot_proxy: bool = False
    bot_proxy_list: Optional[str] = None

    # Admins
    admin_ids: List[int] = [438662734]

    # Paths
    db_path: str = "./data/reviews.db"
    reviews_config_path: str = "./data/reviews_config.json"
    reviews_counter_path: str = "./data/rewiews_counter.json"

    @property
    def bot_proxies(self) -> List[str]:
        """Все прокси из списка (поддержка fallback)."""
        if not self.use_bot_proxy or not self.bot_proxy_list:
            return []
        raw = [p.strip() for p in self.bot_proxy_list.split(",") if p.strip()]
        return [_normalize_proxy_url(p) for p in raw]

    @property
    def bot_proxy(self) -> Optional[str]:
        """Первый прокси из списка (backward compatibility)."""
        proxies = self.bot_proxies
        print(proxies)
        return proxies[0] if proxies else None


def _normalize_proxy_url(url: str) -> str:
    """
    Нормализует URL прокси:
    - Убирает окружающие кавычки (частая ошибка в .env: BOT_PROXY_LIST="socks5://...")
    - Добавляет схему http:// если отсутствует
    - Оборачивает IPv6-адреса в квадратные скобки
    """
    url = url.strip().strip("'\"")
    # Если нет схемы — добавляем http:// (Proxy6 поддерживает оба протокола)
    if "://" not in url:
        url = "http://" + url

    # Обработка IPv6 без скобок: http://login:pass@2a0f:...:994:8080
    if "@" in url:
        scheme_creds, host_port = url.rsplit("@", 1)
        # IPv6 содержит ':' более одного раза и не в скобках
        if ":" in host_port and not host_port.startswith("["):
            if host_port.count(":") > 1:
                # Последнее ':' — разделитель порта
                last_colon = host_port.rfind(":")
                ipv6_addr = host_port[:last_colon]
                port = host_port[last_colon + 1:]
                if port.isdigit():
                    host_port = f"[{ipv6_addr}]:{port}"
                else:
                    host_port = f"[{host_port}]"
                url = f"{scheme_creds}@{host_port}"
    return url


settings = Settings()
