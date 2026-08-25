#!/usr/bin/env python3
"""给每份报告刷上它自己的分数色（越差越红）。

    python3 tools/paint_scores.py      # 在 review/ 目录下

读每份报告 <head> 里的 report-score，算出 --score / --score-bg 写回 :root。
分类色（--read）管「这是哪一类」，分数色管「做得怎么样」，两套并存、各管各的。
改了某份报告的分数就重跑一次。
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figures import score_color  # noqa: E402

REPORTS = Path(__file__).resolve().parent.parent / "reports"
LINE = re.compile(r"^      --score:.*\n", re.M)


def main():
    n = 0
    for p in sorted(REPORTS.glob("*.html")):
        s = p.read_text()
        m = re.search(r'name="report-score" content="([^"]*)"', s)
        if not m:
            continue
        fg, bg = score_color(m.group(1))
        new = f"      --score:{fg}; --score-bg:{bg};\n"
        if LINE.search(s):
            s = LINE.sub(new, s, count=1)
        else:                                   # 第一次刷，插在栏目主色后面
            anchor = re.search(r"^      --read:.*\n", s, re.M)
            if not anchor:
                print(f"  跳过 {p.name}：没找到 --read 那一行")
                continue
            s = s[:anchor.end()] + new + s[anchor.end():]
        p.write_text(s)
        print(f"  {p.name:34s} {m.group(1):>5} → {fg}")
        n += 1
    print(f"刷了 {n} 份")


if __name__ == "__main__":
    main()
