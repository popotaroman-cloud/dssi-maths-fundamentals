# -*- coding: utf-8 -*-
"""
build_slides.py — แปลงชุดสไลด์ Markdown เป็น HTML สไลด์เดียวจบ (KaTeX พร้อมใช้)

ใช้เปลือก HTML (shell) ที่ดึงมาจากคอร์ส `selected topics` ซึ่งมี CSS/JS/KaTeX
ที่ใช้งานจริงมาแล้ว จึงไม่ต้องออกแบบใหม่

การใช้งาน
---------
สร้าง shell ครั้งแรก (ทำครั้งเดียว):
    python tools/build_slides.py --make-shell

แปลงไฟล์:
    python tools/build_slides.py week_01_equations/slides/01_solution_concept.md

แปลงทั้งโฟลเดอร์:
    python tools/build_slides.py week_01_equations/slides/*.md

รูปแบบ Markdown ที่รองรับ
------------------------
    # Slide Deck: <ชื่อชุด>
    > <บรรทัดข้อมูลกำกับ>

    ---

    ## Slide 1 - Title
    **Key Message**: ...
    <เนื้อหา>

    ---

    ## Slide 2 - ...

ข้อควรระวัง (บังคับโดยกฎ SL-5 / M-2 ใน BUILD_RULES.md)
------------------------------------------------------
KaTeX ถูกตั้งค่า ignoredTags = script/noscript/style/textarea/pre/code
=> สมการที่อยู่ใน ``` code fence จะไม่ถูกเรนเดอร์
สคริปต์นี้จะเตือน (warning) ถ้าเจอ `$` อยู่ใน code fence
"""
import sys
import re
import html
import glob
import pathlib

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHELL = ROOT / "templates" / "slide_shell.html"
DEFAULT_SHELL_SOURCE = pathlib.Path(
    r"E:/2569/selected topics/session_02_llm_basics/slides/01_llm_concepts.html"
)

FENCE_TOKEN = "\x00F{}\x00"
MATH_TOKEN = "\x00M{}\x00"


# ─────────────────────────────────────────────────────────────
# shell
# ─────────────────────────────────────────────────────────────
def make_shell(source: pathlib.Path) -> int:
    if not source.exists():
        print(f"[FAIL] ไม่พบไฟล์ต้นแบบ: {source}")
        return 1
    txt = source.read_text(encoding="utf-8")

    open_tag = '<div id="presentation">'
    nav_tag = '<div id="nav">'
    i = txt.find(open_tag)
    j = txt.find(nav_tag)
    if i < 0 or j < 0 or j < i:
        print("[FAIL] โครงสร้าง HTML ต้นแบบไม่ตรงที่คาด (หา #presentation / #nav ไม่เจอ)")
        return 1

    prefix = txt[: i + len(open_tag)]
    suffix = txt[j:]

    prefix = re.sub(
        r"<title>.*?</title>", "<title>{{TITLE}}</title>", prefix, flags=re.DOTALL
    )
    prefix = re.sub(
        r'(id="progress-fill"[^>]*style="width:)[^"]*(")', r"\g<1>0%\g<2>", prefix
    )

    SHELL.parent.mkdir(parents=True, exist_ok=True)
    SHELL.write_text(prefix + "\n{{SLIDES}}\n" + suffix, encoding="utf-8")
    print(f"[OK] เขียน shell แล้ว: {SHELL}  ({len(prefix) + len(suffix)} bytes)")
    print("     เปลือกนี้มี CSS + JS นำทาง + KaTeX ครบ ไม่ต้องแก้อีก")
    return 0


# ─────────────────────────────────────────────────────────────
# marker ภาพ
# ─────────────────────────────────────────────────────────────
FIGURE_RE = re.compile(r"\[FIGURE\s*\|([^|\]]*)\|([^|\]]*)\|([^\]]*)\]")
_FIG_DIR = {"path": None}


def render_figure(marker: str) -> str:
    """แปลง marker เป็น <img> ถ้ามีไฟล์ภาพจริง ไม่งั้นเป็นกล่อง placeholder"""
    m = FIGURE_RE.search(marker)
    if not m:
        return (
            '<div style="border:2px dashed #c62828;border-radius:8px;padding:14px 18px;'
            'color:#c62828;margin:10px 0;">marker ภาพผิดรูปแบบ (กฎ FG-1): '
            + inline(marker)
            + "</div>"
        )
    ftype, fid, caption = (g.strip() for g in m.groups())

    figdir = _FIG_DIR["path"]
    if figdir is not None:
        for ext in (".svg", ".png"):
            asset = figdir / f"{fid}{ext}"
            if asset.exists():
                rel = "../figures/" + asset.name
                return (
                    f'<figure style="margin:10px 0;text-align:center;">'
                    f'<img src="{rel}" alt="{html.escape(caption, quote=True)}" '
                    f'style="max-width:100%;max-height:52vh;">'
                    f"</figure>"
                )

    return (
        '<div class="figure-placeholder" style="border:2px dashed #90a4ae;'
        "border-radius:8px;padding:14px 18px;color:#546e7a;font-style:italic;"
        'margin:10px 0;">'
        f"<strong>[ยังไม่มีภาพ · type {html.escape(ftype)} · {html.escape(fid)}]</strong><br>"
        + inline(caption)
        + "</div>"
    )


# ─────────────────────────────────────────────────────────────
# markdown -> html (เฉพาะที่กฎ SL-* อนุญาต)
# ─────────────────────────────────────────────────────────────
def extract_fences(text, store):
    def repl(m):
        store.append(m.group(2))
        return FENCE_TOKEN.format(len(store) - 1)

    return re.sub(r"```(\w*)\n(.*?)```", repl, text, flags=re.DOTALL)


def protect_math(text, store):
    def repl(m):
        store.append(m.group(0))
        return MATH_TOKEN.format(len(store) - 1)

    text = re.sub(r"\$\$.*?\$\$", repl, text, flags=re.DOTALL)
    text = re.sub(r"\$[^$\n]+?\$", repl, text)
    return text


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def render_table(rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    head, body = cells[0], cells[2:]
    out = ["<table><thead><tr>"]
    out += [f"<th>{inline(c)}</th>" for c in head]
    out.append("</tr></thead><tbody>")
    for row in body:
        out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def blocks_to_html(text):
    lines = text.split("\n")
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # ตาราง
        if stripped.startswith("|") and i + 1 < len(lines) and re.match(
            r"^\s*\|[\s:\-|]+\|\s*$", lines[i + 1]
        ):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            out.append(render_table(rows))
            continue

        # หัวข้อย่อยในสไลด์
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            lvl = min(len(m.group(1)) + 1, 4)
            out.append(
                f'<h{lvl} class="content-heading">{inline(m.group(2))}</h{lvl}>'
            )
            i += 1
            continue

        # marker ภาพ: [FIGURE | type | id | คำบรรยาย]  (กฎ FG-1)
        if stripped.startswith("[FIGURE"):
            out.append(render_figure(stripped))
            i += 1
            continue

        # blockquote
        if stripped.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            out.append("<blockquote>" + inline(" ".join(buf)) + "</blockquote>")
            continue

        # รายการ
        if re.match(r"^[-*+]\s+", stripped) or re.match(r"^\d+\.\s+", stripped):
            ordered = bool(re.match(r"^\d+\.\s+", stripped))
            tag = "ol" if ordered else "ul"
            cls = "" if ordered else ' class="slide-list"'
            items = []
            while i < len(lines):
                s = lines[i].strip()
                m2 = re.match(r"^(?:[-*+]|\d+\.)\s+(.*)$", s)
                if not m2:
                    break
                items.append(m2.group(1))
                i += 1
            out.append(
                f"<{tag}{cls}>"
                + "".join(f"<li>{inline(t)}</li>" for t in items)
                + f"</{tag}>"
            )
            continue

        # ย่อหน้า
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(
            r"^\s*(\||#{1,4}\s|[-*+]\s|\d+\.\s|>|\[FIGURE)", lines[i]
        ):
            buf.append(lines[i].strip())
            i += 1
        if buf:
            out.append("<p>" + inline(" ".join(buf)) + "</p>")

    return "\n".join(out)


def restore(text, fences, maths):
    for idx, code in enumerate(fences):
        block = (
            '<div class="code-block"><pre><code>'
            + html.escape(code.rstrip("\n"), quote=False)
            + "</code></pre></div>"
        )
        text = text.replace(FENCE_TOKEN.format(idx), block)
    for idx, m in enumerate(maths):
        text = text.replace(MATH_TOKEN.format(idx), html.escape(m, quote=False))
    return text


def md_to_html(md):
    fences, maths = [], []
    t = extract_fences(md, fences)
    t = protect_math(t, maths)
    t = blocks_to_html(t)
    return restore(t, fences, maths)


# ─────────────────────────────────────────────────────────────
# build
# ─────────────────────────────────────────────────────────────
SLIDE_RE = re.compile(r"^##\s+Slide\s+\d+\s*[-—–]\s*(.*)$", re.MULTILINE)


def build(md_path: pathlib.Path) -> int:
    if not SHELL.exists():
        print(f"[FAIL] ไม่พบ {SHELL} — รัน `python tools/build_slides.py --make-shell` ก่อน")
        return 1

    md = md_path.read_text(encoding="utf-8")
    warnings = []
    _FIG_DIR["path"] = md_path.parent.parent / "figures"

    m = re.search(r"^#\s+Slide Deck:\s*(.*)$", md, re.MULTILINE)
    deck_title = m.group(1).strip() if m else md_path.stem
    if not m:
        warnings.append("ไม่พบบรรทัด `# Slide Deck: ...` — ใช้ชื่อไฟล์เป็น title")

    for fm in re.finditer(r"```\w*\n(.*?)```", md, re.DOTALL):
        if "$" in fm.group(1):
            warnings.append(
                "พบ `$` ใน code fence — KaTeX จะไม่เรนเดอร์ (กฎ SL-5) ให้ย้ายสมการออกมา"
            )
            break

    n_fig = len(FIGURE_RE.findall(md))
    if n_fig == 0:
        warnings.append("ชุดนี้ไม่มีภาพเลย — ทุกชุดสไลด์ต้องมีภาพ >= 1 (กฎ FG-6)")
    for bad in re.finditer(r"\[FIGURE\s*:", md):
        warnings.append("พบ marker แบบเก่า `[FIGURE: ...]` — ต้องใช้รูปแบบ 4 ช่อง (กฎ FG-1)")
        break

    matches = list(SLIDE_RE.finditer(md))
    if not matches:
        print("[FAIL] ไม่พบสไลด์เลย — หัวเรื่องต้องเป็นรูป `## Slide N — ชื่อ`")
        return 1

    slides_html = []
    for idx, mt in enumerate(matches):
        title = mt.group(1).strip()
        start = mt.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(md)
        body = md[start:end]
        body = re.sub(r"^\s*-{3,}\s*$", "", body, flags=re.MULTILINE)

        km = re.search(r"^\s*\*\*Key Message\*\*\s*:\s*(.*)$", body, re.MULTILINE)
        key_html = ""
        if km:
            key_html = (
                '  <div class="key-message">'
                + md_to_html(km.group(1).strip()).replace("<p>", "").replace("</p>", "")
                + "</div>\n"
            )
            body = body[: km.start()] + body[km.end():]
        else:
            warnings.append(f"Slide {idx + 1} ({title}) ไม่มี **Key Message** (กฎ SL-2)")

        slides_html.append(
            f'<div class="slide slide-{idx}" data-title="{html.escape(title, quote=True)}">\n'
            f'  <div class="slide-header">\n'
            f'    <div class="slide-num">Slide {idx + 1}</div>\n'
            f'    <div class="slide-title">{inline(title)}</div>\n'
            f"  </div>\n"
            f"{key_html}"
            f'  <div class="slide-content">{md_to_html(body.strip())}</div>\n'
            f"</div>"
        )

    n = len(slides_html)
    if n < 6:
        warnings.append(f"ชุดนี้มี {n} สไลด์ — ต่ำสุด 6 สไลด์/ชุด (กฎ SL-1a)")
    elif n > 23:
        warnings.append(f"ชุดนี้มี {n} สไลด์ — สูงสุด 23 สไลด์/ชุด (กฎ SL-1a)")

    shell = SHELL.read_text(encoding="utf-8")
    page = shell.replace("{{TITLE}}", html.escape(f"Slide Deck: {deck_title}")).replace(
        "{{SLIDES}}", "\n".join(slides_html)
    )

    out = md_path.with_suffix(".html")
    out.write_text(page, encoding="utf-8")
    print(f"[OK] {md_path.name} -> {out.name}  ({n} สไลด์)")
    for w in warnings:
        print(f"  [WARN] {w}")
    return 0


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "--make-shell":
        src = pathlib.Path(argv[1]) if len(argv) > 1 else DEFAULT_SHELL_SOURCE
        return make_shell(src)

    paths = []
    for a in argv:
        paths += [pathlib.Path(p) for p in glob.glob(a)] or [pathlib.Path(a)]
    rc = 0
    for p in paths:
        if not p.exists():
            print(f"[FAIL] ไม่พบไฟล์: {p}")
            rc = 1
            continue
        rc |= build(p)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
