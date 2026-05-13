"""Build page-faithful interactive module bundles for EPS-TOPIK textbook 2.

Inputs:
  - assets/langit-korea-modules/unit_31..60*.pdf
  - assets/langit-korea-modules/manifest.json
  - assets/langit-korea-extracted/unit_31..60/*.json
  - scripts/extracted_mp3/unit_XX_listening_N.mp3

Outputs:
  - assets/modules/textbook2/index.json
  - assets/modules/textbook2/unit_XX/module.json
  - assets/modules/textbook2/unit_XX/pages/page_NN.jpg
  - assets/modules/textbook2/audio/unit_XX/listening_N.mp3
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
SOURCE_MODULES = ROOT / "assets" / "langit-korea-modules"
SOURCE_EXTRACTED = ROOT / "assets" / "langit-korea-extracted"
SOURCE_UNIT_DATA = ROOT / "data"
SOURCE_AUDIO = ROOT / "scripts" / "extracted_mp3"
OUT_ROOT = ROOT / "assets" / "modules" / "textbook2"


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def clean_text(value: str) -> str:
    value = str(value or "").replace("\x07", "").replace("\ufeff", "")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def as_list(value):
    return value if isinstance(value, list) else []


def normalize_cards(items, kind: str) -> list[dict]:
    cards = []
    for idx, item in enumerate(as_list(items), 1):
        if not isinstance(item, dict):
            continue
        if kind == "grammar":
            front = clean_text(item.get("pattern", ""))
            back = clean_text(item.get("explanation", ""))
        elif kind == "conversation":
            front = clean_text(item.get("text", ""))
            speaker = clean_text(item.get("speaker", ""))
            back = speaker
        else:
            front = clean_text(item.get("korean", ""))
            back = clean_text(item.get("indonesia", ""))
        if not front and not back:
            continue
        cards.append({"id": f"{kind}_{idx}", "front": front, "back": back, "raw": item})
    return cards


def normalize_choice_path(unit: int, source: str) -> str:
    if not source:
        return ""
    unit_dir = SOURCE_EXTRACTED / f"unit_{unit}"
    candidates = [
        unit_dir / source,
        unit_dir / source.replace("_0a.", "_01."),
        unit_dir / source.replace("_0b.", "_02."),
        unit_dir / source.replace("_0c.", "_03."),
        unit_dir / source.replace("_0d.", "_04."),
    ]
    for candidate in candidates:
        if candidate.exists():
            return rel(candidate)
    return ""


def normalize_question(unit: int, q: dict, qtype: str, idx: int) -> dict:
    out = {
        "id": clean_text(q.get("id")) or f"u{unit}_{qtype}_{idx}",
        "nomor": q.get("nomor") or idx,
        "tipe": qtype,
        "instruksi": clean_text(q.get("instruksi")),
        "teks_soal": clean_text(q.get("teks_soal")),
        "jawaban": clean_text(q.get("jawaban")).lower(),
        "audio_teks": clean_text(q.get("audio_teks")),
        "audio_url": "",
        "pilihan": [],
        "gambar_pilihan": {},
    }
    for key, label in zip(("a", "b", "c", "d"), ("A", "B", "C", "D")):
        text = clean_text(q.get(f"pilihan_{key}"))
        image = ""
        if isinstance(q.get("gambar_pilihan"), dict):
            image = normalize_choice_path(unit, clean_text(q["gambar_pilihan"].get(key, "")))
        if text or image:
            out["pilihan"].append({"key": key, "label": label, "text": text, "image": image})
            if image:
                out["gambar_pilihan"][key] = image
    return out


def copy_audio(unit: int, number: int) -> str:
    src = SOURCE_AUDIO / f"unit_{unit}_listening_{number}.mp3"
    if not src.exists():
        src = SOURCE_AUDIO / f"unit_{unit:02d}_listening_{number}.mp3"
    if not src.exists():
        return ""
    dst_dir = OUT_ROOT / "audio" / f"unit_{unit}"
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / f"listening_{number}.mp3"
    if not dst.exists() or dst.stat().st_size != src.stat().st_size:
        shutil.copy2(src, dst)
    return rel(dst)


def render_pdf_pages(pdf_path: Path, out_dir: Path, force: bool = False) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    pages = []
    try:
        for idx, page in enumerate(doc, 1):
            image_path = out_dir / f"page_{idx:02d}.jpg"
            if force or not image_path.exists():
                pix = page.get_pixmap(matrix=fitz.Matrix(1.65, 1.65), alpha=False)
                pix.save(image_path)
            pages.append({
                "number": idx,
                "image": rel(image_path),
                "text": clean_text(page.get_text()),
            })
    finally:
        doc.close()
    return pages


def build_unit(manifest_item: dict, force: bool = False) -> dict:
    unit = int(manifest_item["unit"])
    source_pdf = SOURCE_MODULES / manifest_item["filename"]
    if not source_pdf.exists():
        raise FileNotFoundError(source_pdf)

    extracted_dir = SOURCE_EXTRACTED / f"unit_{unit}"
    old_data = read_json(SOURCE_UNIT_DATA / f"unit_{unit}.json", {})
    extracted_meta = read_json(extracted_dir / "data.json", {})
    reading_data = read_json(extracted_dir / "reading_data.json", {})
    listening_data = read_json(extracted_dir / "listening_data.json", {})

    out_unit = OUT_ROOT / f"unit_{unit}"
    pages = render_pdf_pages(source_pdf, out_unit / "pages", force=force)

    reading = [
        normalize_question(unit, q, "membaca", idx)
        for idx, q in enumerate(as_list(reading_data.get("soal")), 1)
    ]
    listening = [
        normalize_question(unit, q, "mendengarkan", idx)
        for idx, q in enumerate(as_list(listening_data.get("soal")), 1)
    ]
    for q in listening:
        q["audio_url"] = copy_audio(unit, int(q["nomor"]))
        if not q["instruksi"]:
            q["instruksi"] = "듣고 알맞은 답을 고르십시오."

    module = {
        "book": "textbook2",
        "source": "EPS-TOPIK Standard Textbook 2",
        "unit": unit,
        "title_ko": clean_text(manifest_item.get("title_ko") or extracted_meta.get("title_ko")),
        "title_en": clean_text(manifest_item.get("title_en") or extracted_meta.get("title_id")),
        "title_id": clean_text(extracted_meta.get("title_id") or manifest_item.get("title_en")),
        "source_pdf": rel(source_pdf),
        "page_start": manifest_item.get("page_start"),
        "page_end": manifest_item.get("page_end"),
        "pages": pages,
        "sections": {
            "vocab": normalize_cards(as_list(old_data.get("vocab1")) + as_list(old_data.get("vocab2")), "vocab"),
            "grammar": normalize_cards(as_list(old_data.get("grammar1")) + as_list(old_data.get("grammar2")), "grammar"),
            "conversation": normalize_cards(as_list(old_data.get("conversation1")) + as_list(old_data.get("conversation2")), "conversation"),
            "culture": normalize_cards(as_list(old_data.get("budaya")), "culture"),
            "reading": reading,
            "listening": listening,
        },
        "integrity": {
            "pdf_pages": len(pages),
            "vocab_cards": len(as_list(old_data.get("vocab1")) + as_list(old_data.get("vocab2"))),
            "reading_questions": len(reading),
            "listening_questions": len(listening),
            "listening_audio": sum(1 for q in listening if q.get("audio_url")),
        },
    }
    out_unit.mkdir(parents=True, exist_ok=True)
    (out_unit / "module.json").write_text(json.dumps(module, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Rerender page images even if they already exist")
    args = parser.parse_args()

    manifest = read_json(SOURCE_MODULES / "manifest.json", [])
    unit_items = [m for m in manifest if m.get("type") == "unit" and 31 <= int(m.get("unit", 0)) <= 60]
    if len(unit_items) != 30:
        raise RuntimeError(f"Expected 30 textbook2 units, found {len(unit_items)}")

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    modules = []
    for item in unit_items:
        module = build_unit(item, force=args.force)
        modules.append({
            "book": module["book"],
            "unit": module["unit"],
            "title_ko": module["title_ko"],
            "title_en": module["title_en"],
            "title_id": module["title_id"],
            "module_url": f"assets/modules/textbook2/unit_{module['unit']}/module.json",
            "source_pdf": module["source_pdf"],
            "integrity": module["integrity"],
        })
        print(
            f"Unit {module['unit']}: {module['integrity']['pdf_pages']} pages, "
            f"{module['integrity']['reading_questions']} reading, "
            f"{module['integrity']['listening_questions']} listening, "
            f"{module['integrity']['listening_audio']} audio"
        )

    index = {
        "book": "textbook2",
        "source": "EPS-TOPIK Standard Textbook 2",
        "unit_start": 31,
        "unit_end": 60,
        "units": modules,
    }
    (OUT_ROOT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {rel(OUT_ROOT / 'index.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
