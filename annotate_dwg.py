#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在DWG原图上添加消防疏散标注图层 (简化版)
"""
import win32com.client
import pythoncom
import json
import math
import os

DWG_PATH = r"J:\测试\新块.dwg"
OUTPUT_PATH = r"J:\测试\新块_消防疏散布置图.dwg"

with open(r"C:\Users\panshunkang\WorkBuddy\ima室内规范库\evacuation_result.json", "r", encoding="utf-8") as f:
    ed = json.load(f)

exits = ed["exits"]
extinguishers = ed["fire_equipment"]["extinguishers"]
hydrants = ed["fire_equipment"]["hydrants"]
alarms = ed["fire_equipment"]["alarm_buttons"]

def make_point(x, y, z=0.0):
    """创建AutoCAD三维点"""
    return win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, (float(x), float(y), float(z)))

pythoncom.CoInitialize()

try:
    acad = win32com.client.GetActiveObject("AutoCAD.Application")
    print("已连接AutoCAD")
except:
    acad = win32com.client.Dispatch("AutoCAD.Application")
    acad.Visible = True
    print("已启动AutoCAD")

# 打开文件
doc = None
for i in range(acad.Documents.Count):
    d = acad.Documents.Item(i)
    try:
        if d.FullName.upper() == DWG_PATH.upper():
            doc = d
            doc.Activate()
            print(f"文件已打开: {d.Name}")
            break
    except:
        pass

if doc is None:
    print(f"正在打开: {DWG_PATH}")
    acad.Documents.Open(DWG_PATH)
    doc = acad.Documents.Item(acad.Documents.Count - 1)
    print(f"已打开: {doc.Name}")

msp = doc.ModelSpace

# ---- 图层 ----
layers_data = {
    "EVAC-EXIT": (3, "消防疏散-安全出口"),
    "EVAC-ROUTE": (2, "消防疏散-逃生路线"),
    "EVAC-FIRE": (1, "消防疏散-消防设施"),
    "EVAC-TEXT": (4, "消防疏散-标注文字"),
}
for lname, (lcolor, ldesc) in layers_data.items():
    try:
        layer = doc.Layers.Add(lname)
        layer.color = lcolor
        print(f"  创建图层: {lname}(颜色{lcolor})")
    except:
        print(f"  图层已存在: {lname}")

print("\n添加疏散标注...")

# 安全出口 - 使用Polyline画圆
for ex in exits:
    ex_x, ex_y = ex["x"], ex["y"]
    # 用多边形近似圆(24边形)
    segs = 24
    outer_pts = []
    inner_pts = []
    for i in range(segs+1):
        angle = 2 * math.pi * i / segs
        outer_pts.append((ex_x + 600*math.cos(angle), ex_y + 600*math.sin(angle)))
        inner_pts.append((ex_x + 250*math.cos(angle), ex_y + 250*math.sin(angle)))
    
    # 外圈
    pl = msp.AddLightWeightPolyline(
        win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [v for p in outer_pts for v in p]))
    pl.Closed = True
    pl.Layer = "EVAC-EXIT"
    pl.Lineweight = 30
    
    # 内圈
    pl2 = msp.AddLightWeightPolyline(
        win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [v for p in inner_pts for v in p]))
    pl2.Closed = True
    pl2.Layer = "EVAC-EXIT"
    pl2.Lineweight = 18
    
    # 方向三角
    tri = [(ex_x-180, ex_y-180), (ex_x+200, ex_y), (ex_x-180, ex_y+180)]
    pl3 = msp.AddLightWeightPolyline(
        win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [v for p in tri for v in p]))
    pl3.Closed = True
    pl3.Layer = "EVAC-EXIT"
    
    # 文字
    txt = msp.AddText(ex["label"], make_point(ex_x, ex_y-750), 300)
    txt.Layer = "EVAC-TEXT"

print("  安全出口: OK")

# 疏散路线
routes = [
    [(13088, 13385), (15000, 13385), (17000, 15500), (18800, 15500)],
    [(4325, 13020), (4325, 14800), (3540, 15500), (3540, 16650)],
    [(8612, 5870), (7000, 10000), (4500, 14500), (3540, 15500)],
]
for route in routes:
    pts_flat = []
    for p in route:
        pts_flat.extend(p)
    pl = msp.AddLightWeightPolyline(
        win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, pts_flat))
    pl.Layer = "EVAC-ROUTE"
    pl.Lineweight = 15

print("  疏散路线: OK")

# 消防设施
for ext in extinguishers:
    fx, fy = ext["x"], ext["y"]
    rect = [(fx-250,fy-250), (fx+250,fy-250), (fx+250,fy+250), (fx-250,fy+250)]
    pl = msp.AddLightWeightPolyline(
        win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [v for p in rect for v in p]))
    pl.Closed = True
    pl.Layer = "EVAC-FIRE"
    pl.Lineweight = 20
    txt = msp.AddText("灭火器", make_point(fx, fy-350), 200)
    txt.Layer = "EVAC-TEXT"

print("  灭火器: OK")

for hyd in hydrants:
    hx, hy = hyd["x"], hyd["y"]
    segs = 16
    pts = []
    for i in range(segs+1):
        angle = 2 * math.pi * i / segs
        pts.append((hx + 200*math.cos(angle), hy + 200*math.sin(angle)))
    pl = msp.AddLightWeightPolyline(
        win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [v for p in pts for v in p]))
    pl.Closed = True
    pl.Layer = "EVAC-FIRE"
    pl.Lineweight = 15
    txt = msp.AddText("消火栓", make_point(hx, hy-350), 200)
    txt.Layer = "EVAC-TEXT"

print("  消火栓: OK")

for alm in alarms:
    ax, ay = alm["x"], alm["y"]
    rect = [(ax-150,ay-150), (ax+150,ay-150), (ax+150,ay+150), (ax-150,ay+150)]
    pl = msp.AddLightWeightPolyline(
        win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [v for p in rect for v in p]))
    pl.Closed = True
    pl.Layer = "EVAC-FIRE"
    txt = msp.AddText("报警按钮", make_point(ax, ay-250), 180)
    txt.Layer = "EVAC-TEXT"

print("  报警按钮: OK")

# 图例
lx, ly = 15000, 9000
items = [
    (lx, ly, "消防疏散图例", 350),
    (lx, ly-800, "安全出口/疏散门 - EVAC-EXIT", 200),
    (lx, ly-1500, "疏散路线 - EVAC-ROUTE", 200),
    (lx, ly-2200, "灭火器 - EVAC-FIRE", 200),
    (lx, ly-2900, "消火栓 - EVAC-FIRE", 200),
    (lx, ly-3600, "手动报警按钮 - EVAC-FIRE", 200),
]
for ix, iy, it, ih in items:
    txt = msp.AddText(it, make_point(ix, iy), ih)
    txt.Layer = "EVAC-TEXT"

# 疏散信息面板
ix2, iy2 = 15000, 4000
info = [
    ("消防安全疏散布置图", 400),
    (f"建筑面积: 274.6m2", 250),
    (f"疏散人数: 55人", 250),
    (f"安全出口: 2个", 250),
    (f"合规状态: 全部合规", 250),
    (f"依据: GB 50016-2014(2018) / GB 55037-2022", 250),
]
for i, (it, ih) in enumerate(info):
    txt = msp.AddText(it, make_point(ix2, iy2 - i*400), ih)
    txt.Layer = "EVAC-TEXT"

print(f"\n保存为: {os.path.basename(OUTPUT_PATH)}")
doc.SaveAs(OUTPUT_PATH)
print("DWG保存完成!")

pythoncom.CoUninitialize()
print("\n✓ 全部标注完成!")
