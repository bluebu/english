#!/usr/bin/env python3
"""生成某一天的点读总结页：review/daily/YYYY-MM-DD.html

    python3 tools/build_daily.py 2026-08-25      # 在 review/ 目录下

数据来源两处：
  1. reports/*.html 里的 report-* meta —— 表格和合计全自动算
  2. daily/YYYY-MM-DD.json —— 当天的判断和建议，手写（这部分机器给不了）

另外会顺手去 ../homework/specs/YYYYMMDD.txt 里把当天的「点读 / 读」两项抄过来，
让总结页上能看见作业原文。**这只发生在生成时**：产出的 HTML 不引用 homework/ 的任何文件，
栏目之间照旧互不引用。拿不到 spec 就跳过这一块，不报错。
"""

import html
import json
import string
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS, DAILY = ROOT / "reports", ROOT / "daily"
SPECS = ROOT.parent / "homework" / "specs"

FIELDS = ("date", "order", "cat", "score", "title", "sub", "words", "secs", "acc", "wcpm")
CAT_ORDER = ("单词", "超8", "G3", "语法")

# 分类 → palette.css 里的色 token（fallback 是同一份值，防 CSS 没加载）
CAT_COLOR = {
    "单词": ("word", "#5BA97E", "#E2F1E9"),
    "超8":  ("read", "#E08B3C", "#FBEBD9"),
    "G3":   ("listen", "#4A90D9", "#DFECFA"),
    "语法": ("gram", "#D97070", "#FAE4E4"),
}


def cat_style(cat):
    tok, c, bg = CAT_COLOR.get(cat, ("drill", "#A97EC4", "#F0E7F7"))
    return f'--c:var(--c-{tok},{c});--cbg:var(--c-{tok}-bg,{bg})'


def read_meta(path):
    head = path.read_text()[:9000]
    got = {}
    for f in FIELDS:
        m = re.search(rf'<meta name="report-{f}" content="([^"]*)"', head)
        if not m:
            return None
        got[f] = m.group(1)
    got["href"] = f"../reports/{path.name}"
    return got


def homework_items(date):
    """从当天的打卡 spec 里挑出会出报告的那几项，抄成纯文本。

    [练] 下面还有 AI 之类不评的条目，所以只留标题带「抄写」的那一条。
    """
    f = SPECS / (date.replace("-", "") + ".txt")
    if not f.exists():
        return []
    items, cur = [], None
    for line in f.read_text().split("\n"):
        m = re.match(r"\[(点读|读|语法|练)\]\s*(.+)", line.strip())
        if m:
            kind, title = m.group(1), m.group(2).split("|")[0].strip()
            if kind == "练" and "抄写" not in title:
                cur = None
                continue
            cur = {"kind": kind, "title": title, "subs": []}
            items.append(cur)
            continue
        if cur is not None:
            if line.startswith("    *"):
                cur["subs"].append(line.strip("* ").strip())
            elif line.strip() and not line.startswith(" "):
                cur = None
    return items


def mmss(sec):
    sec = int(round(sec))
    return f"{sec//60} 分 {sec%60:02d} 秒" if sec >= 60 else f"{sec} 秒"


def zh_date(iso):
    y, m, d = iso.split("-")
    return f"{int(m)}月{int(d)}日"


def build(date):
    reports = [m for m in (read_meta(p) for p in sorted(REPORTS.glob("*.html"))) if m]
    rank = lambda c: CAT_ORDER.index(c) if c in CAT_ORDER else len(CAT_ORDER)
    day = sorted([r for r in reports if r["date"] == date],
                 key=lambda r: (rank(r["cat"]), int(r["order"])))
    if not day:
        sys.exit(f"{date} 没有报告")

    note = json.loads((DAILY / f"{date}.json").read_text())

    # 合计只算课文（wcpm 为 "-" 的是单词表，不进合计）
    passages = [r for r in day if r["wcpm"] != "-"]
    words = sum(int(r["words"]) for r in passages)
    secs = sum(float(r["secs"]) for r in day)
    correct = sum(round(int(r["words"]) * float(r["acc"]) / 100) for r in passages)
    acc = correct / words * 100
    wcpm = correct / sum(float(r["secs"]) for r in passages) * 60

    rows, seen = [], None
    for r in day:
        if r["cat"] != seen:                       # 每换一类插一条小标签
            seen = r["cat"]
            rows.append(f'        <p class="cat" style="{cat_style(seen)}">{seen}</p>')
        ac = f'{r["acc"]}%' if r["acc"] != "-" else "—"
        wc = r["wcpm"] if r["wcpm"] != "-" else "—"
        rows.append(f'''        <a class="r" href="{html.escape(r["href"], quote=True)}" style="{cat_style(r["cat"])}">
          <span class="n">{r["score"]}</span>
          <span class="tt"><span class="zh">{r["title"]}</span>
            <span class="en">{r["sub"]}</span></span>
          <span class="m"><b>{ac}</b><i>正确率</i></span>
          <span class="m"><b>{wc}</b><i>词/分</i></span>
        </a>''')

    hw = homework_items(date)
    hw_html = ""
    if hw:
        lis = []
        for it in hw:
            subs = ("<ul>" + "".join(f"<li>{html.escape(s)}</li>" for s in it["subs"]) + "</ul>") if it["subs"] else ""
            lis.append(f'<li><b>[{it["kind"]}]</b> {html.escape(it["title"])}{subs}</li>')
        hw_html = f'''
    <h2 class="mini-h"><span>📋</span> 今天打卡单上，这几项出了报告</h2>
    <section class="box hw">
      <ul class="hwl">{"".join(lis)}</ul>
      <p class="sc-note">上面每一项都做完了，各出了一份报告 ✓</p>
    </section>
'''
    todos = "\n".join(
        f'''      <div class="t"><span class="ic">{t["ic"]}</span>
        <span><p class="h">{t["h"]}</p><p class="d2">{t["d"]}</p></span></div>'''
        for t in note["todos"])
    # 模板里 CSS 满是花括号，所以用 $name 占位（string.Template），不用 .format()
    tpl = string.Template((Path(__file__).parent / "daily_template.html").read_text())
    return tpl.substitute(
        date=date, zh=zh_date(date), title=note["title"], lead=note["lead"], tip=note["tip"],
        words=words, secs=mmss(secs), acc=f"{acc:.1f}", wcpm=f"{wcpm:.0f}", n=len(day),
        hw=hw_html, rows="\n".join(rows), blocks="\n".join(note["blocks"]), todos=todos)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    d = sys.argv[1]
    DAILY.mkdir(exist_ok=True)
    out = DAILY / f"{d}.html"
    out.write_text(build(d))
    print(f"写好 {out.relative_to(ROOT)}")
