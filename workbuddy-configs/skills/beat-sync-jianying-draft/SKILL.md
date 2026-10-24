---
name: beat-sync-jianying-draft
description: 从音乐文件自动生成固定节奏卡点剪映（JianYing）草稿。检测 BPM/节拍后按固定节拍网格切纯色占位片段，写入剪映草稿目录。触发词：卡点、节奏、剪映草稿、BGM 打点、beat sync、音乐踩点。
---

# 音乐 → 固定节奏卡点剪映草稿

## 用途
用户提供一首音乐（mp3/wav 等），生成一份剪映草稿：音频轨放整曲，视频轨按固定节拍间隔（BPM）切成纯色占位片段，用户在剪映里「替换素材」换成自己的视频/图片即可得到卡点视频。

## 环境准备（一次性）

Python venv（用受管 Python 3.13.12 建）：
```bash
"C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" -m venv "C:/Users/Administrator/.workbuddy/binaries/python/envs/jianying"
# PyPI 直连会超时，必须走清华镜像：
"C:/Users/Administrator/.workbuddy/binaries/python/envs/jianying/Scripts/python.exe" -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pyJianYingDraft librosa soundfile pillow imageio-ffmpeg
```

## 关键事实（本机）
- 剪映草稿实际根目录：`D:\收集\爱剪辑\临时\JianyingPro Drafts`（自定义位置，不是 AppData 默认目录；可用 `C:\Users\Administrator\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft\root_meta_info.json` 里 `draft_root_path` 确认）。
- pyJianYingDraft 的 `DraftFolder(root).create_draft()` 会同时更新 root_meta_info.json，剪映首页立即可见。
- ffmpeg 二进制来自 `imageio_ffmpeg.get_ffmpeg_exe()`，无需系统安装。

## 工作流

1. **节拍分析**（librosa，注意新版 librosa `beat_track` 返回的 tempo 是数组，要 `float(np.atleast_1d(tempo)[0])`）：
   - `librosa.beat.beat_track(y, sr, units="frames")` → beat_times
   - 取**节拍间隔中位数**作为固定网格间隔（比原始检测点更"固定"，适合匀速电音/舞曲）
2. **生成纯色占位视频**：ffmpeg lavfi color 源，`1080x1920 d=5 r=30 yuv420p libx264`，黑/白/红/ cyan 各一个（长片段如片头需要 source ≥ 片长）。
3. **建草稿**（pyJianYingDraft API 要点，容易踩坑）：
   ```python
   folder = DraftFolder(r"D:\收集\爱剪辑\临时\JianyingPro Drafts")
   script = folder.create_draft(name, 1080, 1920, 30)
   # 必须先手动建轨道，否则 add_segment 报 "不存在接受 ... 的轨道"
   script.append_track(TrackSpec(TrackType.video, name="卡点画面"))
   script.append_track(TrackSpec(TrackType.audio, name="BGM"))
   ```
   - 时间单位是**微秒**（`Timerange(start, duration)`）
   - 片段先 `add_material`，占位视频多个片段可共用同一 material（source_timerange 指向同一文件不同区间）
   - 视频片段建议 `volume=0.0`
4. **节奏图样**：每拍一切；偶数拍白/奇数拍黑，每 8 拍（2 小节）首拍闪霓虹色（红/青交替）。片头（第一拍前）铺黑。
5. **失败重跑**：create_draft 失败后要删掉半成品草稿文件夹再重跑，否则 has_draft 会加 " 2" 后缀产生重复草稿。

## 已验证参数
- `sexy girl (Remaster).mp3`：288s，129.2 BPM，间隔 0.4644s，615 拍，第一拍在 2.786s。
- 参考实现脚本：本 skill 目录 `scripts/analyze.py`、`scripts/build_draft.py`（按需改 AUDIO 路径、画幅、颜色、每拍/每两拍切）。

## 可调项
- 画幅：1080x1920 竖屏 ↔ 1920x1080 横屏（改 create_draft 参数和 ffmpeg s=）
- 切拍密度：每 1 拍（0.46s，闪切）↔ 每 2 拍（0.93s，常规卡点）↔ 每 4 拍（1.86s，慢摇）
- 占位色：改 COLORS 字典
