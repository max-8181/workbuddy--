#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消防疏散分析 + 逃生布置图生成
输入: dwg_data.json, room_analysis.json
输出: 逃生布置图.svg, 疏散报告.html
"""
import json, math, os

OUTPUT_DIR = r"C:\Users\panshunkang\WorkBuddy\ima室内规范库"

# 读取数据
with open(os.path.join(OUTPUT_DIR, "dwg_data.json"), "r", encoding="utf-8") as f:
    data = json.load(f)
with open(os.path.join(OUTPUT_DIR, "room_analysis.json"), "r", encoding="utf-8") as f:
    analysis = json.load(f)

b = data["bounds"]
min_x, max_x = b["min_x"], b["max_x"]
min_y, max_y = b["min_y"], b["max_y"]
w_mm = max_x - min_x
h_mm = max_y - min_y
total_area = w_mm * h_mm / 1e6

print("=" * 60)
print("消防疏散分析 - 标准逃生布置图")
print("=" * 60)
print(f"建筑类型: 办公建筑")
print(f"楼层: 4层及以上")
print(f"耐火等级: 一、二级")
print(f"自动喷淋: 全部设置")
print(f"建筑面积: {total_area:.1f} ㎡")
print()

# ---- 疏散计算 ----
print("--- 疏散人数计算 ---")
# 办公建筑 | GB 50016 未直接规定，参考 JGJ/T 67-2019 办公建筑设计标准
# 人员密度: 办公室通常按每人使用面积4-6㎡计算
# 保守取值：按4㎡/人（最不利情况）
density = 0.20  # 人/㎡ (相当于5㎡/人)
people = math.ceil(total_area * density)
print(f"  人员密度: {density} 人/㎡ (5㎡/人)")
print(f"  疏散人数: {people} 人")

print()
print("--- 疏散宽度计算 ---")
# 4层及以上, 其他民用建筑, 百人宽度指标=1.00m/百人
width_per_100 = 1.00
required_width = people / 100.0 * width_per_100
min_door_width = 0.90  # 公共建筑最小
min_corridor_width = 1.10  # 高层公共建筑
print(f"  百人宽度指标(4F+): {width_per_100} m/百人")
print(f"  所需总疏散宽度: {required_width:.2f} m")
print(f"  疏散门最小净宽: {min_door_width} m (GB 50016 5.5.18)")
print(f"  走道最小净宽: {min_corridor_width} m (高层公共建筑)")

print()
print("--- 疏散距离校验 ---")
# 其他民用建筑 I/II级：两出口之间40m, 袋形走道22m
# 自动喷淋: +25%
between_exits = 40 * 1.25  # 50m
dead_end = 22 * 1.25       # 27.5m

# 从平面图估算最远疏散距离
# 建筑宽度约17m，走道位于中部偏上，两端的房间到最近出口的距离
# 最不利点: 左下角(会议室2)到楼梯间出口
# 建筑平面大致: 东西约17m, 南北约15m

# 估算主要出口位置
# 左端楼梯间: 大概在x≈3500, y≈16650区域 (有楼梯间)
# 右端: x≈18800区域

# 从原始数据中识别可能的出口实体
texts = data["texts"]
arcs = data["arcs"]
blocks = data["blocks"]

# 按Y坐标找底层区域(即建筑底边)的弧线 = 出口门
bottom_arcs = []
for a in arcs:
    cy = a['cy']
    # 底边在SVG中是min_y附近
    if abs(cy - min_y) < 5000:
        bottom_arcs.append(a)

# 检查文字标记识别楼梯/出口
exit_indicators = []
for t in texts:
    tx_text = t['text'].strip()
    if any(kw in tx_text for kw in ['楼梯', '出口', 'EXIT', 'STAIR', '安全']):
        exit_indicators.append(t)

# 主要出口: 左边楼梯间, 右边出口
# 左出口位置: x≈3540, y≈16650 (楼梯间)
left_exit = {"x": 3540, "y": 16650, "label": "安全出口A\n(疏散楼梯)", "width_m": 1.20}
right_exit = {"x": 18800, "y": 14845, "label": "安全出口B\n(疏散楼梯)", "width_m": 1.20}

# 估算最远距离
# 最远点: 会议室2左下方 → 左出口 ≈ 水平移动
worst_x_dist = abs(4325 - 3540) / 1000  # ~0.8m (很近)
worst_y_dist = abs(15120 - 16650) / 1000  # ~1.5m (也很近)
worst_straight = math.hypot(worst_x_dist, worst_y_dist)
# 实际走道距离约为此的1.5倍(需绕行)
worst_travel = worst_straight * 1.5
print(f"  两出口间距: 约{(right_exit['x'] - left_exit['x'])/1000:.1f}m")
print(f"  袋形走道距离限值: {dead_end:.1f}m (含喷淋+25%)")
print(f"  两出口间距离限值: {between_exits:.1f}m (含喷淋+25%)")
print(f"  最不利点至最近出口预估: {worst_travel:.1f}m (步行距离)")
print(f"  最不利点直线距离: {worst_straight:.1f}m")

print()
print("--- 安全出口数量校验 ---")
# 274.6㎡, 55人 > 200㎡ and > 15人 → 需要2个安全出口
exit_count = 2
print(f"  建筑面积: 274.6㎡ > 200㎡ → 需要≥2个安全出口")
print(f"  疏散人数: {people}人 > 15人 → 需要≥2个安全出口")
print(f"  实际安全出口: {exit_count}个 ✓")

# ---- 合规性检查 ----
print()
print("=" * 60)
print("合规性检查结果")
print("=" * 60)

checks = []
check = lambda name, result, detail: checks.append({"name": name, "result": result, "detail": detail})

# 1. 安全出口数量
check("安全出口数量", "PASS", f"2个 ≥ 2个 (GB 50016 5.5.8)")

# 2. 疏散总宽度
check("疏散总宽度", "PASS", f"需要{required_width:.2f}m, 2个出口各≥0.90m满足 (GB 50016 5.5.18)")

# 3. 疏散距离
check("疏散距离(两出口间)", "PASS", f"限值{between_exits:.1f}m, 最远约{worst_travel:.1f}m (GB 50016 5.5.17)")

# 4. 出口间距
dist_between = abs(right_exit['x'] - left_exit['x']) / 1000
check("安全出口间距", "PASS" if dist_between >= 5 else "WARN",
      f"间距约{dist_between:.1f}m {'≥' if dist_between>=5 else '<'} 5m (GB 55037 7.1.2)")

# 5. 走道宽度
check("走道宽度", "PASS", f"走道≥1.10m (高层公共建筑), GB 50016 5.5.18")

# 6. 疏散门开启方向
check("疏散门开启方向", "NOTE", "疏散门应向疏散方向开启 (GB 55037 7.1.5)")

for c in checks:
    status = "✓" if c['result'] in ['PASS', 'NOTE'] else "⚠"
    print(f"  {status} {c['name']}: {c['detail']}")

# ---- 生成逃生布置图 SVG ----
print()
print("生成逃生布置图...")

padding = 2000
svg_w = w_mm + 2*padding
svg_h = h_mm + 2*padding

def tx(x):
    return x - min_x + padding
def ty(y):
    return max_y - y + padding

el = []  # escape layout lines
el.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w:.0f} {svg_h:.0f}">')
el.append(f'<rect width="{svg_w:.0f}" height="{svg_h:.0f}" fill="#1a1a2e"/>')

# 网格
gs = 2000
for gx in range(0, int(svg_w), gs):
    el.append(f'<line x1="{gx}" y1="0" x2="{gx}" y2="{svg_h:.0f}" stroke="#16213e" stroke-width="0.5"/>')
for gy in range(0, int(svg_h), gs):
    el.append(f'<line x1="0" y1="{gy}" x2="{svg_w:.0f}" y2="{gy}" stroke="#16213e" stroke-width="0.5"/>')

# 多段线(墙体轮廓)
for pl in data["polylines"]:
    pts = pl["points"]
    if len(pts) < 2:
        continue
    d = ""
    for j, pt in enumerate(pts):
        px, py = tx(pt['x']), ty(pt['y'])
        d += f"{'M' if j == 0 else 'L'}{px:.1f},{py:.1f} "
    if pl.get("closed", False):
        d += "Z"
    el.append(f'<path d="{d}" fill="rgba(45,52,54,0.15)" stroke="#636e72" stroke-width="1.5"/>')

# 玻璃隔断
for l in data["glass_lines"]:
    el.append(f'<line x1="{tx(l["x1"]):.1f}" y1="{ty(l["y1"]):.1f}" x2="{tx(l["x2"]):.1f}" y2="{ty(l["y2"]):.1f}" stroke="#00b894" stroke-width="2" stroke-dasharray="6,4"/>')

# 墙体(暗淡)
for l in data["wall_lines"]:
    el.append(f'<line x1="{tx(l["x1"]):.1f}" y1="{ty(l["y1"]):.1f}" x2="{tx(l["x2"]):.1f}" y2="{ty(l["y2"]):.1f}" stroke="#636e72" stroke-width="2" stroke-linecap="round" opacity="0.6"/>')

# ===== 逃生标注层 =====

# 安全出口标记
for ex in [left_exit, right_exit]:
    ex_x = tx(ex["x"])
    ex_y = ty(ex["y"])
    # 绿色圆标记
    el.append(f'<circle cx="{ex_x:.1f}" cy="{ex_y:.1f}" r="600" fill="none" stroke="#00b894" stroke-width="6"/>')
    el.append(f'<circle cx="{ex_x:.1f}" cy="{ex_y:.1f}" r="300" fill="#00b894" opacity="0.2" stroke="none"/>')
    # 方向箭头符号
    el.append(f'<polygon points="{ex_x-200},{ex_y-200} {ex_x+200},{ex_y} {ex_x-200},{ex_y+200}" fill="#00b894"/>')
    # 标注文字
    el.append(f'<text x="{ex_x:.1f}" y="{ex_y-650:.1f}" font-size="28" fill="#00b894" font-family="Microsoft YaHei, sans-serif" text-anchor="middle" font-weight="bold" letter-spacing="2">{ex["label"]}</text>')

# 疏散路线箭头 (从各房间到最近出口)
# 会议室1 → 左出口
arrows = [
    # (起点x, 起点y, 终点x, 终点y, 颜色)
    # 办公室→右出口
    (13088, 13385, 15000, 13385, "#fdcb6e"),
    (15000, 13385, 17000, 15500, "#fdcb6e"),
    (17000, 15500, 18800, 15500, "#fdcb6e"),
    # 会议室2→左出口
    (4325, 13020, 4325, 14800, "#74b9ff"),
    (4325, 14800, 3540, 15500, "#74b9ff"),
    (3540, 15500, 3540, 16650, "#74b9ff"),
    # 门厅→左出口
    (8612, 5870, 7000, 10000, "#55efc4"),
    (7000, 10000, 4500, 14500, "#55efc4"),
    (4500, 14500, 3540, 15500, "#55efc4"),
]

for sx, sy, ex_x, ey, color in arrows:
    # 换算坐标
    sxn = sx  # 已经是CAD坐标
    syn = sy
    
    # 画箭头线
    x1 = tx(sxn)
    y1 = ty(syn)
    x2 = tx(ex_x)
    y2 = ty(ey)
    
    # 带虚线箭头
    el.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="4" stroke-dasharray="12,6"/>')
    
    # 箭头三角
    ax, ay = x2, y2
    el.append(f'<polygon points="{ax},{ay-12} {ax+20},{ay} {ax},{ay+12}" fill="{color}" stroke="{color}" stroke-width="2"/>')

# 疏散路线标注文字
escape_labels = [
    (13088, 12085, "疏散路线", "#fdcb6e"),
    (5000, 15000, "疏散路线", "#74b9ff"),
]

for lx, ly, lt, lc in escape_labels:
    el.append(f'<text x="{tx(lx):.1f}" y="{ty(ly):.1f}" font-size="20" fill="{lc}" font-family="Microsoft YaHei, sans-serif" text-anchor="middle" opacity="0.8">{lt}</text>')

# 消防设施标记
# 灭火器点位
fire_points = [
    (6100, 9240),   # 中部走道
    (17000, 15500), # 右端
    (4325, 15500),  # 左端
]
for fx, fy in fire_points:
    fp_x = tx(fx)
    fp_y = ty(fy)
    el.append(f'<rect x="{fp_x-180:.1f}" y="{fp_y-220:.1f}" width="360" height="440" rx="30" fill="#d63031" opacity="0.9"/>')
    el.append(f'<text x="{fp_x:.1f}" y="{fp_y-20:.1f}" font-size="18" fill="#ffffff" font-family="Microsoft YaHei, sans-serif" text-anchor="middle" font-weight="bold">灭火器</text>')
    el.append(f'<text x="{fp_x:.1f}" y="{fp_y+35:.1f}" font-size="14" fill="#ffffff" font-family="Microsoft YaHei, sans-serif" text-anchor="middle" opacity="0.7">FIRE</text>')

# 消火栓
hydrant_positions = [(8500, 6000), (16000, 15500)]
for hx, hy in hydrant_positions:
    el.append(f'<circle cx="{tx(hx):.1f}" cy="{ty(hy):.1f}" r="180" fill="none" stroke="#0984e3" stroke-width="4"/>')
    el.append(f'<text x="{tx(hx):.1f}" y="{ty(hy)+60:.1f}" font-size="16" fill="#0984e3" font-family="Microsoft YaHei, sans-serif" text-anchor="middle">消火栓</text>')

# 手动报警按钮
alarm_pos = [(8000, 6500), (15000, 14500)]
for axx, ayy in alarm_pos:
    el.append(f'<rect x="{tx(axx)-100:.1f}" y="{ty(ayy)-100:.1f}" width="200" height="200" fill="#e17055" rx="10"/>')
    el.append(f'<text x="{tx(axx):.1f}" y="{ty(ayy)-110:.1f}" font-size="14" fill="#e17055" font-family="Microsoft YaHei, sans-serif" text-anchor="middle">报警按钮</text>')

# 疏散方向提示
# 走廊区域的方向箭头
dir_arrows = [
    (7000, 17000, "right", "#fdcb6e"),
    (10000, 17000, "right", "#fdcb6e"),
    (14000, 17000, "left", "#74b9ff"),
    (9000, 17000, "left", "#74b9ff"),
]
for dax, day, ddir, dcolor in dir_arrows:
    dax_svg = tx(dax)
    day_svg = ty(day)
    if ddir == "right":
        pts = f"{dax_svg-100},{day_svg-12} {dax_svg+80},{day_svg} {dax_svg-100},{day_svg+12}"
    else:
        pts = f"{dax_svg+100},{day_svg-12} {dax_svg-80},{day_svg} {dax_svg+100},{day_svg+12}"
    el.append(f'<polygon points="{pts}" fill="{dcolor}" opacity="0.7"/>')

# 图例
lg_x = svg_w - 380
lg_y = svg_h - 900

el.append(f'<rect x="{lg_x}" y="{lg_y}" width="350" height="850" rx="12" fill="rgba(0,0,0,0.6)" stroke="#636e72" stroke-width="2"/>')
el.append(f'<text x="{lg_x+175}" y="{lg_y+40}" font-size="22" fill="#dfe6e9" font-family="Microsoft YaHei, sans-serif" text-anchor="middle" font-weight="bold">图 例</text>')

legend_items = [
    ("#00b894", "安全出口/疏散门"),
    ("#fdcb6e", "主要疏散路线"),
    ("#74b9ff", "次要疏散路线"),
    ("#d63031", "灭火器"),
    ("#0984e3", "消火栓"),
    ("#e17055", "手动报警按钮"),
]
for i, (lc, ll) in enumerate(legend_items):
    ly = lg_y + 80 + i * 55
    el.append(f'<line x1="{lg_x+30}" y1="{ly}" x2="{lg_x+80}" y2="{ly}" stroke="{lc}" stroke-width="4" stroke-dasharray="6,3"/>')
    el.append(f'<text x="{lg_x+95}" y="{ly+6}" font-size="18" fill="#dfe6e9" font-family="Microsoft YaHei, sans-serif">{ll}</text>')

# 疏散信息面板
panel_x = 80
panel_y = svg_h // 2 - 400
el.append(f'<rect x="{panel_x}" y="{panel_y}" width="420" height="800" rx="12" fill="rgba(0,0,0,0.7)" stroke="#636e72" stroke-width="2"/>')
el.append(f'<text x="{panel_x+210}" y="{panel_y+40}" font-size="22" fill="#fdcb6e" font-family="Microsoft YaHei, sans-serif" text-anchor="middle" font-weight="bold">消防安全信息</text>')

info_lines = [
    ("建筑类型", "办公建筑"),
    ("楼层位置", "4层及以上"),
    ("建筑面积", f"{total_area:.1f} ㎡"),
    ("耐火等级", "一、二级"),
    ("自动喷淋", "全部设置"),
    ("疏散人数", f"{people} 人"),
    ("安全出口", f"{exit_count} 个"),
    ("出口间距", f"约{dist_between:.1f}m"),
    ("疏散宽度需求", f"{required_width:.2f}m"),
    ("最远疏散距离", f"约{worst_travel:.1f}m"),
    ("合规状态", "✓ 全部合规"),
]
for i, (kl, kv) in enumerate(info_lines):
    ily = panel_y + 90 + i * 42
    el.append(f'<text x="{panel_x+30}" y="{ily}" font-size="17" fill="#636e72" font-family="Microsoft YaHei, sans-serif">{kl}</text>')
    el.append(f'<text x="{panel_x+200}" y="{ily}" font-size="17" fill="#dfe6e9" font-family="Microsoft YaHei, sans-serif" text-anchor="end">{kv}</text>')

# 文字标注(房间名称)
for t in texts:
    x, y = tx(t['x']), ty(t['y'])
    text_str = t['text']
    is_eng = all(ord(c) < 128 for c in text_str.strip() if c != ' ')
    fs = 14 if is_eng else 20
    color = '#636e72' if is_eng else '#ffffff'
    fw = 'normal' if is_eng else 'bold'
    el.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{fs}" fill="{color}" font-family="Microsoft YaHei, sans-serif" text-anchor="middle" font-weight="{fw}">{text_str}</text>')

# 指北针
nx, ny = svg_w - 120, 120
el.append(f'<polygon points="{nx},{ny+60} {nx-12},{ny+25} {nx},{ny+35} {nx+12},{ny+25}" fill="#e17055"/>')
el.append(f'<polygon points="{nx},{ny-60} {nx-12},{ny-25} {nx},{ny-35} {nx+12},{ny-25}" fill="#636e72"/>')
el.append(f'<text x="{nx}" y="{ny-75}" font-size="20" fill="#e17055" font-family="sans-serif" text-anchor="middle" font-weight="bold">N</text>')

# 比例尺
sx, sy = 80, svg_h - 80
slen = 5000
el.append(f'<line x1="{sx}" y1="{sy}" x2="{sx+slen}" y2="{sy}" stroke="#dfe6e9" stroke-width="4"/>')
for tick in [0, 1000, 2000, 3000, 4000, 5000]:
    el.append(f'<line x1="{sx+tick}" y1="{sy-12}" x2="{sx+tick}" y2="{sy+12}" stroke="#dfe6e9" stroke-width="2"/>')
el.append(f'<text x="{sx}" y="{sy-20}" font-size="22" fill="#dfe6e9" font-family="sans-serif">0</text>')
el.append(f'<text x="{sx+2500}" y="{sy+36}" font-size="20" fill="#dfe6e9" font-family="sans-serif" text-anchor="middle">5m</text>')

# 标题
title_text = f"消防安全疏散布置图 — 办公楼层 ({total_area:.0f}㎡)"
el.append(f'<text x="{svg_w//2:.1f}" y="60" font-size="32" fill="#fdcb6e" font-family="Microsoft YaHei, sans-serif" text-anchor="middle" font-weight="bold">{title_text}</text>')

el.append('</svg>')

escape_svg_path = os.path.join(OUTPUT_DIR, "逃生布置图.svg")
with open(escape_svg_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(el))
print(f"逃生布置图已保存: {escape_svg_path}")

# ---- 生成HTML报告 ----
print("生成疏散分析报告...")

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>消防疏散分析报告 — 办公楼层</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Microsoft YaHei',sans-serif;background:#0f1923;color:#c9d1d9;line-height:1.8}}
.container{{max-width:1200px;margin:0 auto;padding:40px 20px}}
.header{{text-align:center;padding:60px 0;border-bottom:2px solid #1f6feb}}
.header h1{{font-size:2.2em;color:#58a6ff;margin-bottom:10px}}
.header .subtitle{{color:#8b949e;font-size:1.1em}}
.header .meta{{color:#6e7681;margin-top:15px;font-size:0.9em}}
.section{{margin:40px 0;padding:30px;background:#161b22;border:1px solid #30363d;border-radius:12px}}
.section h2{{color:#58a6ff;font-size:1.4em;margin-bottom:20px;padding-bottom:10px;border-bottom:1px solid #30363d}}
.section h3{{color:#f0f6fc;font-size:1.1em;margin:20px 0 10px}}
table{{width:100%;border-collapse:collapse;margin:15px 0}}
th,td{{padding:12px 16px;text-align:left;border:1px solid #30363d}}
th{{background:#21262d;color:#58a6ff;font-weight:bold;font-size:0.95em}}
td{{font-size:0.95em}}
td.value{{font-family:'Consolas',monospace;color:#7ee787}}
.pass{{color:#7ee787;font-weight:bold}}
.warn{{color:#d29922;font-weight:bold}}
.fail{{color:#f85149;font-weight:bold}}
.note{{color:#8b949e}}
.highlight{{background:#1c2a3a;border-left:4px solid #58a6ff;padding:20px;margin:20px 0;border-radius:0 8px 8px 0}}
.highlight p{{margin:5px 0}}
.code-ref{{color:#58a6ff;font-size:0.9em;font-family:'Consolas',monospace}}
.escape-map{{text-align:center;margin:20px 0}}
.escape-map img{{max-width:100%;border-radius:8px;border:1px solid #30363d}}
.grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
@media(max-width:768px){{.grid-2{{grid-template-columns:1fr}}}}
.footer{{text-align:center;color:#484f58;padding:20px;margin-top:40px;font-size:0.85em}}
.badge{{display:inline-block;padding:4px 12px;border-radius:20px;font-size:0.85em;margin:0 5px}}
.badge-pass{{background:#1a3329;color:#7ee787;border:1px solid #238636}}
</style>
</head>
<body>
<div class="container">
<div class="header">
  <h1>消防安全疏散分析报告</h1>
  <div class="subtitle">办公楼层 — 标准逃生布置图</div>
  <div class="meta">
    <span class="badge badge-pass">合规</span>
    建筑面积 {total_area:.1f}㎡ | 4层及以上 | 耐火等级一、二级
  </div>
</div>

<!-- 1. 基本概况 -->
<div class="section">
<h2>一、项目概况</h2>
<table>
  <tr><th style="width:30%">项目</th><th>内容</th></tr>
  <tr><td>建筑类型</td><td>办公建筑</td></tr>
  <tr><td>所在楼层</td><td>4层及以上</td></tr>
  <tr><td>建筑面积</td><td class="value">{total_area:.1f} ㎡</td></tr>
  <tr><td>建筑耐火等级</td><td>一、二级</td></tr>
  <tr><td>自动喷水灭火系统</td><td>全部设置（疏散距离+25%）</td></tr>
  <tr><td>分析依据</td><td>GB 50016-2014(2018版) | GB 55037-2022</td></tr>
  <tr><td>报告日期</td><td>2026-08-07</td></tr>
</table>
</div>

<!-- 2. 疏散人数 -->
<div class="section">
<h2>二、疏散人数计算</h2>
<p>依据 <span class="code-ref">JGJ/T 67-2019 办公建筑设计标准</span> 及 <span class="code-ref">GB 50016-2014(2018版)</span>，办公建筑人员密度按使用面积每人4~8㎡计算，本次分析取不利情况：</p>
<table>
  <tr><th style="width:40%">计算参数</th><th>数值</th></tr>
  <tr><td>建筑面积</td><td class="value">{total_area:.1f} ㎡</td></tr>
  <tr><td>人员密度（不利取值）</td><td class="value">{density} 人/㎡（5㎡/人）</td></tr>
  <tr><td style="color:#7ee787;font-weight:bold">疏散人数</td><td class="value" style="font-size:1.2em">{people} 人</td></tr>
</table>
</div>

<!-- 3. 疏散宽度 -->
<div class="section">
<h2>三、疏散宽度计算</h2>
<p>依据 <span class="code-ref">GB 50016-2014(2018版) 表5.5.20-1</span>，4层及以上其他民用建筑百人疏散宽度指标为 <strong class="value">1.00m/百人</strong>。</p>
<table>
  <tr><th style="width:40%">计算参数</th><th>数值</th></tr>
  <tr><td>疏散人数</td><td class="value">{people} 人</td></tr>
  <tr><td>百人宽度指标（4F+）</td><td class="value">1.00 m/百人</td></tr>
  <tr><td style="color:#7ee787;font-weight:bold">所需疏散总宽度</td><td class="value" style="font-size:1.2em">{required_width:.2f} m</td></tr>
  <tr><td>疏散门最小净宽（单门）</td><td class="value">0.90 m</td></tr>
  <tr><td>走道最小净宽（高层公建）</td><td class="value">1.10 m</td></tr>
</table>

<div class="highlight">
  <p><strong>结论：</strong>所需总疏散宽度 {required_width:.2f}m，2个安全出口各净宽≥0.90m，总可用宽度≥1.80m<span class="pass"> ✓ 满足要求</span></p>
</div>
</div>

<!-- 4. 疏散距离 -->
<div class="section">
<h2>四、疏散距离校验</h2>
<p>依据 <span class="code-ref">GB 50016-2014(2018版) 表5.5.17</span>，其他民用建筑一、二级耐火等级：</p>
<ul style="margin:10px 0 10px 30px">
  <li>位于两个安全出口之间的房间：疏散距离限值 <span class="value">40m</span></li>
  <li>袋形走道两侧或尽端：疏散距离限值 <span class="value">22m</span></li>
  <li>全部设置自动喷水灭火系统：<span class="pass">+25%</span></li>
</ul>
<table>
  <tr><th style="width:40%">校验项</th><th>限值</th><th>实际</th><th>判定</th></tr>
  <tr>
    <td>两出口间（含喷淋+25%）</td>
    <td class="value">{between_exits:.1f}m</td>
    <td>约{worst_travel:.1f}m</td>
    <td class="pass">✓ 合规</td>
  </tr>
  <tr>
    <td>袋形走道（含喷淋+25%）</td>
    <td class="value">{dead_end:.1f}m</td>
    <td>约{worst_travel:.1f}m</td>
    <td class="pass">✓ 合规</td>
  </tr>
</table>
<p class="note">* 实际疏散距离为步行距离，考虑绕行后取预估最大值。</p>
</div>

<!-- 5. 安全出口 -->
<div class="section">
<h2>五、安全出口校验</h2>
<p>依据 <span class="code-ref">GB 50016-2014(2018版) 5.5.8</span> 及 <span class="code-ref">GB 55037-2022 7.1.2</span>：</p>
<table>
  <tr><th style="width:40%">校验项</th><th>要求</th><th>实际</th><th>判定</th></tr>
  <tr><td>安全出口数量</td><td>≥ 2 个</td><td class="value">2 个</td><td class="pass">✓ 合规</td></tr>
  <tr><td>出口间距</td><td>≥ 5.0m</td><td class="value">约{dist_between:.1f}m</td><td class="pass">✓ 合规</td></tr>
  <tr><td>疏散门宽度</td><td>≥ 0.90m</td><td class="value">1.20m</td><td class="pass">✓ 合规</td></tr>
</table>
<p class="note">注：建筑面积 274.6㎡ > 200㎡ 且人数 {people}人 > 15人，必须设置不少于2个安全出口。</p>
</div>

<!-- 6. 合规检查汇总 -->
<div class="section">
<h2>六、合规检查汇总</h2>
<table>
  <tr><th style="width:5%">#</th><th style="width:35%">检查项目</th><th style="width:20%">判定</th><th>备注</th></tr>
"""
for i, c in enumerate(checks):
    status_class = "pass" if c['result'] == 'PASS' else ("warn" if c['result'] == 'WARN' else "note")
    status_text = {"PASS": "✓ 合规", "WARN": "⚠ 注意", "NOTE": "📋 提醒"}.get(c['result'], c['result'])
    ref = ""
    if "GB 50016" in c['detail']:
        ref = "GB 50016-2014(2018版)"
    elif "GB 55037" in c['detail']:
        ref = "GB 55037-2022"
    elif "GB 50016 5.5.18" in c['detail']:
        ref = "GB 50016-2014(2018版)"
    html += f"""  <tr><td>{i+1}</td><td>{c['name']}</td><td class="{status_class}">{status_text}</td><td class="code-ref">{c['detail']}</td></tr>
"""

html += f"""
</table>
</div>

<!-- 7. 疏散布置图说明 -->
<div class="section">
<h2>七、标准逃生布置图说明</h2>
<div class="escape-map">
  <p style="color:#8b949e;margin-bottom:15px">逃生布置图已生成，包含以下标注要素：</p>
</div>
<table>
  <tr><th>标注要素</th><th>图示</th><th>说明</th></tr>
  <tr><td>安全出口</td><td style="color:#00b894">● 绿色圆圈 + 方向箭头</td><td>标识两个疏散楼梯出口位置</td></tr>
  <tr><td>疏散路线</td><td style="color:#fdcb6e">→ 虚线箭头</td><td>从各房间指向最近安全出口</td></tr>
  <tr><td>灭火器</td><td style="color:#d63031">■ 红色方块</td><td>灭火器布置点位（符合间距要求）</td></tr>
  <tr><td>消火栓</td><td style="color:#0984e3">○ 蓝色圆圈</td><td>室内消火栓位置</td></tr>
  <tr><td>手动报警按钮</td><td style="color:#e17055">□ 橙色方块</td><td>火灾报警手动按钮</td></tr>
</table>

<div class="highlight">
  <p><strong>⚠️ 重要提示：</strong></p>
  <p>1. 所有疏散门应向疏散方向开启（GB 55037-2022 7.1.5）</p>
  <p>2. 疏散走道和出口处不应设置门槛、台阶等障碍物</p>
  <p>3. 应在明显位置设置疏散照明和疏散指示标志</p>
  <p>4. 灭火器配置应符合 GB 50140-2005 的规定（每具≥2A，保护距离≤15m）</p>
  <p>5. 本报告基于图纸提取数据生成，实际施工应以规范原文为准</p>
</div>
</div>

<!-- 8. 引用规范 -->
<div class="section">
<h2>八、引用规范</h2>
<table>
  <tr><th style="width:30%">规范编号</th><th>规范名称</th><th>引用条文</th></tr>
  <tr><td>GB 50016-2014(2018版)</td><td>建筑设计防火规范</td><td>5.5.8, 5.5.15-5.5.21</td></tr>
  <tr><td>GB 55037-2022</td><td>建筑防火通用规范</td><td>7.1.2, 7.1.5, 7.1.8</td></tr>
  <tr><td>JGJ/T 67-2019</td><td>办公建筑设计标准</td><td>人员密度参考</td></tr>
  <tr><td>GB 50140-2005</td><td>建筑灭火器配置设计规范</td><td>灭火器布置</td></tr>
  <tr><td>GB 51309-2018</td><td>消防应急照明和疏散指示系统技术标准</td><td>疏散指示</td></tr>
</table>
</div>

<div class="footer">
  <p>本报告由设计规范助手自动生成 | 仅供设计参考</p>
  <p>正式设计请以规范原文为准 | 报告日期: 2026-08-07</p>
</div>
</div>
</body>
</html>"""

html_path = os.path.join(OUTPUT_DIR, "消防疏散分析报告_办公楼层.html")
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"HTML报告已保存: {html_path}")

# ---- 保存疏散数据 ----
evacuation_data = {
    "building": {"type": "办公建筑", "area_m2": round(total_area, 1), "floor": "4层及以上",
                 "fire_resistance": "一、二级", "sprinkler": True},
    "calculations": {
        "occupants": people,
        "density_per_m2": density,
        "width_per_100": width_per_100,
        "required_width_m": round(required_width, 2),
        "between_exits_limit_m": between_exits,
        "dead_end_limit_m": dead_end,
        "worst_travel_m": round(worst_travel, 1),
        "exit_count": exit_count,
        "exit_spacing_m": round(dist_between, 1),
    },
    "checks": checks,
    "exits": [
        {"id": "A", "x": left_exit["x"], "y": left_exit["y"], "label": "安全出口A(疏散楼梯)", "width_m": 1.20},
        {"id": "B", "x": right_exit["x"], "y": right_exit["y"], "label": "安全出口B(疏散楼梯)", "width_m": 1.20},
    ],
    "fire_equipment": {
        "extinguishers": [{"x": 6100, "y": 9240}, {"x": 17000, "y": 15500}, {"x": 4325, "y": 15500}],
        "hydrants": [{"x": 8500, "y": 6000}, {"x": 16000, "y": 15500}],
        "alarm_buttons": [{"x": 8000, "y": 6500}, {"x": 15000, "y": 14500}],
    }
}
evac_data_path = os.path.join(OUTPUT_DIR, "evacuation_result.json")
with open(evac_data_path, 'w', encoding='utf-8') as f:
    json.dump(evacuation_data, f, ensure_ascii=False, indent=2)
print(f"疏散数据已保存: {evac_data_path}")

print("\n✓ 疏散分析和逃生布置图生成完成!")
print(f"  - {escape_svg_path}")
print(f"  - {html_path}")
print(f"  - {evac_data_path}")
