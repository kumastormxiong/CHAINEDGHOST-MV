# GhostChain MV 导出任务（给执行导出的 AI 使用）

## 任务目标

把 CHAINEDGHOST MV 逐帧导出为一个 MP4 文件：

- 分辨率 1920×1080
- 帧率严格 60 fps，不掉帧、不重复
- 视频 H.264，音频 AAC（音频来自 `web\audio\GhostChain.wav`）
- 时长约 239.7 秒，共 14384 帧

## 项目位置

- 项目根目录：`D:\AI\GhostChain MV\GhostChain_MV`
- 导出脚本：`tools\export_mp4.py`（已写好，直接运行即可，不要重写它）
- 双击入口：`export_MV.bat`（等同于运行脚本，可以带参数，例如 `export_MV.bat --start 0 --end 600`）
- 输出文件：`output\CHAINEDGHOST_1080p60.mp4`

## 工作原理（了解即可）

- 画面只由时间 t 决定。脚本对每一帧调用页面的 `window.__shot(t)`，t = 帧号 ÷ 60，不是录屏，也不依赖实时播放。
- 默认开 4 个独立的 Chrome 进程并行渲染不同的帧，并强制使用独立显卡。渲染结果按帧号排序后送进 ffmpeg，帧序和时长都是精确的。
- 编码优先用 NVIDIA NVENC（独显硬件编码）；没有 NVIDIA 显卡时自动改用 libx264。

## 执行步骤

1. **环境检查（只读）**
   - `python --version` 需要 3.10 以上
   - `_bin\ffmpeg.exe` 存在（或 PATH 中有 ffmpeg）
   - `web\audio\GhostChain.wav` 存在
2. **安装依赖**
   - `pip install -U playwright`
   - `python -m playwright install chromium`
3. **设置独立显卡（笔记本是混合显卡时必须做）**
   - 先运行一次脚本（`python tools\export_mp4.py --start 0 --end 60`），它会打印“Chrome 路径”和“渲染器”。
   - 如果渲染器是 Intel 核显，脚本会停止。这时在 Windows 设置 → 系统 → 显示 → 图形 中，点“浏览”，选中打印出来的 chrome.exe，点“选项”，设为“高性能”。
   - 或者在 NVIDIA 控制面板 → 管理 3D 设置 → 程序设置 中，添加该 chrome.exe，首选“高性能 NVIDIA 处理器”。
   - 设置后重新运行，渲染器应显示 NVIDIA / GeForce / RTX 等独显名称。
4. **试跑 10 秒**：`python tools\export_mp4.py --start 0 --end 600 --out output\test_10s.mp4`。检查画面、音画同步和速度。
5. **全量导出**：`python tools\export_mp4.py`
   - 显存或内存紧张、进程崩溃：加 `--workers 2`（或 3）
   - 没有 NVIDIA 显卡：加 `--encoder libx264`（脚本通常会自动回退，这里可以显式指定）
6. **验收**：脚本结束时会打印视频与音频的信息，需要满足：
   - Video：h264，1920x1080，60 fps
   - Audio：aac
   - Duration：约 00:03:59.7
   - 日志中“确定性自检”显示“通过”
   - 抽查：打开 MP4，看开头、约 19.46 秒处的段落切换、结尾字幕，以及音画是否同步。

## 注意事项

- **不要修改** `web\` 下的任何文件（画面源码、时间轴、音频、歌词）。
- 不要删除 `output\` 之外的文件。`output\test_*.mp4` 这类试跑文件可以删除。
- 导出失败可以直接重跑，会覆盖同名输出。不要改用 Windows 录屏代替。
- 如果自检显示“未通过”，用 `--workers 1` 重跑，并在报告里说明。
- 如果画面明显异常（黑屏、缺字、颜色错误），先停止，不要硬导出。用 `python tools\shot.py --times 6,28,52` 生成样片截图，然后报告问题。

## 常见问题

| 现象 | 处理 |
|---|---|
| 渲染器是 Intel 核显，脚本停止 | 按步骤 3 设置“高性能”，重新运行 |
| 提示 Executable doesn't exist | 运行 `python -m playwright install chromium` |
| 提示找不到 ffmpeg | 确认 `_bin\ffmpeg.exe` 存在，或用 `--ffmpeg 路径` 指定 |
| 速度很慢（低于 15 帧/秒） | 确认是独显在渲染；关闭其他占用显卡的程序；尝试 `--workers 2` 或 `3` |
| 进程崩溃或显存不足 | 减少 `--workers`，例如改为 2 |
| 页面加载超时 | 加 `--timeout 600` 重跑 |

## 报告格式

完成后请报告以下内容：

- 输出文件的完整路径和文件大小
- 用时，以及平均帧率（脚本进度里的“帧/秒”）
- 渲染器名称（独显型号）和编码器（nvenc 或 libx264）
- 确定性自检结果
- 抽查结论
- 如果失败：附上脚本输出的最后 30 行
