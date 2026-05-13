"""Build a page-faithful Special EPS-TOPIK work-related question bundle.

Source: HRD Korea public workbook page.

Outputs:
  - assets/special-eps/work-related/index.json
  - assets/special-eps/work-related/sources/*.pdf
  - assets/special-eps/work-related/<category>/pages/page_NN.jpg
  - assets/special-eps/work-related/<category>/module.json
  - assets/special-eps/work-related/answers/*.xlsx
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import fitz


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "assets" / "special-eps" / "work-related"
SOURCE_ROOT = OUT_ROOT / "sources"
ANSWER_ROOT = OUT_ROOT / "answers"

ANSWER_ZIP_URL = "https://eps.hrdkorea.or.kr/epstopik/eps_klt/upload/special/answersinSpecialEPSTOPIK.zip"


@dataclass(frozen=True)
class Category:
    slug: str
    title: str
    title_ko: str
    url: str
    answer_sheet: str


CATEGORIES = [
    Category("machinery-molding", "Machinery, Molding", "기계, 금형", "https://eps.hrdkorea.or.kr/epstopik/eps_klt/upload/special/MachineryMolding.pdf", "Machinery, Molding"),
    Category("metal", "Metal", "금속", "https://eps.hrdkorea.or.kr/epstopik/eps_klt/upload/special/Metal.pdf", "Metal"),
    Category("electronics-electricity", "Electronics, Electricity", "전자, 전기", "https://eps.hrdkorea.or.kr/epstopik/eps_klt/upload/special/ElectronicsElectricity.pdf", "Electronics, Electricity"),
    Category("food-related", "Food Related", "음식료", "https://eps.hrdkorea.or.kr/epstopik/eps_klt/upload/special/Food%20Related.pdf", "Food Related"),
    Category("textile-sewing", "Textile, Sewing", "섬유, 봉제", "https://eps.hrdkorea.or.kr/epstopik/eps_klt/upload/special/TextileSewing.pdf", "Textile, Sewing"),
    Category("chemical", "Chemical", "화학", "https://eps.hrdkorea.or.kr/epstopik/eps_klt/upload/special/Chemical.pdf", "Chemical"),
    Category("rubber-plastic", "Rubber, Plastic", "고무, 플라스틱", "https://eps.hrdkorea.or.kr/epstopik/eps_klt/upload/special/RubberPlastic.pdf", "Rubber, Plastic"),
    Category("pulp-paper-wood", "Pulp, Paper, Wood", "펄프, 종이, 목재", "https://eps.hrdkorea.or.kr/epstopik/eps_klt/upload/special/PulpPaperWood.pdf", "Pulp, Paper, Wood"),
]

NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

CHOICE_MAP = {
    "①": "a",
    "②": "b",
    "③": "c",
    "④": "d",
    "1": "a",
    "2": "b",
    "3": "c",
    "4": "d",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def download(url: str, out_path: Path, force: bool = False) -> None:
    if out_path.exists() and not force:
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "LangitKoreaBuilder/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response, out_path.open("wb") as out_file:
        shutil.copyfileobj(response, out_file)


def render_pdf(pdf_path: Path, category_root: Path, force: bool) -> list[dict]:
    doc = fitz.open(pdf_path)
    pages = []
    pages_root = category_root / "pages"
    for page_index in range(doc.page_count):
        out_image = pages_root / f"page_{page_index + 1:02d}.jpg"
        if force or not out_image.exists():
            out_image.parent.mkdir(parents=True, exist_ok=True)
            pix = doc[page_index].get_pixmap(matrix=fitz.Matrix(1.65, 1.65), alpha=False)
            pix.save(str(out_image), jpg_quality=88)
        pages.append({
            "number": page_index + 1,
            "image": rel(out_image),
            "text": doc[page_index].get_text("text").strip(),
        })
    doc.close()
    return pages


def decode_zip_name(name: str) -> str:
    try:
        return name.encode("cp437").decode("cp949")
    except UnicodeError:
        return name


def cell_ref_to_col(ref: str) -> int:
    letters = re.sub(r"[^A-Z]", "", ref.upper())
    value = 0
    for letter in letters:
        value = value * 26 + ord(letter) - ord("A") + 1
    return value


def read_shared_strings(xlsx: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in xlsx.namelist():
        return []
    root = ET.fromstring(xlsx.read("xl/sharedStrings.xml"))
    values = []
    for si in root.findall("a:si", NS):
        values.append("".join(t.text or "" for t in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")))
    return values


def cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    value_el = cell.find("a:v", NS)
    if value_el is None or value_el.text is None:
        return ""
    value = value_el.text.strip()
    if cell.attrib.get("t") == "s" and value:
        return shared_strings[int(value)].strip()
    return value


def parse_answer_sheet(xlsx_bytes: bytes) -> dict[str, list[dict]]:
    with ZipFile(BytesIO(xlsx_bytes)) as xlsx:
        workbook = ET.fromstring(xlsx.read("xl/workbook.xml"))
        relationships = ET.fromstring(xlsx.read("xl/_rels/workbook.xml.rels"))
        rel_targets = {
            rel.attrib["Id"]: rel.attrib["Target"].lstrip("/")
            for rel in relationships.findall("rel:Relationship", NS)
        }
        shared_strings = read_shared_strings(xlsx)
        answers_by_sheet: dict[str, list[dict]] = {}

        for sheet in workbook.findall("a:sheets/a:sheet", NS):
            sheet_name = sheet.attrib["name"]
            rel_id = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            target = rel_targets[rel_id]
            sheet_path = target if target.startswith("xl/") else f"xl/{target}"
            root = ET.fromstring(xlsx.read(sheet_path))
            rows = root.findall("a:sheetData/a:row", NS)
            answers: list[dict] = []
            for row in rows[2:]:
                cells_by_col = {
                    cell_ref_to_col(cell.attrib.get("r", "")): cell_value(cell, shared_strings)
                    for cell in row.findall("a:c", NS)
                }
                for q_col, a_col in [(1, 2), (3, 4), (5, 6), (7, 8)]:
                    question_raw = cells_by_col.get(q_col, "").strip()
                    answer_raw = cells_by_col.get(a_col, "").strip()
                    if not question_raw or not answer_raw:
                        continue
                    try:
                        question = int(float(question_raw))
                    except ValueError:
                        continue
                    symbol = answer_raw.replace(" ", "")
                    answers.append({
                        "number": question,
                        "answer_symbol": symbol,
                        "answer_key": CHOICE_MAP.get(symbol, ""),
                    })
            answers_by_sheet[sheet_name] = sorted(answers, key=lambda item: item["number"])
    return answers_by_sheet


def extract_answers(zip_path: Path, force: bool) -> dict[str, list[dict]]:
    answers_by_sheet: dict[str, list[dict]] = {}
    with ZipFile(zip_path) as zip_file:
        for info in zip_file.infolist():
            if not info.filename.lower().endswith(".xlsx"):
                continue
            decoded_name = decode_zip_name(info.filename)
            out_path = ANSWER_ROOT / decoded_name
            if force or not out_path.exists():
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(zip_file.read(info))
            if "Work related" in decoded_name:
                answers_by_sheet = parse_answer_sheet(zip_file.read(info))
    return answers_by_sheet


def build(force: bool = False) -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    SOURCE_ROOT.mkdir(parents=True, exist_ok=True)
    ANSWER_ROOT.mkdir(parents=True, exist_ok=True)

    answer_zip = ANSWER_ROOT / "answersinSpecialEPSTOPIK.zip"
    download(ANSWER_ZIP_URL, answer_zip, force)
    answers_by_sheet = extract_answers(answer_zip, force)

    categories = []
    for category in CATEGORIES:
        source_name = Path(urllib.parse.unquote(urllib.parse.urlparse(category.url).path)).name
        pdf_path = SOURCE_ROOT / source_name
        download(category.url, pdf_path, force)

        category_root = OUT_ROOT / category.slug
        pages = render_pdf(pdf_path, category_root, force)
        answers = answers_by_sheet.get(category.answer_sheet, [])
        module = {
            "source": "Special EPS-TOPIK Work Related Questions",
            "source_page": "https://epstopik.hrdkorea.or.kr/epstopik/book/pub/publicWorkBookList.do?lang=en",
            "slug": category.slug,
            "title": category.title,
            "title_ko": category.title_ko,
            "source_url": category.url,
            "source_pdf": rel(pdf_path),
            "pages": pages,
            "answers": answers,
            "integrity": {
                "pdf_pages": len(pages),
                "answers": len(answers),
            },
        }
        module_path = category_root / "module.json"
        module_path.write_text(json.dumps(module, ensure_ascii=False, indent=2), encoding="utf-8")
        categories.append({
            "slug": category.slug,
            "title": category.title,
            "title_ko": category.title_ko,
            "module": rel(module_path),
            "source_pdf": rel(pdf_path),
            "pdf_pages": len(pages),
            "answers": len(answers),
        })
        print(f"{category.slug}: pages={len(pages)} answers={len(answers)}")

    index = {
        "source": "Special EPS-TOPIK Work Related Questions",
        "source_page": "https://epstopik.hrdkorea.or.kr/epstopik/book/pub/publicWorkBookList.do?lang=en",
        "categories": categories,
        "answers_zip": rel(answer_zip),
        "integrity": {
            "category_count": len(categories),
            "pdf_pages": sum(item["pdf_pages"] for item in categories),
            "answers": sum(item["answers"] for item in categories),
        },
    }
    (OUT_ROOT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        "done: "
        f"{index['integrity']['category_count']} categories, "
        f"{index['integrity']['pdf_pages']} pages, "
        f"{index['integrity']['answers']} answers"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Redownload and rerender all files")
    args = parser.parse_args()
    build(force=args.force)


if __name__ == "__main__":
    main()
