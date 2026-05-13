"""
Pure parsing rules for EPS-TOPIK PDF layout blocks.
No I/O, no classes — pure functions only.
"""
import re
from typing import List, Dict, Tuple, Optional

# ── Constants ──
CIRCLED = "\u2460\u2461\u2462\u2463"  # ①②③④
CIRCLED_MAP = {"\u2460": "①", "\u2461": "②", "\u2462": "③", "\u2463": "④"}
LABEL_MAP = {"\u2460": "a", "\u2461": "b", "\u2462": "c", "\u2463": "d",
             "①": "a", "②": "b", "③": "c", "④": "d",
             "a": "a", "b": "b", "c": "c", "d": "d",
             "A": "a", "B": "b", "C": "c", "D": "d"}

QUESTION_START_RE = re.compile(r"^\s*(\d{1,2})\s*[\.\s\)]")
OPTION_CIRCLED_RE = re.compile(r"([\u2460-\u2463\u2460-\u2463])\s*([^\u2460-\u2463\u2460-\u2463]+?)(?=[\u2460-\u2463\u2460-\u2463]|$)")
OPTION_PAREN_RE = re.compile(r"\(([A-Da-d])\)\s*([^\(]+?)(?=\([A-Da-d]\)|$)")
OPTION_NUM_RE = re.compile(r"^(?:1\)|2\)|3\)|4\))\s*(.+)$", re.MULTILINE)
DIALOG_SPEAKER_RE = re.compile(r"^[\[\(]?([남여MmWw])[\]\)]?\s*[:.\s]\s*.*")
DIALOG_OPEN_RE = re.compile(r"^[\[\(]([남여Mm]an?|[Ww]oman?)[\]\)]\s*[:.\s]\s*(.*)")

# ── Question Detection ──

def is_question_start(text: str) -> Tuple[bool, Optional[int]]:
    """Return (True, question_number) if text starts with a question number."""
    text = text.strip().replace("\n", " ")
    m = QUESTION_START_RE.match(text)
    if m:
        num = int(m.group(1))
        if 1 <= num <= 40:
            return True, num
    return False, None


def is_question_group_header(text: str) -> Tuple[bool, int, int]:
    """Detect [1~4] [5~6] style group headers."""
    m = re.match(r"^\s*\[(\d{1,2})\s*~\s*(\d{1,2})\]\s*(.*)", text.strip())
    if m:
        return True, int(m.group(1)), int(m.group(2))
    return False, 0, 0


# ── Option Extraction ──

def extract_options(text: str) -> List[Dict[str, str]]:
    """Extract multiple-choice options from text.

    Supports formats:
    - ① text (circled + text on same line)
    - ①\n text (circled on its own line, text on next)
    - ① text ② text (multiple on same line)
    - (A) text (B) text
    - Fallback: split by newlines

    Returns list of {"label": "①"/"(A)", "text": "..."}
    """
    if not text or not text.strip():
        return []

    lines = text.split("\n")
    opts = []

    # Strategy 1: circled number on its own line, text on next line
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        m = re.match(r"^([\u2460-\u2463])\s*$", line)
        if m:
            label = m.group(1)
            # Look ahead: text on the next non-empty line
            next_text = ""
            j = i + 1
            while j < len(lines):
                nxt = lines[j].strip()
                if nxt and not re.match(r"^[\u2460-\u2463]", nxt):
                    next_text = nxt.rstrip("|").strip()
                    break
                elif nxt and re.match(r"^[\u2460-\u2463]", nxt):
                    break
                j += 1
            if next_text:
                opts.append({"label": label, "text": next_text})
                i = j
                continue
        i += 1

    if len(opts) >= 2:
        return opts

    # Strategy 2: circled + text on same line
    for line in lines:
        m = re.match(r"^([\u2460-\u2463])\s*(.*)", line.strip())
        if m:
            opt_text = m.group(2).strip().rstrip("|").strip()
            if opt_text and not any(o["label"] == m.group(1) for o in opts):
                opts.append({"label": m.group(1), "text": opt_text})

    if len(opts) >= 2:
        return opts

    # Strategy 3: inline circled (multiple per line)
    for m in OPTION_CIRCLED_RE.finditer(text):
        label = m.group(1)
        opt_text = m.group(2).strip().rstrip("|").strip()
        if opt_text and not any(o["label"] == label for o in opts):
            opts.append({"label": label, "text": opt_text})
    if len(opts) >= 2:
        return opts

    # Strategy 4: (A)(B)(C)(D) format
    for m in OPTION_PAREN_RE.finditer(text):
        label = f"({m.group(1).upper()})"
        opt_text = m.group(2).strip()
        if opt_text and not any(o["label"] == label for o in opts):
            opts.append({"label": label, "text": opt_text})
    if len(opts) >= 2:
        return opts

    # Strategy 5: fallback — split by newlines
    clean_lines = [l.strip() for l in lines if l.strip()]
    if len(clean_lines) >= 2:
        labels = ["①", "②", "③", "④"]
        for i_cl, line in enumerate(clean_lines[:4]):
            if not any(lbl in line for lbl in labels):
                pass  # still add it
            opts.append({"label": labels[i_cl], "text": line[:500]})
        if any(o["text"] for o in opts):
            return opts

    return opts


def split_option_line(line: str) -> List[Dict[str, str]]:
    """Split a single line containing multiple options.
    E.g.: "① 설명 ② 거절" -> [{"label":"①","text":"설명"}, {"label":"②","text":"거절"}]
    """
    return extract_options(line)


# ── Reading Section Splitting ──

def split_reading_questions(blocks: List[Dict]) -> Tuple[str, List[List[Dict]]]:
    """Split reading page blocks into passage + list of question blocks.

    Args:
        blocks: List of dicts with keys 'text', 'x0', 'y0', 'x1', 'y1', 'page'

    Returns:
        (passage_text, question_blocks_list)
        - passage_text: combined text before first question
        - question_blocks_list: each item is list of blocks for one question number
    """
    # Sort by vertical position
    sorted_blocks = sorted(blocks, key=lambda b: (b.get("page", 1), b.get("y0", 0), b.get("x0", 0)))

    passage_blocks: List[Dict] = []
    question_groups: List[List[Dict]] = []
    current_group: List[Dict] = []
    found_first_question = False
    current_qnum: Optional[int] = None

    for block in sorted_blocks:
        text = block.get("text", "").strip()
        if not text:
            continue

        # Skip headers
        if any(h in text for h in ["EPS-TOPIK", "Reading", "읽기", "TOPIK"]):
            if len(text) < 30:
                continue

        is_q, qnum = is_question_start(text)
        is_group, gs, ge = is_question_group_header(text)

        if is_q and qnum and 1 <= qnum <= 20:
            if current_group:
                question_groups.append(current_group)
            current_group = [block]
            current_qnum = qnum
            found_first_question = True
        elif is_group and found_first_question:
            # Group header like [1~4] — attach to current question if any
            if current_group:
                current_group.append(block)
            else:
                passage_blocks.append(block)
        elif found_first_question:
            if current_group is not None:
                current_group.append(block)
        else:
            passage_blocks.append(block)

    # Don't forget last question
    if current_group:
        question_groups.append(current_group)

    # Build passage text
    passage_text = "\n".join(
        b.get("text", "") for b in passage_blocks
        if not any(h in b.get("text", "") for h in ["EPS-TOPIK", "Reading"])
    ).strip()

    return passage_text, question_groups


# ── Listening Item Splitting ──

def split_listening_items(blocks: List[Dict]) -> List[Dict]:
    """Split listening page blocks into items.

    Args:
        blocks: List of dicts from PDF layout

    Returns:
        List of {"number": int, "script": str, "question": str, "options": [...], "blocks": [...]}
    """
    sorted_blocks = sorted(blocks, key=lambda b: (b.get("page", 1), b.get("y0", 0), b.get("x0", 0)))

    items: List[Dict] = []
    current: Optional[Dict] = None
    dialog_lines: List[str] = []

    for block in sorted_blocks:
        text = block.get("text", "").strip()
        if not text:
            continue

        # Skip headers
        if text.strip() in ("Listening", "듣기", "EPS-TOPIK"):
            if any(h in text for h in ["Listening", "듣기", "TOPIK"]) and len(text) < 20:
                continue

        is_q, qnum = is_question_start(text)

        if is_q and qnum and 21 <= qnum <= 40:
            # Save previous item
            if current:
                current["script"] = "\n".join(dialog_lines).strip()
                items.append(current)

            current = {
                "number": qnum,
                "script": "",
                "question": text,
                "options": [],
                "blocks": [block],
            }
            dialog_lines = []
        elif current is not None:
            current.setdefault("blocks", []).append(block)

            # Check for options in this block
            opts = extract_options(text)
            if opts:
                current["options"].extend(opts)

            # Check for dialog markers
            dm = DIALOG_OPEN_RE.match(text)
            if dm:
                dialog_lines.append(dm.group(2).strip())
            elif re.match(r"^[\[\(][남여MmWw]", text):
                # Remove speaker marker
                clean = re.sub(r"^[\[\(][^\]\)]*[\]\)]\s*", "", text).strip()
                if clean:
                    dialog_lines.append(clean)
            elif dialog_lines and not opts:
                # Continuation of dialog (indented or same paragraph)
                dialog_lines.append(text)

    # Save last item
    if current:
        current["script"] = "\n".join(dialog_lines).strip()
        items.append(current)

    return items


# ── Block Cleaning ──

def clean_block_text(text: str) -> str:
    """Clean block text: remove repeated spaces, normalize newlines."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def is_image_metadata(text: str) -> bool:
    """Check if text line is image metadata (to skip)."""
    lower = text.lower()
    if any(x in lower for x in ["pixel", "photoshop", "exif", "srgb", "adobe"]):
        return True
    if re.match(r"^\d{4}[년]\s*\d{1,2}[월]\s*\d{1,2}[일]", text):
        return True
    if re.match(r"^\d+_?\d+_", text) and not re.search(r"[\uAC00-\uD7AF]", text):
        return True
    return False


def extract_answer_from_line(text: str) -> Optional[str]:
    """Extract answer letter from a line containing circled answer."""
    for c in text:
        if c in LABEL_MAP:
            return LABEL_MAP[c]
    return None
