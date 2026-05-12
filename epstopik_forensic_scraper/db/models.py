from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship, JSON, Column


class ScrapingJob(SQLModel, table=True):
    __tablename__ = "scraping_jobs"

    id: Optional[int] = Field(default=None, primary_key=True)
    started_at: datetime = Field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    target_url: str
    start_page: int = 1
    max_pages: int = 0
    status: str = "running"  # running / success / failed / partial

    raw_pages: list["RawPage"] = Relationship(back_populates="job")
    extracted_items: list["ExtractedItem"] = Relationship(back_populates="job")


class RawPage(SQLModel, table=True):
    __tablename__ = "raw_pages"

    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="scraping_jobs.id")
    url: str
    page_num: int
    fetch_method: str  # httpx / playwright
    raw_html_path: str
    html_sha256: str
    screenshot_path: Optional[str] = None
    fetched_at: datetime = Field(default_factory=datetime.now)

    job: ScrapingJob = Relationship(back_populates="raw_pages")
    extracted_items: list["ExtractedItem"] = Relationship(back_populates="raw_page")


class ExtractedItem(SQLModel, table=True):
    __tablename__ = "extracted_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="scraping_jobs.id")
    page_id: int = Field(foreign_key="raw_pages.id")
    row_index: int
    title: str
    published_date: Optional[str] = None
    detail_url: Optional[str] = None
    detail_js: Optional[str] = None
    pdf_urls: str = Field(default="[]")  # JSON array
    hwp_urls: str = Field(default="[]")  # JSON array
    audio_zip_url: Optional[str] = None
    view_count: Optional[str] = None
    file_assets_json: str = Field(default="[]", alias="file_assets_json")

    job: ScrapingJob = Relationship(back_populates="extracted_items")
    raw_page: RawPage = Relationship(back_populates="extracted_items")
    downloaded_files: list["DownloadedFile"] = Relationship(back_populates="item")


class DownloadedFile(SQLModel, table=True):
    __tablename__ = "downloaded_files"

    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="extracted_items.id")
    source_url: str
    local_path: str
    file_sha256: str
    file_size: int
    mime_type: str
    downloaded_at: datetime = Field(default_factory=datetime.now)

    item: ExtractedItem = Relationship(back_populates="downloaded_files")
