---
name: fire-evacuation-analysis
description: 消防疏散分析与计算。当用户提供平面布置图并需要消防逃生计算、疏散宽度校验、疏散距离校验、安全出口数量校验、疏散人数计算时触发此技能。支持从平面图提取空间信息，自动计算四项核心疏散指标，生成HTML合规报告。典型触发词：消防疏散、逃生计算、疏散宽度、疏散距离、安全出口、疏散人数、消防校验、平面图消防分析等。
agent_created: true
---

# 消防疏散分析

## 概述

本技能用于对建筑平面布置图进行消防疏散分析与合规性校验。接收平面图（图片/PDF/DXF）和建筑基本信息，自动计算疏散人数、疏散宽度、疏散距离、安全出口数量四项核心指标，与规范限值对比，生成HTML合规报告。

## 依赖资源

| 资源 | 路径 | 说明 |
|------|------|------|
| 参数数据库 | `evacuation_params.json` | 结构化的疏散计算参数（人员密度、百人宽度指标、距离限值等） |
| 计算脚本 | `evacuation_calc.py` | Python计算引擎，4个模块 |
| IMA知识库 | ID `7415660309141938` | 可检索 GB 55037、GB 50016 等规范条文 |
| GB 50016条文摘要 | `条文摘要/GB50016-2014_建筑设计防火规范_条文摘要.md` | 疏散计算参数速查 |
| GB 55037条文摘要 | `条文摘要/GB55037-2022_建筑防火通用规范_条文摘要.md` | 强制性条文速查 |
| ezdxf库 | Python venv | DXF格式平面图解析（已安装v1.4.4） |
| pywin32库 | Python venv | AutoCAD COM自动化（已安装v312） |
| AutoCAD | 本机已安装2012-2020多版本 | DWG格式直接读写标注 |

## 执行流程

### 第一步：收集建筑基本信息

向用户确认以下参数（如未提供则逐项询问）：

```
1. 建筑类型：住宅/办公/商业/学校/医院/其他
2. 建筑高度：___m（或层数：___层）
3. 耐火等级：一级/二级/三级/四级（不确定时默认一二级）
4. 是否设自动喷水灭火系统：是/否/部分
5. 楼层位置：地上第__层 / 地下第__层
6. 防火分区面积：___㎡（如已知）
7. 平面图比例尺：1:___（如已知，用于图片测量距离）
```

### 第二步：解析平面图

根据输入格式选择解析方式：

**A. 图片格式（JPG/PNG）— 多模态识别**

使用多模态能力查看平面图，识别并提取：
1. 房间布局：各房间位置、面积（需比例尺换算）
2. 房间功能：办公/会议室/走廊/卫生间等（看文字标注）
3. 门位置和类型：疏散门、防火门、普通门
4. 安全出口位置：直通室外的出口
5. 疏散走道走向：走廊布局
6. 疏散楼梯位置和形式

提取后整理为结构化数据：
```json
{
  "rooms": [
    {"name": "办公室A", "area_m2": 35, "function": "office"},
    {"name": "会议室", "area_m2": 50, "function": "meeting"},
    {"name": "走廊", "area_m2": 30, "function": "corridor"}
  ],
  "doors": [
    {"id": "D1", "location": "办公室A入口", "width_m": 0.9, "type": "疏散门"},
    {"id": "D2", "location": "走廊尽头", "width_m": 1.2, "type": "安全出口"}
  ],
  "exits": [
    {"id": "E1", "description": "东面安全出口", "width_m": 1.2},
    {"id": "E2", "description": "西面安全出口", "width_m": 1.5}
  ],
  "corridors": [
    {"id": "C1", "width_m": 1.5, "length_m": 25, "type": "普通走道"}
  ],
  "stairs": [
    {"id": "S1", "width_m": 1.2, "type": "防烟楼梯间"}
  ],
  "travel_distances": [
    {"from": "办公室A最远点", "to": "E1", "distance_m": 28, "path_type": "between_exits"},
    {"from": "会议室最远点", "to": "E2", "distance_m": 18, "path_type": "dead_end"}
  ]
}
```

**B. PDF格式 — pymupdf提取**

使用Python脚本提取PDF中的矢量数据和文本标注：
```python
import fitz
doc = fitz.open(pdf_path)
page = doc[0]
# 提取文本（房间名称、尺寸标注）
text = page.get_text()
# 提取矢量图形（墙体线条、门弧线）
drawings = page.get_drawings()
```

**C. DXF格式 — ezdxf解析**

使用ezdxf库精确提取CAD数据：
```python
import ezdxf
doc = ezdxf.readfile(dxf_path)
msp = doc.modelspace()
# 提取实体：LWPOLYLINE(房间轮廓)、INSERT(门图块)、TEXT(标注)
for entity in msp:
    if entity.dxftype() == 'LWPOLYLINE':
        # 计算闭合多段线面积
    elif entity.dxftype() == 'INSERT':
        # 识别门图块，提取宽度
    elif entity.dxftype() == 'TEXT':
        # 提取房间名称和尺寸标注
```

**D. DWG格式 — AutoCAD COM自动化（两种模式）**

本机已安装 AutoCAD 2012-2020，通过 pywin32 COM 接口可直接操作 DWG 文件。

**模式B：后台处理（推荐默认）**
```python
import win32com.client
# 连接AutoCAD（后台启动，不弹界面）
acad = win32com.client.Dispatch('AutoCAD.Application')
acad.Visible = False  # 后台模式
# 打开DWG
doc = acad.Documents.Open(r"C:\path\to\plan.dwg")
msp = doc.ModelSpace
# 读取实体：面积、门宽、文字标注
for entity in msp:
    if entity.EntityName == 'AcDbPolyline':
        area = entity.Area  # 精确面积
    elif entity.EntityName == 'AcDbBlockReference':
        # 识别门图块
    elif entity.EntityName == 'AcDbText':
        text = entity.TextString  # 房间名称
# 计算完成后添加标注图层
# 添加疏散路径箭头、距离标注、合规标记
doc.SaveAs(r"C:\path\to\plan_annotated.dwg")
doc.Close()
```

**模式C：实时AutoCAD（用户可见）**
```python
acad = win32com.client.Dispatch('AutoCAD.Application')
acad.Visible = True  # 显示界面
doc = acad.Documents.Open(r"C:\path\to\plan.dwg")
# 读取 → 计算 → 添加标注
# 用户在AutoCAD中实时看到标注出现
# 可交互调整标注位置
```

**DWG标注内容**（两种模式通用）：
1. 疏散路径箭头（红色多段线+箭头）
2. 疏散距离文字标注（房间最远点→最近出口）
3. 安全出口标记（绿色圆圈+编号）
4. 疏散人数标注（每房间：面积×密度=人数）
5. 合规/不合规标记（绿色✓或红色✗）
6. 新建独立图层"消防疏散分析"，不修改原图层

**DWG vs DXF选择**：
- 用户给DWG → 用COM直接操作，无需转换
- 用户给DXF → 用ezdxf操作
- 两者精度相同（mm级）

### 第三步：用户确认

将提取的空间信息以表格形式呈现给用户确认：
- 房间面积是否准确
- 门宽度和位置是否正确
- 安全出口位置是否遗漏
- 疏散路径是否正确

用户确认或修正后进入计算阶段。

### 第四步：自动计算

调用 `evacuation_calc.py` 脚本执行四项计算：

```bash
C:\Users\panshunkang\.workbuddy\binaries\python\envs\default\Scripts\python.exe evacuation_calc.py \
  --params evacuation_params.json \
  --building-type office \
  --fire-resistance class_1_2 \
  --floor ground_2 \
  --has-sprinkler \
  --rooms '[{"name":"办公室A","area_m2":35,"function":"office"},...]' \
  --exits '[{"id":"E1","width_m":1.2},...]' \
  --travel-distances '[{"from":"...","to":"E1","distance_m":28,"path_type":"between_exits"},...]'
```

或直接在Python中调用：
```python
from evacuation_calc import EvacuationCalculator
calc = EvacuationCalculator("evacuation_params.json")
result = calc.full_analysis(
    building_type="office",
    fire_resistance="class_1_2",
    floor="ground_2",
    has_sprinkler=True,
    rooms=[...],
    exits=[...],
    travel_distances=[...]
)
```

四项计算逻辑：

**1. 疏散人数**
```
人数 = 各房间面积 × 对应人员密度
办公建筑密度 = 0.20人/㎡（典型值，或面积÷5㎡/人）
商店营业厅密度 = 查表5.5.20-2（按楼层取值）
```

**2. 疏散宽度**
```
所需疏散总宽度 = 疏散人数 ÷ 100 × 百人宽度指标
百人指标 = 查表5.5.20-1（按建筑类型和楼层取值）
实际疏散总宽度 = 各安全出口宽度之和
判定：实际宽度 ≥ 所需宽度 → 合规
```

**3. 疏散距离**
```
对每个房间最远点到最近安全出口：
- 判断路径类型：位于两出口之间 / 袋形走道
- 查表5.5.17获取限值
- 如设自动喷淋：限值 × 1.25
- 判定：实际距离 ≤ 限值 → 合规
```

**4. 安全出口数量**
```
查5.5.15获取最低出口数量要求
检查出口间距 ≥ 5m
判定：实际数量 ≥ 要求数量 且 间距达标 → 合规
```

### 第五步：生成HTML报告

生成包含以下内容的HTML合规报告：

```html
报告结构：
1. 项目概况（建筑类型、层数、耐火等级等）
2. 平面图（原图展示，标注出口和疏散路径）
3. 疏散计算表
   - 疏散人数计算（各房间面积×密度，汇总）
   - 疏散宽度计算（所需vs实际，合规判定）
   - 疏散距离校验（各点距离vs限值，合规判定）
   - 安全出口校验（数量、间距、宽度，合规判定）
4. 不合规项及整改建议
5. 规范条文引用
```

报告样式参考已有的 `电源插座配置规范检索报告.html` 和 `电源点位预留规范检索报告.html`。

## 规范依据

| 规范 | 用途 | 条文 |
|------|------|------|
| GB 55037-2022 建筑防火通用规范 | 强制性原则要求 | 7.1章安全疏散 |
| GB 50016-2014(2018版) 建筑设计防火规范 | 量化计算参数 | 5.5章安全疏散 |
| GB 50222-2017 建筑内部装修设计防火规范 | 装修材料防火 | — |
| JGJ/T 67-2019 办公建筑设计标准 | 办公建筑人员密度参考 | — |

## 注意事项

1. **数据准确性**：图片识别提取的面积和距离为估算值，应提示用户确认。DXF解析数据为精确值。
2. **强制性条文优先**：GB 55037的强制性条文优先于GB 50016的非强制性条文。
3. **自动喷淋加成**：仅当建筑内**全部**设自动喷水灭火系统时，疏散距离才可增加25%。
4. **袋形走道判定**：袋形走道是指只有一个疏散方向的走道（尽端走道），距离限值更严格。
5. **免责声明**：分析结果仅供参考，正式设计应以规范原文为准，建议由注册消防工程师审核。
