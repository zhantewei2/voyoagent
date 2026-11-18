import os

from pathlib import Path
from pydantic import model_validator
from dotenv import dotenv_values
from pydantic_settings import SettingsConfigDict,BaseSettings




class Settings(BaseSettings):
    model_config=SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    ANTHROPIC_BASE_URL:str
    ANTHROPIC_MODEL:str
    ANTHROPIC_AUTH_TOKEN:str
    OPENAI_BASE_URL:str
    OPENAI_MODEL:str
    OPENAI_AUTH_TOKEN:str




settings=Settings()
