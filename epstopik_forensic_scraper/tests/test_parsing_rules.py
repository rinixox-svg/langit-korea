"""
Unit tests for parsing_rules.py using simulated block data.
Run with: pytest tests/test_parsing_rules.py -v
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scraper.parsing_rules import (
    is_question_start, extract_options, split_reading_questions,
    split_listening_items, is_question_group_header,
    clean_block_text, is_image_metadata,
)


# ── Sample Data ──
# ASSUMPTION: Blocks mimic PyMuPDF get_text("dict") output with position keys.

SAMPLE_READING_BLOCKS = [
    {"text": "EPS-TOPIK Reading", "x0": 100, "y0": 50, "x1": 400, "y1": 70, "page": 1},
    {"text": "다음을 읽고 물음에 답하십시오.", "x0": 100, "y0": 100, "x1": 400, "y1": 120, "page": 1},
    {"text": "(광고문안)\n안녕하십니까. 저희 회사는 새로운 제품을 출시했습니다.", "x0": 100, "y0": 150, "x1": 400, "y1": 250, "page": 1},
    {"text": "저희 제품은 품질과 가격 모두 만족스럽습니다.", "x0": 100, "y0": 260, "x1": 400, "y1": 300, "page": 1},
    {"text": "1.\n이 글의 중심 내용은 무엇입니까?", "x0": 100, "y0": 400, "x1": 400, "y1": 440, "page": 1},
    {"text": "① 신제품 홍보\n② 회사 연혁", "x0": 120, "y0": 450, "x1": 400, "y1": 500, "page": 1},
    {"text": "③ 시장 분석\n④ 고객 서비스", "x0": 120, "y0": 510, "x1": 400, "y1": 550, "page": 1},
    {"text": "2.\n밑줄 친 부분의 의미는?", "x0": 100, "y0": 580, "x1": 400, "y1": 620, "page": 1},
    {"text": "① 가능하다\n② 불가능하다\n③ 확실하다\n④ 의심스럽다", "x0": 120, "y0": 630, "x1": 400, "y1": 700, "page": 1},
]

SAMPLE_LISTENING_BLOCKS = [
    {"text": "Listening", "x0": 100, "y0": 50, "x1": 200, "y1": 70, "page": 2},
    {"text": "21.\n다음을 듣고 물음에 답하십시오.", "x0": 100, "y0": 100, "x1": 400, "y1": 140, "page": 2},
    {"text": "[남자] 어서 오십시오. 무엇을 도와드릴까요?", "x0": 100, "y0": 160, "x1": 400, "y1": 200, "page": 2},
    {"text": "[여자] 네, 이 제품에 대해 문의하려고 왔습니다.", "x0": 100, "y0": 210, "x1": 400, "y1": 250, "page": 2},
    {"text": "① 가격을 묻는다\n② 제품을 교환한다", "x0": 120, "y0": 270, "x1": 400, "y1": 310, "page": 2},
    {"text": "③ 환불을 요청한다\n④ 배송을 문의한다", "x0": 120, "y0": 320, "x1": 400, "y1": 360, "page": 2},
    {"text": "22.\n다음을 듣고 고르십시오.", "x0": 100, "y0": 380, "x1": 400, "y1": 420, "page": 2},
    {"text": "[남자] 이번 주말에 시간 있으세요?", "x0": 100, "y0": 440, "x1": 400, "y1": 480, "page": 2},
    {"text": "[여자] 네, 왜요?", "x0": 100, "y0": 490, "x1": 400, "y1": 520, "page": 2},
    {"text": "① 영화\n② 운동", "x0": 120, "y0": 540, "x1": 400, "y1": 580, "page": 2},
    {"text": "③ 여행\n④ 쇼핑", "x0": 120, "y0": 590, "x1": 400, "y1": 630, "page": 2},
]


# ── Tests: is_question_start ──

def test_question_start_detected():
    assert is_question_start("1. 본문 내용") == (True, 1)
    assert is_question_start("21. 듣기 문제") == (True, 21)
    assert is_question_start("10. \n다음 글을 읽고") == (True, 10)


def test_question_start_not_detected():
    assert is_question_start("EPS-TOPIK Reading") == (False, None)
    assert is_question_start("(광고문안)") == (False, None)
    assert is_question_start("① 옵션1") == (False, None)


# ── Tests: extract_options ──

def test_extract_circled_options():
    text = "① 설명\n② 거절\n③ 비교\n④ 선택"
    opts = extract_options(text)
    assert len(opts) == 4
    assert opts[0]["label"] == "\u2460"
    assert opts[0]["text"] == "설명"
    assert opts[3]["text"] == "선택"


def test_extract_inline_options():
    text = "① 신제품 홍보\n② 회사 연혁"
    opts = extract_options(text)
    assert len(opts) >= 2


def test_extract_options_single_line():
    text = "① 가능 ② 불가능 ③ 확실 ④ 의심"
    opts = extract_options(text)
    assert len(opts) == 4
    assert opts[1]["text"] == "불가능"


def test_extract_empty_text():
    assert extract_options("") == []
    assert extract_options("   ") == []


# ── Tests: split_reading_questions ──

def test_split_reading_two_questions():
    passage, questions = split_reading_questions(SAMPLE_READING_BLOCKS)
    assert len(questions) == 2, f"Expected 2 questions, got {len(questions)}"
    assert "중심 내용" in questions[0][0].get("text", "")
    assert "밑줄" in questions[1][0].get("text", "")


def test_split_reading_passage_extracted():
    passage, questions = split_reading_questions(SAMPLE_READING_BLOCKS)
    assert passage, "Passage text should not be empty"
    assert "안녕하십니까" in passage
    assert "EPS-TOPIK" not in passage  # header should be excluded


def test_split_reading_question_has_options():
    _, questions = split_reading_questions(SAMPLE_READING_BLOCKS)
    question1_blocks = questions[0]
    all_text = " ".join(b.get("text", "") for b in question1_blocks)
    opts = extract_options(all_text)
    assert len(opts) >= 2, f"Q1 should have options, got {opts}"
    # ASSUMPTION: First question has 4 options split across two text blocks
    assert any("신제품" in o["text"] for o in opts), f"Expected '신제품' in options: {opts}"


# ── Tests: split_listening_items ──

def test_split_listening_two_items():
    items = split_listening_items(SAMPLE_LISTENING_BLOCKS)
    assert len(items) == 2, f"Expected 2 listening items, got {len(items)}"


def test_listening_item_numbers():
    items = split_listening_items(SAMPLE_LISTENING_BLOCKS)
    assert items[0]["number"] == 21
    assert items[1]["number"] == 22


def test_listening_item_script():
    items = split_listening_items(SAMPLE_LISTENING_BLOCKS)
    # ASSUMPTION: Dialog script contains the Man/Woman conversation
    script = items[0].get("script", "")
    assert "어서 오십시오" in script or "문의" in script, f"Script missing dialog: {script[:100]}"


def test_listening_item_options():
    items = split_listening_items(SAMPLE_LISTENING_BLOCKS)
    opts = items[0].get("options", [])
    assert len(opts) >= 2, f"Q21 should have options, got {len(opts)}"
    # ASSUMPTION: First option mentions price or exchange
    opt_texts = " ".join(o["text"] for o in opts)
    assert any(kw in opt_texts for kw in ["가격", "제품", "환불", "배송"]), f"Unexpected options: {opt_texts}"


def test_listening_item_question_text():
    items = split_listening_items(SAMPLE_LISTENING_BLOCKS)
    # ASSUMPTION: Question text contains "듣고"
    assert "듣고" in items[0].get("question", "")


# ── Tests: edge cases ──

def test_empty_blocks():
    passage, questions = split_reading_questions([])
    assert passage == ""
    assert questions == []

    items = split_listening_items([])
    assert items == []


def test_only_passage_no_questions():
    blocks = [
        {"text": "다음을 읽고 물음에 답하십시오.", "x0": 100, "y0": 100, "x1": 400, "y1": 120, "page": 1},
        {"text": "이것은 테스트 문단입니다.", "x0": 100, "y0": 200, "x1": 400, "y1": 220, "page": 1},
    ]
    passage, questions = split_reading_questions(blocks)
    assert passage
    assert questions == []


def test_image_metadata_filtering():
    assert is_image_metadata("Adobe Photoshop CC 2019")
    assert is_image_metadata("1181pixel x 827pixel")
    assert is_image_metadata("EXIF 데이터")
    assert not is_image_metadata("안녕하십니까")


def test_question_group_header():
    result = is_question_group_header("[1~4] 다음을 읽고")
    assert result[0] is True
    assert result[1] == 1
    assert result[2] == 4

    result2 = is_question_group_header("1. 일반 텍스트")
    assert result2[0] is False


# ── Run directly ──
if __name__ == "__main__":
    # Manual run without pytest
    tests = [
        test_question_start_detected,
        test_question_start_not_detected,
        test_extract_circled_options,
        test_extract_inline_options,
        test_extract_options_single_line,
        test_extract_empty_text,
        test_split_reading_two_questions,
        test_split_reading_passage_extracted,
        test_split_reading_question_has_options,
        test_split_listening_two_items,
        test_listening_item_numbers,
        test_listening_item_script,
        test_listening_item_options,
        test_listening_item_question_text,
        test_empty_blocks,
        test_only_passage_no_questions,
        test_image_metadata_filtering,
        test_question_group_header,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    print(f"\n{passed}/{passed + failed} passed")
