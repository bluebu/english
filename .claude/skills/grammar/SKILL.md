---
name: grammar
description: 儿童英语语法小手册(grammar/ 目录)的关卡工作台。子命令:new = 新增或修改某一关(关卡布局、组件、颜色与朗读机制、注意事项、发布步骤);review = 对照美国权威体系(古典教材 + CCSS)审稿某一关。当要做/改/审第 N 关时使用,如 /grammar new 5、/grammar review 5。
argument-hint: new <N> | review <N>
---

# /grammar — 语法小手册工作台

手册的全部页面与资源都隔离在 `grammar/` 目录里(根目录只有跳转页与其他栏目)。
无论哪个子命令,都先读根 `CLAUDE.md`(体系、教学法、发布准则)。

按第一个参数分发:

- **`new <N>`** — 新增或修改第 N 关(`grammar/lesson-NN.html`)
  → 读本目录 `new-lesson.md`,按其中的布局、组件、颜色/朗读机制与步骤执行。
- **`review <N>`** — 审稿第 N 关(语法准确性、术语、教学序列、例句与题目)
  → 读本目录 `review-lesson.md`,按其中的对标信源、审查维度与输出格式执行。

没给子命令或意图不明时,先问用户是要"做/改一关"还是"审稿一关"。
