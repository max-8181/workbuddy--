#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一次性完成：DWG数据提取 + SVG渲染 + 空间分析
"""
import win32com.client
import pythoncom
import json
import math
import os

DWG_PATH = r"J:\测试\新块.dwg"
OUTPUT_DIR = r"C:\Users\panshunkang\WorkBuddy\ima室内规范库"

# ---- 连接AutoCAD并打开文件 ----
pythoncom.CoInitialize()
app = win32com.client.Dispatch("AutoCAD.Application.20")
print(f"AutoCAD: {app.Caption}")

# 遍历所有文档找目标文件
doc = None
for i in range(app.Documents.Count):
    d = app.Documents.Item(i)
    try:
        if d.FullName.upper() == DWG_PATH.upper():
            doc = d
            print(f"文件已在打开: {d.Name}")
            break
    except:
        pass

if doc is None:
    print(f"正在打开: {DWG_PATH}")
    doc = app.Documents.Open(DWG_PATH)
    print(f"已打开: {doc.Name}")

msp = doc.ModelSpace
total = msp.Count
print(f"实体总数: {total}")

# ---- 提取所有实体 ----
wall_lines = []
glass_lines = []
window_lines = []
texts_data = []
circles_data = []
arcs_data = []
blocks_data = []

entity_types = {}
print("提取中...")

for i in range(total):
    entity = msp.Item(i)
    try:
        ename = str(entity.EntityName) if hasattr(entity, 'EntityName') else str(entity.ObjectName)
    except:
        continue
    
    entity_types[ename] = entity_types.get(ename, 0) + 1
    
    try:
        layer = str(entity.Layer) if hasattr(entity, 'Layer') else ""
    except:
        layer = ""
    
    try:
        if ename == 'AcDbLine':
            sp = entity.StartPoint
            ep = entity.EndPoint
            dx = ep[0] - sp[0]
            dy = ep[1] - sp[1]
            line = {
                "x1": sp[0], "y1": sp[1],
                "x2": ep[0], "y2": ep[1],
                "length": math.sqrt(dx*dx + dy*dy),
                "layer": layer
            }
            if layer == 'WALL':
                wall_lines.append(line)
            elif layer == 'WALLA':
                wall_lines.append(line)
            elif layer == 'DS-GLASS':
                glass_lines.append(line)
            elif layer == 'WINDOW':
                window_lines.append(line)
        
        elif ename == 'AcDbText':
            texts_data.append({
                "text": str(entity.TextString),
                "x": entity.InsertionPoint[0],
                "y": entity.InsertionPoint[1],
                "height": entity.Height if hasattr(entity, 'Height') else 0,
                "layer": layer,
            })
        
        elif ename == 'AcDbArc':
            arcs_data.append({
                "cx": entity.Center[0],
                "cy": entity.Center[1],
                "radius": entity.Radius,
                "sa": entity.StartAngle,
                "ea": entity.EndAngle,
                "layer": layer,
            })
        
        elif ename == 'AcDbCircle':
            circles_data.append({
                "cx": entity.Center[0],
                "cy": entity.Center[1],
                "radius": entity.Radius,
                "layer": layer,
            })
        
        elif ename == 'AcDbBlockReference':
            name = ""
            try:
                name = str(entity.EffectiveName)
            except:
                try:
                    name = str(entity.Name)
                except:
                    pass
            blocks_data.append({
                "name": name,
                "x": entity.InsertionPoint[0],
                "y": entity.InsertionPoint[1],
                "layer": layer,
            })
    except:
        continue

doc.Close(False)
pythoncom.CoUninitialize()

print(f"\n提取完成:")
print(f"  墙体(WALL+WALLA): {len(wall_lines)}")
print(f"  玻璃(DS-GLASS): {len(glass_lines)}")
print(f"  窗户(WINDOW): {len(window_lines)}")
print(f"  文字: {len(texts_data)}")
print(f"  圆弧: {len(arcs_data)}")
print(f"  圆: {len(circles_data)}")
print(f"  图块: {len(blocks_data)}")

for et, count in sorted(entity_types.items()):
    print(f"    {et}: {count}")

# ---- 计算图纸范围 ----
all_x, all_y = [], []
for line in wall_lines + glass_lines + window_lines:
    all_x.extend([line['x1'], line['x2']])
    all_y.extend([line['y1'], line['y2']])

if not all_x:
    print("错误: 未提取到任何墙体数据!")
    exit(1)

min_x, max_x = min(all_x), max(all_x)
min_y, max_y = min(all_y), max(all_y)
w_mm = max_x - min_x
h_mm = max_y - min_y

print(f"\n图纸范围: {w_mm:.0f}mm x {h_mm:.0f}mm = {w_mm/1000:.2f}m x {h_mm/1000:.2f}m")
total_area = w_mm * h_mm / 1e6
print(f"总建筑面积: {total_area:.1f} ㎡")

# ---- 保存完整数据 ----
full_data = {
    "bounds": {"min_x": min_x, "max_x": max_x, "min_y": min_y, "max_y": max_y,
               "width_mm": w_mm, "height_mm": h_mm, "area_m2": round(total_area, 1)},
    "wall_lines": [{"x1": round(l['x1'],1), "y1": round(l['y1'],1), "x2": round(l['x2'],1), "y2": round(l['y2'],1), "layer": l['layer']} for l in wall_lines],
    "glass_lines": [{"x1": round(l['x1'],1), "y1": round(l['y1'],1), "x2": round(l['x2'],1), "y2": round(l['y2'],1)} for l in glass_lines],
    "texts": [{"text": t['text'], "x": round(t['x'],1), "y": round(t['y'],1), "layer": t['layer']} for t in texts_data],
    "arcs": [{"cx": round(a['cx'],1), "cy": round(a['cy'],1), "radius": round(a['radius'],1), "sa": a['sa'], "ea": a['ea'], "layer": a['layer']} for a in arcs_data],
    "circles": [{"cx": round(c['cx'],1), "cy": round(c['cy'],1), "radius": round(c['radius'],1), "layer": c['layer']} for c in circles_data],
}

json_path = os.path.join(OUTPUT_DIR, "dwg_complete.json")
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(full_data, f, ensure_ascii=False, indent=2)
print(f"完整数据已保存: {json_path}")

# ---- 渲染SVG ----
print("\n渲染SVG平面图...")

padding = 2000
svg_w = w_mm + 2*padding
svg_h = h_mm + 2*padding

def tx(x):
    return x - min_x + padding

def ty(y):
    return max_y - y + padding

svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w:.0f} {svg_h:.0f}" width="1920">')
svg.append(f'<rect width="{svg_w:.0f}" height="{svg_h:.0f}" fill="#f8f9fa"/>')

# 背景网格
grid_spacing = 1000  # 1m = 1000mm
for gx in range(0, int(svg_w), grid_spacing):
    svg.append(f'<line x1="{gx}" y1="0" x2="{gx}" y2="{svg_h:.0f}" stroke="#e9ecef" stroke-width="0.5"/>')
for gy in range(0, int(svg_h), grid_spacing):
    svg.append(f'<line x1="0" y1="{gy}" x2="{svg_w:.0f}" y2="{gy}" stroke="#e9ecef" stroke-width="0.5"/>')

# 比例尺
sx, sy = 80, svg_h - 80
slen = 5000  # 5m
svg.append(f'<line x1="{sx}" y1="{sy}" x2="{sx+slen}" y2="{sy}" stroke="#333" stroke-width="4"/>')
for tick in [0, 1000, 2000, 3000, 4000, 5000]:
    svg.append(f'<line x1="{sx+tick}" y1="{sy-15}" x2="{sx+tick}" y2="{sy+15}" stroke="#333" stroke-width="2"/>')
svg.append(f'<text x="{sx}" y="{sy-25}" font-size="28" fill="#333" font-family="sans-serif">0</text>')
svg.append(f'<text x="{sx+2500}" y="{sy+40}" font-size="24" fill="#333" font-family="sans-serif" text-anchor="middle">5m</text>')

# 玻璃隔断 (底层，虚线)
for l in glass_lines:
    svg.append(f'<line x1="{tx(l["x1"]):.1f}" y1="{ty(l["y1"]):.1f}" x2="{tx(l["x2"]):.1f}" y2="{ty(l["y2"]):.1f}" stroke="#b2df8a" stroke-width="4" stroke-dasharray="10,6"/>')

# 窗户
for l in window_lines:
    svg.append(f'<line x1="{tx(l["x1"]):.1f}" y1="{ty(l["y1"]):.1f}" x2="{tx(l["x2"]):.1f}" y2="{ty(l["y2"]):.1f}" stroke="#74b9ff" stroke-width="3"/>')

# 墙体
for l in wall_lines:
    color = '#d63031' if l['layer'] == 'WALLA' else '#2d3436'
    width = 6 if l['layer'] == 'WALLA' else 4
    svg.append(f'<line x1="{tx(l["x1"]):.1f}" y1="{ty(l["y1"]):.1f}" x2="{tx(l["x2"]):.1f}" y2="{ty(l["y2"]):.1f}" stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>')

# 圆弧(门)
for a in arcs_data:
    cx, cy = tx(a['cx']), ty(a['cy'])
    r = a['radius']
    sa, ea = a['sa'], a['ea']
    if abs(ea - sa) < 0.01:
        continue
    sx = cx + r * math.cos(sa)
    sy = cy - r * math.sin(sa)
    ex = cx + r * math.cos(ea)
    ey = cy - r * math.sin(ea)
    sweep = 1
    large = 1 if abs(ea - sa) > math.pi else 0
    svg.append(f'<path d="M{sx:.1f},{sy:.1f} A{r:.1f},{r:.1f} 0 {large},{sweep} {ex:.1f},{ey:.1f}" fill="none" stroke="#0984e3" stroke-width="3"/>')

# 圆(柱子)
for c in circles_data:
    cx, cy = tx(c['cx']), ty(c['cy'])
    r = c['radius']
    fill = '#dfe6e9' if c['layer'] == 'WALL' else 'none'
    svg.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" stroke="#636e72" stroke-width="1.5"/>')

# 文字标注
for t in texts_data:
    x, y = tx(t['x']), ty(t['y'])
    text = t['text']
    is_english = all(ord(c) < 128 for c in text.strip() if c != ' ')
    font_size = 16 if is_english else 22
    color = '#636e72' if is_english else '#2d3436'
    font_weight = 'normal' if is_english else 'bold'
    svg.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{font_size}" fill="{color}" font-family="Microsoft YaHei, sans-serif" text-anchor="middle" font-weight="{font_weight}">{text}</text>')

# 指北针
nx, ny = svg_w - 120, 120
svg.append(f'<polygon points="{nx},{ny+60} {nx-12},{ny+25} {nx},{ny+35} {nx+12},{ny+25}" fill="#d63031"/>')
svg.append(f'<polygon points="{nx},{ny-60} {nx-12},{ny-25} {nx},{ny-35} {nx+12},{ny-25}" fill="#636e72"/>')
svg.append(f'<text x="{nx}" y="{ny-75}" font-size="22" fill="#d63031" font-family="sans-serif" text-anchor="middle" font-weight="bold">N</text>')

svg.append('</svg>')

svg_path = os.path.join(OUTPUT_DIR, "平面图_渲染.svg")
with open(svg_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(svg))
print(f"SVG已保存: {svg_path}")

# ---- 空间分析 ----
print("\n" + "="*60)
print("空间与疏散分析")
print("="*60)

# 按文字标注识别主要房间
main_rooms = []
for t in texts_data:
    text = t['text'].strip()
    is_chinese = any('\u4e00' <= c <= '\u9fff' for c in text)
    is_english_all = all(ord(c) < 128 for c in text if c != ' ')
    
    if is_chinese:
        # 找对应英文名
        eng_name = ""
        for t2 in texts_data:
            if abs(t2['x'] - t['x']) < 500 and abs(t2['y'] - t['y']) < 500 and t2 != t:
                t2_text = t2['text'].strip()
                if all(ord(c) < 128 for c in t2_text if c != ' '):
                    eng_name = t2_text
                    break
        
        main_rooms.append({
            "name": text,
            "eng_name": eng_name,
            "x": t['x'],
            "y": t['y'],
        })

# 根据墙体位置估算各房间面积
# 策略: 用墙体围合的矩形区域来估算
# 收集所有墙线的X和Y坐标，找网格

all_wx = []
all_wy = []
for l in wall_lines:
    all_wx.extend([l['x1'], l['x2']])
    all_wy.extend([l['y1'], l['y2']])

# 去重并排序
unique_x = sorted(set(round(x, -1) for x in all_wx))  # 精度10mm
unique_y = sorted(set(round(y, -1) for y in all_wy))

print(f"墙体坐标网格: X轴{len(unique_x)}个, Y轴{len(unique_y)}个")

# 尝试为每个房间匹配墙体围合的矩形
room_estimates = []

for room in main_rooms:
    rx, ry = room['x'], room['y']
    
    # 找包围此点的水平墙和垂直墙
    # 左墙: x < rx 的最大x
    left_x = max([x for x in unique_x if x < rx - 200], default=rx - 3000)
    # 右墙: x > rx 的最小x
    right_x = min([x for x in unique_x if x > rx + 200], default=rx + 3000)
    # 下墙(在CAD中Y更小): y < ry 的最大y
    bottom_y = max([y for y in unique_y if y < ry - 200], default=ry - 3000)
    # 上墙(在CAD中Y更大): y > ry 的最小y
    top_y = min([y for y in unique_y if y > ry + 200], default=ry + 3000)
    
    width_m = (right_x - left_x) / 1000
    height_m = (top_y - bottom_y) / 1000
    area = abs(width_m * height_m)
    
    room_estimates.append({
        "name": room['name'],
        "eng_name": room.get('eng_name', ''),
        "x": rx, "y": ry,
        "left_x": left_x, "right_x": right_x,
        "bottom_y": bottom_y, "top_y": top_y,
        "width_m": round(width_m, 1),
        "height_m": round(height_m, 1),
        "area_m2": round(area, 1),
    })

print(f"\n房间面积估算:")
total_room_area = 0
for r in room_estimates:
    print(f"  {r['name']:10s}: {r['width_m']:.1f}m x {r['height_m']:.1f}m = {r['area_m2']:.1f}㎡")
    total_room_area += r['area_m2']

print(f"\n功能房间总面积: {total_room_area:.1f}㎡")
print(f"建筑总面积: {total_area:.1f}㎡")
print(f"走道+公共区域: {total_area - total_room_area:.1f}㎡")

# 保存分析结果
analysis = {
    "building": {
        "total_area_m2": round(total_area, 1),
        "width_m": round(w_mm/1000, 2),
        "height_m": round(h_mm/1000, 2),
        "svc_room_area_m2": round(total_room_area, 1),
        "corridor_area_m2": round(total_area - total_room_area, 1),
    },
    "rooms": room_estimates,
}

analysis_path = os.path.join(OUTPUT_DIR, "room_analysis.json")
with open(analysis_path, 'w', encoding='utf-8') as f:
    json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)
print(f"\n分析结果已保存: {analysis_path}")

print("\n完成!")
