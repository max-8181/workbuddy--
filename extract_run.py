#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
稳健版：DWG数据提取 + SVG渲染 + 空间分析
"""
import sys, os, json, math

DWG_PATH = r"J:\测试\新块.dwg"
OUTPUT_DIR = r"C:\Users\panshunkang\WorkBuddy\ima室内规范库"

print("=" * 60)
print("步骤1: 连接AutoCAD并打开文件")

import pythoncom
import win32com.client

pythoncom.CoInitialize()

try:
    acad = win32com.client.GetActiveObject("AutoCAD.Application")
    print("  已连接到运行中的AutoCAD")
except:
    acad = win32com.client.Dispatch("AutoCAD.Application")
    acad.Visible = True
    print("  已启动AutoCAD")

# 查找/打开目标文件
doc = None
for i in range(acad.Documents.Count):
    d = acad.Documents.Item(i)
    try:
        fp = d.FullName
        if fp.upper() == DWG_PATH.upper():
            doc = d
            doc.Activate()
            print(f"  目标文件已打开: {d.Name}")
            break
    except:
        pass

if doc is None:
    print(f"  正在打开: {DWG_PATH}")
    acad.Documents.Open(DWG_PATH)
    # Documents.Open() 有时返回None，文档实际在Documents集合末尾
    doc = acad.Documents.Item(acad.Documents.Count - 1)
    print(f"  已打开: {doc.Name}")

msp = doc.ModelSpace
total = msp.Count
print(f"  实体总数: {total}")

print("\n步骤2: 提取所有实体...")

wall_lines = []
glass_lines = []
window_lines = []
texts_data = []
circles_data = []
arcs_data = []
blocks_data = []
polylines_data = []

for i in range(total):
    entity = msp.Item(i)
    try:
        ename = str(entity.EntityName)
    except:
        try:
            ename = str(entity.ObjectName)
        except:
            continue
    
    try:
        layer = str(entity.Layer)
    except:
        layer = ""
    
    try:
        if ename == 'AcDbLine':
            sp = entity.StartPoint
            ep = entity.EndPoint
            if sp is None or ep is None:
                continue
            dx = ep[0] - sp[0]
            dy = ep[1] - sp[1]
            line = {"x1": float(sp[0]), "y1": float(sp[1]),
                    "x2": float(ep[0]), "y2": float(ep[1]),
                    "length": math.hypot(dx, dy), "layer": layer}
            low = layer.upper()
            if 'WALL' in low:
                wall_lines.append(line)
            elif 'GLASS' in low:
                glass_lines.append(line)
            elif 'WINDOW' in low or 'WIND' in low:
                window_lines.append(line)
            else:
                wall_lines.append(line)  # 默认层也算墙体
        
        elif ename == 'AcDbPolyline':
            pts = []
            try:
                coords = entity.Coordinates
                for j in range(0, len(coords), 2):
                    pts.append({"x": float(coords[j]), "y": float(coords[j+1])})
            except:
                pass
            polylines_data.append({"points": pts, "layer": layer, "closed": entity.Closed})
        
        elif ename == 'AcDbText':
            texts_data.append({
                "text": str(entity.TextString),
                "x": float(entity.InsertionPoint[0]),
                "y": float(entity.InsertionPoint[1]),
                "height": float(entity.Height) if hasattr(entity, 'Height') else 0,
                "layer": layer,
            })
        
        elif ename == 'AcDbArc':
            arcs_data.append({
                "cx": float(entity.Center[0]), "cy": float(entity.Center[1]),
                "radius": float(entity.Radius),
                "sa": float(entity.StartAngle), "ea": float(entity.EndAngle),
                "layer": layer,
            })
        
        elif ename == 'AcDbCircle':
            circles_data.append({
                "cx": float(entity.Center[0]), "cy": float(entity.Center[1]),
                "radius": float(entity.Radius), "layer": layer,
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
                "name": name, "layer": layer,
                "x": float(entity.InsertionPoint[0]),
                "y": float(entity.InsertionPoint[1]),
            })
    except Exception as e:
        continue

print(f"  墙体: {len(wall_lines)}  玻璃: {len(glass_lines)}  窗户: {len(window_lines)}")
print(f"  文字: {len(texts_data)}  圆弧(门): {len(arcs_data)}  圆: {len(circles_data)}")
print(f"  图块: {len(blocks_data)}  多段线: {len(polylines_data)}")

# 不关闭文档，后续还需要标注
print("\n步骤3: 计算图纸范围...")
all_x, all_y = [], []
for lines in [wall_lines, glass_lines, window_lines]:
    for l in lines:
        all_x.extend([l['x1'], l['x2']])
        all_y.extend([l['y1'], l['y2']])

if not all_x:
    for p in polylines_data:
        for pt in p['points']:
            all_x.append(pt['x'])
            all_y.append(pt['y'])

if not all_x:
    print("错误: 未提取到任何几何数据!")
    doc.Close(False)
    pythoncom.CoUninitialize()
    sys.exit(1)

min_x, max_x = min(all_x), max(all_x)
min_y, max_y = min(all_y), max(all_y)
w_mm = max_x - min_x
h_mm = max_y - min_y

print(f"  范围: {w_mm:.0f}mm x {h_mm:.0f}mm = {w_mm/1000:.2f}m x {h_mm/1000:.2f}m")
total_area = w_mm * h_mm / 1e6
print(f"  面积: {total_area:.1f} ㎡")

# 保存JSON数据
full_data = {
    "bounds": {"min_x": min_x, "max_x": max_x, "min_y": min_y, "max_y": max_y,
               "width_mm": w_mm, "height_mm": h_mm, "area_m2": round(total_area, 1)},
    "wall_lines": [{"x1": round(l['x1'],1), "y1": round(l['y1'],1), "x2": round(l['x2'],1), "y2": round(l['y2'],1), "layer": l['layer']} for l in wall_lines],
    "glass_lines": [{"x1": round(l['x1'],1), "y1": round(l['y1'],1), "x2": round(l['x2'],1), "y2": round(l['y2'],1)} for l in glass_lines],
    "texts": [{"text": t['text'], "x": round(t['x'],1), "y": round(t['y'],1), "height": t['height'], "layer": t['layer']} for t in texts_data],
    "arcs": [{"cx": round(a['cx'],1), "cy": round(a['cy'],1), "radius": round(a['radius'],1), "sa": a['sa'], "ea": a['ea'], "layer": a['layer']} for a in arcs_data],
    "circles": [{"cx": round(c['cx'],1), "cy": round(c['cy'],1), "radius": round(c['radius'],1), "layer": c['layer']} for c in circles_data],
    "blocks": [{"name": b['name'], "x": round(b['x'],1), "y": round(b['y'],1), "layer": b['layer']} for b in blocks_data],
    "polylines": [{"points": [{"x": round(p['x'],1), "y": round(p['y'],1)} for p in pl['points']], "closed": pl['closed'], "layer": pl['layer']} for pl in polylines_data],
}
json_path = os.path.join(OUTPUT_DIR, "dwg_data.json")
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(full_data, f, ensure_ascii=False, indent=2)
print(f"  数据已保存: {json_path}")

print("\n步骤4: 渲染SVG...")

padding = 2000
svg_w = w_mm + 2*padding
svg_h = h_mm + 2*padding

def tx(x):
    return x - min_x + padding

def ty(y):
    return max_y - y + padding

svg_lines = []
svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w:.0f} {svg_h:.0f}">')
svg_lines.append(f'<rect width="{svg_w:.0f}" height="{svg_h:.0f}" fill="#1a1a2e"/>')

# 网格
gs = 1000
for gx in range(0, int(svg_w), gs):
    svg_lines.append(f'<line x1="{gx}" y1="0" x2="{gx}" y2="{svg_h:.0f}" stroke="#16213e" stroke-width="0.5"/>')
for gy in range(0, int(svg_h), gs):
    svg_lines.append(f'<line x1="0" y1="{gy}" x2="{svg_w:.0f}" y2="{gy}" stroke="#16213e" stroke-width="0.5"/>')

# 多段线(墙体轮廓)
for pl in polylines_data:
    pts = pl['points']
    if len(pts) < 2:
        continue
    d = ""
    for j, pt in enumerate(pts):
        px, py = tx(pt['x']), ty(pt['y'])
        d += f"{'M' if j == 0 else 'L'}{px:.1f},{py:.1f} "
    if pl['closed']:
        d += "Z"
    svg_lines.append(f'<path d="{d}" fill="rgba(45,52,54,0.15)" stroke="#636e72" stroke-width="2"/>')

# 玻璃
for l in glass_lines:
    svg_lines.append(f'<line x1="{tx(l["x1"]):.1f}" y1="{ty(l["y1"]):.1f}" x2="{tx(l["x2"]):.1f}" y2="{ty(l["y2"]):.1f}" stroke="#00b894" stroke-width="3" stroke-dasharray="8,5"/>')

# 窗户
for l in window_lines:
    svg_lines.append(f'<line x1="{tx(l["x1"]):.1f}" y1="{ty(l["y1"]):.1f}" x2="{tx(l["x2"]):.1f}" y2="{ty(l["y2"]):.1f}" stroke="#74b9ff" stroke-width="4" opacity="0.7"/>')

# 墙体
for l in wall_lines:
    color = '#e17055' if 'WALLA' in l['layer'].upper() else '#dfe6e9'
    width = 6 if 'WALLA' in l['layer'].upper() else 3
    svg_lines.append(f'<line x1="{tx(l["x1"]):.1f}" y1="{ty(l["y1"]):.1f}" x2="{tx(l["x2"]):.1f}" y2="{ty(l["y2"]):.1f}" stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>')

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
    svg_lines.append(f'<path d="M{sx:.1f},{sy:.1f} A{r:.1f},{r:.1f} 0 {large},{sweep} {ex:.1f},{ey:.1f}" fill="none" stroke="#74b9ff" stroke-width="3"/>')
    # 门扇线
    svg_lines.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="#74b9ff" stroke-width="1.5" stroke-dasharray="4,3"/>')

# 圆(柱子)
for c in circles_data:
    cx, cy = tx(c['cx']), ty(c['cy'])
    r = c['radius']
    svg_lines.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="rgba(108,117,125,0.3)" stroke="#636e72" stroke-width="1"/>')

# 文字
for t in texts_data:
    x, y = tx(t['x']), ty(t['y'])
    text = t['text']
    is_eng = all(ord(c) < 128 for c in text.strip() if c != ' ')
    fs = 14 if is_eng else 20
    color = '#636e72' if is_eng else '#ffffff'
    fw = 'normal' if is_eng else 'bold'
    svg_lines.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{fs}" fill="{color}" font-family="Microsoft YaHei, sans-serif" text-anchor="middle" font-weight="{fw}">{text}</text>')

# 指北针
nx, ny = svg_w - 120, 120
svg_lines.append(f'<polygon points="{nx},{ny+60} {nx-12},{ny+25} {nx},{ny+35} {nx+12},{ny+25}" fill="#e17055"/>')
svg_lines.append(f'<polygon points="{nx},{ny-60} {nx-12},{ny-25} {nx},{ny-35} {nx+12},{ny-25}" fill="#636e72"/>')
svg_lines.append(f'<text x="{nx}" y="{ny-75}" font-size="20" fill="#e17055" font-family="sans-serif" text-anchor="middle" font-weight="bold">N</text>')

# 比例尺
sx, sy = 80, svg_h - 80
slen = 5000
svg_lines.append(f'<line x1="{sx}" y1="{sy}" x2="{sx+slen}" y2="{sy}" stroke="#dfe6e9" stroke-width="4"/>')
for tick in [0, 1000, 2000, 3000, 4000, 5000]:
    svg_lines.append(f'<line x1="{sx+tick}" y1="{sy-12}" x2="{sx+tick}" y2="{sy+12}" stroke="#dfe6e9" stroke-width="2"/>')
svg_lines.append(f'<text x="{sx}" y="{sy-20}" font-size="22" fill="#dfe6e9" font-family="sans-serif">0</text>')
svg_lines.append(f'<text x="{sx+2500}" y="{sy+36}" font-size="20" fill="#dfe6e9" font-family="sans-serif" text-anchor="middle">5m</text>')

svg_lines.append('</svg>')

svg_content = '\n'.join(svg_lines)
svg_path = os.path.join(OUTPUT_DIR, "平面图_原始.svg")
with open(svg_path, 'w', encoding='utf-8') as f:
    f.write(svg_content)
print(f"  SVG已保存: {svg_path}")

print("\n步骤5: 文字标注分析...")
main_rooms = []
for t in texts_data:
    text = t['text'].strip()
    is_cn = any('\u4e00' <= c <= '\u9fff' for c in text)
    if is_cn:
        eng_name = ""
        for t2 in texts_data:
            if abs(t2['x'] - t['x']) < 500 and abs(t2['y'] - t['y']) < 400 and t2 != t:
                t2t = t2['text'].strip()
                if t2t and all(ord(c) < 128 for c in t2t if c != ' '):
                    eng_name = t2t
                    break
        main_rooms.append({"name": text, "eng_name": eng_name, "x": t['x'], "y": t['y']})
        print(f"  {text}" + (f" ({eng_name})" if eng_name else ""))

# 墙面坐标网格(精度50mm)
all_wx = []
all_wy = []
for l in wall_lines:
    all_wx.extend([l['x1'], l['x2']])
    all_wy.extend([l['y1'], l['y2']])
unique_x = sorted(set(round(x/50)*50 for x in all_wx))
unique_y = sorted(set(round(y/50)*50 for y in all_wy))

print(f"\n  墙体坐标网格: X {len(unique_x)}点, Y {len(unique_y)}点")

room_estimates = []
for room in main_rooms:
    rx, ry = room['x'], room['y']
    left_x = max((x for x in unique_x if x < rx - 200), default=rx - 4000)
    right_x = min((x for x in unique_x if x > rx + 200), default=rx + 4000)
    bottom_y = max((y for y in unique_y if y < ry - 200), default=ry - 4000)
    top_y = min((y for y in unique_y if y > ry + 200), default=ry + 4000)
    w, h = (right_x - left_x)/1000, (top_y - bottom_y)/1000
    area = round(abs(w * h), 1)
    room_estimates.append({
        "name": room['name'], "eng_name": room.get('eng_name', ''),
        "x": round(rx,1), "y": round(ry,1),
        "left_x": left_x, "right_x": right_x,
        "bottom_y": bottom_y, "top_y": top_y,
        "width_m": round(w, 1), "height_m": round(h, 1),
        "area_m2": area,
    })

total_svc = sum(r['area_m2'] for r in room_estimates)
analysis = {
    "building": {
        "total_area_m2": round(total_area, 1),
        "width_m": round(w_mm/1000, 2), "height_m": round(h_mm/1000, 2),
        "svc_area_m2": round(total_svc, 1),
        "corridor_area_m2": round(total_area - total_svc, 1),
    },
    "rooms": room_estimates,
    "text_count": len(texts_data),
    "wall_count": len(wall_lines),
    "arc_count": len(arcs_data),
    "block_count": len(blocks_data),
}
analysis_path = os.path.join(OUTPUT_DIR, "room_analysis.json")
with open(analysis_path, 'w', encoding='utf-8') as f:
    json.dump(analysis, f, ensure_ascii=False, indent=2)
print(f"  分析结果: {analysis_path}")

# 关闭COM
doc.Close(False)
pythoncom.CoUninitialize()

print("\n✓ 提取完成!")
print(f"  建筑类型: 办公(用户确认)")
print(f"  楼层: 4层及以上")
print(f"  耐火等级: 一、二级")
print(f"  自动喷淋: 全部设置")
