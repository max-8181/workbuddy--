#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接从活动文档导出DWG为图片+提取完整数据
"""
import win32com.client
from win32com.client import Dispatch, constants
import pythoncom
import os
import time
import json
import math

DWG_PATH = r"J:\测试\新块.dwg"
OUTPUT_DIR = r"C:\Users\panshunkang\WorkBuddy\ima室内规范库"
OUTPUT_PNG = os.path.join(OUTPUT_DIR, "平面图_export.png")
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "dwg_full_data.json")

pythoncom.CoInitialize()

# 连接AutoCAD
try:
    acad = win32com.client.GetActiveObject("AutoCAD.Application")
    print("已连接到AutoCAD实例")
except:
    acad = win32com.client.Dispatch("AutoCAD.Application")
    acad.Visible = True
    print("已启动AutoCAD")

print(f"Caption: {acad.Caption}")

# 方法1：直接用ActiveDocument
doc = acad.ActiveDocument
print(f"ActiveDocument: {doc.Name}")

# 检查是否是目标文件，如果不是则遍历Documents
target_doc = None
if doc.FullName and doc.FullName.upper() == DWG_PATH.upper():
    target_doc = doc
    print(f"活动文档即目标文件: {doc.FullName}")
else:
    # 遍历所有文档
    docs_collection = acad.Documents
    for i in range(docs_collection.Count):
        d = docs_collection.Item(i)
        print(f"  文档{i}: {d.Name} -> {d.FullName}")
        if d.FullName and d.FullName.upper() == DWG_PATH.upper():
            target_doc = d
            break

if target_doc is None:
    print(f"错误: 找不到 {DWG_PATH}")
    pythoncom.CoUninitialize()
    exit(1)

doc = target_doc
print(f"使用文档: {doc.Name}")

# ---- 导出图片 ----
try:
    # 方法A: BMPOUT 命令
    doc.SendCommand(f'(command "._BMPOUT" "{OUTPUT_DIR}\\平面图_temp" "_ALL" "") ')
    print("BMPOUT命令已发送...")
    time.sleep(3)  # 等待命令完成
    
    bmp_file = os.path.join(OUTPUT_DIR, "平面图_temp.bmp")
    if os.path.exists(bmp_file) and os.path.getsize(bmp_file) > 0:
        from PIL import Image
        img = Image.open(bmp_file)
        img.save(OUTPUT_PNG, "PNG")
        print(f"BMPOUT成功! PNG: {OUTPUT_PNG} ({img.size[0]}x{img.size[1]})")
        os.remove(bmp_file)
    else:
        raise Exception("BMP文件未生成")
        
except Exception as e1:
    print(f"BMPOUT失败: {e1}")
    # 方法B: 用WMFOUT
    try:
        wmf_file = os.path.join(OUTPUT_DIR, "平面图_temp.wmf")
        doc.SendCommand(f'(command "._WMFOUT" "{wmf_file}" "_ALL" "") ')
        print("WMFOUT命令已发送...")
        time.sleep(3)
        if os.path.exists(wmf_file) and os.path.getsize(wmf_file) > 0:
            print(f"WMF导出成功: {wmf_file} ({os.path.getsize(wmf_file)} bytes)")
            # PIL can open WMF on Windows
            from PIL import Image
            img = Image.open(wmf_file)
            img.save(OUTPUT_PNG, "PNG")
            print(f"WMFOUT→PNG: {OUTPUT_PNG}")
            os.remove(wmf_file)
        else:
            raise Exception("WMF文件未生成")
    except Exception as e2:
        print(f"WMFOUT也失败: {e2}")

# ---- 详细提取空间数据 ----
print("\n" + "="*60)
print("详细空间数据提取")
print("="*60)

msp = doc.ModelSpace

# 收集所有数据
lines_data = []        # 所有直线（墙壁）
texts_data = []        # 文字标注
blocks_data = []       # 图块
arcs_data = []         # 圆弧
circles_data = []      # 圆
polylines_data = []    # 多段线

for i in range(msp.Count):
    entity = msp.Item(i)
    try:
        ename = ""
        try:
            ename = entity.EntityName
        except:
            try:
                ename = str(entity.ObjectName)
            except:
                continue
        
        layer = ""
        try:
            layer = entity.Layer
        except:
            pass
        
        if ename == 'AcDbLine':
            try:
                sp = entity.StartPoint
                ep = entity.EndPoint
                dx = ep[0] - sp[0]
                dy = ep[1] - sp[1]
                length = math.sqrt(dx*dx + dy*dy)
                lines_data.append({
                    "x1": sp[0], "y1": sp[1],
                    "x2": ep[0], "y2": ep[1],
                    "length": length,
                    "layer": layer,
                })
            except:
                pass
        
        elif ename == 'AcDbText':
            try:
                texts_data.append({
                    "text": str(entity.TextString),
                    "x": entity.InsertionPoint[0],
                    "y": entity.InsertionPoint[1],
                    "height": entity.Height if hasattr(entity, 'Height') else 0,
                    "layer": layer,
                })
            except:
                pass
        
        elif ename == 'AcDbMText':
            try:
                texts_data.append({
                    "text": str(entity.TextString),
                    "x": entity.InsertionPoint[0],
                    "y": entity.InsertionPoint[1],
                    "height": 0,
                    "layer": layer,
                    "mtext": True,
                })
            except:
                pass
        
        elif ename == 'AcDbArc':
            try:
                arcs_data.append({
                    "cx": entity.Center[0], "cy": entity.Center[1],
                    "radius": entity.Radius,
                    "start_angle": entity.StartAngle,
                    "end_angle": entity.EndAngle,
                    "layer": layer,
                })
            except:
                pass
        
        elif ename == 'AcDbCircle':
            try:
                circles_data.append({
                    "cx": entity.Center[0], "cy": entity.Center[1],
                    "radius": entity.Radius,
                    "layer": layer,
                })
            except:
                pass
        
        elif ename == 'AcDbBlockReference':
            try:
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
                    "x": entity.InsertionPoint[0],
                    "y": entity.InsertionPoint[1],
                    "layer": layer,
                })
            except:
                pass
        
        elif ename in ('AcDbPolyline', 'AcDb2dPolyline'):
            try:
                poly = {
                    "closed": entity.Closed,
                    "layer": layer,
                }
                try:
                    poly["area_mm2"] = entity.Area
                    poly["area_m2"] = round(entity.Area / 1000000, 2)
                except:
                    pass
                polylines_data.append(poly)
            except:
                pass
                
    except:
        continue

# 统计数据
print(f"\n实体统计:")
print(f"  直线(Lines): {len(lines_data)} 条")
print(f"  文字标注: {len(texts_data)} 条")
print(f"  图块: {len(blocks_data)} 个")
print(f"  圆弧: {len(arcs_data)} 个")
print(f"  圆: {len(circles_data)} 个")
print(f"  多段线: {len(polylines_data)} 个")

# 分析图层分布
layers = {}
for l in lines_data:
    layers[l['layer']] = layers.get(l['layer'], 0) + 1
print(f"\n直线图层分布:")
for layer, count in sorted(layers.items(), key=lambda x: -x[1])[:15]:
    print(f"  {layer}: {count}条")

# 计算图纸尺寸范围
if lines_data:
    xs = []
    ys = []
    for l in lines_data:
        xs.extend([l['x1'], l['x2']])
        ys.extend([l['y1'], l['y2']])
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    width_mm = max_x - min_x
    height_mm = max_y - min_y
    print(f"\n图纸范围(模型空间):")
    print(f"  X: {min_x:.0f} ~ {max_x:.0f} (宽度={width_mm:.0f}mm = {width_mm/1000:.1f}m)")
    print(f"  Y: {min_y:.0f} ~ {max_y:.0f} (高度={height_mm:.0f}mm = {height_mm/1000:.1f}m)")

# 输出所有文字标注
print(f"\n所有文字标注:")
for t in texts_data:
    mtag = "[MTEXT]" if t.get('mtext') else ""
    print(f"  \"{t['text']}\" @ ({t['x']:.0f}, {t['y']:.0f}) {mtag} [{t['layer']}]")

# 输出所有圆（可能是柱子）
if circles_data:
    print(f"\n圆(可能为柱子):")
    for c in circles_data:
        print(f"  圆心({c['cx']:.0f}, {c['cy']:.0f}) R={c['radius']:.0f}mm [{c['layer']}]")

# 输出图块中的门
door_blocks = [b for b in blocks_data if 'door' in b['name'].lower() or '门' in b['name'] or 'DEDFDF' in b['name']]
print(f"\n可能的门图块: {len(door_blocks)} 个")
if door_blocks:
    # DEDFDF probably is a door
    for db in door_blocks[:20]:
        print(f"  {db['name']} @ ({db['x']:.0f}, {db['y']:.0f}) [{db['layer']}]")

# 全部保存
data = {
    "file": DWG_PATH,
    "bounds": {"min_x": min_x, "max_x": max_x, "min_y": min_y, "max_y": max_y,
                "width_mm": width_mm, "height_mm": height_mm} if lines_data else {},
    "counts": {
        "lines": len(lines_data),
        "texts": len(texts_data),
        "blocks": len(blocks_data),
        "arcs": len(arcs_data),
        "circles": len(circles_data),
        "polylines": len(polylines_data),
    },
    "texts": texts_data,
    "circles": circles_data,
    "blocks_with_door_keyword": [b for b in blocks_data if any(kw in b['name'].lower() for kw in ['door','门','dedfdf','tuak','ch600'])],
    "blocks_summary": {},
}

# 图块名称统计
for b in blocks_data:
    name = b['name']
    data["blocks_summary"][name] = data["blocks_summary"].get(name, 0) + 1

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2, default=str)

print(f"\n完整数据已保存到: {OUTPUT_JSON}")

doc.Close(False)
pythoncom.CoUninitialize()
print("\n完成")
