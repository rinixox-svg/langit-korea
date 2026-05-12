from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field
from .enums import MimeType, ScrapeStatus


class WorkbookItem(BaseModel):
    row_index: int = Field(ge=0, description="Row number on page")
    title: str = Field(min_length=1)
    detail_url: Optional[str] = None
    detail_js: Optional[str] = None
    pdf_urls: list[str] = Field(default_factory=list)
    hwp_urls: list[str] = Field(default_factory=list)
    audio_zip_url: Optional[str] = None
    published_date: Optional[str] = None
    view_count: Optional[str] = None
    page_num: int = 0


class FileAsset(BaseModel):
    source_url: str
    local_path: str
    sha256: str
    size_bytes: int
    mime_type: MimeType
    downloaded_at: datetime = Field(default_factory=datetime.now)


class PageSnapshot(BaseModel):
    job_id: int
    page_num: int
    url: str
    fetch_method: str
    raw_html_path: str
    html_sha256: str
    fetched_at: datetime = Field(default_factory=datetime.now)
    screenshot_path: Optional[str] = None
    status: ScrapeStatus = ScrapeStatus.SUCCESS
