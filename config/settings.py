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
    def bot_proxy(self) -> Optional[str]:
        if self.use_bot_proxy and self.bot_proxy_list:
            proxies = [p.strip() for p in self.bot_proxy_list.split(",") if p.strip()]
            return proxies[0] if proxies else None
        return None


settings = Settings()
