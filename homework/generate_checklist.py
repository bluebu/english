#!/usr/bin/env python3
"""从 specs/*.txt 生成 A4 每日打卡作业单（HTML + PDF）。

用法（在 homework/ 目录下运行）:
  python3 generate_checklist.py specs/20260820.txt [--pdf]
  python3 generate_checklist.py [--pdf]        # 不给 spec 就用 specs/ 里最新改动的那份

输出: sheets/<spec 同名>.html，加 --pdf 时同时导出同名 .pdf；
      并刷新 index.html 的打卡单列表（LIST:BEGIN/END 之间由脚本生成）

spec 写法见 README.md（顶部 key: value，任务行 [标签] 标题 | 小标签，缩进行是子内容）。
"""
import html
import math
import re
import subprocess
import sys
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SPEC_DIR = Path("specs")
OUT_DIR = Path("sheets")
INDEX = Path("index.html")
MARK_BEGIN = "<!-- LIST:BEGIN 由 generate_checklist.py 自动生成，别手改 -->"
MARK_END = "<!-- LIST:END -->"
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def _palette():
    """从根目录 palette.css 取五个基色（和打卡评价栏目共用同一份）。

    读不到就退回内置值——脚本不能因为少个 CSS 文件就跑不了。
    """
    fallback = {"listen": "#4A90D9", "read": "#E08B3C", "word": "#5BA97E",
                "gram": "#D97070", "drill": "#A97EC4"}
    f = Path(__file__).resolve().parent.parent / "palette.css"
    if not f.exists():
        return fallback
    found = dict(re.findall(r"--c-(\w+)\s*:\s*(#[0-9A-Fa-f]{6})", f.read_text()))
    return {k: found.get(k, v) for k, v in fallback.items()}


_C = _palette()

# 类别关键字 → 色条颜色；标签里含哪个关键字就用哪个色
CATEGORY_COLORS = [
    ("听", _C["listen"]), ("指", _C["listen"]),
    ("读", _C["read"]),   ("点", _C["read"]),
    ("词", _C["word"]),   ("写", _C["word"]),
    ("练", _C["drill"]),  ("AI", _C["drill"]),
    ("语", _C["gram"]),   ("法", _C["gram"]),
]
CYCLE = [_C["listen"], _C["read"], _C["word"], _C["drill"], _C["gram"]]

META_KEYS = {"date", "title", "subtitle", "cheer", "memo", "tip-left", "tip-right"}

DEFAULTS = {
    "title": "每日打卡作业",
    "subtitle": "Daily Checklist",
    "cheer": "加油，每天一小步 👣 成就未来一大步",
    "memo": "2",
    "tip-left": "做完一项，就在右边的方框里打一个 ✓",
    "tip-right": "全部完成后，按模板在群里打卡",
}

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{doc_title}</title>
<style>
  @page {{ size: A4; margin: 10mm 12mm; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: "PingFang SC", "Helvetica Neue", "Hiragino Sans GB", "Songti SC", sans-serif;
    color: #22201d;
    font-size: 13px;
    line-height: 1.5;
    /* 打印时保留背景色，否则色条、勾选框底色都印不出来 */
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}
  @media screen {{
    body {{ background: #8b8b8b; padding: 20px 0; }}
    .page {{
      width: 210mm; min-height: 297mm; margin: 0 auto;
      background: #fffdf8; box-shadow: 0 2px 10px rgba(0,0,0,.4);
      padding: 10mm 12mm;
    }}
  }}
  .page {{ background: #fffdf8; }}

  /* ── 页头 ───────────────────────────── */
  .head {{
    display: flex; align-items: flex-end; justify-content: space-between;
    border-bottom: 3px solid #f0a830; padding-bottom: 8px; margin-bottom: 4px;
  }}
  .head .t {{ display: flex; align-items: baseline; gap: 10px; }}
  .head .date {{
    background: #f0a830; color: #fff; font-size: 17px; font-weight: 700;
    padding: 3px 11px; border-radius: 8px; letter-spacing: .5px;
  }}
  .head h1 {{ font-size: 20px; font-weight: 700; letter-spacing: 2px; }}
  .head .en {{ font-size: 10px; color: #a8a096; letter-spacing: 1.5px; text-transform: uppercase; }}
  .head .who {{ font-size: 11.5px; color: #6b6459; white-space: nowrap; }}
  .head .who span {{ margin-left: 14px; }}
  .u {{ display: inline-block; border-bottom: 1px solid #b9b1a5; width: 62px; }}

  .tip {{
    margin: 9px 0 12px; font-size: 11px; color: #9a9186;
    display: flex; justify-content: space-between;
  }}

  /* ── 任务卡 ─────────────────────────── */
  .task {{
    display: flex; align-items: stretch; gap: 9px;
    border: 1.5px solid #ece4d6; border-left: 5px solid var(--c);
    border-radius: 9px; background: #fff;
    padding: 11px 12px; margin-bottom: 10px;
    break-inside: avoid;
  }}
  .task .no {{
    flex: 0 0 22px; height: 22px; border-radius: 50%;
    background: var(--c); color: #fff; font-size: 12px; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    margin-top: 1px;
  }}
  .task .body {{ flex: 1; min-width: 0; }}
  .task .title {{ font-size: 15px; font-weight: 700; letter-spacing: .3px; }}
  .task .title .tag {{
    font-size: 10.5px; font-weight: 600; color: var(--c);
    border: 1px solid var(--c); border-radius: 4px;
    padding: 0 4px; margin-left: 6px; vertical-align: 1.5px;
  }}
  .task .sub {{ font-size: 12.5px; color: #6b6459; margin-top: 3px; }}
  .task .sub li {{ list-style: none; margin-top: 2px; padding-left: 12px; position: relative; }}
  .task .sub li::before {{
    content: ""; position: absolute; left: 2px; top: 6px;
    width: 4px; height: 4px; border-radius: 50%; background: var(--c); opacity: .55;
  }}
  .fill {{ border-bottom: 1px solid #cfc7b9; display: inline-block; width: 40px; }}

  /* 勾选框 */
  .box {{
    flex: 0 0 auto; width: 22px; height: 22px;
    border: 1.8px solid #c9c0b1; border-radius: 5px; background: #fffdf8;
  }}
  .task > .box {{ align-self: center; width: 28px; height: 28px; border-width: 2px; }}
  .mini {{ display: inline-flex; gap: 4px; vertical-align: -3px; margin-left: 4px; }}
  .mini i {{ width: 13px; height: 13px; border: 1.4px solid #c9c0b1; border-radius: 3px; display: inline-block; }}

  /* ── 单词表 ─────────────────────────── */
  .words {{ display: grid; grid-auto-flow: column;
           column-gap: 18px; row-gap: 7px; margin-top: 8px; }}
  .w {{ display: flex; align-items: center; gap: 7px; font-size: 12.5px; }}
  .w .box {{ width: 16px; height: 16px; border-radius: 4px; }}
  .w b {{ font-weight: 700; font-size: 13px; min-width: 68px; }}
  .w s {{ text-decoration: none; color: #857d71; }}

  /* ── 页脚 ───────────────────────────── */
  .memo {{
    margin-top: 12px; border: 1.5px dashed #e2d9c8; border-radius: 9px;
    background: #fffaf0; padding: 8px 12px 10px;
  }}
  .memo .lb {{ font-size: 11.5px; color: #b08a3e; font-weight: 700; letter-spacing: .5px; }}
  .memo .ln {{ border-bottom: 1px solid #eadfc9; height: 19px; }}
  .foot {{
    margin-top: 14px; border-top: 2px dashed #e2d9c8; padding-top: 8px;
    display: flex; align-items: center; justify-content: space-between;
  }}
  .foot .sign {{ font-size: 12.5px; color: #6b6459; }}
  .foot .sign span {{ margin-right: 16px; }}
  .foot .cheer {{
    font-size: 12.5px; color: #b8860b; font-weight: 600;
    background: #fdf4dd; border-radius: 20px; padding: 4px 12px;
  }}
</style>
</head>
<body>
<div class="page">

  <div class="head">
    <div class="t">
      {date_html}<div>
        <h1>{title}</h1>
        <div class="en">{subtitle}</div>
      </div>
    </div>
    <div class="who">姓名 <i class="u"></i><span>家长签字 <i class="u"></i></span></div>
  </div>

  <div class="tip">
    <span>{tip_left}</span>
    <span>{tip_right}</span>
  </div>

{tasks}
{memo}
  <div class="foot">
    <div class="sign">
      <span>完成时间 <i class="u"></i></span>
      <span>今日自评 ☆☆☆☆☆</span>
    </div>
    <div class="cheer">{cheer}</div>
  </div>

</div>
</body>
</html>
"""


# ── 解析 ─────────────────────────────────────────────
def parse_spec(path: Path) -> tuple[dict, list]:
    """spec → (meta, tasks)。tasks 里每项 {color, title, tag, subs, words}。"""
    meta, tasks = {}, []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indented = raw[0] in " \t"
        line = raw.strip()

        # 顶部 key: value（只认白名单键，免得中文冒号标题被吃掉）
        if not indented and not tasks and ":" in line:
            key, _, val = line.partition(":")
            if key.strip().lower() in META_KEYS:
                meta[key.strip().lower()] = val.strip()
                continue

        if not indented:                       # 新任务
            tasks.append(new_task(line, len(tasks)))
            continue

        if not tasks:
            raise SystemExit(f"缩进行没有对应的任务：{line}")
        task = tasks[-1]
        if line.startswith("+"):               # 单词表条目
            word, _, mean = line[1:].strip().partition("=")
            task["words"].append((word.strip(), mean.strip()))
        elif line.startswith("*"):             # 圆点列表项
            task["subs"].append(("li", line[1:].strip()))
        else:                                  # 普通说明行
            task["subs"].append(("p", line))
    return meta, tasks


def new_task(line: str, index: int) -> dict:
    color = CYCLE[index % len(CYCLE)]
    m = re.match(r"\[([^\]]*)\]\s*(.*)", line)
    if m:
        label, line = m.group(1).strip(), m.group(2).strip()
        color = label if label.startswith("#") else color_for(label, color)
    title, _, tag = line.partition("|")
    return {"color": color, "title": title.strip(), "tag": tag.strip(),
            "subs": [], "words": []}


def color_for(label: str, fallback: str) -> str:
    for key, color in CATEGORY_COLORS:
        if key in label:
            return color
    return fallback


# ── 渲染 ─────────────────────────────────────────────
def inline(text: str) -> str:
    """转义后还原两种记号：__ → 填空横线，<<n>> → n 个小方格。"""
    out = html.escape(text)
    out = re.sub(r"_{2,}",
                 lambda m: f'<i class="fill" style="width:{max(40, len(m.group()) * 11)}px"></i>',
                 out)
    out = re.sub(r"&lt;&lt;(\d+)&gt;&gt;",
                 lambda m: '<span class="mini">' + "<i></i>" * int(m.group(1)) + "</span>",
                 out)
    return out


def render_task(task: dict, no: int) -> str:
    title = inline(task["title"])
    if task["tag"]:
        title += f' <span class="tag">{inline(task["tag"])}</span>'

    body = [f'      <div class="title">{title}</div>']
    plain = [t for kind, t in task["subs"] if kind == "p"]
    items = [t for kind, t in task["subs"] if kind == "li"]
    for text in plain:
        body.append(f'      <div class="sub">{inline(text)}</div>')
    if items:
        lis = "".join(f'<li>{inline(t)}</li>' for t in items)
        body.append(f'      <ul class="sub">{lis}</ul>')
    if task["words"]:
        rows = math.ceil(len(task["words"]) / 2)
        cells = "".join(
            f'<div class="w"><div class="box"></div><b>{html.escape(w)}</b>'
            f'<s>{html.escape(m)}</s></div>'
            for w, m in task["words"])
        body.append(f'      <div class="words" style="grid-template-rows: repeat({rows}, auto)">'
                    f'{cells}</div>')

    return (f'  <div class="task" style="--c:{task["color"]}">\n'
            f'    <div class="no">{no}</div>\n'
            f'    <div class="body">\n' + "\n".join(body) + "\n"
            f'    </div>\n'
            f'    <div class="box"></div>\n'
            f'  </div>\n')


def build(meta: dict, tasks: list) -> str:
    cfg = {**DEFAULTS, **meta}
    date = cfg.get("date", "").strip()
    memo_lines = int(cfg["memo"] or 0)
    memo = ""
    if memo_lines:
        lns = "\n".join('    <div class="ln"></div>' for _ in range(memo_lines))
        memo = ('\n  <div class="memo">\n'
                '    <div class="lb">今日备注 · 想记下来的话</div>\n'
                f'{lns}\n'
                '  </div>\n')
    return TEMPLATE.format(
        doc_title=" ".join(x for x in (date, cfg["title"]) if x),
        date_html=f'<div class="date">{html.escape(date)}</div>\n      ' if date else "",
        title=html.escape(cfg["title"]),
        subtitle=html.escape(cfg["subtitle"]),
        tip_left=inline(cfg["tip-left"]),
        tip_right=inline(cfg["tip-right"]),
        tasks="".join(render_task(t, i + 1) for i, t in enumerate(tasks)),
        memo=memo,
        cheer=html.escape(cfg["cheer"]),
    )


# ── 目录页 ───────────────────────────────────────────
def update_index() -> None:
    """按 sheets/ 里现有的单子刷新 index.html 列表区，日期新的排在上面。"""
    if not INDEX.exists():
        return
    page = INDEX.read_text(encoding="utf-8")
    if MARK_BEGIN not in page or MARK_END not in page:
        print("index.html 里找不到 LIST 标记，列表没更新")
        return

    rows = []
    for sheet in sorted(OUT_DIR.glob("*.html"), reverse=True):
        stem = sheet.stem
        label, count = stem, 0
        spec = SPEC_DIR / f"{stem}.txt"
        if spec.exists():
            meta, tasks = parse_spec(spec)
            label, count = meta.get("date") or stem, len(tasks)
        ymd = re.fullmatch(r"(\d{4})(\d{2})(\d{2})", stem)
        day = str(int(ymd.group(3))) if ymd else "·"
        en = (f"{MONTHS_EN[int(ymd.group(2)) - 1]} {day} · Daily checklist"
              if ymd else "Daily checklist")
        links = [f'<a href="./{OUT_DIR}/{stem}.html">预览</a>']
        if (OUT_DIR / f"{stem}.pdf").exists():
            links.append(f'<a class="pdf" href="./{OUT_DIR}/{stem}.pdf">PDF</a>')
        rows.append(
            '      <div class="row">\n'
            f'        <span class="n">{day}</span>\n'
            f'        <span class="tt"><span class="zh">'
            f'{html.escape(label)}{f" · {count} 项" if count else ""}</span>\n'
            f'          <span class="en">{en}</span></span>\n'
            '        <span class="links">\n          '
            + "\n          ".join(links)
            + '\n        </span>\n'
            '      </div>')

    head, _, rest = page.partition(MARK_BEGIN)
    _, _, tail = rest.partition(MARK_END)
    INDEX.write_text(f"{head}{MARK_BEGIN}\n" + "\n".join(rows) + f"\n{MARK_END}{tail}",
                     encoding="utf-8")
    print(f"{INDEX}（{len(rows)} 份）")


def main(argv: list) -> None:
    pdf = "--pdf" in argv
    rest = [a for a in argv if not a.startswith("--")]
    if rest:
        spec = Path(rest[0])
    else:
        specs = sorted(SPEC_DIR.glob("*.txt"), key=lambda p: p.stat().st_mtime)
        if not specs:
            raise SystemExit(f"{SPEC_DIR}/ 里没有 spec 文件")
        spec = specs[-1]
    if not spec.exists():
        raise SystemExit(f"找不到 spec：{spec}")

    meta, tasks = parse_spec(spec)
    if not tasks:
        raise SystemExit(f"{spec} 里没有解析到任务行")

    OUT_DIR.mkdir(exist_ok=True)
    out = OUT_DIR / f"{spec.stem}.html"
    out.write_text(build(meta, tasks), encoding="utf-8")
    print(f"{out}（{len(tasks)} 项）")

    if pdf:
        pdf_path = out.with_suffix(".pdf")
        subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf_path}", f"file://{out.resolve()}"],
                       check=True, capture_output=True)
        print(pdf_path)

    update_index()


if __name__ == "__main__":
    main(sys.argv[1:])
