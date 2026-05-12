"""
HWP extraction engine with multi-strategy:
1. LibreOffice → PDF (if available)
2. zlib BodyText decompression + smart filtering (primary)
3. olefile PrvText fallback (simplest)
"""
import hashlib
import re
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path
from typing import Optional, List, Tuple

import olefile
from loguru import logger


# ── LibreOffice ──

def find_libreoffice() -> Optional[str]:
    candidates = [
        "soffice.com", "soffice",
        r"C:\Program Files\LibreOffice\program\soffice.com",
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.com",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    for path in candidates:
        try:
            r = subprocess.run([path, "--version"], capture_output=True, timeout=10)
            if r.returncode == 0:
                return path
        except:
            continue
    return None


def convert_hwp_to_pdf(hwp_path: str) -> Optional[str]:
    lo = find_libreoffice()
    if not lo:
        return None
    stem = Path(hwp_path).stem
    pdf_path = str(Path(hwp_path).parent / f"{stem}.pdf")
    try:
        r = subprocess.run(
            [lo, "--headless", "--convert-to", "pdf", "--outdir", str(Path(hwp_path).parent), hwp_path],
            capture_output=True, timeout=120
        )
        if r.returncode == 0 and Path(pdf_path).exists() and Path(pdf_path).stat().st_size > 1000:
            return pdf_path
    except:
        pass
    return None


# ── HWP BodyText → clean text via zlib ──

def extract_full_text_from_hwp(hwp_path: str) -> str:
    """Extract clean readable text from HWP file using zlib + smart filtering.
    Returns a single string with all readable Korean/English text."""
    data = Path(hwp_path).read_bytes()
    return _extract_from_bytes(data)


def extract_full_text_from_hwp_data(data: bytes) -> str:
    return _extract_from_bytes(data)


def _extract_from_bytes(data: bytes) -> str:
    """Core extraction: zlib BodyText + smart filtering."""
    import io
    try:
        ole = olefile.OleFileIO(io.BytesIO(data))
    except:
        return ""

    # Try BodyText/Section0 via zlib
    body_text = ""
    if ole.exists("BodyText/Section0"):
        raw = ole.openstream("BodyText/Section0").read()
        try:
            d = zlib.decompress(raw, -zlib.MAX_WBITS)
            body_text = _clean_hwp_body(d.decode("utf-16-le", errors="replace"))
        except:
            pass

    # Fallback: PrvText
    prv_text = ""
    if ole.exists("PrvText"):
        prv_text = ole.openstream("PrvText").read().decode("utf-16-le", errors="replace")

    ole.close()

    # Return the longest meaningful text
    body_lines = len([l for l in body_text.split("\n") if len(l.strip()) > 5])
    prv_lines = len([l for l in prv_text.split("\n") if len(l.strip()) > 5])

    if body_lines >= prv_lines and body_lines > 5:
        return body_text
    return prv_text


def _clean_hwp_body(raw_txt: str) -> str:
    """Clean HWP body text: strip formatting codes, keep runs of Korean/English text."""

    # Strategy: scan character by character, keep meaningful runs
    paragraphs = []
    buf = ""
    korean_count = 0
    total_printable = 0

    for ch in raw_txt:
        cp = ord(ch)

        # Korean syllables (U+AC00–U+D7AF) — main text
        if 0xAC00 <= cp <= 0xD7AF:
            buf += ch
            korean_count += 1
            total_printable += 1

        # Circled numbers ①-④
        elif 0x2460 <= cp <= 0x2463:
            buf += ch
            total_printable += 1

        # ASCII printable
        elif 0x0020 <= cp <= 0x007E:
            buf += ch
            if ch.isalnum() or ch in ".?!,;-:()[]{}":
                total_printable += 1

        # Newline
        elif cp == 10:
            if _is_meaningful_line(buf.strip(), korean_count, total_printable):
                paragraphs.append(buf.strip())
            buf = ""
            korean_count = 0
            total_printable = 0

        # Space or tab
        elif cp in (0x09, 0x20):
            buf += " "

        # Korean Jamo
        elif 0x1100 <= cp <= 0x11FF or 0x3130 <= cp <= 0x318F:
            buf += ch
            korean_count += 1
            total_printable += 1

        # CJK punctuation
        elif 0x3000 <= cp <= 0x303F:
            buf += ch
            total_printable += 1

        # Non-printable: reset buffer (formatting code boundary)
        else:
            if _is_meaningful_line(buf.strip(), korean_count, total_printable):
                paragraphs.append(buf.strip())
            buf = ""
            korean_count = 0
            total_printable = 0

    # Last paragraph
    if _is_meaningful_line(buf.strip(), korean_count, total_printable):
        paragraphs.append(buf.strip())

    # Join and clean
    result = "\n".join(paragraphs)
    result = re.sub(r" {2,}", " ", result)
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result


def _is_meaningful_line(line: str, korean_count: int, total: int) -> bool:
    """Check if a line has meaningful content."""
    if not line or len(line) < 3:
        return False
    
    # Reject pure formatting codes
    if "Clickhere" in line or "HelpState" in line or "wstring" in line:
        return False
    if line.startswith("=") and ":" in line:
        return False
    if re.match(r"^[\d\s\-:/.%()]+$", line):
        return False
    if re.match(r"^[\uAC00-\uD7AF]{1,2}$", line):
        return False  # just 1-2 Korean chars with no context
    
    # Must have enough Korean or meaningful content  
    has_korean = korean_count > 2
    has_sentence = bool(re.search(r"[\uAC00-\uD7AF]{3,}", line))  # 3+ consecutive Korean
    has_meaningful_ascii = total > 10 and any(c.isalpha() for c in line)
    
    return (has_sentence or has_korean) or (has_meaningful_ascii and total > 15)


# ── Extract Key Sections ──

def extract_reading_text(hwp_path: str) -> str:
    """Extract text that contains reading questions (1-20) from HWP."""
    text = extract_full_text_from_hwp(hwp_path)
    return text


def extract_listening_scripts(hwp_path: str) -> str:
    """Extract listening scripts and answer keys."""
    text = extract_full_text_from_hwp(hwp_path)
    return text


# ── Answer Parsing ──

def extract_answers_from_hwp(hwp_path: str) -> dict:
    """Extract answer key (Q# -> a/b/c/d) from answer HWP."""
    data = Path(hwp_path).read_bytes()
    try:
        import io
        ole = olefile.OleFileIO(io.BytesIO(data))
        prv = ""
        if ole.exists("PrvText"):
            prv = ole.openstream("PrvText").read().decode("utf-16-le", errors="replace")
        body = ""
        if ole.exists("BodyText/Section0"):
            raw = ole.openstream("BodyText/Section0").read()
            d = zlib.decompress(raw, -zlib.MAX_WBITS)
            body = _clean_hwp_body(d.decode("utf-16-le", errors="replace"))
        ole.close()
    except:
        return {}

    full_text = prv + "\n" + body
    return _parse_answers(full_text)


def _parse_answers(text: str) -> dict:
    """Parse answer patterns from text."""
    answers = {}
    ans_map = {"\u2460": "a", "\u2461": "b", "\u2462": "c", "\u2463": "d",
               "\u2460": "a", "\u2461": "b", "\u2462": "c", "\u2463": "d",
               "a": "a", "b": "b", "c": "c", "d": "d",
               "A": "a", "B": "b", "C": "c", "D": "d"}

    # Pattern: <1번><④> (reading answers)
    for m in re.finditer(r"<(\d+)\uBC88>\s*<([\u2460-\u2463])>", text):
        num = int(m.group(1))
        if 1 <= num <= 40 and m.group(2) in ans_map:
            answers[num] = ans_map[m.group(2)]

    # Pattern: 21. ① (listening line-start)
    for m in re.finditer(r"^(\d{1,2})\s*[.)]\s*([\u2460-\u2463])", text, re.M):
        num = int(m.group(1))
        if 1 <= num <= 40 and num not in answers:
            answers[num] = ans_map.get(m.group(2), "")

    return answers


# ── Utility ──

def compute_sha256(filepath: str) -> str:
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()
