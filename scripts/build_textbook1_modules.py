"""Build page-faithful interactive module bundles for EPS-TOPIK textbook 1.

Inputs:
  - assets/EPS-TOPIK_textbook1 (1).zip
  - assets/EPS-TOPIK_textbook1_listen (2).zip

Outputs:
  - assets/modules/textbook1/index.json
  - assets/modules/textbook1/unit_XX/source.pdf
  - assets/modules/textbook1/unit_XX/module.json
  - assets/modules/textbook1/unit_XX/pages/page_NN.jpg
  - assets/modules/textbook1/audio/unit_XX/track_NNN.mp3
  - assets/modules/textbook1/preliminary/audio/track_NNN.mp3
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile, ZipInfo

import fitz

from module_textbook_utils import (
    UNIT_TITLE_ID,
    attach_choice_images_from_pdf_page,
    build_lesson_flow,
    extract_conversation_cards,
    extract_culture_cards,
    extract_grammar_cards,
    extract_listening_scripts_from_texts,
    extract_practice_answers_from_texts,
    extract_vocab_cards,
    parse_practice_questions_from_page,
)


ROOT = Path(__file__).resolve().parents[1]
TEXTBOOK_ZIP = ROOT / "assets" / "EPS-TOPIK_textbook1 (1).zip"
LISTENING_ZIP = ROOT / "assets" / "EPS-TOPIK_textbook1_listen (2).zip"
OUT_ROOT = ROOT / "assets" / "modules" / "textbook1"

UNIT_COUNT = 30
UNIT_FIRST_PAGE_INDEX = 50
PAGES_PER_UNIT = 10
UNIT_AUDIO_FIRST_TRACK = 28
UNIT_AUDIO_PER_UNIT = 5
PRELIMINARY_LAST_TRACK = 27


@dataclass(frozen=True)
class AudioTrack:
    track: int
    label: str
    info: ZipInfo


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def clean_text(value: str) -> str:
    value = str(value or "").replace("\x07", "").replace("\ufeff", "")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def decode_zip_name(name: str) -> str:
    try:
        return name.encode("cp437").decode("cp949")
    except UnicodeError:
        return name


def load_main_pdf_bytes() -> bytes:
    with ZipFile(TEXTBOOK_ZIP) as zip_file:
        pdfs = [info for info in zip_file.infolist() if info.filename.lower().endswith(".pdf")]
        if not pdfs:
            raise FileNotFoundError(f"No PDF found inside {TEXTBOOK_ZIP}")
        main_pdf = max(pdfs, key=lambda info: info.file_size)
        return zip_file.read(main_pdf)


def parse_title(page_text: str, unit: int) -> tuple[str, str]:
    lines = [line.strip() for line in page_text.splitlines() if line.strip()]
    title_ko = f"Unit {unit}"
    title_en = ""

    if lines:
        first = re.sub(rf"^{unit}\s+", "", lines[0]).strip()
        if first:
            title_ko = first
    if len(lines) > 1:
        title_en = re.sub(r"\s+\d+$", "", lines[1]).strip()

    return title_ko, title_en


def build_audio_index() -> dict[int, AudioTrack]:
    tracks: dict[int, AudioTrack] = {}
    with ZipFile(LISTENING_ZIP) as zip_file:
        for info in zip_file.infolist():
            if not info.filename.lower().endswith(".mp3"):
                continue
            decoded = decode_zip_name(info.filename)
            match = re.search(r"Track\s+(\d{3})(?:\s+(.+?))?\.mp3$", decoded)
            if not match:
                continue
            track_no = int(match.group(1))
            label = (match.group(2) or f"Track {track_no:03d}").strip()
            tracks[track_no] = AudioTrack(track=track_no, label=label, info=info)
    return tracks


def copy_audio(zip_file: ZipFile, track: AudioTrack, out_path: Path, force: bool) -> None:
    if out_path.exists() and not force:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zip_file.open(track.info) as src, out_path.open("wb") as dst:
        shutil.copyfileobj(src, dst)


def render_page(page: fitz.Page, out_path: Path, force: bool) -> None:
    if out_path.exists() and not force:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    matrix = fitz.Matrix(1.65, 1.65)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    pix.save(str(out_path), jpg_quality=88)


def save_unit_pdf(doc: fitz.Document, start: int, end: int, out_path: Path, force: bool) -> None:
    if out_path.exists() and not force:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    unit_doc = fitz.open()
    unit_doc.insert_pdf(doc, from_page=start, to_page=end)
    unit_doc.save(out_path, garbage=4, deflate=True)
    unit_doc.close()


def build(force: bool = False) -> None:
    if not TEXTBOOK_ZIP.exists():
        raise FileNotFoundError(TEXTBOOK_ZIP)
    if not LISTENING_ZIP.exists():
        raise FileNotFoundError(LISTENING_ZIP)

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    pdf_bytes = load_main_pdf_bytes()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    audio_tracks = build_audio_index()
    practice_answers = extract_practice_answers_from_texts(
        (doc[idx].get_text("text") for idx in range(362, min(366, doc.page_count))),
        1,
        UNIT_COUNT,
    )
    listening_scripts = extract_listening_scripts_from_texts(
        (doc[idx].get_text("text") for idx in range(366, min(370, doc.page_count))),
        1,
        UNIT_COUNT,
    )
    units = []

    with ZipFile(LISTENING_ZIP) as audio_zip:
        preliminary = []
        pre_dir = OUT_ROOT / "preliminary" / "audio"
        for track_no in range(1, PRELIMINARY_LAST_TRACK + 1):
            track = audio_tracks.get(track_no)
            if not track:
                continue
            out_audio = pre_dir / f"track_{track_no:03d}.mp3"
            copy_audio(audio_zip, track, out_audio, force)
            preliminary.append({
                "track": track_no,
                "label": track.label,
                "audio_url": rel(out_audio),
            })

        for unit in range(1, UNIT_COUNT + 1):
            start = UNIT_FIRST_PAGE_INDEX + (unit - 1) * PAGES_PER_UNIT
            end = start + PAGES_PER_UNIT - 1
            if end >= doc.page_count:
                raise IndexError(f"Unit {unit} page range exceeds PDF page count")

            unit_root = OUT_ROOT / f"unit_{unit}"
            pages_root = unit_root / "pages"
            source_pdf = unit_root / "source.pdf"
            save_unit_pdf(doc, start, end, source_pdf, force)

            first_text = clean_text(doc[start].get_text("text"))
            title_ko, title_en = parse_title(first_text, unit)
            pages = []
            for offset, page_index in enumerate(range(start, end + 1), 1):
                page_image = pages_root / f"page_{offset:02d}.jpg"
                render_page(doc[page_index], page_image, force)
                pages.append({
                    "number": offset,
                    "image": rel(page_image),
                    "text": clean_text(doc[page_index].get_text("text")),
                })

            unit_audio = []
            audio_dir = OUT_ROOT / "audio" / f"unit_{unit}"
            first_track = UNIT_AUDIO_FIRST_TRACK + (unit - 1) * UNIT_AUDIO_PER_UNIT
            for track_no in range(first_track, first_track + UNIT_AUDIO_PER_UNIT):
                track = audio_tracks.get(track_no)
                if not track:
                    continue
                out_audio = audio_dir / f"track_{track_no:03d}.mp3"
                copy_audio(audio_zip, track, out_audio, force)
                unit_audio.append({
                    "track": track_no,
                    "label": track.label,
                    "audio_url": rel(out_audio),
                })

            unit_answers = practice_answers.get(unit, {})
            unit_scripts = listening_scripts.get(unit, {})
            reading_questions = parse_practice_questions_from_page(
                pages[7],
                unit,
                "reading",
                answers=unit_answers.get("reading", {}),
            )
            listening_questions = parse_practice_questions_from_page(
                pages[8],
                unit,
                "listening",
                answers=unit_answers.get("listening", {}),
                scripts=unit_scripts,
                audio_url=unit_audio[-1]["audio_url"] if unit_audio else "",
            )
            attach_choice_images_from_pdf_page(
                doc[start + 7],
                reading_questions,
                unit_root / "choice_images" / "reading",
                rel,
                force,
            )
            attach_choice_images_from_pdf_page(
                doc[start + 8],
                listening_questions,
                unit_root / "choice_images" / "listening",
                rel,
                force,
            )
            lesson_flow = build_lesson_flow(pages, page_start=start + 1)
            vocab_cards = extract_vocab_cards(pages)
            grammar_cards = extract_grammar_cards(pages)
            conversation_cards = extract_conversation_cards(pages)
            culture_cards = extract_culture_cards(pages)

            module = {
                "book": "textbook1",
                "source": "EPS-TOPIK Standard Textbook 1",
                "unit": unit,
                "title_ko": title_ko,
                "title_en": title_en,
                "title_id": UNIT_TITLE_ID.get(unit, ""),
                "source_pdf": rel(source_pdf),
                "page_start": start + 1,
                "page_end": end + 1,
                "pages": pages,
                "sections": {
                    "lesson_flow": lesson_flow,
                    "audio": unit_audio,
                    "vocab": vocab_cards,
                    "grammar": grammar_cards,
                    "conversation": conversation_cards,
                    "culture": culture_cards,
                    "reading": reading_questions,
                    "listening": listening_questions,
                },
                "integrity": {
                    "pdf_pages": len(pages),
                    "lesson_audio": len(unit_audio),
                    "lesson_flow": len(lesson_flow),
                    "vocab_cards": len(vocab_cards),
                    "grammar_cards": len(grammar_cards),
                    "conversation_cards": len(conversation_cards),
                    "culture_cards": len(culture_cards),
                    "reading_questions": len(reading_questions),
                    "listening_questions": len(listening_questions),
                    "reading_answers": sum(1 for q in reading_questions if q.get("jawaban")),
                    "listening_answers": sum(1 for q in listening_questions if q.get("jawaban")),
                    "listening_scripts": sum(1 for q in listening_questions if q.get("audio_teks")),
                    "source_page_start_index": start,
                    "source_page_end_index": end,
                },
            }
            (unit_root / "module.json").write_text(
                json.dumps(module, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            units.append({
                "unit": unit,
                "book": "textbook1",
                "title_ko": title_ko,
                "title_en": title_en,
                "title_id": UNIT_TITLE_ID.get(unit, ""),
                "page_start": start + 1,
                "page_end": end + 1,
                "audio_count": len(unit_audio),
                "module": rel(unit_root / "module.json"),
            })
            print(
                f"unit {unit:02d}: pages=10 audio={len(unit_audio)} "
                f"vocab={len(vocab_cards)} reading={len(reading_questions)} "
                f"listening={len(listening_questions)} title={title_ko}"
            )

    index = {
        "book": "textbook1",
        "source": "EPS-TOPIK Standard Textbook 1",
        "units": units,
        "preliminary_audio": preliminary,
        "integrity": {
            "unit_count": len(units),
            "pages_per_unit": PAGES_PER_UNIT,
            "preliminary_audio": len(preliminary),
            "unit_audio": sum(unit["audio_count"] for unit in units),
        },
    }
    (OUT_ROOT / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    doc.close()
    print(
        "done: "
        f"{len(units)} units, "
        f"{len(units) * PAGES_PER_UNIT} pages, "
        f"{index['integrity']['unit_audio']} unit audio, "
        f"{index['integrity']['preliminary_audio']} preliminary audio"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Rebuild existing images, PDFs, and audio")
    args = parser.parse_args()
    build(force=args.force)


if __name__ == "__main__":
    main()
