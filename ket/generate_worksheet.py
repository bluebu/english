#!/usr/bin/env python3
"""从 words/*.csv 生成 A4 默写卷 HTML（给中文写英文）。

用法:
  python3 generate_worksheet.py words/01_appliances.csv [--pdf]   # 单主题
  python3 generate_worksheet.py --merge words_1 [--pdf]           # 合集（words/ 下全部 CSV 连排）
  python3 generate_worksheet.py --select selections/20260820.txt [--pdf] [--answers]
                                                                  # 抽选卷（按 spec 从各主题挑词，章节与题号沿用原主题）
输出: worksheets/<csv同名 / 合集名 / spec 名>.html，加 --pdf 时同时导出同名 .pdf
"""
import csv
import html
import re
import subprocess
import sys
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  @page {{ size: A4; margin: 12mm 14mm; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: "Helvetica Neue", Arial, "PingFang SC", "Songti SC", sans-serif;
    color: #111;
    font-size: 13px;
    /* 打印时保留背景色，否则四线三格（CSS 背景画的）打不出来 */
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}
  /* 屏幕预览时模拟 A4 纸张 */
  @media screen {{
    body {{ background: #888; padding: 20px 0; }}
    .page {{
      width: 210mm; min-height: 297mm; margin: 0 auto 20px;
      background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,.4);
      padding: 12mm 14mm;
    }}
  }}
  @media print {{
    .page {{ page-break-after: always; }}
    .page:last-child {{ page-break-after: auto; }}
  }}
  .header {{
    display: flex; align-items: baseline; justify-content: space-between;
    border-bottom: 2px solid #111; padding-bottom: 6px; margin-bottom: 28px;
  }}
  .header h1 {{ font-size: 15px; padding-right: 10px; }}
  .header .info {{ font-size: 12px; white-space: nowrap; }}
  .header .info span {{ margin-left: 10px; }}
  .blank {{ display: inline-block; border-bottom: 1px solid #111; width: 40px; }}
  .items {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    column-gap: 30px;
    row-gap: 20px;
  }}
  .item {{
    display: flex; align-items: center;
    break-inside: avoid;
  }}
  .item .no {{ width: 26px; color: #555; font-size: 12px; flex-shrink: 0; }}
  .item .zh {{ flex-shrink: 0; max-width: 46%; line-height: 1.3; font-size: 14px; }}
  .item .pos {{ color: #888; font-size: 10px; font-style: italic; margin-left: 3px; flex-shrink: 0; }}
  /* 四线三格：绿色四线、红色基线（第三条），每格 14px，总高约 11mm */
  .item .line {{
    flex: 1; margin-left: 10px; min-width: 60px; height: 43px;
    background-image:
      linear-gradient(#4fae7e, #4fae7e),
      linear-gradient(#4fae7e, #4fae7e),
      linear-gradient(#e04b4b, #e04b4b),
      linear-gradient(#4fae7e, #4fae7e);
    background-size: 100% 1px;
    background-repeat: no-repeat;
    background-position: 0 0, 0 14px, 0 28px, 0 42px;
  }}
  /* 合集模式：章节标题占一整行（跨两栏，等同一行单词的高度）；pad 为对齐占位 */
  .item.section {{ grid-column: 1 / -1; font-weight: 700; font-size: 15px; min-height: 43px; }}
  .item.pad {{ min-height: 43px; }}
  /* 答案对照版：竖排 5 个一组、一行两组；紧凑无线格，英文答案靠右 */
  .items.compact {{ display: block; }}
  .items.compact .band {{
    display: grid; grid-template-columns: 1fr 1fr; column-gap: 30px;
    padding: 3px 6px; margin: 0 -6px 2px; border-radius: 3px;
    break-inside: avoid;
  }}
  /* 组行交替浅底：一眼看出哪 5 个是一组，不占额外高度 */
  .items.compact .band.alt {{ background: #f1f3f5; }}
  .items.compact .group {{ display: flex; flex-direction: column; row-gap: 6px; }}
  .ans {{ display: flex; align-items: baseline; flex-wrap: wrap; min-height: 20px; font-size: 12.5px; }}
  .ans .no {{ width: 26px; color: #555; font-size: 11px; flex-shrink: 0; }}
  .ans .pos {{ color: #888; font-size: 9.5px; font-style: italic; margin-left: 3px; }}
  .ans .en {{ margin-left: auto; font-weight: 600; padding-left: 12px; }}
  .ans .ph {{ color: #666; font-size: 11px; margin-left: 6px; }}
  .ans.section {{ font-weight: 700; font-size: 13.5px; min-height: 26px; align-items: flex-end; margin-bottom: 8px; }}
  .footer {{ margin-top: 8px; text-align: right; color: #999; font-size: 10px; }}
</style>
</head>
<body>
{pages}
</body>
</html>
"""

PAGE_TEMPLATE = """<div class="page">
  <div class="header">
    <h1>{title}{page_tag}</h1>
    <div class="info">{info}</div>
  </div>
  <div class="items{items_class}">
{items}
  </div>
  <div class="footer">共 {total} 词 · 第 {page_no}/{page_count} 页</div>
</div>"""

INFO_HTML = ('姓名 <span class="blank"></span> 日期 <span class="blank"></span> '
             '得分 <span class="blank"></span>')

ITEM_TEMPLATE = ('    <div class="item"><span class="no">{no}</span>'
                 '<span class="zh">{zh}</span>{pos}'
                 '<span class="line"></span></div>')

SECTION_TEMPLATE = '    <div class="item section">{title}</div>'
PAD_TEMPLATE = '    <div class="item pad"></div>'

ANS_ITEM_TEMPLATE = ('    <div class="ans"><span class="no">{no}</span>'
                     '<span class="zh">{zh}</span>{pos}'
                     '<span class="en">{word}</span>{ph}</div>')
ANS_SECTION_TEMPLATE = '  <div class="ans section">{title}</div>'

ANS_BAND_TEMPLATE = '  <div class="band{cls}">\n{groups}\n  </div>'
ANS_GROUP_TEMPLATE = '    <div class="group">\n{items}\n    </div>'

PER_PAGE = 30      # 默写卷：两列 × 15 行，行距和四线格加大后一页放 30 个舒适

# 答案对照版：竖排 GROUP 个一组，一行两组；按估算高度(px)切页
ANS_GROUP = 5
ANS_ROW_H, ANS_ROW_GAP = 20, 6      # 单行高、组内行距
ANS_BAND_GAP = 8                    # 组行上下留白（padding 3+3 + margin 2）
ANS_SEC_H, ANS_SEC_GAP = 26, 8      # 章节标题行
ANS_PAGE_H = 970                    # A4 去掉页边距 / 页眉 / 页脚后可用高度

# 合集分册：out_stem -> 收录的主题编号范围（上册定稿不再变动，新主题进下册）
VOLUMES = {
    "words_1": (1, 12),
    "words_2": (13, 99),
}

TITLES = {
    "appliances": "Appliances 家电",
    "clothes_and_accessories": "Clothes and Accessories 服装与饰品",
    "colours": "Colours 颜色",
    "communication_and_technology": "Communication and Technology 通信与技术",
    "documents_and_texts": "Documents and Texts 文件和文本",
    "education": "Education 教育",
    "entertainment_and_media": "Entertainment and Media 娱乐和媒体",
    "family_and_friends": "Family and Friends 家人和朋友",
    "food_and_drink": "Food and Drink 食物和饮料",
    "health_medicine_and_exercise": "Health, Medicine and Exercise 健康、医药和锻炼",
    "hobbies_and_leisure": "Hobbies and Leisure 爱好和休闲",
    "house_and_home": "House and Home 房子和家",
    "measurements": "Measurements 计量",
    "personal_feelings_opinions_and_experiences": "Personal Feelings 个人感受、观点和经历",
    "places_buildings": "Places: Buildings 地点：建筑",
    "places_countryside": "Places: Countryside 地点：乡村",
    "places_town_and_city": "Places: Town and City 地点：城镇和城市",
    "services": "Services 服务",
    "shopping": "Shopping 购物",
    "sport": "Sport 体育运动",
    "the_natural_world": "The Natural World 自然世界",
    "time": "Time 时间",
    "travel_and_transport": "Travel and Transport 旅游和运输",
    "weather": "Weather 天气",
    "work_and_jobs": "Work and Jobs 工作与职业",
}


def topic_title(stem: str) -> str:
    # 文件名形如 01_appliances：数字是主题编号，显示在标题前
    m = re.match(r"^(\d+)_(.+)$", stem)
    topic_no, key = (m.group(1), m.group(2)) if m else ("", stem)
    title = TITLES.get(key, key.replace("_", " ").title())
    return f"{topic_no} {title}" if topic_no else title


def read_rows(src: Path) -> list:
    with open(src, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def item_html(row: dict, fallback_no: int) -> str:
    pos = row["pos"].strip()
    pos_html = f'<span class="pos">{html.escape(pos)}</span>' if pos else ""
    no = row.get("no", "").strip() or str(fallback_no)
    return ITEM_TEMPLATE.format(no=f"{no}.", zh=html.escape(row["meaning"]),
                                pos=pos_html)


def ans_item_html(row: dict, fallback_no: int) -> str:
    pos = row["pos"].strip()
    pos_html = f'<span class="pos">{html.escape(pos)}</span>' if pos else ""
    ph = row["phonetic"].strip()
    ph_html = f'<span class="ph">{html.escape(ph)}</span>' if ph else ""
    no = row.get("no", "").strip() or str(fallback_no)
    return ANS_ITEM_TEMPLATE.format(no=f"{no}.", zh=html.escape(row["meaning"]),
                                    pos=pos_html, word=html.escape(row["word"]),
                                    ph=ph_html)


def write_doc(out_stem: str, title: str, pages: list, pdf: bool) -> None:
    out_dir = Path("worksheets")
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{out_stem}.html"
    out.write_text(TEMPLATE.format(title=html.escape(title), pages="\n".join(pages)),
                   encoding="utf-8")
    print(out)
    if pdf:
        pdf_path = out.with_suffix(".pdf")
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
             f"--print-to-pdf={pdf_path}", f"file://{out.resolve()}"],
            check=True, capture_output=True)
        print(pdf_path)


def render_page(title: str, items: list, total: int, page_no: int,
                page_count: int, items_class: str = "",
                info: str = INFO_HTML) -> str:
    return PAGE_TEMPLATE.format(
        title=html.escape(title), page_tag="", info=info,
        items_class=items_class, items="\n".join(items),
        total=total, page_no=page_no, page_count=page_count)


def main(csv_path: str, pdf: bool = False) -> None:
    src = Path(csv_path)
    rows = read_rows(src)
    title = topic_title(src.stem) + " 默写"

    pages = []
    page_count = (len(rows) + PER_PAGE - 1) // PER_PAGE
    for p in range(page_count):
        chunk = rows[p * PER_PAGE:(p + 1) * PER_PAGE]
        items = [item_html(row, p * PER_PAGE + 1 + i)
                 for i, row in enumerate(chunk)]
        pages.append(render_page(title, items, len(rows), p + 1, page_count))

    write_doc(src.stem, title, pages, pdf)


def build_answer_doc(sections: list, out_stem: str, title: str,
                     pdf: bool = False) -> None:
    """答案对照版：竖排 ANS_GROUP 个一组，一行两组；按估算高度切页，
    整组不跨页，章节标题不落在页尾（后面至少跟一组）。"""
    blocks, total = [], 0   # blocks: (高度, html, 是否章节标题)
    for sec_title, rows in sections:
        total += len(rows)
        blocks.append((ANS_SEC_H + ANS_SEC_GAP,
                       ANS_SECTION_TEMPLATE.format(title=html.escape(sec_title)),
                       True))
        items = [ans_item_html(row, i) for i, row in enumerate(rows, 1)]
        groups = [items[i:i + ANS_GROUP]
                  for i in range(0, len(items), ANS_GROUP)]
        for i in range(0, len(groups), 2):
            pair = groups[i:i + 2]
            n = max(len(g) for g in pair)
            band = ANS_BAND_TEMPLATE.format(
                cls="" if (i // 2) % 2 == 0 else " alt",
                groups="\n".join(
                    ANS_GROUP_TEMPLATE.format(
                        items="\n".join("  " + it for it in g)) for g in pair))
            blocks.append((n * ANS_ROW_H + (n - 1) * ANS_ROW_GAP + ANS_BAND_GAP,
                           band, False))

    pages_items, page_items, used = [], [], 0
    for i, (h, cell, is_sec) in enumerate(blocks):
        need = h + (blocks[i + 1][0] if is_sec and i + 1 < len(blocks) else 0)
        if page_items and used + need > ANS_PAGE_H:
            pages_items.append(page_items)
            page_items, used = [], 0
        page_items.append(cell)
        used += h
    if page_items:
        pages_items.append(page_items)

    pages = [render_page(title, items, total, p + 1, len(pages_items),
                         items_class=" compact", info="")
             for p, items in enumerate(pages_items)]
    write_doc(out_stem, title, pages, pdf)


def build_doc(sections: list, out_stem: str, title: str,
              pdf: bool = False, answers: bool = False) -> None:
    """把若干 (章节标题, rows) 连排成一份卷子：章节之间不分页，
    章节标题占一整行（2 个词位）；标题起点不在行首时补空位，
    且不让标题落在页面最后一行。题号沿用各章 CSV 里的 no。
    answers=True 生成答案对照版（紧凑、无线格，显示英文和音标）。"""
    if answers:
        return build_answer_doc(sections, out_stem, title, pdf)
    per_page = PER_PAGE
    section_tpl = SECTION_TEMPLATE
    pad_tpl = PAD_TEMPLATE
    render_item = item_html

    cells = []  # (占用词位数, html)
    total = 0
    for sec_title, rows in sections:
        total += len(rows)
        used = sum(s for s, _ in cells)
        if used % 2 == 1:  # 补齐到行首
            cells.append((1, pad_tpl))
            used += 1
        if used % per_page == per_page - 2:  # 标题不落在页面最后一行
            cells.append((1, pad_tpl))
            cells.append((1, pad_tpl))
        cells.append((2, section_tpl.format(title=html.escape(sec_title))))
        for i, row in enumerate(rows, 1):
            cells.append((1, render_item(row, i)))

    # 按词位切页
    page_items, pages_items, used = [], [], 0
    for slots, cell in cells:
        if used + slots > per_page:
            pages_items.append(page_items)
            page_items, used = [], 0
        page_items.append(cell)
        used += slots
    if page_items:
        pages_items.append(page_items)

    pages = [render_page(title, items, total, p + 1, len(pages_items),
                         info=INFO_HTML)
             for p, items in enumerate(pages_items)]
    write_doc(out_stem, title, pages, pdf)


def merge(out_stem: str = "words_1", pdf: bool = False,
          answers: bool = False) -> None:
    """按分册把 words/ 下的主题连排成一份合集（上册 01–12、下册 13 起）。"""
    key = out_stem[:-len("_answers")] if out_stem.endswith("_answers") else out_stem
    lo, hi = VOLUMES.get(key, (1, 99))
    paths = [p for p in sorted(Path("words").glob("[0-9]*_*.csv"))
             if lo <= int(p.stem.split("_")[0]) <= hi]
    if not paths:
        sys.exit(f"{key} 分册（主题 {lo}–{hi}）下没有词表")
    sections = [(topic_title(src.stem), read_rows(src)) for src in paths]
    nos = [int(p.stem.split("_")[0]) for p in paths]
    span = f"{min(nos):02d}–{max(nos):02d}"
    title = f"KET 核心词汇 {span} " + ("答案对照" if answers else "默写")
    build_doc(sections, out_stem, title, pdf, answers)


def parse_nos(spec: str) -> list:
    """'1,2,6,13-16' -> [1, 2, 6, 13, 14, 15, 16]（保持书写顺序）"""
    nos = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            nos.extend(range(int(a), int(b) + 1))
        else:
            nos.append(int(part))
    return nos


def read_selection(spec_path: Path) -> tuple:
    """选词卷 spec 文件：首个 '# xxx' 行是卷名，其余每行 '<主题号>:<题号列表>'。"""
    name, picks = None, []
    for line in spec_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            if name is None:
                name = line.lstrip("#").strip()
            continue
        topic, _, nos = line.partition(":")
        picks.append((topic.strip(), parse_nos(nos)))
    return name, picks


def select(spec_path: str, pdf: bool = False, answers: bool = False) -> None:
    """按 spec 从若干主题里抽词，拼成一份卷子（章节标题和题号都沿用原主题）。"""
    spec = Path(spec_path)
    name, picks = read_selection(spec)
    sections = []
    for topic, nos in picks:
        matches = sorted(Path("words").glob(f"{int(topic):02d}_*.csv"))
        if not matches:
            sys.exit(f"找不到主题 {topic} 的词表")
        src = matches[0]
        by_no = {r["no"].strip(): r for r in read_rows(src)}
        rows = []
        for n in nos:
            row = by_no.get(str(n))
            if row is None:
                sys.exit(f"{src.name} 里没有第 {n} 号词")
            rows.append(row)
        sections.append((topic_title(src.stem), rows))
    title = (name or spec.stem) + (" 答案对照" if answers else " 默写")
    build_doc(sections, spec.stem + ("_answers" if answers else ""),
              title, pdf, answers)


if __name__ == "__main__":
    pdf = "--pdf" in sys.argv
    answers = "--answers" in sys.argv
    argv = [a for a in sys.argv[1:] if a not in ("--pdf", "--answers")]
    if argv and argv[0] == "--merge":
        merge(argv[1] if len(argv) > 1 else "words_1", pdf=pdf)
    elif argv and argv[0] == "--merge-answers":
        merge(argv[1] if len(argv) > 1 else "words_1_answers", pdf=pdf,
              answers=True)
    elif argv and argv[0] == "--select":
        select(argv[1], pdf=pdf, answers=answers)
    else:
        main(argv[0] if argv else "words/09_food_and_drink.csv", pdf=pdf)
