"""
Listening section parser. Parses EPS-TOPIK listening questions with dialog scripts.
"""
import re
from typing import List, Optional

from loguru import logger

from models.extraction_models import ListeningItem, ListeningSection, Option


def parse_listening_section(text: str) -> Optional[ListeningSection]:
    """Parse listening section from PrvText of answers+scripts HWP.

    Expected format from file 4 (listening answers + scripts):
    21. ①
    Dialog or answer text
    
    22. ①  
    Dialog text
    
    23. ③
    Option text here

    Lines with options:
    ① option 1
    ② option 2
    ...
    
    Dialog speaker patterns:
    남: ... (Man speaker)
    여: ... (Woman speaker)
    """
    lines = text.split("\n")
    items: List[ListeningItem] = []
    buffer = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect question start: "21." "21)" "21 ①"
        m = re.match(r"^\s*(\d{1,2})\s*[.)]?\s*([\u2460-\u2463])?\s*(.*)", line)
        if m:
            num = int(m.group(1))
            if 21 <= num <= 40:
                _finalize_item(buffer, items)
                buffer = {
                    "number": num,
                    "dialog": [],
                    "question": "",
                    "options": [],
                    "answer": _circled_to_letter(m.group(2)) if m.group(2) else "",
                    "answer_line_rest": m.group(3).strip(),
                }
                continue

        # Process content lines
        if not buffer:
            continue

        # Option: ① text  ② text ...
        opts = re.findall(r"([\u2460-\u2463])\s*([^\u2460-\u2463]+?)(?=[\u2460-\u2463]|$)", line)
        if opts:
            for label, opt_text in opts:
                buffer["options"].append(Option(label=label, text=opt_text.strip()))
            continue

        # Dialog line with speaker
        speaker_m = re.match(r"^([남여Mm])\s*[:.\s]\s*(.*)", line)
        if speaker_m:
            dialog_line = speaker_m.group(2).strip()
            if dialog_line:
                buffer["dialog"].append(dialog_line)
            continue

        # Answer-only line (just circled number with no other context)
        ans_only = re.match(r"^([\u2460-\u2463])\s*$", line)
        if ans_only:
            if not buffer.get("answer"):
                buffer["answer"] = _circled_to_letter(ans_only.group(1))
            continue

        # Regular text — might be question continuation or answer
        if not buffer.get("question"):
            buffer["question"] = line
        else:
            # Append to dialog if it looks like dialog continuation
            buffer["dialog"].append(line)

    _finalize_item(buffer, items)

    if items:
        logger.info(f"Listening: {len(items)} items")
        return ListeningSection(items=items)

    return None


def _finalize_item(buf: dict, items: List[ListeningItem]):
    if buf and buf.get("number"):
        dialog = "\n".join(buf.get("dialog", []))
        item = ListeningItem(
            number=buf["number"],
            dialog_script=dialog[:5000],
            question=buf.get("question", "")[:2000],
            options=buf.get("options", []),
        )
        items.append(item)
    buf.clear()


def _circled_to_letter(c: str) -> str:
    mapping = {"\u2460": "a", "\u2461": "b", "\u2462": "c", "\u2463": "d"}
    return mapping.get(c, c)
