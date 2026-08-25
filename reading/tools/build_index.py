#!/usr/bin/env python3
"""刷新 reading/index.html 的报告列表：按日期倒序分组，同一天内按 report-order 排。

每份报告在 <head> 里自带五行 meta（report-date / -order / -score / -title / -sub），
这里只读那几行，不解析正文。加了新报告就跑一次：

    python3 tools/build_index.py        # 在 reading/ 目录下

列表写在 index.html 的 LIST:BEGIN / LIST:END 之间，别手改那一段。
"""

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"
DAILY = ROOT / "daily"
INDEX = ROOT / "index.html"

FIELDS = ("date", "order", "cat", "score", "title", "sub")


def read_meta(path: Path):
    head = path.read_text()[:8000]          # meta 都在 <head> 里
    got = {}
    for f in FIELDS:
        m = re.search(rf'<meta name="report-{f}" content="([^"]*)"', head)
        if not m:
            return None                     # 少一行就整份跳过，别半拉子进目录
        got[f] = m.group(1)
    got["href"] = f"./reports/{path.name}"
    return got


# 一天之内报告按这个顺序分组；没列到的分类排在最后
CAT_ORDER = ("单词", "超8", "G3", "语法")


def cat_rank(c):
    return CAT_ORDER.index(c) if c in CAT_ORDER else len(CAT_ORDER)


def zh_date(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{int(m)}月{int(d)}日"


def render(reports):
    days = {}
    for r in reports:
        days.setdefault(r["date"], []).append(r)

    out = ["<!-- LIST:BEGIN 由 tools/build_index.py 自动生成，别手改 -->"]
    for i, date in enumerate(sorted(days, reverse=True)):          # 新的一天在最前
        items = sorted(days[date], key=lambda r: (cat_rank(r["cat"]), int(r["order"])))
        cls = "day first" if i == 0 else "day"
        # 当天有小结页就在日期行右边挂个入口，没有就不挂
        link = (f'<a href="./daily/{date}.html">当日小结 →</a>'
                if (DAILY / f"{date}.html").exists() else "")
        out.append(f'      <div class="{cls}"><b>{zh_date(date)}</b>'
                   f'<span>{len(items)} 份</span><hr>{link}</div>')
        seen_cat = None
        for r in items:
            if r["cat"] != seen_cat:                               # 每换一类插一条小标签
                seen_cat = r["cat"]
                out.append(f'      <p class="cat">{r["cat"]}</p>')
            out.append(f'''      <div class="row">
        <span class="n">{r["score"]}</span>
        <span class="tt"><span class="zh">{r["title"]}</span>
          <span class="en">{r["sub"]}</span></span>
        <span class="links">
          <a href="{html.escape(r["href"], quote=True)}">看报告</a>
        </span>
      </div>''')
    out.append("<!-- LIST:END -->")
    return "\n".join(out)


def main():
    reports = [m for m in (read_meta(p) for p in sorted(REPORTS.glob("*.html"))) if m]
    if not reports:
        sys.exit("reports/ 里没找到带 report-* meta 的报告")
    s = INDEX.read_text()
    new, n = re.subn(r"<!-- LIST:BEGIN.*?<!-- LIST:END -->", lambda _: render(reports), s, flags=re.S)
    if n != 1:
        sys.exit("index.html 里没有唯一的 LIST:BEGIN / LIST:END 标记")
    INDEX.write_text(new)
    days = len({r["date"] for r in reports})
    print(f"目录已刷新：{len(reports)} 份报告 / {days} 天")


if __name__ == "__main__":
    main()
