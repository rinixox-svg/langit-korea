from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BASE_URL: str = "https://epstopik.hrdkorea.or.kr"
    LIST_PATH: str = "/epstopik/book/pub/publicWorkBookList.do"
    CM_LIST_PATH: str = "/epstopik/book/pub/publicWorkBookCmList.do"
    DEFAULT_LANG: str = "en"
    REQUEST_DELAY: float = 1.5
    MAX_RETRIES: int = 3
    ARTIFACTS_DIR: Path = Path("./artifacts")
    DATABASE_URL: str = "sqlite:///./artifacts/provenance.db"
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    HEADERS: dict = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
