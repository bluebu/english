---
name: ket
description: KET 单词表工作流：① 从单词卡照片（HEIC/JPG/PNG）提取单词生成 CSV 到 words/ 目录；② 从 words/*.csv 生成 A4 默写卷（看中文写英文，四线三格）HTML 预览和打印 PDF。当用户提供单词表照片要求整理成 CSV，或要求生成默写卷/打印 PDF 时使用。
---

# ket：单词表照片 → CSV → A4 默写卷

KET 词汇默写栏目（仓库 `ket/` 目录）的两段式工作流。**脚本用相对路径，一律在 `ket/` 目录下运行。**目录约定（均在 `ket/` 内）：

- `words/<NN>_<主题>.csv` — 单词数据（NN 是两位主题编号，主题名用英文小写下划线，如 `01_appliances.csv`）
- `worksheets/<NN>_<主题>.html` / `.pdf` — 生成的默写卷
- `generate_worksheet.py` — 生成脚本
- `index.html` — 栏目目录页，列出合集 + 各主题的预览/PDF 链接和词数；**新增主题或词数变动后要同步更新**

主题编号由用户指定（对应词汇书/海报的板块序号，不是字母序或录入序）。已分配 01–12（见 `words/` 目录）。新主题若用户没给编号要先问。

## 工作流 1：图片 → CSV

用户给出若干张单词卡照片（通常是 HEIC），要求按文件编号顺序提取某个板块的单词。

1. **转格式**：HEIC 无法直接 Read，先用 sips 批量转 PNG 到 scratchpad：
   `sips -s format png IMG_xxxx.heic --out <scratchpad>/IMG_xxxx.png`
2. **按文件编号从小到大**逐张 Read 提取。每行格式通常是：`word /音标/ 词性.中文释义`。
3. **处理照片重叠与边界**（关键，容易漏词/重词）：
   - 相邻照片通常有重叠区域，合并时去重。
   - 照片顶部/底部被裁掉一半的行，必须放大确认是重叠词还是漏词：用 PIL 裁剪
     `python3 -c "from PIL import Image; im=Image.open(...); im.crop((0,0,im.width,300)).resize(...).save(...)"`
     再 Read 查看。⚠️ 不要用 `sips --cropOffset`，实测偏移不生效（永远裁中心）。
   - 可用词表的字母序辅助判断连续性，但以图片实证为准。
4. **忠实转录**：词性、释义照卡片原文写，即使看起来像印刷错误也保留（用户明确要求过，如 boil 卡片印 n.）；只在汇报时口头提醒。全角标点（；，（））保留，正好避免 CSV 逗号转义。
5. **CSV 格式**：表头 `no,word,phonetic,pos,meaning`。`no` 是从 1 开始的编号（每个主题独立编号，默写卷题号直接用它）；词组（如 ice cream、wash up）卡片上无音标词性则留空。
6. **编码**：Write 写完后必须加 UTF-8 BOM（Excel/WPS 打开中文才不乱码）：
   `printf '\xEF\xBB\xBF' | cat - x.csv > .tmp.csv && mv .tmp.csv x.csv`
7. 汇报总词数、板块起止词，以及边界行的核对结论。

## 工作流 2：CSV → HTML/PDF

```bash
python3 generate_worksheet.py words/<NN>_<主题>.csv          # 只生成 HTML
python3 generate_worksheet.py words/<NN>_<主题>.csv --pdf    # HTML + PDF 一起出
python3 generate_worksheet.py --merge words_1 --pdf                  # 合集（默写版）
python3 generate_worksheet.py --merge-answers words_1_answers --pdf  # 合集（答案对照版）
```

合集模式：words/ 全部主题连排，章节之间不分页；章节标题占一整行（2 词位），起点不在行首时补空位，且不让标题落在页面最后一行；各章题号沿用各自 CSV 的编号。默写版每页 30 词位（15 行 × 2 栏），样式与分集完全一致；答案对照版紧凑无线格（每页 70 词位），每行"序号 中文 词性 → 英文（加粗靠右）音标"，页眉无姓名/日期/得分栏。两个合集独立共存，CSV 有更新后两个都要重新生成。

- 输出到 `worksheets/`。格式未定/有改动时先只出 HTML，`open` 给用户在浏览器预览确认，再加 `--pdf`。
- 自查排版用无头 Chrome 截图或导 PDF 后 Read 查看，不要凭 HTML 源码想象。

### 已定稿的格式决策（改动需用户同意，实现都在 generate_worksheet.py）

- A4 竖版，两栏，每页 30 词；页眉：标题 + 姓名/日期/得分；页脚：总词数 + 页码。
- 题型是"看中文写英文"：序号 + 中文释义 + 灰色小字词性提示 + 四线三格书写区。
- 四线三格：绿色四线 + 红色第三线（基线），每格 14px、总高约 11mm，符合小学英语本习惯（用户孩子四年级，行距宁松勿密）。
- `print-color-adjust: exact` 必须保留，否则 Cmd+P 和导出的 PDF 里看不到 CSS 背景画的四线格。
- 页眉标题格式 "NN English 中文 默写"（如 "01 Appliances 家电 默写"）。新主题要在脚本 main() 的 titles 字典里加一条（key 是去掉编号前缀的主题名）。

## 常见后续需求（用户提过但未定）

打乱顺序防背字母序、简化过长释义（如 cut 的"（从动物躯体上）割下的一块肉"）。做之前先问。（答案对照已做成合集版 --merge-answers。）
