# 点读评价（reading/）

把孩子的一段朗读录音，变成一张能和下次对比的成绩单。

```
reading/
  index.html                       目录页（报告列表写在 LIST:BEGIN/END 之间）
  reports/<书>-<课>-p<页>.html      每次一份报告
  data/<同名>.json                  声学分析结果（停顿、语速）
  data/<同名>.words.tsv             逐词时间戳（起 / 止 / 词）
  tools/words.swift                 转写 + 逐词时间戳
  tools/analyze.py                  停顿与语速分析
```

## 做一份报告

```bash
# 1) 转写 + 逐词时间戳（macOS 26 本机 Speech 框架，离线，首次会下模型）
swiftc -O -parse-as-library tools/words.swift -o /tmp/words
/tmp/words 录音.m4a > data/超8-lesson3-p65.words.tsv

# 2) 停顿 / 语速
python3 tools/analyze.py 录音.m4a > data/超8-lesson3-p65.json

# 3) 拿课本原文逐字比对，套 reports/ 里现成的一份改
```

## 口径

- **准确率** = 读对词数 / 原文词数。替换、漏读、读错音计错；插入词和回读只算不流利，不计错
  （Fountas & Pinnell：98% 以上能独立读，95–97% 属于要带一带的教学级）。
- **WCPM** = 读对的词数 ÷ 总时长 × 60。对照 Hasbrouck & Tindal 母语儿童常模，只当参照系。
- **停顿** = 能量低于本底 +8 dB 且持续 ≥0.25 秒。断在句号上的算合理，断在句子中间的是要练的。
- **断句语调** 参考 NAEP 朗读流利度量表（4 级）。

## 注意

- **录音不进仓库**，页面上只放分析结果。
- 发音一项是从转写结果推断的（识别成什么词反推读成了什么音），不如亲耳听准，写结论时留余地。
