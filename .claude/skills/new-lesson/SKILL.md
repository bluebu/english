---
name: new-lesson
description: 创建或修改"儿童英语语法小手册"的某一关(关卡)。当要新增第 N 关、或调整某一关的布局/内容时使用。内含关卡布局、组件、颜色与朗读机制、注意事项和发布步骤。
---

# 做一关 / 改一关

先读根目录 `CLAUDE.md`(体系、教学法、发布准则)。本 skill 给出**关卡布局**、组件用法、机制、**注意事项**与步骤。

## 一、关卡布局(每关固定结构,按此顺序)
1. **封面公式** `.hero`:大标题 = 本关核心公式(如"谁 + 谓语");下面用句子积木拼出公式 + 一句副标题。
2. **引入** `.card`:一两句话说清这关讲什么,配一个中文类比。
3. **彩色步骤卡** `.card.who/.do/...`:**一个概念一张卡**,`.step` 编号 + `.what-line` 一句定义 + 句子积木例句。
4. **★ 规则角** `.card.rule`:大小写 / 标点 / 拼写,用 `.judge` 做对错对照。
5. **🍳 见物能聊** `.card`:一个生活场景(早餐桌等)几句真实句子,`.scene .node` + `.mini .b` 拆成色块。
6. **🎯 练习** `.quiz`:3–5 题(找成分 / 排序 / 判断 / 改错 / 造句),每题配 `details.answer`("看答案")。
7. **🏆 通关锦囊** `.card.rule`:童趣总结,3 条要点 + 一句鼓励金句。

## 二、组件速查(都在 `assets/style.css`)
- 卡片:`.card` + 角色色 `.who/.do/.what/.be/.rule`(决定顶部胶带色与主色)。
- 句子积木:`.sentence` 容器 → `.brick.who/.do/.what/.be`(内含 `.role` 小标签 + `.word` 词);`.glue` 放 `+`/`=`;下方 `.trans` 译文。
- 对错对照 `.judge`(`.ok`/`.no`);提示框 `.tip`(可加 `.who`/`.do` 变色);
  场景 `.scene .node.who/.do/.be` + `.mini .b.who/...`;练习 `.quiz`/`.qitem`/`details.answer`。

## 三、颜色与朗读机制(必守)
**两层(MCT 式),两个通道:**
- 🎨 **颜色 = 成分**(角色):`who=主语(蓝) do=谓语(橙) what=宾语(绿) be=系动词(紫)` …跨关一致,**随概念渐进**(只用已教过的颜色)。
- 🔊 **点击朗读 = 本关所讲的那一层**:
  - **句子结构关**(如第1关)念**成分** → 用 class 默认(who→主语 do→谓语 what→宾语 be→系动词),或 `data-say` 覆盖(表语/句子)。
  - **词性关**(名词/动词/形容词…)念**词性** → 给色块加 `data-say="名词"` 等;**颜色仍按 class(成分)**。
    例(名词关):主语位 `<span class="brick who" data-say="名词">`(蓝、念"名词");宾语位 `<span class="brick what" data-say="名词">`(绿、念"名词")。
- `app.js` 自动接管点击朗读,加内容只需写对 class + `data-say`,不用改 JS。
- **词性关色块写法**:核心句子位用对应颜色 class(主语 who蓝/谓语 do橙/宾语 what绿/系动词 be紫/表语 comp玫红);块的 `.role` 小标签写**词性**(名词/动词…)、`data-say` 也写词性。独立列举的词(没进句子)用中性 `.brick`(无 class)+ `data-say=词性`。
- **一个词念词性还是成分?** 它的**词性一旦在前面关教过**就念词性,没教过就念成分(例:动词在 L1–3 未教 → 念"谓语";L4 起 → 念"动词")。
- **独立词汇展示块(封面 chips、四家族等,没进句子)**:用 `class="brick vocab tintN"`(N=1~6)上**柔和多彩贴纸色**,别用灰中性(参照"what家族"那种彩色卡)。vocab 是装饰色、不表成分;颜色靠 tint 循环或按家族分组。**句子里的非核心词(形容词/副词/介词/连词当修饰/连接时)保持中性**,以保证"句子里有颜色 = 核心成分"的信号干净。
- 口诀:**看颜色知角色,听声音知词类。**

## 四、注意事项(踩过的坑)
1. **"谓语"是大谓语**(主语之外的整块 = complete predicate),不是只指动词。`eat an apple` 整块都是谓语;`eat`=动词、`an apple`=宾语属于"谓语内部",留到后面关再拆——**讲到时点一句即可,别展开成长段**。
2. **be 动词句**:am/is/are 念"**系动词**"(不是谓语),后面的词念"**表语**"(不是宾语)。对应主系表 / 美式 linking verb + subject complement。
3. **低阅读压力**:定义一句话讲完,细节放进 `.tip`;不要密集长段,孩子读不动。
4. **文案不标年级**(title / meta / 页眉 / 页脚都别写"三年级")。
5. **朗读读中文术语,不读英文单词**——这是语法手册,不是单词书。
6. iOS Safari 首次点击可能要再点一次才出声;中文音色用系统自带(PingFang 设备都有)。
7. 全部用**相对路径**(`./assets/…`、`./lesson-NN.html`),保证根域名与子路径都能打开。

## 五、步骤
1. 复制 `lesson-01.html` → `lesson-NN.html`;改 `<title>`、`meta`、页眉 crumb、页脚、`.pager`(上一关 / 下一关)。
2. 按"一、关卡布局"填内容;按"三"给色块加 `data-say`。
3. `index.html`:把对应目录项从 `soon` 改 `ready`,加 `href="./lesson-NN.html"` 和英文副标题;给编号块上对应颜色 class(`c-who`/`c-do`/…)。
4. **自检**:用 playwright(`playwright-core` + 系统缓存的 chromium)在手机(390/412)和 iPad(834)视口截图,检查排版、色块、朗读高亮;并核对每个色块 `aria-label` = 期望术语。(脚本可临时生成,参考会话里 `shot.js` / `verify3.js` 的写法。)
5. **发布**:`make up` 本地预览 → `git add -A && git commit && git push origin master`;commit message 末尾加
   `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`。
