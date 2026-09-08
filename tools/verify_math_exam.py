# -*- coding: utf-8 -*-
"""
verify_math_exam.py — ตรวจไฟล์ข้อสอบตอบสั้น (short_answer) ของวิชาคณิตศาสตร์

ทำไมต้องมีตัวนี้
----------------
`verify_exam_json.py` ของคอร์ส `selected topics` ตรวจเฉพาะ `multiple_choice`
(บรรทัด `if item.get("type") != "multiple_choice": continue`) => ข้อสอบตอบสั้น
จะไม่ถูกตรวจอะไรเลยนอกจากมีฟิลด์ครบ สคริปต์นี้เติมส่วนที่ขาด และบังคับกฎ
SA-1 … SA-11 ใน BUILD_RULES.md

การใช้งาน
---------
    python tools/verify_math_exam.py exams/final_items.json

exit code 1 ถ้ามี hard error
"""
import sys
import re
import io
import json
import math
import pathlib
from collections import Counter, defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TAG_RE = re.compile(r"\[M(\d)\]\[L(\d{1,2})\]\[S(\d{2})\]\[Bloom:(\w+(?:/\w+)?)\]\s*$")

LEVEL_BLOOM = {
    1: "Remember", 2: "Remember",
    3: "Understand",
    4: "Apply", 5: "Apply", 6: "Apply",
    7: "Analyze", 8: "Analyze",
    9: "Evaluate", 10: "Evaluate",
}
LEVEL_POINTS = {
    1: 1.0, 2: 1.0, 3: 1.0,
    4: 2.0, 5: 2.0, 6: 2.0,
    7: 3.0, 8: 3.0,
    9: 4.0, 10: 4.0,
}

# วิชาคำนวณด้วยมือ: Apply เป็นแกน และ Evaluate ทำเป็นข้อตอบสั้นไม่ได้จริง
BLOOM_TARGET = {
    "Remember": 0.10,
    "Understand": 0.20,
    "Apply": 0.45,
    "Analyze": 0.25,
    "Evaluate": 0.00,
}
BLOOM_TOLERANCE_PP = 7

# ผังข้อสอบตามสัปดาห์ (ถ่วงด้วยคะแนน)
WEEK_TARGET = {1: 0.15, 2: 0.15, 3: 0.20, 4: 0.20, 5: 0.30}
WEEK_TOLERANCE_PP = 7

UNICODE_MINUS = "−"
DECIMAL_RE = re.compile(r"^[-−+]?\d+\.(\d+)$")
FRACTION_RE = re.compile(r"^([-−+]?\d+)\s*/\s*(\d+)$")
# กฎ SA-4: รูปแบบคำตอบต้องอยู่ในวงเล็บและมีคำว่า "ตอบ"
ANSWER_SPEC_RE = re.compile(r"\([^)]*ตอบ[^)]*\)")


def main(path):
    hard, warn = [], []
    p = pathlib.Path(path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"[FAIL] ไม่พบไฟล์: {path}")
        return 1
    except json.JSONDecodeError as e:
        print(f"[FAIL] JSON ไม่ถูกต้อง: {e}")
        return 1

    if not isinstance(data, list):
        print("[FAIL] โครงสร้างชั้นนอกต้องเป็น JSON array")
        return 1

    bloom = Counter()
    week_points = defaultdict(float)
    seen_text = {}
    total_points = 0.0
    sa_count = 0

    for i, item in enumerate(data):
        tag = f"item[{i}]"

        for field in ("type", "text", "points", "feedback", "options"):
            if field not in item:
                hard.append(f"{tag}: ขาดฟิลด์ '{field}'")
        if "text" not in item or "options" not in item:
            continue

        itype = item.get("type")
        if itype != "short_answer":
            warn.append(
                f"{tag}: type = '{itype}' — คอร์สนี้กำหนดให้ final เป็น short_answer ทั้งหมด"
            )
            continue
        sa_count += 1

        text = item["text"]
        norm = re.sub(r"\s+", " ", text).strip()
        if norm in seen_text:
            hard.append(f"{tag}: โจทย์ซ้ำกับ item[{seen_text[norm]}]")
        else:
            seen_text[norm] = i

        # ── SA-4: ต้องบอกรูปแบบคำตอบในตัวโจทย์
        if not ANSWER_SPEC_RE.search(text):
            hard.append(
                f"{tag}: ไม่ระบุรูปแบบคำตอบในวงเล็บ (กฎ SA-4) "
                f'เช่น "(ตอบเป็นจำนวนเต็ม)" หรือ "(ถ้าไม่มีผลเฉลย ตอบ NONE)"'
            )

        # ── ignore_case
        if item.get("ignore_case") is not True:
            hard.append(f"{tag}: short_answer ต้องตั้ง \"ignore_case\": true (กฎ SA-5)")

        # ── options: ต้องมีทุกตัวและ is_correct ทุกตัว
        opts = item.get("options") or []
        if not opts:
            hard.append(f"{tag}: options ว่าง — ต้องใส่คำตอบที่ยอมรับอย่างน้อย 1 รูป")
        for j, o in enumerate(opts):
            if "text" not in o:
                hard.append(f"{tag}.options[{j}]: ขาด 'text'")
            if o.get("is_correct") is not True:
                hard.append(
                    f"{tag}.options[{j}]: short_answer ต้อง is_correct: true ทุกตัว (กฎ SA-5)"
                )

        accepted = [str(o.get("text", "")).strip() for o in opts]
        acc_set = set(accepted)

        # ── SA-6: เครื่องหมายลบสองรูป
        for a in accepted:
            if "-" in a:
                twin = a.replace("-", UNICODE_MINUS)
                if twin not in acc_set:
                    hard.append(
                        f"{tag}: มีคำตอบ '{a}' แต่ไม่มีรูป Unicode minus '{twin}' (กฎ SA-6)"
                    )
            if UNICODE_MINUS in a:
                twin = a.replace(UNICODE_MINUS, "-")
                if twin not in acc_set:
                    hard.append(
                        f"{tag}: มีคำตอบ '{a}' แต่ไม่มีรูป ASCII '-' คือ '{twin}' (กฎ SA-6)"
                    )

        # ── SA-1 / M-6: ตัวเลขต้องสวย
        for a in accepted:
            m = DECIMAL_RE.match(a)
            if m and len(m.group(1)) > 2:
                hard.append(
                    f"{tag}: คำตอบ '{a}' มีทศนิยม {len(m.group(1))} ตำแหน่ง "
                    f"— เกิน 2 ตำแหน่ง ถือว่าเลขไม่สวย (กฎ SA-1 / M-6)"
                )
            fm = FRACTION_RE.match(a)
            if fm:
                num = abs(int(fm.group(1).replace(UNICODE_MINUS, "-")))
                den = int(fm.group(2))
                if den == 0:
                    hard.append(f"{tag}: คำตอบ '{a}' ตัวส่วนเป็นศูนย์")
                elif num and math.gcd(num, den) != 1:
                    warn.append(f"{tag}: เศษส่วน '{a}' ยังไม่เป็นอย่างต่ำ")

        # ── คำตอบที่เป็นเศษส่วน/ทศนิยม มีรูปสมมูลแน่ ๆ จึงไม่ควรยอมรับรูปเดียว
        # (จำนวนเต็มไม่เข้าข่าย เพราะไม่มีรูปสมมูลที่นักศึกษาจะเขียนต่างออกไป)
        has_variant_form = any(
            DECIMAL_RE.match(a) or FRACTION_RE.match(a) for a in accepted
        )
        if len(accepted) == 1 and has_variant_form:
            warn.append(
                f"{tag}: คำตอบ '{accepted[0]}' เป็นเศษส่วน/ทศนิยมแต่ยอมรับรูปเดียว "
                f"— ต้องเพิ่มรูปสมมูลอีกรูป (เศษส่วน ↔ ทศนิยม)"
            )

        # ── points + tag
        pts = item.get("points")
        if not isinstance(pts, (int, float)) or pts <= 0:
            hard.append(f"{tag}: points ต้องเป็นจำนวนบวก ได้ {pts!r}")

        m = TAG_RE.search(item.get("feedback", ""))
        if not m:
            hard.append(
                f"{tag}: feedback ไม่มีแท็ก [M<n>][L<n>][S<nn>][Bloom:<verb>] ท้ายข้อความ"
            )
            continue

        _module, level, week, verb = m.groups()
        level, week = int(level), int(week)

        expected_bloom = LEVEL_BLOOM.get(level)
        if expected_bloom is None:
            hard.append(f"{tag}: L{level} อยู่นอกช่วง 1–10")
            continue
        if verb.split("/")[0] != expected_bloom:
            warn.append(f"{tag}: แท็กเขียน Bloom:{verb} แต่ L{level} ควรเป็น {expected_bloom}")
        bloom[expected_bloom] += 1

        if expected_bloom == "Evaluate":
            warn.append(
                f"{tag}: เป็นข้อระดับ Evaluate — รูปแบบตอบสั้นวัด Evaluate ไม่ได้จริง "
                f"เป้าคือ 0% (ดู blueprint)"
            )

        exp_pts = LEVEL_POINTS.get(level)
        if isinstance(pts, (int, float)) and exp_pts and pts != exp_pts:
            warn.append(f"{tag}: L{level} ควรได้ points={exp_pts} แต่ได้ {pts}")

        if not 1 <= week <= 5:
            hard.append(f"{tag}: S{week:02d} — สัปดาห์ต้องเป็น 01–05")
        else:
            week_points[week] += float(pts) if isinstance(pts, (int, float)) else 0.0
            total_points += float(pts) if isinstance(pts, (int, float)) else 0.0

    # ── รายงาน
    print(f"\n=== {path} ===")
    print(f"จำนวนข้อทั้งหมด: {len(data)} | short_answer: {sa_count} | คะแนนรวม: {total_points:g}")

    n_bloom = sum(bloom.values())
    if n_bloom:
        print("\nการกระจาย Bloom (ตามจำนวนข้อ):")
        for cat, target in BLOOM_TARGET.items():
            actual = bloom.get(cat, 0)
            ap, tp = 100 * actual / n_bloom, 100 * target
            over = abs(ap - tp) > BLOOM_TOLERANCE_PP
            print(
                f"  {cat:<11} เป้า {tp:5.1f}%  จริง {ap:5.1f}% ({actual})"
                + ("   <-- เกินเกณฑ์" if over else "")
            )
            if over:
                warn.append(
                    f"Bloom '{cat}' อยู่ที่ {ap:.1f}% เทียบเป้า {tp:.1f}% "
                    f"(ยอมรับ ±{BLOOM_TOLERANCE_PP}pp)"
                )

    if total_points:
        print("\nการกระจายตามสัปดาห์ (ตามคะแนน):")
        for wk, target in WEEK_TARGET.items():
            actual = week_points.get(wk, 0.0)
            ap, tp = 100 * actual / total_points, 100 * target
            over = abs(ap - tp) > WEEK_TOLERANCE_PP
            print(
                f"  สัปดาห์ {wk}   เป้า {tp:5.1f}%  จริง {ap:5.1f}% ({actual:g} คะแนน)"
                + ("   <-- เกินเกณฑ์" if over else "")
            )
            if over:
                warn.append(
                    f"สัปดาห์ {wk} อยู่ที่ {ap:.1f}% เทียบเป้า {tp:.1f}% "
                    f"(ยอมรับ ±{WEEK_TOLERANCE_PP}pp)"
                )

    print(f"\nHard errors: {len(hard)}")
    for e in hard:
        print(f"[FAIL] {e}")
    print(f"\nWarnings: {len(warn)}")
    for w in warn:
        print(f"[WARN] {w}")

    if hard:
        print("\nRESULT: FAILED")
        return 1
    print("\nRESULT: PASSED" + (" (มี warning)" if warn else ""))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python tools/verify_math_exam.py <path/to/items.json>")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
