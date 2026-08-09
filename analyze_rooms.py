#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于DWG线条数据渲染SVG平面图并分析疏散布局
"""
import json
import math
import os

DWGDATA = r"C:\Users\panshunkang\WorkBuddy\ima室内规范库\dwg_full_data.json"
OUTPUT_SVG = r"C:\Users\panshunkang\WorkBuddy\ima室内规范库\平面图_渲染.svg"
OUTPUT_ANALYSIS = r"C:\Users\panshunkang\WorkBuddy\ima室内规范库\room_analysis.json"

with open(DWGDATA, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 获取图纸范围
bounds = data['bounds']
min_x, max_x = bounds['min_x'], bounds['max_x']
min_y, max_y = bounds['min_y'], bounds['max_y']
width_mm = bounds['width_mm']
height_mm = bounds['height_mm']

print(f"图纸范围: {width_mm:.0f} x {height_mm:.0f} mm = {width_mm/1000:.1f} x {height_mm/1000:.1f} m")

# SVG画布参数 (增加padding)
padding = 1000
svg_w = width_mm + 2*padding
svg_h = height_mm + 2*padding

def to_svg_x(x):
    return x - min_x + padding

def to_svg_y(y):
    # Y轴翻转 (CAD Y向上, SVG Y向下)
    return max_y - y + padding

# 颜色映射
layer_colors = {
    'WALL': ('#1a1a2e', 4.0),
    'WALLA': ('#2d3436', 8.0),  # 加粗外墙
    'WINDOW': ('#74b9ff', 2.0),
    'DS-GLASS': ('#a8e6cf', 1.5),
    'RC-18Noet': ('#dfe6e9', 1.0),
    'FF-FURN': ('#b2bec3', 1.0),
    'DS-HIGH CABINET': ('#636e72', 1.5),
}

# 读取原始lines
# 需要重新提取线条，因为JSON可能没有保存完整的lines
# 实际上我们保存了lines_data但没在JSON里... 让我们从原始数据重新提取

# data中有counts里lines=280，但没有完整lines数组
# 我需要回到COM重新提取完整line数据，或者简化处理

print("\n由于图片导出失败，我将基于文字标注位置和图纸尺寸进行空间分析。")
print("\n从文字标注识别的功能区:")

texts = data['texts']

# 按Y坐标分组，识别空间层次
texts_by_y = sorted(texts, key=lambda t: -t['y'])  # Y坐标从上到下 (CAD坐标系)
print("\n功能区列表 (从上到下):")
for t in texts_by_y:
    print(f"  {t['text']:20s} X={t['x']:.0f}  Y={t['y']:.0f}")

# 估算房间面积 - 基于布局和标注
# 从文字标注位置推测空间分隔
print("\n" + "="*60)
print("空间布局分析")
print("="*60)

# 分析墙体走向 - 需要重新提取
# 由于JSON没保存完整lines，我们需要回到COM
# 让我换个方法：基于文字距离和已知尺寸推断

# 根据建筑外观 - 18m x 15.2m
total_area = (width_mm/1000) * (height_mm/1000)
print(f"\n总建筑面积(模型空间): {total_area:.1f} ㎡")

# 从文字标注分析潜在房间
rooms_text = [t for t in texts if t['layer'] == 'FF-TEXT']
room_names = [t['text'] for t in rooms_text if not t['text'].isascii() or t['text'].startswith('MEET') or t['text'].startswith('ENTRANCE') or t['text'].startswith('STORE') or t['text'].startswith('ADMIN')]

print("\n中文房间名:", [t['text'] for t in rooms_text if any('\u4e00' <= c <= '\u9fff' for c in t['text'])])

# 保存分析结果
print("\n由于无法从COM精确获取房间边界，采用多模态方案。")
print("请提供CAD截图，或让我使用现有的Plan B方案。")

# 尝试另一种方法: 再次尝试通过不同的COM方式获取数据
