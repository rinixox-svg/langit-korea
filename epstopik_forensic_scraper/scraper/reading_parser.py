"""
Reading section parser.
Parses EPS-TOPIK reading questions (1-20) from extracted text.
"""
import re
from typing import List, Optional

from loguru import logger

from models.extraction_models import ReadingSection, Question, Option


def parse_reading_section(text: str) -> Optional[ReadingSection]:
    """Parse reading section from cleaned HWP text.

    Expected text patterns:
    - [1~4] Group header indicating question range
    - 1. Question text
    - ① option 1  ② option 2 ...
    - Passage text before questions
    """
    lines = text.split("\n")
    passage_lines: List[str] = []
    questions: List[Question] = []
    buffer_q: dict = {}
    in_question = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip image metadata lines
        if re.search(r"\.(jpg|png|bmp|jpeg)", line, re.I) or "pixel" in line:
            continue
        if re.match(r"^\d{4}[년]\s*\d{1,2}[월]\s*\d{1,2}[일]", line):
            continue  # date metadata
        if "Adobe Photoshop" in line or "EXIF" in line or "sRGB" in line:
            continue
        if re.match(r"^\d+_?\d+_", line) and not re.search(r"[\uAC00-\uD7AF]", line):
            continue  # image filenames

        # Group header like [1~4], [5~6]
        group_m = re.match(r"^\[(\d+)~(\d+)\]\s*(.*)$", line)
        if group_m:
            in_question = True
            # If we have questions already in the buffer, finalize them
            _finalize_question(buffer_q, questions)
            continue

        # Question number: "1." "1)" "7."
        qnum_m = re.match(r"^\s*(\d{1,2})\s*[.)]\s*(.*)$", line)
        if qnum_m:
            num = int(qnum_m.group(1))
            if 1 <= num <= 20:
                _finalize_question(buffer_q, questions)
                buffer_q = {"number": num, "text": qnum_m.group(2), "options": []}
                in_question = True
                continue

        # Option line: ① text  ② text ...
        opt_m = re.findall(r"([\u2460-\u2463])\s*([^\u2460-\u2463]+?)(?=[\u2460-\u2463]|$)", line)
        if opt_m and buffer_q:
            for label, opt_text in opt_m:
                buffer_q["options"].append(Option(label=label, text=opt_text.strip()))
            continue

        # Continuation of passage or question text
        if in_question and buffer_q:
            # Check if line looks like continuation text
            if not re.match(r"^[\u2460-\u2463]", line):
                buffer_q["text"] += " " + line
        else:
            passage_lines.append(line)

    _finalize_question(buffer_q, questions)

    if questions:
        passage = "\n".join(passage_lines)
        logger.info(f"Reading: {len(questions)} questions, passage={len(passage)} chars")
        return ReadingSection(passage_text=passage, questions=questions)

    return None


def _finalize_question(buf: dict, questions: List[Question]):
    """Add buffered question to list if valid."""
    if buf and buf.get("number"):
        q = Question(
            number=buf["number"],
            text=buf["text"].strip()[:2000],
            options=buf.get("options", []),
        )
        questions.append(q)
    buf.clear()
