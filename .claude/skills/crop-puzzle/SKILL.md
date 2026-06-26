---
name: crop-puzzle
description: 把一张角色图做成"福袋拼图"用的标准图(米底、正方、800² JPG、~40K)。新增/替换某关拼图形象时用。角色裁切(框角色、去水印)建议先自己用 Preview/PS 做,本 skill 负责标准化后处理。
---

# 拼图图标准化(福袋拼图素材)

把任意角色图 → 关卡拼图图 `assets/puzzles/lesson-NN.jpg`(普通)/ `lesson-NN-secret.jpg`(隐藏款)。
**目标**:米底(`#F4ECDD`)、正方、**角色填满画面**、800×800、~35–60K JPG、**无水印/杂物**。底色与 L1 一致、和问号格无缝。

## 分工
- **角色裁切(框角色、去水印)**:白底 + 水印的图自动检测不可靠 —— **自己用 Preview / PS / 截图先裁**最快最准。
- **本 skill(PIL 后处理)**:统一底色 + 正方 + 800² + 压缩。

## 普通款 vs 隐藏款(两张图,别搞混)
- **普通款** → `assets/puzzles/lesson-NN.jpg`:本关主形象(L1 蛋小黄、L2 蛋小粉),集齐普通拼图见到的就是它。
- **隐藏款** → `assets/puzzles/lesson-NN-secret.jpg`:同角色的华丽 / 限定版(天使翅膀、金色等),**15 秒挑战通关才解锁**。
- 两张都走下面**同一套**标准化(米底 / 正方 / 800² JPG),**只改输出文件名**;`<body>` 上 `data-puzzle`(普通)与 `data-puzzle-secret`(隐藏)分别指向两款。
- 隐藏款**用户没给时**:先拿普通款调金做占位,拿到真图再替换——别让 `-secret.jpg` 缺失(挑战通关时会 404):
  ```python
  from PIL import Image, ImageEnhance, ImageChops
  im = ImageEnhance.Color(Image.open('assets/puzzles/lesson-NN.jpg').convert('RGB')).enhance(1.55)
  im = ImageChops.screen(im, Image.new('RGB', im.size, (255,196,60)).point(lambda p: int(p*0.2)))
  im.save('assets/puzzles/lesson-NN-secret.jpg', 'JPEG', quality=90, optimize=True, progressive=True)
  ```

## 关键技巧
- **米底常量** `(244, 236, 221)` = `#F4ECDD`。
- **透明 PNG**:`im.getbbox()` 裁掉透明边,再 pad 米底(L1 蛋小黄即此法)。
- **白底 / 浅色底 → 米底**:从四角 + 四边中点 `ImageDraw.floodfill(im, seed, 米底, thresh≈38)` —— 连通的白背景、浅阴影、浅水印都被填成米底,**被角色包住的白手套 / 白鞋会保留**(floodfill 进不去)。比"阈值 difference"稳:后者会被白底渐变 / JPEG 噪点误判成整图。
- **实色水印 / 杂物**:floodfill 吃不掉(有硬边界)→ 先自己裁掉,或 `ImageDraw.Draw(im).rectangle([x0,y0,x1,y1], fill=米底)` 把那块抹掉。
- **填满**:角色要占满画面,正方画布 = `max(角色宽,高) × ~1.08`(留一点呼吸边),角色居中;否则切块发空。

## 脚本模板(改 SRC / 参数即可)
```python
from PIL import Image, ImageDraw
SRC = '/path/to/角色图.png'
OUT = 'assets/puzzles/lesson-NN.jpg'
BG  = (244, 236, 221)                        # 米底 #F4ECDD
im = Image.open(SRC).convert('RGB'); W, H = im.size

# A) 白底 → 米底(透明 PNG 跳过本段,见下方透明版)
for s in [(2,2),(W-2,2),(2,H-2),(W-2,H-2),(W//2,2),(W//2,H-2),(2,H//2),(W-2,H//2)]:
    ImageDraw.floodfill(im, s, BG, thresh=38)
# 仍有实色水印/杂物时:ImageDraw.Draw(im).rectangle([x0,y0,x1,y1], fill=BG)

# B) 居中裁正方(角色已居中填满时);角色偏置 → 改用 im = im.crop((x0,y0,x1,y1)) 人工框先框角色
sq = min(W, H)
im = im.crop(((W-sq)//2, (H-sq)//2, (W-sq)//2+sq, (H-sq)//2+sq))

im.resize((800, 800), Image.LANCZOS).save(OUT, 'JPEG', quality=90, optimize=True, progressive=True)
import os; print(OUT, os.path.getsize(OUT)//1024, 'KB')
```
**透明 PNG 版**(替换 A/B 两段):
```python
im = Image.open(SRC).convert('RGBA'); im = im.crop(im.getbbox())
w, h = im.size; side = int(max(w, h) * 1.08)
c = Image.new('RGBA', (side, side), BG + (255,)); c.paste(im, ((side-w)//2, (side-h)//2), im)
c.convert('RGB').resize((800, 800), Image.LANCZOS).save(OUT, 'JPEG', quality=90, optimize=True, progressive=True)
```

## 必做:Read 确认
生成后用 Read 看输出:角色**居中、填满、无水印、米底无白方块边**。不对就调 floodfill `thresh`、水印矩形坐标、或换人工 `crop` 框,重跑。两张图就位后回 `/new-lesson` 第六节接进关卡。
