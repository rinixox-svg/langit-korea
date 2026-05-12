from enum import StrEnum


class MimeType(StrEnum):
    PDF = "application/pdf"
    HWP = "application/hwp"
    ZIP = "application/zip"
    MP3 = "audio/mpeg"
    IMAGE_JPEG = "image/jpeg"
    IMAGE_PNG = "image/png"
    HTML = "text/html"
    OCTET = "application/octet-stream"


class ScrapeStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class FetchMethod(StrEnum):
    HTTPX = "httpx"
    PLAYWRIGHT = "playwright"
    AUTO = "auto"
