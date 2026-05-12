from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class Option:
    label: str
    text: str


@dataclass(frozen=True)
class InlineImage:
    filename: str
    page: int
    bbox: Tuple[float, float, float, float]
    sha256: str
    width: int
    height: int


@dataclass(frozen=True)
class Question:
    number: int
    text: str
    options: List[Option]
    images: List[InlineImage] = field(default_factory=list)


@dataclass(frozen=True)
class ReadingSection:
    passage_text: str
    questions: List[Question]
    images: List[InlineImage] = field(default_factory=list)


@dataclass(frozen=True)
class ListeningItem:
    number: int
    dialog_script: str
    question: str
    options: List[Option]
    images: List[InlineImage] = field(default_factory=list)


@dataclass(frozen=True)
class ListeningSection:
    items: List[ListeningItem]


@dataclass(frozen=True)
class OpenTestSet:
    filename: str
    hwp_sha256: str
    pdf_sha256: str
    reading: Optional[ReadingSection] = None
    listening: Optional[ListeningSection] = None
