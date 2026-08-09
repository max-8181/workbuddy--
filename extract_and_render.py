#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整提取DWG墙体数据 + 渲染SVG + 疏散分析
"""
import win32com.client
import pythoncom
import json
import math
import os

DWG_PATH = r"J:\测试\新块.dwg"
OUTPUT_DIR = r"C:\Users\panshunkang\WorkBuddy\ima室内规范库"

pythoncom.CoInitialize()

# 连接AutoCAD
try:
    acad = win32com.client.GetActiveObject("AutoCAD.Application")
except:
    acad = win32com.client.Dispatch("AutoCAD.Application")

doc = acad.ActiveDocument
msp = doc.ModelSpace

# ---- 完整提取 ----
wall_lines = []    # WALL + WALLA
glass_lines = []   # DS-GLASS
window_lines = []  # WINDOW
other_lines = []   
texts_data = []
circles_data = []
arcs_data = []
blocks_data = []

for i in range(msp.Count):
    entity = msp.Item(i)
    try:
        ename = ""
        try:
            ename = entity.EntityName
        except:
            continue
        
        layer = ""
        try:
            layer = entity.Layer
        except:
            pass
        
        if ename == 'AcDbLine':
            sp = entity.StartPoint
            ep = entity.EndPoint
            dx = ep[0] - sp[0]
            dy = ep[1] - sp[1]
            line = {
                "x1": round(sp[0], 1), "y1": round(sp[1], 1),
                "x2": round(ep[0], 1), "y2": round(ep[1], 1),
                "length": round(math.sqrt(dx*dx + dy*dy), 1),
                "layer": layer
            }
            if layer in ('WALL', 'WALLA'):
                wall_lines.append(line)
            elif layer == 'DS-GLASS':
                glass_lines.append(line)
            elif layer == 'WINDOW':
                window_lines.append(line)
            else:
                other_lines.append(line)
        
        elif ename == 'AcDbText':
            texts_data.append({
                "text": str(entity.TextString),
                "x": round(entity.InsertionPoint[0], 1),
                "y": round(entity.InsertionPoint[1], 1),
                "height": round(entity.Height, 1),
                "layer": layer,
            })
        
        elif ename == 'AcDbArc':
            arcs_data.append({
                "cx": round(entity.Center[0], 1),
                "cy": round(entity.Center[1], 1),
                "radius": round(entity.Radius, 1),
                "sa": round(entity.StartAngle, 3),
                "ea": round(entity.EndAngle, 3),
                "layer": layer,
            })
        
        elif ename == 'AcDbCircle':
            circles_data.append({
                "cx": round(entity.Center[0], 1),
                "cy": round(entity.Center[1], 1),
                "radius": round(entity.Radius, 1),
                "layer": layer,
            })
        
        elif ename == 'AcDbBlockReference':
            name = ""
            try:
                name = entity.EffectiveName
            except:
                try:
                    name = entity.Name
                except:
                    pass
            blocks_data.append({
                "name": str(name),
                "x": round(entity.InsertionPoint[0], 1),
                "y": round(entity.InsertionPoint[1], 1),
                "layer": layer,
            })
                
    except:
        continue

doc.Close(False)
pythoncom.CoUninitialize()

print(f"提取完成:")
print(f"  墙体线条: {len(wall_lines)}")
print(f"  玻璃隔断: {len(glass_lines)}")
print(f"  窗户: {len(window_lines)}")
print(f"  文字: {len(texts_data)}")
print(f"  圆弧: {len(arcs_data)}")
print(f"  圆: {len(circles_data)}")
print(f"  图块: {len(blocks_data)}")

# 计算图纸范围
all_x, all_y = [], []
for line in wall_lines + glass_lines:
    all_x.extend([line['x1'], line['x2']])
    all_y.extend([line['y1'], line['y2']])

if all_x:
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
else:
    min_x, max_x = 0, 10000
    min_y, max_y = 0, 10000

w_mm = max_x - min_x
h_mm = max_y - min_y
print(f"\n图纸范围: {w_mm:.0f}mm x {h_mm:.0f}mm = {w_mm/1000:.1f}m x {h_mm/1000:.1f}m")
print(f"总面积: {(w_mm*h_mm/1e6):.1f} ㎡")

# 保存完整数据
full_data = {
    "bounds": {"min_x": min_x, "max_x": max_x, "min_y": min_y, "max_y": max_y},
    "wall_lines": wall_lines,
    "glass_lines": glass_lines,
    "window_lines": window_lines,
    "texts": texts_data,
    "arcs": arcs_data,
    "circles": circles_data,
}

json_path = os.path.join(OUTPUT_DIR, "dwg_complete.json")
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(full_data, f, ensure_ascii=False, indent=2)
print(f"\n完整数据已保存: {json_path}")

# ---- 渲染SVG ----
print("\n渲染SVG平面图...")

padding_mm = 1000
svg_w = w_mm + 2*padding_mm
svg_h = h_mm + 2*padding_mm

def tx(x):
    """CAD X → SVG X"""
    return x - min_x + padding_mm

def ty(y):
    """CAD Y → SVG Y (flip)"""
    return max_y - y + padding_mm

def line_svg(x1, y1, x2, y2, color, width=2, dash=None, layer=""):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{tx(x1):.1f}" y1="{ty(y1):.1f}" x2="{tx(x2):.1f}" y2="{ty(y2):.1f}" stroke="{color}" stroke-width="{width}"{d} data-layer="{layer}"/>'

svg_lines = []
svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w:.0f} {svg_h:.0f}" width="100%" height="100%">')
svg_lines.append(f'<rect width="{svg_w:.0f}" height="{svg_h:.0f}" fill="#fafafa"/>')

# 比例尺
scale_bar_y = svg_h - 50
scale_bar_x = 50
scale_len = 5000  # 5m = 5000mm
svg_lines.append(f'<line x1="{scale_bar_x}" y1="{scale_bar_y}" x2="{scale_bar_x+scale_len}" y2="{scale_bar_y}" stroke="#333" stroke-width="3"/>')
svg_lines.append(f'<line x1="{scale_bar_x}" y1="{scale_bar_y-10}" x2="{scale_bar_x}" y2="{scale_bar_y+10}" stroke="#333" stroke-width="2"/>')
svg_lines.append(f'<line x1="{scale_bar_x+scale_len}" y1="{scale_bar_y-10}" x2="{scale_bar_x+scale_len}" y2="{scale_bar_y+10}" stroke="#333" stroke-width="2"/>')
svg_lines.append(f'<text x="{scale_bar_x}" y="{scale_bar_y-20}" font-size="24" fill="#333" font-family="sans-serif">0</text>')
svg_lines.append(f'<text x="{scale_bar_x+scale_len}" y="{scale_bar_y-20}" font-size="24" fill="#333" font-family="sans-serif" text-anchor="end">5m</text>')

# 渲染玻璃隔断 (先画，作为背景)
for l in glass_lines:
    svg_lines.append(line_svg(l['x1'], l['y1'], l['x2'], l['y2'], '#b8e6c8', 3, dash="6,4"))

# 渲染窗户
for l in window_lines:
    svg_lines.append(line_svg(l['x1'], l['y1'], l['x2'], l['y2'], '#74b9ff', 2))

# 渲染墙体 (最上层)
for l in wall_lines:
    color = '#1a1a2e' if l['layer'] == 'WALL' else '#d63031'
    width = 4 if l['layer'] == 'WALLA' else 3
    svg_lines.append(line_svg(l['x1'], l['y1'], l['x2'], l['y2'], color, width))

# 渲染圆弧(门弧)
for a in arcs_data:
    # 简化：用path近似圆弧
    cx, cy = tx(a['cx']), ty(a['cy'])
    r = a['radius']
    sa, ea = a['sa'], a['ea']
    # 计算起点和终点
    sx = cx + r * math.cos(sa)
    sy = cy - r * math.sin(sa)  # SVG Y flip注意：arc角度也需要处理
    ex = cx + r * math.cos(ea)
    ey = cy - r * math.sin(ea)
    # 简化 - 画圆弧
    large = 0 if abs(ea - sa) <= math.pi else 1
    sweep = 1  # 简化
    svg_lines.append(f'<path d="M {sx:.1f} {sy:.1f} A {r:.1f} {r:.1f} 0 {large} {sweep} {ex:.1f} {ey:.1f}" fill="none" stroke="#e17055" stroke-width="2"/>')

# 渲染圆
for c in circles_data:
    cx, cy = tx(c['cx']), ty(c['cy'])
    r = c['radius']
    svg_lines.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="none" stroke="#636e72" stroke-width="1.5"/>')

# 渲染文字标注
for t in texts_data:
    x, y = tx(t['x']), ty(t['y'])
    # 房间名用大字体
    text = t['text']
    is_chinese = any('\u4e00' <= c <= '\u9fff' for c in text)
    font_size = 28 if is_chinese else 22
    color = '#2d3436' if is_chinese else '#636e72'
    svg_lines.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{font_size}" fill="{color}" font-family="Microsoft YaHei, sans-serif" text-anchor="middle">{text}</text>')

svg_lines.append('</svg>')

svg_path = os.path.join(OUTPUT_DIR, "平面图_渲染.svg")
with open(svg_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(svg_lines))

print(f"SVG已保存: {svg_path}")

# ---- 空间分析 ----
print("\n" + "="*60)
print("空间分析")
print("="*60)

# 基于文字标注位置和墙体关系推断房间边界
# 思路: 对于每个房间名的文字，找到包围它的WALL线条，围合成多边形

# 先分析墙体构成的封闭空间
# 找出所有墙线的端点，构建端点图
print("\n墙体分析:")
print(f"  WALL线条: {len([l for l in wall_lines if l['layer']=='WALL'])}")
print(f"  WALLA线条: {len([l for l in wall_lines if l['layer']=='WALLA'])}")

# 文字标注的功能房间
main_rooms = [
    {"name": "会议室1", "x": 302628, "y": -162778},
    {"name": "会议室2", "x": 303584, "y": -171267},
    {"name": "门厅",    "x": 307744, "y": -164033},
    {"name": "复印",    "x": 310350, "y": -167278},
    {"name": "茶水间",  "x": 312603, "y": -167073},
    {"name": "行政办公室","x": 312220, "y": -171547},
    {"name": "仓库",    "x": 302528, "y": -166429},
]

print(f"\n功能区列表:")
for r in main_rooms:
    print(f"  {r['name']:10s} 中心点=({r['x']:.0f}, {r['y']:.0f})")

# 找出每个房间周围的墙体
# 简单方法：扫描水平和垂直墙体，推断房间矩形区域
print("\n墙线按方向分类:")
h_walls = []  # 水平墙 (Y1≈Y2)
v_walls = []  # 垂直墙 (X1≈X2)
for l in wall_lines:
    dx = abs(l['x2'] - l['x1'])
    dy = abs(l['y2'] - l['y1'])
    if dy < 100:  # 近似水平
        h_walls.append(l)
    elif dx < 100:  # 近似垂直
        v_walls.append(l)

print(f"  水平墙: {len(h_walls)} 条")
print(f"  垂直墙: {len(v_walls)} 条")

# 收集墙线坐标
h_y_coords = sorted(set([l['y1'] for l in h_walls] + [l['y2'] for l in h_walls]))
v_x_coords = sorted(set([l['x1'] for l in v_walls] + [l['x2'] for l in v_walls]))

print(f"\n水平墙Y坐标 (前10): {[round(y) for y in h_y_coords[:10]]}")
print(f"垂直墙X坐标 (前10): {[round(x) for x in v_x_coords[:10]]}")

# 输出分析结果
analysis = {
    "total_area_m2": round(w_mm * h_mm / 1e6, 1),
    "total_width_m": round(w_mm/1000, 1),
    "total_height_m": round(h_mm/1000, 1),
    "rooms_identified": main_rooms,
    "wall_data": {
        "horizontal_count": len(h_walls),
        "vertical_count": len(v_walls),
        "h_y_coords": [round(y) for y in h_y_coords],
        "v_x_coords": [round(x) for x in v_x_coords],
    },
    "arcs_count": len(arcs_data),
    "circles_count": len(circles_data),
}

analysis_path = os.path.join(OUTPUT_DIR, "room_analysis.json")
with open(analysis_path, 'w', encoding='utf-8') as f:
    json.dump(analysis, f, ensure_ascii=False, indent=2)
print(f"\n空间分析已保存: {analysis_path}")

print("\n" + "="*60)
print("完成")
print("="*60)
