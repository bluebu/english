# 打卡评价（review/）

每天打卡做完的作业，逐项出一份能和下次对比的成绩单。

```
review/
  index.html                       目录页（列表由 build_index.py 刷新，别手改）
  reports/<书>-<课>-p<页>.html      每次一份报告
  data/<同名>.json                  声学分析结果（停顿、语速）
  data/<同名>.words.tsv             逐词时间戳（起 / 止 / 词）
  data/<同名>.per-word.json         单词表专用：逐词的犹豫时间与对齐结果
  tools/words.swift                 转写 + 逐词时间戳
  tools/analyze.py                  停顿与语速分析
  tools/figures.py                  停顿地图 + 「三把尺子上的位置」三张图
  tools/build_index.py              刷新目录页列表：按日期倒序分组
  tools/build_daily.py              生成当日小结页
  tools/daily_template.html         当日小结的页面模板（$name 占位）
  daily/YYYY-MM-DD.json             当日小结的文字部分，手写
  daily/YYYY-MM-DD.html             生成结果
```

## 做一份报告

```bash
# 1) 转写 + 逐词时间戳（macOS 26 本机 Speech 框架，离线，首次会下模型）
swiftc -O -parse-as-library tools/words.swift -o /tmp/words
/tmp/words 录音.m4a > data/超8-lesson3-p65.words.tsv

# 2) 停顿 / 语速
python3 tools/analyze.py 录音.m4a > data/超8-lesson3-p65.json

# 3) 拿课本原文逐字比对，套 reports/ 里现成的一份改

# 4) 刷新目录页
python3 tools/build_index.py

# 5) 当天的报告都做完后，写 daily/<日期>.json，再生成当日小结
python3 tools/build_daily.py 2026-08-25
python3 tools/build_index.py        # 小结页存在时，日期行右边会自动挂上入口
```

新报告的 `<head>` 里必须带这五行，`build_index.py` 只认这个：

```html
<meta name="report-date"  content="2026-08-25" />   <!-- 分组用，倒序排 -->
<meta name="report-order" content="66" />           <!-- 同一天、同一类里的顺序 -->
<meta name="report-cat"   content="超8" />          <!-- 分类，见下 -->
<meta name="report-score" content="61" />
<meta name="report-title" content="超8 · Lesson 3 · 第 66 页" />
<meta name="report-sub"   content="Prince Darling · 110 words" />
<meta name="report-words" content="110" />          <!-- 下面四行给当日小结汇总用 -->
<meta name="report-secs"  content="86.0" />
<meta name="report-acc"   content="96.4" />
<meta name="report-wcpm"  content="74" />           <!-- 单词表没有 WCPM，填 "-" -->
```

少任何一行，这份报告会被整个跳过（宁可不进目录，也不进半拉子的）。

**分类** `report-cat`：目录页和当日小结都按 **单词 → 超8 → G3 → 语法** 的顺序分组
（`CAT_ORDER`，两个脚本里各有一份，要改一起改）。没列到的分类排在最后。

`report-order` 只管同一类内部的先后，用「书序 × 100 + 页码」：
超8 = 61–67，Wonders = 208–211，语法练习册 = 308–310。

## 换书就换了一把尺子

分数是给「**这个孩子 + 这本书**」的，不是给孩子的。同一天：超8 96.4% / WCPM 74，
Wonders G3 89.0% / WCPM 52 —— 跨本比只用来判断**书难不难**，要看进步得同一本书跨天比。
报告里要把这句话写出来，别让人误读成孩子退步了。

Wonders 是美国本土教材，年级对得上，H&T 常模在那儿是**同类相比**；
超8 是中国出的分级读物，常模只能当参照系。两种情况报告里的措辞不一样。

## 口径（数值都在 tools/figures.py 顶部，改之前先回一手来源核）

- **准确率** = 读对词数 / 原文词数。替换、漏读、读错音计错；插入词和回读只算不流利，不计错。
  分档用 **Fountas & Pinnell Benchmark Assessment System 1, p.40**（Heinemann 官方）：
  L–N 级及以上 **≥98% 独立 / 95–97% 教学 / <95% 偏难**；A–K 级是另一套（95–100 / 90–94）。
  章节书按 L 级以上算。
- **WCPM** = 读对的词数 ÷ 总时长 × 60。常模用 **Hasbrouck & Tindal (2017) Technical Report #1702,
  Table 4「Compiled ORF Norms 2017」**（figures.py 里存的是秋季一列，按录音季节换）。
  这是**母语儿童**常模，只当参照系，不是及格线。
- **停顿** = 能量低于本底 +8 dB 且持续 ≥0.25 秒。断在句号上的算合理，断在句子中间的是要练的；
  分类需要人工给出原文真正的句末时刻（见报告生成时传给 `timeline_svg` 的 bounds）。
- **断句语调** 用 **NAEP 2002 Special Study of Oral Reading** 的朗读流利度 4 级量表，
  按「平均几个词一组」定级。

## 注意

- **录音不进仓库**，页面上只放分析结果。
- 发音一项是从转写结果推断的（识别成什么词反推读成了什么音），不如亲耳听准，写结论时留余地。
- **别提议把 Wonders 换成听读 / 跟读**：它在打卡单上是 `[读]`，学校要求朗读，这一条不可动。
  文本偏难（<95%）时给的建议要落在「偏难文本怎么朗读」上——先扫生词、分段、同一段读两遍
  （repeated reading），而不是降难度或改成听。

## 四种报告

**课文朗读**（p65 / p66 / p67 / wonders）——准确率、WCPM、停顿地图、三把尺子。

**单词表**（words）——**不算 WCPM**：单词表考的是「看见词多久能反应过来」，
每分钟读多少词没有意义。换两个指标：

- **读对率**（分子分母都按实际录到的词算）
- **开口前的犹豫时间** = 上一个词读完到下一个词开口之间的静音，从能量包络量，与识别结果无关

⚠️ **孤立单词的识别远不如句子准**——句子里机器能靠上下文纠错，单个词没有上下文。
单词表报告只给「疑似读岔」并标把握程度（高/中/低），不下定论，最后一步交给家长的耳朵。

**语法练习**（grammar-*）——**不逐题打分，按错因归类**。一页错 15 处，如果 7 处是同一个毛病，
那就是一个规则的缺口，不是 15 个零散的错。分数只统计能逐空核准的大题；
答案叠在题号上、照片判不准的，明说不计入，别硬凑。

**字迹**（handwriting-*）——用美国写字教材通行的可读性五要素
（Zaner-Bloser：shape / size / spacing / slant / smoothness），四线格再加一条**贴线**。
只评字迹，不评拼写。评的是照片，纸面实物可能更清楚，措辞上留余地。

对齐时注意：识别给的词边界在单词表里不可靠（会把两个词并进一段、或把一个长词拆成三段）。
正确做法是先从停顿切出**发声段**，再人工把发声段对到课本词条上（见 per-word.json 的生成过程）。

## 当日小结（daily/）

把一天的几份报告合成一页：合计词数 / 时长 / 整体准确率、报告一览表、
**跨报告才看得出来的规律**（例：词尾 -s 今天丢了 6 次、自我纠正 5 次、hunting 两页读岔两次），
再给明天三件事。表格和合计由 `build_daily.py` 从各报告的 meta 自动算，
判断和建议写在 `daily/<日期>.json` 里——那部分机器给不了。

### 和「每日打卡」的关系

打卡单里的 `[点读]` 和 `[读]` 两项，正好对应这里的报告。
`build_daily.py` 会在**生成时**去读 `../homework/specs/<yyyymmdd>.txt`，
把那两项的原文抄进小结页，让人看见「作业是什么 → 做得怎么样」。

⚠️ **这只是生成时的一次读取**：产出的 HTML 不引用 homework/ 的任何文件，
两个栏目在站点上依旧互不引用（见根 CLAUDE.md）。拿不到 spec 就跳过这一块，不报错。
打卡单是给人打印在纸上的，也不适合往上面加链接。
