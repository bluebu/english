---
name: review-lesson
description: 对照美国语言标准(CCSS)与古典/主流教材,审查某一关的语法准确性、术语、教学序列、例句与题目设计,指出不合理与可改进处。修改或新增关卡后、发布前用。
---

# 关卡内容 · 权威对标 Review

给一关(或一段新增内容)做"语言学 + 教学法"审稿:**语法对不对、术语合不合年级、序列顺不顺、例句与题目稳不稳**——逐条对照权威给 ✓ / ⚠️ / ✗ + 依据 + 建议。

先读根 `CLAUDE.md`(体系准则)与目标 `lesson-NN.html`(及本次 `git diff`,聚焦新增部分)。

## 对标信源(主 → 辅)
- **体系基准(古典 / 头部私立,CLAUDE.md 锁定)**:First Language Lessons、Rod & Staff、Michael Clay Thompson(Grammar/Sentence Island)、Shurley English、Reed-Kellogg 句子图解、Warriner's。
- **对照参考(美国公立主流,用来看 grade-level 适配)**:CCSS ELA **Language** strand(L.K–5);Wonders(McGraw-Hill)、HMH Into Reading / Journeys 的 Grammar 序列。
- 指出与 CCSS / 公立教材的差异时**先判定**:是"刻意的 classical 超前取向(合理)"还是"真问题(要改)"。**体系以古典为准,CCSS 是对照、不是判决。**

## 审查维度
1. **语法准确性**:定义 / 术语是否正确、有无"半真半假";complete vs simple subject/predicate、linking verb + subject complement 等说对没有。
2. **术语 × 年级**:用 subject/predicate 还是 naming/telling part?对标古典(早教)还是公立(晚教)?中文借词(如"谓语"= predicate)是否与中文语法学冲突、要不要加英文小注。
3. **教学序列**:概念出现顺序、前置依赖;有没有用到"尚未教"的概念(对照 11 关大纲与 CCSS 进阶)。
4. **例句质量**:典型性、真命题、最小充分、是否混入未教点(如只讲主谓却用 be 句)。
5. **题目设计(新增测试的重点)**:区分度、干扰项有没有考到要害、是否"靠颜色 / 位置泄题"、是否覆盖该关核心概念(别只考边角)。
6. **CCSS 对齐**:能对上的标注编号(如 L.1.1.j / L.1.2.b),证明内容落在标准内。

## 输出格式
- **结论先行**(1–2 句:整体稳不稳 + 有几个真问题)。
- **✓ 站得住 / ⚠️ 可改进 / ✗ 不合理** 三档,每条:`判断 — 依据(引标准/教材) — 建议`。
- **Top 改进**(按优先级 2–4 条,可直接动手)。
- 只给分析,**不替用户拍板**——改不改由用户定。
