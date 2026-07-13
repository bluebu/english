#!/usr/bin/env python3
"""从 words/*.csv 生成 A4 默写卷 HTML（给中文写英文）。

用法:
  python3 generate_worksheet.py words/01_appliances.csv [--pdf]   # 单主题
  python3 generate_worksheet.py --merge words_1 [--pdf]           # 合集（words/ 下全部 CSV 连排）
输出: worksheets/<csv同名或合集名>.html，加 --pdf 时同时导出同名 .pdf
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
  /* 答案对照版：紧凑两栏、无线格，英文答案靠右 */
  .items.compact {{ row-gap: 6px; }}
  .ans {{ display: flex; align-items: baseline; flex-wrap: wrap; min-height: 20px; font-size: 12.5px; }}
  .ans .no {{ width: 26px; color: #555; font-size: 11px; flex-shrink: 0; }}
  .ans .pos {{ color: #888; font-size: 9.5px; font-style: italic; margin-left: 3px; }}
  .ans .en {{ margin-left: auto; font-weight: 600; padding-left: 12px; }}
  .ans .ph {{ color: #666; font-size: 11px; margin-left: 6px; }}
  .ans.section {{ grid-column: 1 / -1; font-weight: 700; font-size: 13.5px; min-height: 26px; align-items: flex-end; }}
  .ans.pad {{ min-height: 20px; }}
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
ANS_SECTION_TEMPLATE = '    <div class="ans section">{title}</div>'
ANS_PAD_TEMPLATE = '    <div class="ans pad"></div>'

PER_PAGE = 30      # 默写卷：两列 × 15 行，行距和四线格加大后一页放 30 个舒适
ANS_PER_PAGE = 70  # 答案对照版：紧凑行高，两列 × 35 行

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


def merge(out_stem: str = "words_1", pdf: bool = False,
          answers: bool = False) -> None:
    """全部主题连排成一份合集：章节之间不分页，章节标题占一整行（2 个词位）；
    标题起点不在行首时补空位，避免落在页面最后一行。
    answers=True 生成答案对照版（紧凑、无线格，显示英文和音标）。"""
    per_page = ANS_PER_PAGE if answers else PER_PAGE
    section_tpl = ANS_SECTION_TEMPLATE if answers else SECTION_TEMPLATE
    pad_tpl = ANS_PAD_TEMPLATE if answers else PAD_TEMPLATE
    render_item = ans_item_html if answers else item_html

    paths = sorted(Path("words").glob("[0-9]*_*.csv"))
    cells = []  # (占用词位数, html)
    total = 0
    for src in paths:
        rows = read_rows(src)
        total += len(rows)
        used = sum(s for s, _ in cells)
        if used % 2 == 1:  # 补齐到行首
            cells.append((1, pad_tpl))
            used += 1
        if used % per_page == per_page - 2:  # 标题不落在页面最后一行
            cells.append((1, pad_tpl))
            cells.append((1, pad_tpl))
        cells.append((2, section_tpl.format(
            title=html.escape(topic_title(src.stem)))))
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

    title = "KET 核心词汇 01–12 " + ("答案对照" if answers else "默写")
    pages = [render_page(title, items, total, p + 1, len(pages_items),
                         items_class=" compact" if answers else "",
                         info="" if answers else INFO_HTML)
             for p, items in enumerate(pages_items)]
    write_doc(out_stem, title, pages, pdf)


if __name__ == "__main__":
    pdf = "--pdf" in sys.argv
    argv = [a for a in sys.argv[1:] if a != "--pdf"]
    if argv and argv[0] == "--merge":
        merge(argv[1] if len(argv) > 1 else "words_1", pdf=pdf)
    elif argv and argv[0] == "--merge-answers":
        merge(argv[1] if len(argv) > 1 else "words_1_answers", pdf=pdf,
              answers=True)
    else:
        main(argv[0] if argv else "words/09_food_and_drink.csv", pdf=pdf)
