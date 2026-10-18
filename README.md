# CHAINEDGHOST MV

[![Code: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![three.js](https://img.shields.io/badge/three.js-0.186-black.svg)](https://threejs.org/)

**A lyric-synced music video, rendered in real time with three.js.**
A browser-based music video where every frame is driven by the audio, and lyrics are timed word by word. Because each frame depends only on the time `t`, the same project can also be exported frame by frame to a 1080p60 MP4.

基于 three.js 的歌词同步音乐视频（MV）实时网页。画面由音频特征逐帧驱动，歌词按逐字打点显示。画面只由时间 `t` 决定，因此既能在浏览器里实时播放，也能逐帧导出 1080p60 MP4，结果可复现。

---

## 目录 / Contents

- [段落与场景](#段落与场景)
- [快速开始](#快速开始)
- [导出 MP4](#导出-mp4)
- [工作原理](#工作原理)
- [目录结构](#目录结构)
- [技术栈与致谢](#技术栈与致谢)
- [许可证与音乐授权](#许可证与音乐授权)
- [联系方式](#联系方式)

---

## 段落与场景

整首歌约 3 分 59 秒（导出为 239.7 秒，含片尾）。段落时间由 `web/data/timing.json` 定义，播放页下方的按钮可以直接跳转到对应段落。

| 段落 | 起始时间 | 段落 | 起始时间 |
|---|---|---|---|
| Intro | 0:00 | Chorus 2 | 1:39 |
| Verse 1 | 0:19.8 | オオオ 2 | 2:08 |
| Pre-Chorus 1 | 0:31.0 | Break 2 | 2:13 |
| Chorus 1 | 0:40.8 | Bridge | 2:18 |
| オオオ 1 | 1:00.1 | Chorus 3 | 2:27.8 |
| Break 1 | 1:04.6 | Outro | 2:37.2 |
| CPU | 1:14.5 | DNA | 2:56.5 |
| Verse 2 | 1:19.1 | CPU 2 | 3:06.2 |
| Pre-Chorus 2 | 1:29.5 | 魂 A | 3:21 |
| | | 魂 B | 3:30 |
| | | 魂 C | 3:40.1 |
| | | End | 3:54 |

---

## 快速开始

### 环境要求

- **Windows 10/11**：主要测试平台，`.bat` 脚本只在 Windows 下可直接双击。其他系统可以直接运行 `python tools/...` 脚本。
- **Node.js**：用于安装 three.js（`npm install`）。
- **Python 3.10+**：本地服务、打点与导出脚本。
- **Chrome 或 Edge**：需要 WebGL2。
- **ffmpeg**（仅导出 MP4 时需要）：放到 `_bin/ffmpeg.exe`，或加入系统 PATH。
- **NVIDIA 显卡**（可选）：导出时使用 NVENC 硬件编码；没有时自动改用 libx264。

### 安装与运行

```bash
git clone https://github.com/kumastormxiong/CHAINEDGHOST-MV.git
cd CHAINEDGHOST-MV/web
npm install          # 安装 three.js 到 web/node_modules
cd ..
play_MV.bat          # 或：python tools/serve.py
```

服务默认使用 8800 端口（被占用时会自动换用其他端口，以终端显示为准），启动时会自动打开浏览器。进入 <http://localhost:8800/index.html> 后点击"点击开始"即可播放。

歌曲文件已包含在仓库中（`web/audio/GhostChain.wav`）。

### 逐字打点

打开 <http://localhost:8800/timing.html>：

- 空格：播放 / 暂停
- 回车：在当前位置打点
- 速度：30% – 100%

打点结果写入 `web/data/char_times.json`。

---

## 导出 MP4

导出的是 1920×1080、60 fps、H.264 + AAC 的 MP4。

```bash
pip install -U playwright
python -m playwright install chromium
export_MV.bat       # 或：python tools/export_mp4.py
```

输出文件：`output/CHAINEDGHOST_1080p60.mp4`。

常用参数：

| 参数 | 说明 |
|---|---|
| `--start 0 --end 600` | 只导出一段（单位：帧，60 帧 = 1 秒），用于试跑 |
| `--out 路径` | 指定输出文件 |
| `--workers 2` | 并行渲染的 Chrome 进程数，显存或内存紧张时调小 |
| `--encoder libx264` | 强制使用 CPU 编码 |
| `--ffmpeg 路径` | 指定 ffmpeg 可执行文件 |
| `--timeout 600` | 页面加载超时时间（秒） |

如果笔记本是双显卡，请在 Windows 图形设置里把 Chrome 设为"高性能"，否则脚本会使用核显渲染，速度很慢。

静态截图用 `python tools/shot.py --times 6,28,52`。

---

## 工作原理

- **时间驱动**：`web/src/timeline.js` 根据 `web/data/timing.json` 判断当前段落、段内进度 `lt` 以及鼓点、命中等信号。
- **场景**：`web/src/worlds/` 下每个段落一个 three.js 场景，由 `web/src/worlds/index.js` 统一调度。
- **音频特征**：`web/data/features.json`、`web/data/spectrum.json`，由 `tools/analyze_audio.py`、`tools/analyze_spectrum.py` 从音频分析得到，画面里的节拍与强度都来自这里。
- **歌词与时间表**：`tools/build_lyrics.py` 由本地歌词卡（`timing/original_lyrics_card.txt`，未上传）生成 `web/data/lyrics.json`；`tools/build_timing.py` 由 `timing/lyrics_timed.lrc` 生成段落时间表 `web/data/timing.json`；逐字时间 `web/data/char_times.json` 由打点工具保存（同时备份到 `timing/char_times.json`）。
- **后期效果**：`web/src/post.js` 处理泛光、色差、扫描线、故障等效果。
- **确定性导出**：导出时每帧调用页面的 `window.__shot(t)`，`t = 帧号 / 60`，不依赖实时播放，因此结果可以逐帧复现。

---

## 目录结构

```
web/                  网页主程序
  index.html          播放页
  timing.html         逐字打点工具
  src/                渲染与场景代码（worlds/ 为各段落场景）
  data/               段落时间轴、歌词、音频特征
  assets/             贴图、眼睛素材、字体
  audio/              歌曲 GhostChain.wav
timing/               歌词 LRC 与打点原始材料
tools/                本地服务、分析、渲染与导出脚本
docs/                 导出任务说明（给执行导出的 AI 代理使用）
play_MV.bat           双击启动本地服务
export_MV.bat         双击导出 MP4
```

---

## 技术栈与致谢

- [three.js](https://threejs.org/) 0.186（MIT）：通过 import map 从 `web/node_modules` 加载
- [Playwright](https://playwright.dev/)：逐帧渲染与截图
- [ffmpeg](https://ffmpeg.org/)：视频与音频编码
- 字体：Michroma、Exo 2、Righteous、Press Start 2P、Dela Gothic One、Noto Sans SC，来自 [Google Fonts](https://fonts.google.com/)，作者理解其授权为 SIL Open Font License。

> **字体授权提示**：作者未能逐一核实所有字体的商用条款。`web/assets/fonts/SciKanji-HYZhongHei.ttf` 的授权尚未确认。如需商用或再分发，请先自行核实字体授权，或替换为可商用的字体。

---

## 许可证与音乐授权

本仓库分为两部分，授权方式不同。

**1. 代码与工程文件**（`web/src/`、`tools/`、`docs/` 以及画面素材等）

以 [MIT License](LICENSE) 发布，可以自由使用、修改、再分发，但需保留版权与许可证声明。

**2. 音乐与歌词**（`web/audio/GhostChain.wav`、歌词文本、`timing/` 与 `web/data/` 中的逐字与段落时间表等）

版权归作者所有，**不适用 MIT License**，保留所有权利。

欢迎使用这首歌，但在任何用途（包括翻唱、二次创作、商业或非商业发布）之前，请先与作者联系取得授权：

**FFVoid@Dreamy.Voyage**

---

## 联系方式

- 邮箱：FFVoid@Dreamy.Voyage
- 音乐授权、合作与问题反馈均可通过邮件联系。
