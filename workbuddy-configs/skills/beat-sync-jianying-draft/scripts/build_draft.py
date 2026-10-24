# -*- coding: utf-8 -*-
"""生成 sexy girl (Remaster) 的固定节奏卡点剪映草稿"""
import json
import os
import statistics
import subprocess

import imageio_ffmpeg

import pyJianYingDraft as draft
from pyJianYingDraft import (
    AudioMaterial,
    AudioSegment,
    DraftFolder,
    Timerange,
    VideoMaterial,
    VideoSegment,
)

AUDIO = r"D:\收集\爱剪辑\临时\自娱自乐\new\分片\项目四\BGM\sexy girl (Remaster).mp3"
DRAFT_ROOT = r"D:\收集\爱剪辑\临时\JianyingPro Drafts"
WORK = os.path.dirname(os.path.abspath(__file__))
PLACEHOLDER_DIR = os.path.join(WORK, "placeholders")
os.makedirs(PLACEHOLDER_DIR, exist_ok=True)

US = 1_000_000  # 秒 -> 微秒

# ---------- 1. 读取节奏分析 ----------
info = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))
duration = info["duration"]
beats = info["beats"]
first_beat = beats[0]
interval = statistics.median(
    [b - a for a, b in zip(beats, beats[1:])]
)  # 固定节拍间隔

# 固定网格：从第一个节拍开始，按固定间隔铺满整首歌
grid = [first_beat]
while grid[-1] + interval <= duration:
    grid.append(grid[-1] + interval)
print(f"固定网格: {len(grid)} 拍, 间隔 {interval:.4f}s, BPM={60/interval:.1f}")

# ---------- 2. 生成纯色占位视频 ----------
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
COLORS = {
    "black": "0x000000",
    "white": "0xFFFFFF",
    "red": "0xFF2D55",
    "cyan": "0x00E5FF",
}
for name, hexcolor in COLORS.items():
    out = os.path.join(PLACEHOLDER_DIR, f"{name}.mp4")
    if not os.path.exists(out):
        cmd = [
            FFMPEG, "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", f"color=c={hexcolor}:s=1080x1920:d=5:r=30",
            "-pix_fmt", "yuv420p", "-c:v", "libx264",
            out,
        ]
        subprocess.run(cmd, check=True)
        print(f"生成占位: {out}")

# ---------- 3. 生成草稿 ----------
folder = DraftFolder(DRAFT_ROOT)
draft_name = "sexy girl 卡点129BPM"
if folder.has_draft(draft_name):
    draft_name += " 2"

script = folder.create_draft(draft_name, 1080, 1920, 30)

# 先建轨道（视频轨 + 音频轨）
from pyJianYingDraft import TrackSpec, TrackType

script.append_track(TrackSpec(TrackType.video, name="卡点画面"))
script.append_track(TrackSpec(TrackType.audio, name="BGM"))

audio_mat = AudioMaterial(AUDIO, "sexy girl (Remaster)")
script.add_material(audio_mat)

video_mats = {
    n: VideoMaterial(os.path.join(PLACEHOLDER_DIR, f"{n}.mp4"), f"placeholder_{n}")
    for n in COLORS
}
for m in video_mats.values():
    script.add_material(m)

# 音频轨：整首歌
script.add_segment(
    AudioSegment(audio_mat, Timerange(0, int(duration * US)))
)

def add_clip(color, start, end):
    seg = VideoSegment(
        video_mats[color],
        Timerange(int(start * US), int((end - start) * US)),
        source_timerange=Timerange(0, int((end - start) * US)),
        volume=0.0,
    )
    script.add_segment(seg)

# 片头（第一拍之前）
add_clip("black", 0, grid[0])

# 每拍一切：偶数拍白、奇数拍黑，每 2 小节（8 拍）的首拍闪霓虹色
neons = ["red", "cyan"]
for i, t in enumerate(grid):
    end = grid[i + 1] if i + 1 < len(grid) else duration
    if end <= t:
        break
    if i % 8 == 0:
        color = neons[(i // 8) % 2]
    elif i % 2 == 0:
        color = "white"
    else:
        color = "black"
    add_clip(color, t, end)

script.save()

draft_path = os.path.join(DRAFT_ROOT, draft_name)
print("草稿目录:", draft_path)
print("存在 draft_content.json:", os.path.exists(os.path.join(draft_path, "draft_content.json")))
json.dump(
    {"draft_name": draft_name, "draft_path": draft_path, "grid": grid, "interval": interval},
    open(os.path.join(WORK, "result.json"), "w", encoding="utf-8"),
)
