"""
Orchestrator: HWP → PDF → layout mining → parsing_rules → OpenTestSet JSON.
Combines LibreOffice converter, PyMuPDF layout miner, and parsing rules.
"""
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import fitz  # PyMuPDF
from loguru import logger

from models.extraction_models import (
    OpenTestSet, ReadingSection, ListeningSection,
    Question, Option, InlineImage, ListeningItem,
)
from scraper.parsing_rules import (
    split_reading_questions, split_listening_items,
    extract_options, clean_block_text, is_question_start,
    is_image_metadata,
)


# ── LibreOffice Bridge ──

def find_libreoffice() -> Optional[str]:
    """Locate LibreOffice soffice binary."""
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


def convert_hwp_to_pdf(hwp_path: str, out_dir: Optional[str] = None) -> Optional[str]:
    """Convert HWP to PDF via LibreOffice. Returns PDF path or None."""
    lo = find_libreoffice()
    if not lo:
        logger.error("LibreOffice not found. Cannot convert HWP to PDF.")
        return None

    if out_dir is None:
        out_dir = os.path.dirname(hwp_path) or "."
    stem = Path(hwp_path).stem
    pdf_path = os.path.join(out_dir, f"{stem}.pdf")

    try:
        result = subprocess.run(
            [lo, "--headless", "--convert-to", "pdf", "--outdir", out_dir, hwp_path],
            capture_output=True, timeout=120
        )
        if result.returncode == 0 and os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000:
            logger.info(f"Converted: {hwp_path} -> {pdf_path}")
            return pdf_path
        else:
            err = result.stderr.decode("utf-8", errors="replace")[:200]
            logger.error(f"LibreOffice convert failed for {hwp_path}: {err}")
    except subprocess.TimeoutExpired:
        logger.error("LibreOffice timeout (120s)")
    except Exception as e:
        logger.error(f"LibreOffice error: {e}")

    return None


# ── PDF Layout Miner ──

class PDFLayoutMiner:
    """Extract text blocks and images from PDF with position data."""

    def __init__(self, pdf_path: str, artifacts_dir: str = "artifacts"):
        self.pdf_path = pdf_path
        self.artifacts_dir = artifacts_dir
        self.blocks: List[Dict] = []
        self.images: List[Dict] = []
        self._raw_pages: List[str] = []

    def mine(self) -> Tuple[List[Dict], List[Dict]]:
        """Process PDF: extract all text blocks and images with positions."""
        doc = fitz.open(self.pdf_path)
        out_dir = Path(self.artifacts_dir) / "pdf_layout"
        out_dir.mkdir(parents=True, exist_ok=True)

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_num_1 = page_num + 1

            # Extract text blocks with positions
            page_dict = page.get_text("dict")
            for block in page_dict.get("blocks", []):
                if block["type"] == 0:  # text
                    for line in block.get("lines", []):
                        text = "".join(s["text"] for s in line.get("spans", []))
                        if text.strip():
                            bbox = line["bbox"]
                            self.blocks.append({
                                "text": text.strip(),
                                "x0": round(bbox[0], 1),
                                "y0": round(bbox[1], 1),
                                "x1": round(bbox[2], 1),
                                "y1": round(bbox[3], 1),
                                "page": page_num_1,
                            })

                elif block["type"] == 1:  # image
                    bbox = block["bbox"]
                    img_info = {
                        "page": page_num_1,
                        "x0": round(bbox[0], 1),
                        "y0": round(bbox[1], 1),
                        "x1": round(bbox[2], 1),
                        "y1": round(bbox[3], 1),
                        "width": round(bbox[2] - bbox[0], 0),
                        "height": round(bbox[3] - bbox[1], 0),
                    }

                    # Extract image binary
                    for img in page.get_images(full=True):
                        xref = img[0]
                        base = page.parent.extract_image(xref)
                        if base:
                            img_bytes = base["image"]
                            sha = hashlib.sha256(img_bytes).hexdigest()[:16]
                            ext = base["ext"]
                            fname = f"img_p{page_num_1}_{sha}.{ext}"
                            (out_dir / fname).write_bytes(img_bytes)
                            img_info["filename"] = fname
                            img_info["sha256"] = sha
                            break

                    self.images.append(img_info)

            # Save raw text per page
            self._raw_pages.append(page.get_text())

        doc.close()

        # Save debug outputs
        self._save_debug(out_dir)

        logger.info(f"Mined {len(self.blocks)} text blocks, {len(self.images)} images from {self.pdf_path}")
        return self.blocks, self.images

    def _save_debug(self, out_dir: Path):
        """Save debug JSON files."""
        with open(out_dir / "blocks.json", "w", encoding="utf-8") as f:
            json.dump(self.blocks, f, ensure_ascii=False, indent=2)
        with open(out_dir / "images.json", "w", encoding="utf-8") as f:
            json.dump(self.images, f, ensure_ascii=False, indent=2)

    def get_page_text(self, page_num: int) -> str:
        """Get raw text for a specific page (0-indexed)."""
        if page_num < len(self._raw_pages):
            return self._raw_pages[page_num]
        return ""


# ── Spatial Image to Question Mapping ──

def map_images_to_questions(
    images: List[Dict],
    reading_question_groups: List[List[Dict]],
    first_question_y: float,
) -> Tuple[List[InlineImage], Dict[int, List[InlineImage]]]:
    """Map extracted images to passage or inline question images.

    Args:
        images: List of image dicts with page, y0, filename, sha256, width, height
        reading_question_groups: List of question block groups
        first_question_y: y0 of the first detected question

    Returns:
        (passage_images, question_images)
        passage_images: images with y0 < first_question_y (belong to passage)
        question_images: dict of question_number -> list of InlineImage
    """
    passage_imgs: List[InlineImage] = []
    question_imgs: Dict[int, List[InlineImage]] = {}

    for img in images:
        iimg = InlineImage(
            filename=img.get("filename", ""),
            page=img.get("page", 1),
            bbox=(img["x0"], img["y0"], img["x1"], img["y1"]),
            sha256=img.get("sha256", ""),
            width=int(img.get("width", 0)),
            height=int(img.get("height", 0)),
        )

        # If image y0 < first question y0, it belongs to passage
        if img["y0"] < first_question_y:
            if not any(h in Path(img.get("filename", "")).stem for h in ["header", "logo", "banner"]):
                passage_imgs.append(iimg)
        else:
            # Assign to the question whose y0 is just above this image
            assigned = False
            for qgroup in reading_question_groups:
                q_y0 = qgroup[0].get("y0", 0) if qgroup else 0
                if abs(img["y0"] - q_y0) < 200:  # within 200px of question
                    # Find question number from first block text
                    from scraper.parsing_rules import is_question_start
                    for block in qgroup:
                        is_q, qnum = is_question_start(block.get("text", ""))
                        if is_q and qnum:
                            question_imgs.setdefault(qnum, []).append(iimg)
                            assigned = True
                            break
                    if assigned:
                        break

            if not assigned:
                passage_imgs.append(iimg)

    return passage_imgs, question_imgs


# ── Reading Section Builder ──

def build_reading_section(
    passage_text: str,
    question_groups: List[List[Dict]],
    images: List[dict],
) -> Optional[ReadingSection]:
    """Build ReadingSection dataclass from parsed blocks."""
    if not question_groups:
        return None

    questions: List[Question] = []
    first_q_y = question_groups[0][0].get("y0", 0) if question_groups else 0

    # Map images
    passage_imgs, question_img_map = map_images_to_questions(images, question_groups, first_q_y)

    for qgroup in question_groups:
        qnum = None
        q_text = ""
        all_options: List[Option] = []
        q_images: List[InlineImage] = []

        for block in qgroup:
            text = clean_block_text(block.get("text", ""))
            if not text:
                continue

            is_q, detected_num = is_question_start(text)
            if is_q and detected_num:
                qnum = detected_num
                # Extract question text after the number
                import re
                m = re.match(r"^\s*\d{1,2}\s*[\.\s\)]\s*(.*)", text, re.DOTALL)
                if m:
                    q_text = m.group(1).strip()

            # Extract options
            opts = extract_options(text)
            for opt in opts:
                all_options.append(Option(label=opt["label"], text=opt["text"][:500]))

            # Attach images for this question
            if qnum and qnum in question_img_map:
                q_images.extend(question_img_map[qnum])

        if qnum and (q_text or all_options):
            questions.append(Question(
                number=qnum,
                text=q_text[:2000] if q_text else f"Question {qnum}",
                options=all_options[:4],  # max 4 options
                images=q_images,
            ))

    if not questions:
        return None

    return ReadingSection(
        passage_text=passage_text[:10000],
        questions=questions,
        images=passage_imgs,
    )


# ── Listening Section Builder ──

def build_listening_section(items_data: List[Dict]) -> Optional[ListeningSection]:
    """Build ListeningSection dataclass from parsed items."""
    if not items_data:
        return None

    items: List[ListeningItem] = []
    for item in items_data:
        opts = item.get("options", [])
        # If no options were parsed, try extracting from blocks
        if not opts:
            for block in item.get("blocks", []):
                opts = extract_options(block.get("text", ""))
                if opts:
                    break

        option_objects = [Option(label=o["label"], text=o["text"][:500]) for o in opts[:4]]

        items.append(ListeningItem(
            number=item["number"],
            dialog_script=item.get("script", "")[:5000],
            question=item.get("question", "")[:2000],
            options=option_objects,
        ))

    return ListeningSection(items=items) if items else None


# ── Full Pipeline ──

def process_hwp(hwp_path: str, artifacts_dir: str = "artifacts") -> OpenTestSet:
    """Full pipeline: HWP → PDF → mine → parse → OpenTestSet."""
    import hashlib

    result = OpenTestSet(
        filename=os.path.basename(hwp_path),
        hwp_sha256="",
        pdf_sha256="",
    )

    # 1. SHA256 of source
    with open(hwp_path, "rb") as f:
        result.hwp_sha256 = hashlib.sha256(f.read()).hexdigest()

    # 2. Convert to PDF
    pdf_path = convert_hwp_to_pdf(hwp_path)
    if not pdf_path:
        logger.warning(f"LibreOffice conversion failed for {hwp_path}. Returning empty set.")
        return result

    with open(pdf_path, "rb") as f:
        result.pdf_sha256 = hashlib.sha256(f.read()).hexdigest()

    # 3. Mine layout
    miner = PDFLayoutMiner(pdf_path, artifacts_dir)
    blocks, images = miner.mine()

    if not blocks:
        logger.warning("No text blocks found in PDF.")
        return result

    # 4. Detect reading vs listening
    has_reading = any(
        1 <= qnum <= 20 for _, qnum in [is_question_start(b.get("text", "")) for b in blocks[:50]]
        if qnum is not None
    )
    has_listening = any(
        21 <= qnum <= 40 for _, qnum in [is_question_start(b.get("text", "")) for b in blocks[:50]]
        if qnum is not None
    )

    # Separate reading and listening blocks
    reading_blocks: List[Dict] = []
    listening_blocks: List[Dict] = []
    in_listening = False

    for b in blocks:
        is_q, qnum = is_question_start(b.get("text", ""))
        if is_q and qnum and qnum >= 21:
            in_listening = True
        if in_listening:
            listening_blocks.append(b)
        else:
            reading_blocks.append(b)

    # 5. Parse reading
    if has_reading:
        try:
            passage_text, qgroups = split_reading_questions(reading_blocks)
            rs = build_reading_section(passage_text, qgroups, images)
            if rs:
                result.reading = rs
                logger.info(f"Reading: {len(rs.questions)} questions, passage={len(rs.passage_text)} chars")
        except Exception as e:
            logger.error(f"Reading parsing error (non-fatal): {e}")

    # 6. Parse listening
    if has_listening:
        try:
            items_data = split_listening_items(listening_blocks)
            ls = build_listening_section(items_data)
            if ls:
                result.listening = ls
                logger.info(f"Listening: {len(ls.items)} items")
        except Exception as e:
            logger.error(f"Listening parsing error (non-fatal): {e}")

    return result


# ── CLI Entry Point ──

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="EPS-TOPIK HWP to JSON via LibreOffice + PyMuPDF")
    parser.add_argument("hwp", help="Path to .hwp file")
    parser.add_argument("--artifacts", default="artifacts")
    args = parser.parse_args()

    if not find_libreoffice():
        print("ERROR: LibreOffice not found. Install LibreOffice 7.0+ first.")
        sys.exit(1)

    print(f"Processing: {args.hwp}")
    result = process_hwp(args.hwp, args.artifacts)

    out_path = f"{Path(args.hwp).stem}_extracted.json"
    # Convert dataclass to dict
    result_dict = {
        "filename": result.filename,
        "hwp_sha256": result.hwp_sha256,
        "pdf_sha256": result.pdf_sha256,
        "reading": {
            "passage_text": result.reading.passage_text if result.reading else "",
            "questions": [
                {"number": q.number, "text": q.text, "options": [{"label": o.label, "text": o.text} for o in q.options]}
                for q in result.reading.questions
            ] if result.reading else [],
            "images": [
                {"filename": i.filename, "page": i.page, "bbox": list(i.bbox)}
                for i in result.reading.images
            ] if result.reading else [],
        } if result.reading else None,
        "listening": {
            "items": [
                {"number": i.number, "question": i.question, "dialog_script": i.dialog_script,
                 "options": [{"label": o.label, "text": o.text} for o in i.options]}
                for i in result.listening.items
            ] if result.listening and hasattr(result.listening, 'items') else [],
        } if result.listening else None,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, ensure_ascii=False, indent=2)

    r_count = len(result.reading.questions) if result.reading else 0
    l_count = len(result.listening.items) if result.listening else 0
    print(f"\nDone: {r_count} reading questions, {l_count} listening items")
    print(f"Saved: {out_path}")
