"""server 层配置：只放 server 自己需要的项（数据库、日志）。"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = ""
    PG_POOL_MIN_SIZE: int = 2
    PG_POOL_MAX_SIZE: int = 10
    LOG_DIR: str = "logs"
    SKILL_WORK_DIR: str = "runtime/skills"  # 技能物化目录，agent 装配时写入 skill.md


settings = ServerSettings()
