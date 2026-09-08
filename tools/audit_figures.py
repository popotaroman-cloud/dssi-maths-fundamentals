# -*- coding: utf-8 -*-
"""
audit_figures.py — ตรวจสอบภาพ กราฟ และแผนภาพทั้งคอร์ส

ทำไมต้องมี
----------
marker แบบ `[FIGURE: คำบรรยาย]` เป็นข้อความอิสระ ไม่มีใครตรวจได้ว่าภาพครบหรือหาย
สคริปต์นี้บังคับ marker ให้มีโครงสร้าง แล้วเทียบกับไฟล์ภาพจริงในโฟลเดอร์ figures/

รูปแบบ marker ที่บังคับ (กฎ FG-1)
--------------------------------
    [FIGURE | <type A|B|C> | <id> | <คำบรรยาย>]

    ตัวอย่าง:
    [FIGURE | A | w01_f01_solution_widening | เส้นจำนวนสองเส้นวางซ้อนกัน ...]

id ต้องเป็น  w<NN>_f<NN>_<slug>  โดย <NN> ตัวแรกตรงกับสัปดาห์ของไฟล์ (กฎ FG-2)
ไฟล์ภาพอยู่ที่  week_0N_*/figures/<id>.svg  (หรือ .png เฉพาะ type B)  (กฎ FG-4)

การใช้งาน
---------
    python tools/audit_figures.py                  ตรวจ + เขียน FIGURE_AUDIT.md
    python tools/audit_figures.py --allow-missing  ระหว่างร่าง ยังไม่ต้องมีไฟล์ภาพ

exit code 1 ถ้ามี hard error
"""
import sys
import re
import io
import pathlib
from collections import Counter, defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPORT = ROOT / "FIGURE_AUDIT.md"

MARKER_RE = re.compile(r"\[FIGURE\s*\|([^|\]]*)\|([^|\]]*)\|([^\]]*)\]")
OLD_MARKER_RE = re.compile(r"\[FIGURE\s*:")
ID_RE = re.compile(r"^w(\d{2})_f(\d{2})_[a-z0-9_]+$")
WEEK_DIR_RE = re.compile(r"^week_(\d{2})_")
VALID_TYPES = {"A", "B", "C"}
TYPE_B_MAX_SHARE = 0.40  # กฎ FG-8


def week_of(path: pathlib.Path):
    for part in path.parts:
        m = WEEK_DIR_RE.match(part)
        if m:
            return int(m.group(1))
    return None


def week_dir_of(path: pathlib.Path):
    for i, part in enumerate(path.parts):
        if WEEK_DIR_RE.match(part):
            return pathlib.Path(*path.parts[: i + 1])
    return None


def main(allow_missing=False):
    hard, warn = [], []

    sources = sorted(ROOT.glob("week_*/notes/*.md")) + sorted(
        ROOT.glob("week_*/slides/*.md")
    )
    if not sources:
        print("[WARN] ไม่พบไฟล์ note หรือสไลด์เลย (week_*/notes/*.md, week_*/slides/*.md)")

    # id -> ข้อมูลรวม
    figures = {}
    # ไฟล์ -> จำนวนภาพ
    per_file = defaultdict(int)
    type_count = Counter()

    for src in sources:
        rel = src.relative_to(ROOT).as_posix()
        text = src.read_text(encoding="utf-8")
        wk = week_of(src)

        # marker แบบเก่า
        for _ in OLD_MARKER_RE.finditer(text):
            hard.append(f"{rel}: พบ marker แบบเก่า `[FIGURE: ...]` — ต้องใช้รูปแบบ 4 ช่อง (กฎ FG-1)")
            break

        for m in MARKER_RE.finditer(text):
            ftype = m.group(1).strip()
            fid = m.group(2).strip()
            caption = re.sub(r"\s+", " ", m.group(3)).strip()
            per_file[rel] += 1

            if ftype not in VALID_TYPES:
                hard.append(f"{rel}: id '{fid}' — type '{ftype}' ไม่ใช่ A, B หรือ C (กฎ FG-1)")
                continue

            idm = ID_RE.match(fid)
            if not idm:
                hard.append(
                    f"{rel}: id '{fid}' ผิดรูป — ต้องเป็น w<NN>_f<NN>_<slug> "
                    f"(slug เป็นตัวพิมพ์เล็ก ตัวเลข และ _ เท่านั้น) (กฎ FG-2)"
                )
                continue

            id_week = int(idm.group(1))
            if wk is not None and id_week != wk:
                hard.append(
                    f"{rel}: id '{fid}' บอกสัปดาห์ {id_week} แต่ไฟล์อยู่สัปดาห์ {wk} (กฎ FG-2)"
                )

            if not caption or len(caption) < 25:
                warn.append(
                    f"{rel}: id '{fid}' คำบรรยายสั้นเกินไป ({len(caption)} ตัวอักษร) "
                    f"— ต้องละเอียดพอให้คนอื่นวาดตามได้ (กฎ FG-7)"
                )

            if fid in figures:
                prev = figures[fid]
                if prev["type"] != ftype:
                    hard.append(
                        f"id '{fid}' ถูกใช้เป็น type {prev['type']} ที่ {prev['sources'][0]} "
                        f"แต่เป็น type {ftype} ที่ {rel}"
                    )
                if prev["caption"] != caption:
                    warn.append(
                        f"id '{fid}' ใช้ซ้ำแต่คำบรรยายไม่ตรงกัน "
                        f"({prev['sources'][0]} vs {rel}) — ถ้าเป็นภาพเดียวกันควรเขียนคำบรรยายให้ตรง"
                    )
                prev["sources"].append(rel)
            else:
                figures[fid] = {
                    "type": ftype,
                    "caption": caption,
                    "sources": [rel],
                    "week": id_week,
                    "week_dir": week_dir_of(src),
                }
                type_count[ftype] += 1

    # ── เทียบกับไฟล์ภาพจริง
    missing, present = [], []
    for fid, info in sorted(figures.items()):
        wd = info["week_dir"]
        asset = None
        if wd is not None:
            for ext in (".svg", ".png"):
                cand = wd / "figures" / f"{fid}{ext}"
                if cand.exists():
                    asset = cand
                    break
        info["asset"] = asset
        if asset is None:
            missing.append(fid)
        else:
            present.append(fid)
            if info["type"] == "A" and asset.suffix == ".png":
                warn.append(
                    f"id '{fid}' เป็น type A แต่เป็นไฟล์ .png — type A ควรเป็น SVG เรียบ ๆ "
                    f"ที่นักศึกษาวาดตามได้ (กฎ FG-5)"
                )

    # ── ไฟล์ภาพที่ไม่มี marker อ้างถึง
    orphans = []
    for asset in sorted(ROOT.glob("week_*/figures/*")):
        if asset.suffix.lower() not in (".svg", ".png"):
            continue
        if asset.stem not in figures:
            orphans.append(asset.relative_to(ROOT).as_posix())

    # ── FG-6: สไลด์ทุกชุด >= 1 ภาพ, note >= 2 ภาพ
    for deck in sorted(ROOT.glob("week_*/slides/*.md")):
        rel = deck.relative_to(ROOT).as_posix()
        if per_file.get(rel, 0) < 1:
            warn.append(f"{rel}: ไม่มีภาพเลย — ทุกชุดสไลด์ต้องมีภาพ ≥ 1 (กฎ FG-6)")
    for note in sorted(ROOT.glob("week_*/notes/*.md")):
        rel = note.relative_to(ROOT).as_posix()
        n = per_file.get(rel, 0)
        if n < 2:
            warn.append(f"{rel}: มีภาพ {n} ภาพ — note ต้องมีภาพ ≥ 2 (กฎ FG-6)")

    # ── FG-8: สัดส่วน type B
    total = sum(type_count.values())
    if total:
        share_b = type_count.get("B", 0) / total
        if share_b > TYPE_B_MAX_SHARE:
            warn.append(
                f"ภาพ type B คิดเป็น {100*share_b:.1f}% ของทั้งหมด เกินเพดาน "
                f"{100*TYPE_B_MAX_SHARE:.0f}% (กฎ FG-8) — กำลังสอนให้ดูภาพแทนการทำมือ"
            )

    if missing and not allow_missing:
        for fid in missing:
            wd = figures[fid]["week_dir"]
            hard.append(
                f"id '{fid}' ยังไม่มีไฟล์ภาพ — คาดหวังที่ "
                f"{(wd / 'figures' / (fid + '.svg')).relative_to(ROOT).as_posix()}"
            )

    # ── รายงานหน้าจอ
    print(f"\n=== FIGURE AUDIT ===")
    print(f"ไฟล์ที่สแกน: {len(sources)} | ภาพที่อ้างถึง: {total} | มีไฟล์แล้ว: {len(present)} | missing: {len(missing)}")
    if total:
        print("\nสัดส่วน type:")
        for t in ("A", "B", "C"):
            c = type_count.get(t, 0)
            print(f"  type {t}  {c:3d}  ({100*c/total:5.1f}%)")
    if orphans:
        print(f"\nไฟล์ภาพที่ไม่มี marker อ้างถึง (orphan): {len(orphans)}")
        for o in orphans:
            print(f"  {o}")

    print(f"\nHard errors: {len(hard)}")
    for e in hard:
        print(f"[FAIL] {e}")
    print(f"\nWarnings: {len(warn)}")
    for w in warn:
        print(f"[WARN] {w}")

    # ── เขียนรายงาน
    lines = [
        "# FIGURE_AUDIT.md",
        "",
        "> สร้างอัตโนมัติด้วย `python tools/audit_figures.py` — **ห้ามแก้ด้วยมือ**",
        "",
        f"ภาพที่อ้างถึงทั้งหมด **{total}** ภาพ · มีไฟล์แล้ว **{len(present)}** · ยังขาด **{len(missing)}**",
        "",
        "## สถานะภาพทั้งคอร์ส",
        "",
        "| สถานะ | Type | id | สัปดาห์ | อ้างถึงที่ | คำบรรยาย |",
        "|---|---|---|---|---|---|",
    ]
    for fid, info in sorted(figures.items(), key=lambda kv: (kv[1]["week"], kv[0])):
        status = "✅" if info["asset"] else "❌ ขาด"
        srcs = "<br>".join(info["sources"])
        cap = info["caption"]
        cap = cap if len(cap) <= 90 else cap[:87] + "..."
        lines.append(
            f"| {status} | {info['type']} | `{fid}` | {info['week']} | {srcs} | {cap} |"
        )

    lines += ["", "## สัดส่วน type", "", "| Type | ความหมาย | จำนวน | สัดส่วน |", "|---|---|---|---|"]
    meaning = {
        "A": "นักศึกษาต้องวาดตามได้",
        "B": "ดูเพื่อเข้าใจ ไม่ต้องวาดเอง",
        "C": "แผนภาพเชิงมโนทัศน์",
    }
    for t in ("A", "B", "C"):
        c = type_count.get(t, 0)
        pct = f"{100*c/total:.1f}%" if total else "-"
        lines.append(f"| {t} | {meaning[t]} | {c} | {pct} |")

    if orphans:
        lines += ["", "## ไฟล์ภาพที่ไม่มี marker อ้างถึง", ""]
        lines += [f"- `{o}`" for o in orphans]

    if hard or warn:
        lines += ["", "## ปัญหาที่พบ", ""]
        lines += [f"- **FAIL** — {e}" for e in hard]
        lines += [f"- WARN — {w}" for w in warn]

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nเขียนรายงานแล้ว: {REPORT.relative_to(ROOT).as_posix()}")

    if hard:
        print("\nRESULT: FAILED")
        return 1
    print("\nRESULT: PASSED" + (" (มี warning)" if warn else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(allow_missing="--allow-missing" in sys.argv[1:]))
