# CHAINEDGHOST MV

基于 three.js 的歌词同步音乐视频（MV）实时网页。画面由音频特征逐帧驱动，歌词按打点时间显示。

## 目录

- `web/`：网页主程序（`src/` 场景与渲染，`index.html` 播放页，`timing.html` 歌词打点工具）
- `web/data/`：场景时间轴 `timing.json`，逐字打点结果 `char_times.json`（打点后生成）
- `web/assets/`：贴图
- `timing/`：歌词 LRC 与时间轴生成所需文件
- `tools/`：本地服务、渲染（`shot.py`）、时间轴构建（`build_timing.py`）等脚本
- `play_MV.bat`：Windows 下一键启动本地服务

## 不包含的内容

- 音乐文件（需自行放入 `web/audio/GhostChain.wav`）
- 渲染测试图片与视频输出（`render/`、`output/`）

## 运行

1. 把歌曲放到 `web/audio/GhostChain.wav`
2. 双击 `play_MV.bat`，浏览器打开 `http://localhost:8800/index.html` 播放
3. 打开 `http://localhost:8800/timing.html` 进行逐字打点（空格播放/暂停，回车打点，速度 30%–100%）
