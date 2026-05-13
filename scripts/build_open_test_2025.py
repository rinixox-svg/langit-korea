"""Build verified EPS-TOPIK Open Test 2025 assets and JSON.

Source files are the official PDFs/audio ZIPs stored in ../downloads.
The output is deterministic and safe to rerun:
  - assets/open-test/2025/images/*.png
  - assets/open-test/2025/audio/qNN.mp3
  - open_test_2025.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import zipfile
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = ROOT / "downloads"
YEAR = 2025
ASSET_ROOT = ROOT / "assets" / "open-test" / str(YEAR)
IMAGE_DIR = ASSET_ROOT / "images"
AUDIO_DIR = ASSET_ROOT / "audio"
JSON_OUT = ROOT / f"open_test_{YEAR}.json"

LETTERS = {"①": "a", "②": "b", "③": "c", "④": "d"}


def find_one(pattern: str) -> Path:
    matches = sorted(glob.glob(str(DOWNLOADS / pattern)))
    if not matches:
        raise FileNotFoundError(f"Missing source file: downloads/{pattern}")
    return Path(matches[0])


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def ensure_dirs() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def crop_pdf_image(pdf: Path, page_no: int, image_index: int, name: str) -> str:
    """Crop an image block from a 1-based PDF page and save it as PNG."""
    doc = fitz.open(pdf)
    try:
        page = doc[page_no - 1]
        images = [b for b in page.get_text("dict")["blocks"] if b["type"] == 1]
        if image_index >= len(images):
            raise IndexError(
                f"{pdf.name} page {page_no} has {len(images)} image blocks, "
                f"cannot read index {image_index}"
            )
        rect = fitz.Rect(images[image_index]["bbox"])
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=rect, alpha=False)
        out = IMAGE_DIR / name
        pix.save(out)
        return rel(out)
    finally:
        doc.close()


def extract_question_images(reading_pdf: Path, listening_pdf: Path) -> tuple[dict[int, list[str]], dict[int, dict[str, str]]]:
    """Return question images and image-choice URLs keyed by original number."""
    question_images: dict[int, list[str]] = {
        1: [crop_pdf_image(reading_pdf, 1, 0, "q01_prompt.png")],
        2: [crop_pdf_image(reading_pdf, 1, 1, "q02_prompt.png")],
        3: [crop_pdf_image(reading_pdf, 2, 0, "q03_prompt.png")],
        4: [crop_pdf_image(reading_pdf, 2, 1, "q04_prompt.png")],
        7: [crop_pdf_image(reading_pdf, 4, 0, "q07_prompt.png")],
        10: [crop_pdf_image(reading_pdf, 5, 0, "q10_prompt.png")],
        19: [crop_pdf_image(reading_pdf, 10, 0, "q19_prompt.png")],
        37: [crop_pdf_image(listening_pdf, 12, 0, "q37_prompt.png")],
    }

    image_choices: dict[int, dict[str, str]] = {}
    for qnum, page_no in {
        23: 2,
        24: 3,
        25: 4,
        26: 5,
        27: 6,
        28: 7,
        34: 9,
        35: 10,
        36: 11,
    }.items():
        image_choices[qnum] = {}
        for idx, key in enumerate(("a", "b", "c", "d")):
            image_choices[qnum][key] = crop_pdf_image(
                listening_pdf,
                page_no,
                idx,
                f"q{qnum:02d}_choice_{key}.png",
            )
    return question_images, image_choices


def extract_audio() -> dict[int, str]:
    """Extract only question/prompt audio (T files), never answer-choice audio."""
    zip_path = find_one("듣기문제 오디오 파일.zip")
    audio_urls: dict[int, str] = {}
    with zipfile.ZipFile(zip_path) as zf:
        entries = {entry.filename.upper().replace("_", "-"): entry for entry in zf.infolist()}
        for qnum in range(21, 41):
            key = f"{qnum}-T.MP3"
            entry = entries.get(key)
            if not entry:
                raise FileNotFoundError(f"Missing {key} in {zip_path.name}")
            out = AUDIO_DIR / f"q{qnum:02d}.mp3"
            with zf.open(entry) as src, out.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            audio_urls[qnum] = rel(out)
    return audio_urls


def base_record(qnum: int, qtype: str, text: str, answer: str) -> dict[str, object]:
    return {
        "unit": YEAR,
        "tipe": qtype,
        "teks_soal": text,
        "gambar_url": "",
        "audio_url": "",
        "pilihan_a": "",
        "pilihan_b": "",
        "pilihan_c": "",
        "pilihan_d": "",
        "gambar_pilihan_a": "",
        "gambar_pilihan_b": "",
        "gambar_pilihan_c": "",
        "gambar_pilihan_d": "",
        "jawaban": answer,
        "sumber": "open_test",
        "tahun_soal": YEAR,
        "nomor_asli": qnum,
        "tingkat": "sedang",
        "akses": "free",
    }


def with_options(record: dict[str, object], options: list[str]) -> dict[str, object]:
    for key, value in zip(("pilihan_a", "pilihan_b", "pilihan_c", "pilihan_d"), options):
        record[key] = value
    return record


def build_records(question_images: dict[int, list[str]], image_choices: dict[int, dict[str, str]], audio_urls: dict[int, str]) -> list[dict[str, object]]:
    reading: dict[int, dict[str, object]] = {}

    reading[1] = with_options(base_record(1, "membaca", "다음 그림을 보고 맞는 단어나 문장을 고르십시오.", "d"), ["볼펜입니다.", "가위입니다.", "안경입니다.", "가방입니다."])
    reading[2] = with_options(base_record(2, "membaca", "다음 그림을 보고 맞는 단어나 문장을 고르십시오.", "a"), ["지게차입니다.", "굴착기입니다.", "트랙터입니다.", "경운기입니다."])
    reading[3] = with_options(base_record(3, "membaca", "다음 그림을 보고 맞는 단어나 문장을 고르십시오.", "d"), ["책을 읽고 있습니다.", "밥을 먹고 있습니다.", "친구를 만나고 있습니다.", "피아노를 치고 있습니다."])
    reading[4] = with_options(base_record(4, "membaca", "다음 그림을 보고 맞는 단어나 문장을 고르십시오.", "b"), ["전기가 흐르니까 조심하세요.", "떨어질 수 있으니까 조심하세요.", "바닥이 미끄러우니까 조심하세요.", "불이 붙을 수 있으니까 조심하세요."])
    reading[5] = with_options(base_record(5, "membaca", "다음 중 밑줄 친 부분이 맞는 것은 무엇입니까?", "c"), ["집을 작아요.", "딸기가 먹어요.", "회사에 다녀요.", "겨울에서 추워요."])
    reading[6] = with_options(base_record(6, "membaca", "다음 중 밑줄 친 부분이 맞는 것은 무엇입니까?", "b"), ["퇴근할 때 문을 달으세요.", "친구한테서 선물을 받았어요.", "심심하면 한국 노래를 듣어요.", "오늘 시내에서 많이 걷었어요."])
    reading[7] = with_options(base_record(7, "membaca", "이 병원이 문을 여는 시간은 언제입니까?", "d"), ["부천시입니다.", "김미소입니다.", "튼튼치과입니다.", "오전 아홉 시입니다."])
    reading[8] = with_options(base_record(8, "membaca", "다음 단어와 관계있는 것은 무엇입니까?\n복장", "b"), ["컴퓨터", "작업복", "비빔밥", "기차표"])
    reading[9] = with_options(base_record(9, "membaca", "다음 단어와 관계있는 것은 무엇입니까?\n작업장", "a"), ["근로자가 일하는 곳이에요.", "근로자가 거주하는 곳이에요.", "근로자가 운동하는 곳이에요.", "근로자가 상담하는 곳이에요."])
    reading[10] = with_options(base_record(10, "membaca", "한국의 수산물 수입 현황에 대한 설명으로 맞는 것은 무엇입니까?", "d"), ["한국은 수산물을 중국에서 가장 많이 수입합니다.", "한국이 수입하는 수산물 중 베트남산은 5% 미만입니다.", "한국이 수산물을 수입하는 국가 중 2위는 노르웨이입니다.", "한국은 미국보다 러시아에서 수산물을 더 많이 수입합니다."])
    reading[11] = with_options(base_record(11, "membaca", "빈칸에 들어갈 가장 알맞은 것을 고르십시오.\n지급 방법: _____________", "d"), ["가족 모임", "생일 선물", "출근 시간", "통장 입금"])
    reading[12] = with_options(base_record(12, "membaca", "빈칸에 들어갈 가장 알맞은 것을 고르십시오.\n한국어를 배우고 싶지만 학원에 갈 시간이 없습니다. 그래서 퇴근 후에 인터넷 강의를 __________ 한국어를 공부하고 있습니다.", "c"), ["듣느라고", "들으려고", "들으면서", "듣자마자"])
    reading[13] = with_options(base_record(13, "membaca", "빈칸에 들어갈 가장 알맞은 것을 고르십시오.\n오늘은 다른 날보다 길이 많이 막힙니다. __________ 가지 않으면 회사에 늦을 것 같습니다.", "d"), ["조심하게", "조심해서", "서두르게", "서둘러서"])
    reading[14] = with_options(base_record(14, "membaca", "빈칸에 들어갈 가장 알맞은 것을 고르십시오.\n오늘은 날씨가 너무 덥습니다. 집에 오자마자 선풍기를 __________ 시원한 물을 마셨습니다.", "b"), ["틀면", "틀고", "틀려면", "틀려고"])
    reading[15] = with_options(base_record(15, "membaca", "빈칸에 들어갈 가장 알맞은 것을 고르십시오.\n못에 찔렸을 때는 상처가 가벼워도 바로 소독을 해야 합니다. 그리고 병원에 가서 진료를 받고 주사를 __________.", "a"), ["맞는 것이 좋습니다", "놓는 것이 좋습니다", "맞지 않도록 합니다", "놓지 않도록 합니다"])
    reading[16] = with_options(base_record(16, "membaca", "빈칸에 들어갈 가장 알맞은 것을 고르십시오.\n어두운 곳에서 작업할 때는 가시성이 높은 ____________. 이것을 입으면 멀리서도 잘 보여 사고를 막을 수 있습니다.", "a"), ["반사 조끼를 착용해야 합니다", "보호 장갑을 구매해야 합니다", "비상 계단을 이용해야 합니다", "환기 장치를 작동해야 합니다"])
    reading[17] = with_options(base_record(17, "membaca", "다음 설명에 알맞은 어휘를 고르십시오.\n손에 쥐고 철사를 끊거나 구부릴 때 쓰는 도구입니다. 전선이나 작은 부품을 잡을 때도 사용합니다.", "b"), ["토치", "펜치", "쇠톱", "망치"])
    reading[18] = with_options(base_record(18, "membaca", "다음 글을 읽고 무엇에 대한 글인지 고르십시오.\n한국 사람들은 계절마다 즐겨 먹는 음식이 있습니다. 여름에는 차갑고 시원한 냉면, 콩국수, 팥빙수 등을 많이 먹습니다. 겨울에는 뜨거운 국이나 따뜻한 팥죽, 군고구마, 호떡 등을 자주 먹습니다.", "a"), ["계절 음식", "음식 재료", "조리 방법", "조리 시기"])
    reading[19] = with_options(base_record(19, "membaca", "다음 글을 읽고 내용과 같은 것을 고르십시오.", "b"), ["사내 휴게실의 출입문 비밀번호는 따로 없습니다.", "회사 직원은 누구나 휴게실을 이용할 수 있습니다.", "휴게실 이용 후에는 문을 열어 두고 나가야 합니다.", "점심 도시락을 싸 가서 휴게실에서 먹을 수 있습니다."])
    reading[20] = with_options(base_record(20, "membaca", "다음 글을 읽고 내용과 같은 것을 고르십시오.\n한국에서 일하는 외국인 근로자는 4대 사회보험 혜택을 받습니다. 4대 사회보험 중 산재보험은 사업주만 가입하면 되지만 국민연금, 건강보험, 고용보험은 사업주와 근로자 모두 반드시 가입해야 합니다. 외국인 근로자는 질병, 부상, 상해, 실업 등이 발생하였을 때 가입한 4대 보험의 보험금을 받을 수 있습니다.", "a"), ["사업주는 4대 사회보험에 모두 가입해야 합니다.", "산재보험은 근로자와 사업주가 모두 가입해야 합니다.", "사업주는 사고가 발생하면 보험금을 받을 수 있습니다.", "근로자는 가입하고 싶은 보험을 선택하여 가입할 수 있습니다."])

    listening: dict[int, dict[str, object]] = {}
    listening[21] = with_options(base_record(21, "mendengarkan", "들은 것을 고르십시오.", "a"), ["가구", "기구", "가게", "거기"])
    listening[22] = with_options(base_record(22, "mendengarkan", "들은 것을 고르십시오.", "a"), ["적재", "직장", "적정", "정전"])
    for qnum, answer in {23: "c", 24: "b", 25: "a", 26: "a", 27: "c", 28: "a"}.items():
        listening[qnum] = base_record(qnum, "mendengarkan", "다음을 듣고 들은 내용과 관계있는 그림을 고르십시오.", answer)
    listening[29] = with_options(base_record(29, "mendengarkan", "다음을 듣고 질문에 알맞은 대답을 고르십시오.", "d"), ["그럼요, 법률 교육은 못해요.", "아니요, 항상 수업을 하고 있어요.", "아니요, 법률 교육을 받고 있어요.", "그럼요, 상담을 받고 신청하면 돼요."])
    listening[30] = with_options(base_record(30, "mendengarkan", "다음을 듣고 질문에 알맞은 대답을 고르십시오.", "c"), ["네, 교육 일정을 좀 알려 주세요.", "네, 취업이 빨리 돼야 할 텐데요.", "아니요, 다음 주라고 들었는데요.", "아니요, 교육 내용이 어려웠어요."])
    listening[31] = with_options(base_record(31, "mendengarkan", "다음을 듣고 질문에 알맞은 대답을 고르십시오.", "c"), ["집에서 드세요.", "감기약을 드세요.", "밥을 먹은 후에 드세요.", "따뜻한 물과 같이 드세요."])
    listening[32] = with_options(base_record(32, "mendengarkan", "다음을 듣고 질문에 알맞은 대답을 고르십시오.", "a"), ["3층 회의실에서 한다고 들었어요.", "교육은 누구나 받을 수 있어요.", "성희롱 예방 교육은 두 시에 있어요.", "성희롱 예방 교육은 꼭 들어야 돼요."])
    listening[33] = with_options(base_record(33, "mendengarkan", "다음을 듣고 이어지는 말을 고르십시오.", "d"), ["비상구가 어디인지 가르쳐 주세요.", "불이 나자마자 밖으로 대피했어요.", "소화기가 있어서 빨리 불을 껐어요.", "비상구 위치를 잘 기억해 놓을게요."])
    for qnum, answer in {34: "a", 35: "b", 36: "c"}.items():
        listening[qnum] = base_record(qnum, "mendengarkan", "다음을 듣고 들은 내용과 관계있는 그림을 고르십시오.", answer)
    listening[37] = with_options(base_record(37, "mendengarkan", "안경은 어디에 있습니까?", "d"), ["시계 아래에 있습니다.", "가방 안에 있습니다.", "의자 밑에 있습니다.", "서류 옆에 있습니다."])
    listening[38] = with_options(base_record(38, "mendengarkan", "남자가 이곳에 온 이유는 무엇입니까?", "c"), ["노트북 수리를 맡기려고", "지하철 표를 구입하려고", "잃어버린 가방을 찾으려고", "내려야 할 역을 물어보려고"])
    listening[39] = with_options(base_record(39, "mendengarkan", "점심시간 전까지 포장 작업을 끝내야 하는 이유는 무엇입니까?", "d"), ["작업 시간이 많이 걸려서", "포장할 물건이 너무 많아서", "오후에 라벨을 붙여야 해서", "오후에 제품을 출고해야 해서"])
    listening[40] = with_options(base_record(40, "mendengarkan", "다음 중 들은 내용과 같은 것은 무엇입니까?", "c"), ["남자는 여자와 같은 공장에서 일합니다.", "남자는 아직 공장장님을 못 만났습니다.", "남자는 새 회사 사람들이 마음에 듭니다.", "남자는 이전 공장에서와 같은 일을 합니다."])

    records = [reading[i] for i in range(1, 21)] + [listening[i] for i in range(21, 41)]
    for record in records:
        qnum = int(record["nomor_asli"])
        if qnum in question_images:
            record["gambar_url"] = json.dumps(question_images[qnum], ensure_ascii=False)
        if qnum in image_choices:
            for key, url in image_choices[qnum].items():
                record[f"gambar_pilihan_{key}"] = url
        if qnum in audio_urls:
            record["audio_url"] = audio_urls[qnum]
    return records


def validate(records: list[dict[str, object]]) -> None:
    if len(records) != 40:
        raise AssertionError(f"Expected 40 records, got {len(records)}")
    nums = [r["nomor_asli"] for r in records]
    if nums != list(range(1, 41)):
        raise AssertionError(f"Bad numbering: {nums}")
    for record in records:
        qnum = int(record["nomor_asli"])
        answer = record.get("jawaban")
        if answer not in {"a", "b", "c", "d"}:
            raise AssertionError(f"Q{qnum} has invalid answer: {answer!r}")
        has_text_options = all(str(record.get(f"pilihan_{k}") or "").strip() for k in ("a", "b", "c", "d"))
        has_image_options = all(str(record.get(f"gambar_pilihan_{k}") or "").strip() for k in ("a", "b", "c", "d"))
        if not (has_text_options or has_image_options):
            raise AssertionError(f"Q{qnum} has incomplete options")
        if qnum >= 21 and not record.get("audio_url"):
            raise AssertionError(f"Q{qnum} is missing prompt audio")


def maybe_upload_supabase(records: list[dict[str, object]]) -> None:
    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv(ROOT / ".env")
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY are required")
    supa = create_client(url, key)
    for record in records:
        existing = (
            supa.table("soal_eps")
            .select("id")
            .eq("sumber", "open_test")
            .eq("tahun_soal", YEAR)
            .eq("nomor_asli", record["nomor_asli"])
            .limit(1)
            .execute()
            .data
        )
        if existing:
            (
                supa.table("soal_eps")
                .update(record)
                .eq("id", existing[0]["id"])
                .execute()
            )
        else:
            supa.table("soal_eps").insert(record).execute()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upload-supabase", action="store_true", help="Upsert records to Supabase after writing JSON")
    args = parser.parse_args()

    ensure_dirs()
    reading_pdf = find_one("1.*20문항.pdf")
    listening_pdf = find_one("3.*20문항.pdf")
    question_images, image_choices = extract_question_images(reading_pdf, listening_pdf)
    audio_urls = extract_audio()
    records = build_records(question_images, image_choices, audio_urls)
    validate(records)
    JSON_OUT.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {JSON_OUT.relative_to(ROOT)}")
    print(f"Wrote {len(list(IMAGE_DIR.glob('*.png')))} image assets")
    print(f"Wrote {len(list(AUDIO_DIR.glob('*.mp3')))} prompt audio assets")

    if args.upload_supabase:
        maybe_upload_supabase(records)
        print("Uploaded records to Supabase")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
