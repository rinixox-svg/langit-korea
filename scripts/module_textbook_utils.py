from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import fitz


CIRCLED_TO_KEY = {
    "①": "a",
    "②": "b",
    "③": "c",
    "④": "d",
}

KEY_TO_LABEL = {
    "a": "A",
    "b": "B",
    "c": "C",
    "d": "D",
}

KEY_TO_CIRCLED = {value: key for key, value in CIRCLED_TO_KEY.items()}

SECTION_ID_LABELS = {
    "overview": "Ringkasan",
    "vocab": "Kosakata",
    "grammar": "Tata bahasa",
    "pronunciation": "Pelafalan",
    "conversation": "Percakapan",
    "useful_expression": "Ungkapan praktis",
    "culture": "Budaya dan informasi",
    "self_assessment": "Cek diri",
    "reading": "Latihan membaca",
    "listening": "Latihan mendengar",
    "preview": "Preview unit berikutnya",
}

UNIT_TITLE_ID = {
    1: "Perkenalan diri",
    2: "Barang kebutuhan sehari-hari",
    3: "Posisi dan tempat",
    4: "Kegiatan dan benda",
    5: "Tanggal dan hari",
    6: "Rutinitas harian",
    7: "Musim dan cuaca",
    8: "Keluarga dan teman",
    9: "Memesan makanan",
    10: "Membeli barang",
    11: "Pekerjaan rumah",
    12: "Transportasi umum",
    13: "Kegiatan akhir pekan",
    14: "Mencari arah",
    15: "Pakaian",
    16: "Mencari tempat tinggal",
    17: "Liburan",
    18: "Hobi",
    19: "Memasak",
    20: "Internet dan ponsel pintar",
    21: "Rumah sakit",
    22: "Apotek",
    23: "Kantor pos",
    24: "Bank",
    25: "Lembaga bantuan pekerja asing",
    26: "Budaya tempat tinggal dan makanan Korea",
    27: "Hari peringatan Korea",
    28: "Hari raya tradisional Korea",
    29: "Etika Korea",
    30: "Budaya populer Korea",
    31: "Pakaian dan sikap kerja",
    32: "Penggunaan fasilitas perusahaan",
    33: "Hubungan dengan rekan kerja",
    34: "Pencegahan pelecehan seksual",
    35: "Pengelolaan tempat kerja",
    36: "Pengelolaan pengiriman",
    37: "Pemrosesan mesin",
    38: "Perakitan mesin",
    39: "Pengolahan logam",
    40: "Pencetakan plastik dan karet",
    41: "Manufaktur tekstil",
    42: "Pembuatan furnitur",
    43: "Konstruksi bangunan",
    44: "Konstruksi sipil",
    45: "Budidaya tanaman",
    46: "Peternakan",
    47: "Perikanan pesisir dan budidaya perairan",
    48: "Pembuatan lambung kapal",
    49: "Pengembangan sumber daya mineral",
    50: "Pengembangan sumber daya hutan",
    51: "Layanan akomodasi",
    52: "Persiapan makanan",
    53: "Rambu keselamatan industri",
    54: "Peraturan keselamatan industri",
    55: "Peralatan keselamatan dan higiene",
    56: "Kecelakaan kerja dan pertolongan pertama",
    57: "Sistem izin kerja",
    58: "Undang-Undang Standar Ketenagakerjaan",
    59: "Undang-Undang Imigrasi",
    60: "Asuransi pekerja",
}


def clean_text(value: str) -> str:
    value = str(value or "").replace("\x07", "").replace("\ufeff", "")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def clean_lines(value: str) -> list[str]:
    return [clean_text(line) for line in str(value or "").splitlines() if clean_text(line)]


def has_hangul(value: str) -> bool:
    return bool(re.search(r"[가-힣ㄱ-ㅎㅏ-ㅣ]", value or ""))


def has_latin(value: str) -> bool:
    return bool(re.search(r"[A-Za-z]", value or ""))


def is_probably_footer(line: str) -> bool:
    stripped = clean_text(line)
    if not stripped:
        return True
    if stripped in {"EPS-TOPIK", "정답", "듣기지문", "듣기 지문", "부록", "Appendix"}:
        return True
    if "어휘 색인" in stripped or "고용허가제 안내" in stripped:
        return True
    if re.fullmatch(r"\d{1,3}", stripped):
        return True
    if "한국어 표준교재" in stripped:
        return True
    if "STANDARD KOREAN TEXTBOOK" in stripped:
        return True
    if re.match(r"^\d+\s+.+\s+\d{2,3}$", stripped) and has_latin(stripped):
        return True
    return False


def detect_sections(text: str, page_no: int) -> list[str]:
    joined = " ".join(clean_lines(text))
    detected: list[str] = []
    checks = [
        ("vocab", ("어휘", "VOCABULARY")),
        ("grammar", ("문법", "GRAMMAR")),
        ("pronunciation", ("발음", "PRONUNCIATION")),
        ("conversation", ("대화", "CONVERSATION")),
        ("useful_expression", ("유용한 표현", "USEFUL EXPRESSION")),
        ("culture", ("문화와 정보", "CULTURE & INFORMATION")),
        ("self_assessment", ("확인해요", "self assessment")),
        ("reading", ("읽기", "READING")),
        ("listening", ("듣기", "LISTENING")),
        ("overview", ("학습 목표", "LEARNING OBJECTIVES")),
    ]
    for section_id, needles in checks:
        if any(needle in joined for needle in needles):
            detected.append(section_id)
    if page_no == 10 and "학습 목표" in joined:
        detected = ["preview"]
    return detected


def page_flow_title(page_no: int, detected: list[str]) -> tuple[str, str, str]:
    if page_no == 1:
        return "어휘 1", "VOCABULARY 1", "Kosakata 1"
    if page_no == 2:
        return "문법 1", "GRAMMAR 1", "Tata bahasa 1"
    if page_no == 3:
        return "대화 1 / 발음", "CONVERSATION 1 / PRONUNCIATION", "Percakapan 1 dan pelafalan"
    if page_no == 4:
        return "어휘 2", "VOCABULARY 2", "Kosakata 2"
    if page_no == 5:
        return "문법 2", "GRAMMAR 2", "Tata bahasa 2"
    if page_no == 6:
        return "대화 2 / 유용한 표현", "CONVERSATION 2 / USEFUL EXPRESSION", "Percakapan 2 dan ungkapan praktis"
    if page_no == 7:
        return "문화와 정보 / 확인해요", "CULTURE & INFORMATION / SELF ASSESSMENT", "Budaya, informasi, dan cek diri"
    if page_no == 8:
        return "읽기", "READING", "Latihan membaca"
    if page_no == 9:
        return "듣기", "LISTENING", "Latihan mendengar"
    if page_no == 10:
        return "다음 단원 미리보기", "NEXT UNIT PREVIEW", "Preview unit berikutnya"
    label = " / ".join(SECTION_ID_LABELS.get(item, item) for item in detected) or "Halaman asli"
    return label, label, label


def build_lesson_flow(pages: list[dict], page_start: int | None = None) -> list[dict]:
    flow = []
    for page in pages:
        page_no = int(page.get("number", len(flow) + 1))
        detected = detect_sections(page.get("text", ""), page_no)
        title_ko, title_en, title_id = page_flow_title(page_no, detected)
        flow.append(
            {
                "id": f"page_{page_no:02d}",
                "page": page_no,
                "book_page": page_start + page_no - 1 if page_start else None,
                "image": page.get("image", ""),
                "kind": detected[0] if detected else "source",
                "sections": detected,
                "title_ko": title_ko,
                "title_en": title_en,
                "title_id": title_id,
                "body": clean_text(page.get("text", "")),
                "verification": "extracted_from_official_pdf_page",
            }
        )
    return flow


def find_heading_index(lines: list[str], section_id: str) -> int:
    for idx, line in enumerate(lines):
        joined = line.upper()
        if section_id == "vocab" and ("어휘" in line and "VOCABULARY" in joined):
            return idx
        if section_id == "grammar" and ("문법" in line and "GRAMMAR" in joined):
            return idx
        if section_id == "conversation" and ("대화" in line and "CONVERSATION" in joined):
            return idx
        if section_id == "culture" and ("문화와 정보" in line and "CULTURE" in joined):
            return idx
    return -1


def should_stop_vocab(line: str) -> bool:
    if re.match(r"^\d+\.", line):
        return True
    return any(
        token in line
        for token in (
            "관계있는 것끼리",
            "그림을 보고",
            "알맞은 것을",
            "문장을 완성",
            "문법 GRAMMAR",
            "대화 CONVERSATION",
            "발음",
            "문화와 정보",
            "읽기",
            "듣기",
            "확인해요",
        )
    )


def is_noise_vocab_line(line: str) -> bool:
    if is_probably_footer(line):
        return True
    if line in {"어휘", "VOCABULARY"}:
        return True
    if re.fullmatch(r"[⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽①②③④]+", line):
        return True
    if re.match(r"^\[ ?보기 ?\]$", line):
        return True
    return False


def split_inline_pair(line: str) -> tuple[str, str] | None:
    if not (has_hangul(line) and has_latin(line)):
        return None
    if any(token in line for token in ("Connect the", "Look at", "Complete the", "Practice", "CULTURE", "GRAMMAR")):
        return None
    match = re.match(r"^(.+?[가-힣][가-힣ㄱ-ㅎㅏ-ㅣ()/·\-\s]*)\s+([A-Za-z].+)$", line)
    if not match:
        return None
    ko = clean_text(match.group(1))
    en = clean_text(match.group(2))
    if len(ko) > 40 or not en:
        return None
    return ko, en


def strip_option_noise(value: str) -> str:
    value = clean_text(value)
    value = re.sub(r"\s+\[[0-9~]+\].*$", "", value)
    value = re.sub(r"\s+\d{1,2}\s+.+\s+[A-Z][A-Z &/\-]{3,}\s+\d{2,3}$", "", value)
    return clean_text(value)


def question_needs_choice_images(question: dict) -> bool:
    joined = clean_text(
        f"{question.get('instruksi', '')}\n{question.get('teks_soal', '')}"
    )
    if any(not option.get("text") for option in question.get("pilihan", [])):
        return True
    if "그림" in joined or "picture" in joined.lower():
        return True
    return False


def normalize_choice_images(question: dict) -> None:
    options = question.get("pilihan", [])
    images = [option.get("image", "") for option in options if option.get("image")]
    if not images:
        return
    if not question_needs_choice_images(question) and len(set(images)) < len(images):
        for option in options:
            option["image"] = ""
        question["gambar_pilihan"] = {}


def attach_choice_images_from_pdf_page(
    page: fitz.Page,
    questions: list[dict],
    out_dir: Path,
    rel_func,
    force: bool = False,
) -> None:
    words = page.get_text("words")
    question_tops: list[tuple[int, float]] = []
    markers: list[dict] = []
    for word in words:
        text = word[4]
        if re.fullmatch(r"[1-5]\.", text):
            question_tops.append((int(text[0]), float(word[1])))
        if text in CIRCLED_TO_KEY:
            markers.append(
                {
                    "key": CIRCLED_TO_KEY[text],
                    "x0": float(word[0]),
                    "y0": float(word[1]),
                    "x1": float(word[2]),
                    "y1": float(word[3]),
                }
            )
    question_tops = sorted(question_tops, key=lambda item: item[1])
    if not question_tops or not markers:
        return

    starts: dict[int, float] = {}
    for number, y in question_tops:
        if number not in starts:
            starts[number] = y
    ordered_tops = [y for _, y in question_tops]
    page_rect = page.rect
    out_dir.mkdir(parents=True, exist_ok=True)

    for question in questions:
        normalize_choice_images(question)
        if not question_needs_choice_images(question):
            continue
        q_no = int(question.get("nomor") or 0)
        if q_no not in starts:
            continue
        start_y = starts[q_no]
        next_y = next((y for y in ordered_tops if y > start_y + 2), page_rect.y1 - 30)
        q_markers = [
            marker
            for marker in markers
            if start_y - 2 <= marker["y0"] < next_y - 4
        ]
        if not q_markers:
            continue
        rows = group_option_rows(q_markers)
        for row_index, row in enumerate(rows):
            row_top = min(marker["y0"] for marker in row)
            row_bottom = (
                min(marker["y0"] for marker in rows[row_index + 1]) - 6
                if row_index + 1 < len(rows)
                else next_y - 6
            )
            row = sorted(row, key=lambda item: item["x0"])
            for idx, marker in enumerate(row):
                option = next(
                    (
                        candidate
                        for candidate in question.get("pilihan", [])
                        if candidate.get("key") == marker["key"]
                    ),
                    None,
                )
                if option is None:
                    continue
                right = row[idx + 1]["x0"] - 7 if idx + 1 < len(row) else page_rect.x1 - 42
                left = max(page_rect.x0 + 42, marker["x0"] - 7)
                top = max(page_rect.y0 + 20, row_top - 9)
                bottom = min(page_rect.y1 - 35, row_bottom)
                if right - left < 28 or bottom - top < 18:
                    continue
                image_path = out_dir / f"{question['id']}_{marker['key']}.jpg"
                if force or not image_path.exists():
                    pix = page.get_pixmap(
                        matrix=fitz.Matrix(2.2, 2.2),
                        clip=fitz.Rect(left, top, right, bottom),
                        alpha=False,
                    )
                    pix.save(str(image_path), jpg_quality=90)
                option["image"] = rel_func(image_path)
                question.setdefault("gambar_pilihan", {})[marker["key"]] = option["image"]


def group_option_rows(markers: list[dict]) -> list[list[dict]]:
    rows: list[list[dict]] = []
    for marker in sorted(markers, key=lambda item: (item["y0"], item["x0"])):
        for row in rows:
            row_y = sum(item["y0"] for item in row) / len(row)
            if abs(row_y - marker["y0"]) <= 16:
                row.append(marker)
                break
        else:
            rows.append([marker])
    return rows


def extract_vocab_cards(pages: list[dict]) -> list[dict]:
    cards: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for page in pages:
        page_no = int(page.get("number", 0))
        if page_no not in {1, 4}:
            continue
        lines = clean_lines(page.get("text", ""))
        start = find_heading_index(lines, "vocab")
        if start < 0:
            continue
        vocab_lines: list[str] = []
        for line in lines[start + 1 :]:
            if should_stop_vocab(line):
                break
            if not is_noise_vocab_line(line):
                vocab_lines.append(line)

        idx = 0
        while idx < len(vocab_lines):
            line = vocab_lines[idx]
            inline = split_inline_pair(line)
            if inline:
                ko, en = inline
                idx += 1
            elif has_hangul(line):
                ko = line
                en_parts: list[str] = []
                idx += 1
                while idx < len(vocab_lines) and not has_hangul(vocab_lines[idx]):
                    if not is_probably_footer(vocab_lines[idx]):
                        en_parts.append(vocab_lines[idx])
                    idx += 1
                en = clean_text(" ".join(en_parts))
            else:
                idx += 1
                continue
            if not ko or not en:
                continue
            key = (ko, en)
            if key in seen:
                continue
            seen.add(key)
            cards.append(
                {
                    "id": f"vocab_{len(cards) + 1}",
                    "front": ko,
                    "back": en,
                    "back_lang": "en_official",
                    "translation_id": "",
                    "source_page": page_no,
                    "source_image": page.get("image", ""),
                    "verification": "official_pdf_text_pair",
                }
            )
    return cards


def extract_grammar_cards(pages: list[dict]) -> list[dict]:
    cards: list[dict] = []
    for page in pages:
        page_no = int(page.get("number", 0))
        if page_no not in {2, 5}:
            continue
        lines = clean_lines(page.get("text", ""))
        start = find_heading_index(lines, "grammar")
        if start < 0:
            continue
        body: list[str] = []
        for line in lines[start + 1 :]:
            if re.match(r"^1\.", line) or "제시된 표현" in line or find_heading_index([line], "conversation") == 0:
                break
            if not is_probably_footer(line):
                body.append(line)
        if not body:
            continue
        pattern = body[0]
        explanation_lines = []
        for line in body[1:]:
            if line == "예" or line.startswith("예 "):
                break
            explanation_lines.append(line)
        explanation = clean_text("\n".join(explanation_lines)) or clean_text("\n".join(body[1:]))
        cards.append(
            {
                "id": f"grammar_{len(cards) + 1}",
                "front": pattern,
                "back": explanation,
                "back_lang": "ko_en_official",
                "translation_id": "",
                "source_page": page_no,
                "source_image": page.get("image", ""),
                "verification": "official_pdf_grammar_block",
            }
        )
    return cards


def is_short_speaker(line: str) -> bool:
    if not has_hangul(line) or has_latin(line):
        return False
    if any(mark in line for mark in ("?", ".", "요", "다", "까", "네", "아니요", "감사")):
        return False
    return len(line.replace(" ", "")) <= 6


def extract_conversation_cards(pages: list[dict]) -> list[dict]:
    cards: list[dict] = []
    for page in pages:
        page_no = int(page.get("number", 0))
        if page_no not in {3, 6}:
            continue
        lines = clean_lines(page.get("text", ""))
        start = find_heading_index(lines, "conversation")
        if start < 0:
            continue
        block: list[str] = []
        for line in lines[start + 1 :]:
            if "대답해 봐요" in line or "ANSWER ME" in line:
                break
            if not is_probably_footer(line):
                block.append(line)

        idx = 0
        speaker = ""
        while idx < len(block):
            line = block[idx]
            if is_short_speaker(line):
                speaker = line
                idx += 1
                continue
            if not has_hangul(line):
                idx += 1
                continue
            ko_lines = [line]
            idx += 1
            while idx < len(block) and has_hangul(block[idx]) and not is_short_speaker(block[idx]):
                ko_lines.append(block[idx])
                idx += 1
            en_lines: list[str] = []
            while idx < len(block) and not has_hangul(block[idx]):
                if has_latin(block[idx]):
                    en_lines.append(block[idx])
                idx += 1
            front = clean_text("\n".join(ko_lines))
            back = clean_text(" ".join(en_lines))
            if front and (back or len(front) > 4):
                cards.append(
                    {
                        "id": f"conversation_{len(cards) + 1}",
                        "front": front,
                        "back": back,
                        "speaker": speaker,
                        "back_lang": "en_official",
                        "translation_id": "",
                        "source_page": page_no,
                        "source_image": page.get("image", ""),
                        "verification": "official_pdf_conversation_block",
                    }
                )
            speaker = ""
    return cards


def extract_culture_cards(pages: list[dict]) -> list[dict]:
    cards: list[dict] = []
    for page in pages:
        page_no = int(page.get("number", 0))
        if page_no != 7:
            continue
        lines = clean_lines(page.get("text", ""))
        start = find_heading_index(lines, "culture")
        if start < 0:
            continue
        block = [line for line in lines[start + 1 :] if not is_probably_footer(line)]
        if not block:
            continue
        useful = [line for line in block if "self assessment" not in line and "확인해요" not in line and line != "↻"]
        title = next((line for line in useful if has_hangul(line) and not line.startswith("•")), "문화와 정보")
        english = next((line for line in useful if has_latin(line) and not has_hangul(line)), "")
        body = clean_text("\n".join(useful[:16]))
        cards.append(
            {
                "id": f"culture_{len(cards) + 1}",
                "front": title,
                "back": english or body,
                "body": body,
                "back_lang": "en_official",
                "translation_id": "",
                "source_page": page_no,
                "source_image": page.get("image", ""),
                "verification": "official_pdf_culture_block",
            }
        )
    return cards


def extract_practice_answers_from_texts(texts: Iterable[str], unit_min: int, unit_max: int) -> dict[int, dict[str, dict[int, str]]]:
    answers: dict[int, dict[str, dict[int, str]]] = {}
    current_unit: int | None = None
    current_kind: str | None = None
    for text in texts:
        lines = clean_lines(text)
        for idx, line in enumerate(lines):
            if re.fullmatch(r"\d{1,2}", line):
                unit = int(line)
                if unit_min <= unit <= unit_max:
                    prev = lines[idx - 1] if idx else ""
                    next_line = lines[idx + 1] if idx + 1 < len(lines) else ""
                    if has_hangul(prev) and next_line in {"읽기", "듣기"}:
                        current_unit = unit
                        current_kind = None
                        answers.setdefault(unit, {"reading": {}, "listening": {}})
                        continue
            if line == "읽기":
                current_kind = "reading"
                continue
            if line == "듣기":
                current_kind = "listening"
                continue
            if current_unit is None or current_kind is None:
                continue
            for number, circled in re.findall(r"(\d+)\.\s*([①②③④])", line):
                q_no = int(number)
                if 1 <= q_no <= 5:
                    answers[current_unit][current_kind][q_no] = CIRCLED_TO_KEY[circled]
    return answers


def extract_listening_scripts_from_texts(texts: Iterable[str], unit_min: int, unit_max: int) -> dict[int, dict[int, str]]:
    scripts: dict[int, dict[int, str]] = {}
    current_unit: int | None = None
    current_question: int | None = None
    buffers: dict[tuple[int, int], list[str]] = {}
    for text in texts:
        lines = clean_lines(text)
        for idx, line in enumerate(lines):
            if idx + 1 < len(lines) and re.fullmatch(r"\d{1,2}", lines[idx + 1]):
                next_unit = int(lines[idx + 1])
                if unit_min <= next_unit <= unit_max and has_hangul(line):
                    current_question = None
                    continue
            if re.fullmatch(r"\d{1,2}", line):
                unit = int(line)
                if unit_min <= unit <= unit_max:
                    prev = lines[idx - 1] if idx else ""
                    if has_hangul(prev):
                        current_unit = unit
                        current_question = None
                        scripts.setdefault(unit, {})
                        continue
            match = re.match(r"^(\d)[.\s\t]+(.+)$", line)
            if current_unit is not None and match:
                q_no = int(match.group(1))
                if 1 <= q_no <= 5:
                    current_question = q_no
                    buffers.setdefault((current_unit, q_no), []).append(clean_text(match.group(2)))
                    continue
            if current_unit is not None and current_question is not None:
                if line in {"듣기 지문", "듣기지문"} or is_probably_footer(line):
                    current_question = None
                    continue
                buffers.setdefault((current_unit, current_question), []).append(line)

    for (unit, q_no), parts in buffers.items():
        script = clean_text("\n".join(parts))
        if script:
            scripts.setdefault(unit, {})[q_no] = script
    return scripts


def parse_practice_questions_from_page(
    page: dict,
    unit: int,
    kind: str,
    answers: dict[int, str] | None = None,
    scripts: dict[int, str] | None = None,
    audio_url: str = "",
) -> list[dict]:
    lines = clean_lines(page.get("text", ""))
    filtered: list[str] = []
    for line in lines:
        if line in {"읽기 READING", "듣기 LISTENING", "읽기", "듣기"}:
            continue
        if is_probably_footer(line):
            continue
        filtered.append(line)

    if kind == "listening":
        first_option_idx = next(
            (idx for idx, line in enumerate(filtered) if re.match(r"^[①②③④]", line)),
            None,
        )
        if first_option_idx is not None:
            question_starts = [
                idx
                for idx, line in enumerate(filtered[: first_option_idx + 1])
                if re.match(r"^[1-5]\.\s*", line)
            ]
            if question_starts:
                filtered = filtered[question_starts[-1] :]

    starts: list[tuple[int, int, str]] = []
    group_note = ""
    group_range: tuple[int, int] | None = None
    group_notes_by_q: dict[int, str] = {}
    for idx, line in enumerate(filtered):
        group_match = re.match(r"^\[(\d+)~(\d+)\]\s*(.+)$", line)
        if group_match:
            group_range = (int(group_match.group(1)), int(group_match.group(2)))
            group_note = clean_text(group_match.group(3))
            continue
        match = re.match(r"^(\d)\.\s*(.*)$", line)
        if not match:
            continue
        q_no = int(match.group(1))
        if q_no == 1 and len(starts) >= 5:
            break
        if 1 <= q_no <= 5:
            starts.append((idx, q_no, clean_text(match.group(2))))
            if group_range and group_range[0] <= q_no <= group_range[1]:
                group_notes_by_q[q_no] = group_note
            if group_range and q_no >= group_range[1]:
                group_range = None
                group_note = ""
        if len(starts) >= 5:
            continue

    questions: list[dict] = []
    for pos, (start_idx, q_no, first_line) in enumerate(starts[:5]):
        end_idx = starts[pos + 1][0] if pos + 1 < len(starts[:5]) else len(filtered)
        segment = [first_line] if first_line else []
        segment.extend(filtered[start_idx + 1 : end_idx])
        stem_lines: list[str] = []
        options: list[dict] = []
        current_option: dict | None = None
        for raw_line in segment:
            line = clean_text(raw_line)
            if not line or is_probably_footer(line):
                continue
            opt_match = re.match(r"^([①②③④])\s*(.*)$", line)
            if opt_match:
                key = CIRCLED_TO_KEY[opt_match.group(1)]
                current_option = {
                    "key": key,
                    "label": KEY_TO_LABEL[key],
                    "text": strip_option_noise(opt_match.group(2)),
                    "image": "",
                }
                options.append(current_option)
                continue
            if line.startswith("[") or re.match(r"^\d+\s+.+\s+\d{2,3}$", line):
                current_option = None
                continue
            if current_option is not None:
                if re.match(r"^\d\.\s*", line):
                    break
                current_option["text"] = strip_option_noise(f"{current_option['text']} {line}")
            else:
                stem_lines.append(line)
        group = group_notes_by_q.get(q_no, "")
        stem = clean_text("\n".join([group] + stem_lines if group else stem_lines))
        answer = (answers or {}).get(q_no, "")
        question = {
            "id": f"u{unit}_{'l' if kind == 'listening' else 'r'}{q_no}",
            "nomor": q_no,
            "tipe": "mendengarkan" if kind == "listening" else "membaca",
            "instruksi": "",
            "teks_soal": stem,
            "jawaban": answer,
            "audio_teks": (scripts or {}).get(q_no, ""),
            "audio_url": audio_url if kind == "listening" else "",
            "pilihan": options,
            "gambar_pilihan": {},
            "source_page": page.get("number"),
            "source_page_image": page.get("image", ""),
            "verification": "question_from_official_pdf_answer_from_official_appendix" if answer else "question_from_official_pdf",
        }
        questions.append(question)
    return questions
