# 我的英语语法小手册

英语语法入门手册。用**颜色 + 图画 + 生活场景**把英语讲清楚，手机 / iPad 友好。

## 设计思路

- **体系**：参照美国本土主流语法体系（CCSS 语言标准 + Wonders / HMH 等主流教材的编排顺序），骨架为
  `句子 → 名词 → 动词/时态 → 代词 → 形容词 → 副词 → 连词/介词 → 比较级 → 句子类型与标点`，共 11 关。
- **教学法**：具体先行、例句先行、术语随后、配造句练习；并把标点 / 大小写与语法并行教。
- **核心信号——用颜色教结构**：
  - 🔵 蓝 = 谁（主语）
  - 🟠 珊瑚 = 做什么（动词）
  - 🟢 绿 = 什么（宾语 / 怎么样）
  - 🟣 紫 = 是（be 动词）
  - 🟡 黄 = 规则（标点 / 大小写）

## 文件结构

```
index.html                站点入口：暂时跳转到 grammar/（以后放栏目导航）
404.html                  旧链接兜底：/lesson-NN.html → /grammar/lesson-NN.html
grammar/                  栏目一：语法小手册（自包含，和其他栏目隔离）
  index.html              封面 + 11 关目录
  lesson-01.html          第 1 关：一句完整的话 = 谁 + 做什么
  assets/style.css        共享样式（设计系统）
  assets/app.js           入场动画 + 点击朗读
.nojekyll                 让 GitHub Pages 原样服务静态文件
```

新增章节：复制 `grammar/lesson-01.html`，改文件名（如 `lesson-02.html`）和内容，再到 `grammar/index.html` 把对应目录项从 `soon` 改成 `ready` 并加上链接即可。新栏目另建独立目录，不和 `grammar/` 互相引用。

## 本地启动预览

```bash
make up            # 启动本地预览（默认端口 8000）
make up PORT=9000  # 指定端口
make open          # 用浏览器打开
make stop          # 停止预览
make help          # 查看全部命令
```

`make up` 会同时打印**电脑**和**手机 / iPad（同一 WiFi）**的访问地址；装了 `qrencode`（`brew install qrencode`）还会显示手机扫码二维码。按 `Ctrl+C` 退出。

## 部署到 GitHub Pages

1. 在 GitHub 新建一个仓库（例如 `english-grammar`）。
2. 把本目录推上去：
   ```bash
   git init
   git add .
   git commit -m "init: 英语语法小手册 第 1 关"
   git branch -M main
   git remote add origin https://github.com/<你的用户名>/english-grammar.git
   git push -u origin main
   ```
3. 仓库 **Settings → Pages → Build and deployment**：Source 选 `Deploy from a branch`，Branch 选 `main` / `/ (root)`，保存。
4. 等一两分钟，访问 `https://<你的用户名>.github.io/english-grammar/`。

> 全部用相对路径，无论部署在根域名还是 `/仓库名/` 子路径下都能正常打开。
