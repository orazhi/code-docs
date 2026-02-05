from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Service Config
    APP_TITLE: str = "Agentic Translation Service"
    VERSION: str = "1.0.0"

    # Model Config
    # TRANSLATION_MODEL: str = "translategemma"
    TRANSLATION_MODEL: str = "HuggingFaceTB/SmolLM3-3B"
    # QC_MODEL: str = "qwen3:1.7b"
    QC_MODEL: str = "katanemo/Arch-Router-1.5B"

    # Logic Config
    PASS_THRESHOLD: int = 8
    # OLLAMA_HOST: str = "http://localhost:11434"
    HF_TOKEN: str = 'Enter your token'

    LANG_CODES_PATH: Path = Path.cwd().parent / 'langCodes.json'

    class Config:
        env_file: str = ".env"

settings = Settings()
