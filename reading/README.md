# 点读评价（reading/）

把孩子的一段朗读录音，变成一张能和下次对比的成绩单。

```
reading/
  index.html                       目录页（列表由 build_index.py 刷新，别手改）
  reports/<书>-<课>-p<页>.html      每次一份报告
  data/<同名>.json                  声学分析结果（停顿、语速）
  data/<同名>.words.tsv             逐词时间戳（起 / 止 / 词）
  data/<同名>.per-word.json         单词表专用：逐词的犹豫时间与对齐结果
  tools/words.swift                 转写 + 逐词时间戳
  tools/analyze.py                  停顿与语速分析
  tools/figures.py                  停顿地图 + 「三把尺子上的位置」三张图
  tools/build_index.py              刷新目录页列表：按日期倒序分组
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
```

新报告的 `<head>` 里必须带这五行，`build_index.py` 只认这个：

```html
<meta name="report-date"  content="2026-08-25" />   <!-- 分组用，倒序排 -->
<meta name="report-order" content="66" />           <!-- 同一天内的顺序：小的在前 -->
<meta name="report-score" content="61" />
<meta name="report-title" content="超8 · Lesson 3 · 第 66 页" />
<meta name="report-sub"   content="Prince Darling · 110 words" />
```

少任何一行，这份报告会被整个跳过（宁可不进目录，也不进半拉子的）。

一天里读了不止一本书时，`report-order` 用「书序 × 100 + 页码」把同一本书排在一起：
超8 = 61–67，Wonders = 208–211。

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

## 两种报告

**课文段落**（p65 / p66 / p67）——准确率、WCPM、停顿地图、三把尺子。

**单词表**（words）——**不算 WCPM**：单词表考的是「看见词多久能反应过来」，
每分钟读多少词没有意义。换两个指标：

- **读对率**（分子分母都按实际录到的词算）
- **开口前的犹豫时间** = 上一个词读完到下一个词开口之间的静音，从能量包络量，与识别结果无关

⚠️ **孤立单词的识别远不如句子准**——句子里机器能靠上下文纠错，单个词没有上下文。
单词表报告只给「疑似读岔」并标把握程度（高/中/低），不下定论，最后一步交给家长的耳朵。

对齐时注意：识别给的词边界在单词表里不可靠（会把两个词并进一段、或把一个长词拆成三段）。
正确做法是先从停顿切出**发声段**，再人工把发声段对到课本词条上（见 per-word.json 的生成过程）。
