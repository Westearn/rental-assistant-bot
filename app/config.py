from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    bot_token: str
    admins: List[int]
    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8"
    )


settings = Settings()