#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消防疏散计算引擎 - evacuation_calc.py
基于 GB 50016-2014(2018版) 第5.5章 + GB 55037-2022 第7章

四项核心计算：
1. 疏散人数 = 各房间面积 × 人员密度
2. 疏散宽度 = 疏散人数 ÷ 100 × 百人宽度指标（对比实际出口总宽度）
3. 疏散距离 = 各点至最近安全出口距离（对比规范限值）
4. 安全出口数量 = 最低要求数量 + 间距校验 + 宽度校验
"""

import json
import argparse
import sys
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional


# ============================================================
# 数据结构
# ============================================================

@dataclass
class Room:
    name: str
    area_m2: float
    function: str  # office, shop, meeting, corridor, etc.
    floor: str = ""  # ground_1, ground_2, underground_1, etc.


@dataclass
class Exit:
    id: str
    width_m: float
    description: str = ""


@dataclass
class TravelDistance:
    from_point: str
    to_exit: str
    distance_m: float
    path_type: str  # "between_exits" or "dead_end"


@dataclass
class CalculationResult:
    """单项计算结果"""
    item: str
    calculated_value: float
    required_value: float
    unit: str
    compliant: bool
    detail: str = ""
    code_reference: str = ""


@dataclass
class AnalysisReport:
    """完整分析报告"""
    building_type: str
    fire_resistance: str
    floor: str
    has_sprinkler: bool
    total_occupants: int = 0
    results: List[CalculationResult] = field(default_factory=list)
    non_compliant: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("消防疏散分析报告")
        lines.append("=" * 60)
        lines.append(f"建筑类型: {self.building_type}")
        lines.append(f"耐火等级: {self.fire_resistance}")
        lines.append(f"楼层: {self.floor}")
        lines.append(f"自动喷淋: {'是' if self.has_sprinkler else '否'}")
        lines.append(f"疏散总人数: {self.total_occupants} 人")
        lines.append("-" * 60)

        for r in self.results:
            status = "✓ 合规" if r.compliant else "✗ 不合规"
            lines.append(f"[{status}] {r.item}")
            lines.append(f"  计算值: {r.calculated_value}{r.unit}")
            lines.append(f"  限值: {r.required_value}{r.unit}")
            if r.detail:
                lines.append(f"  详情: {r.detail}")
            if r.code_reference:
                lines.append(f"  条文: {r.code_reference}")
            lines.append("")

        if self.non_compliant:
            lines.append("=" * 60)
            lines.append("不合规项汇总:")
            for item in self.non_compliant:
                lines.append(f"  - {item}")
        else:
            lines.append("所有校验项均合规。")

        lines.append("=" * 60)
        return "\n".join(lines)


# ============================================================
# 计算引擎
# ============================================================

class EvacuationCalculator:
    """消防疏散计算器"""

    # 人员密度默认值（人/㎡），当参数库中无具体值时使用
    DEFAULT_DENSITY = {
        "office": 0.20,
        "meeting": 0.50,
        "shop": 0.50,
        "restaurant": 1.00,
        "exhibition": 0.50,
        "corridor": 0.0,  # 走廊不计算人数
        "restroom": 0.0,
        "storage": 0.0,
        "lobby": 0.10,
    }

    def __init__(self, params_path: str = None):
        """加载参数数据库"""
        self.params = {}
        if params_path and os.path.exists(params_path):
            with open(params_path, "r", encoding="utf-8") as f:
                self.params = json.load(f)

    # ---------- 1. 疏散人数计算 ----------

    def calc_occupants(self, rooms: List[Room], building_type: str = "office") -> int:
        """计算疏散人数 = 各房间面积 x 人员密度"""
        total = 0
        details = []

        for room in rooms:
            density = self._get_density(room.function, building_type, room.floor)
            occupants = int(room.area_m2 * density)
            total += occupants
            if density > 0:
                details.append(
                    f"  {room.name}: {room.area_m2}㎡ × {density}人/㎡ = {occupants}人"
                )

        return total, details

    def _get_density(self, function: str, building_type: str, floor: str = "") -> float:
        """获取人员密度"""
        # 商店营业厅使用表5.5.20-2
        if building_type == "shop" or function == "shop":
            shop_data = self.params.get("occupant_density", {}).get("shop_retail", {})
            levels = shop_data.get("levels", {})
            if floor and floor in levels:
                val = levels[floor]
                if isinstance(val, dict):
                    return val.get("max", 0.50)  # 取上限偏安全
                return float(val)

        # 办公房间（不受建筑类型影响，按功能取密度）
        if function == "office":
            office_data = self.params.get("occupant_density", {}).get("office", {})
            if "typical_value" in office_data:
                return office_data["typical_value"]
            return self.DEFAULT_DENSITY.get("office", 0.20)

        # 其他功能房间使用默认值
        return self.DEFAULT_DENSITY.get(function, 0.0)

    # ---------- 2. 疏散宽度计算 ----------

    def calc_evacuation_width(
        self,
        total_occupants: int,
        building_type: str,
        floor: str,
        actual_exits: List[Exit],
    ) -> CalculationResult:
        """计算所需疏散宽度并对比实际宽度"""
        # 获取百人宽度指标
        per_100 = self._get_width_per_100(building_type, floor)

        # 计算所需疏散总宽度
        required_width = total_occupants / 100 * per_100

        # 计算实际疏散总宽度（所有安全出口宽度之和）
        actual_width = sum(e.width_m for e in actual_exits)

        compliant = actual_width >= required_width

        return CalculationResult(
            item="疏散宽度校验",
            calculated_value=round(actual_width, 2),
            required_value=round(required_width, 2),
            unit="m",
            compliant=compliant,
            detail=(
                f"疏散人数{total_occupants}人 ÷ 100 × 百人指标{per_100}m/百人 "
                f"= 所需宽度{required_width:.2f}m；"
                f"实际出口总宽度{actual_width:.2f}m"
                f"（{', '.join(f'{e.id}={e.width_m}m' for e in actual_exits)}）"
            ),
            code_reference="GB 50016 表5.5.20-1",
        )

    def _get_width_per_100(self, building_type: str, floor: str) -> float:
        """获取百人疏散宽度指标"""
        width_data = self.params.get("exit_width_per_100", {})

        # 确定楼层段
        floor_key = self._floor_to_key(floor)

        if building_type == "factory":
            data = width_data.get("factory", {})
        elif building_type in ("shop", "exhibition"):
            data = width_data.get("shop_exhibition", {})
            if floor.startswith("underground"):
                return data.get("underground_1", 1.00)
        else:
            data = width_data.get("civil_other", {})

        return data.get(floor_key, 0.65)

    def _floor_to_key(self, floor: str) -> str:
        """将楼层描述转换为参数表key"""
        if not floor:
            return "floor_1_2"

        if floor.startswith("underground"):
            return "floor_4_plus"  # 地下按最严格取

        # 解析楼层号
        try:
            if floor.startswith("ground_"):
                num = int(floor.split("_")[1])
            else:
                num = int(floor)
        except (ValueError, IndexError):
            return "floor_1_2"

        if num <= 2:
            return "floor_1_2"
        elif num == 3:
            return "floor_3"
        else:
            return "floor_4_plus"

    # ---------- 3. 疏散距离校验 ----------

    def check_travel_distance(
        self,
        travel_distances: List[TravelDistance],
        building_type: str,
        fire_resistance: str,
        has_sprinkler: bool,
    ) -> List[CalculationResult]:
        """校验各点疏散距离"""
        results = []

        # 获取建筑类型对应的距离限值
        distance_data = self.params.get("travel_distance", {})
        buildings = distance_data.get("buildings", {})

        # 映射建筑类型
        type_key = self._map_building_type(building_type)
        type_data = buildings.get(type_key, buildings.get("other_civil", {}))

        # 获取耐火等级对应的限值
        fr_key = fire_resistance if fire_resistance in ("class_1_2", "class_3", "class_4") else "class_1_2"
        limits = type_data.get(fr_key, {"between_exits": 40, "dead_end": 22})

        # 自动喷淋加成
        sprinkler_multiplier = 1.25 if has_sprinkler else 1.0

        for td in travel_distances:
            path_type = td.path_type if td.path_type in ("between_exits", "dead_end") else "between_exits"
            base_limit = limits.get(path_type, 40)
            actual_limit = base_limit * sprinkler_multiplier

            compliant = td.distance_m <= actual_limit

            path_desc = "两出口之间" if path_type == "between_exits" else "袋形走道"
            sprinkler_desc = f" × 1.25(自动喷淋) = {actual_limit:.1f}m" if has_sprinkler else ""

            results.append(CalculationResult(
                item=f"疏散距离: {td.from_point} → {td.to_exit}",
                calculated_value=td.distance_m,
                required_value=round(actual_limit, 1),
                unit="m",
                compliant=compliant,
                detail=f"路径类型: {path_desc}；限值{base_limit}m{sprinkler_desc}",
                code_reference="GB 50016 表5.5.17",
            ))

        return results

    def _map_building_type(self, building_type: str) -> str:
        """映射建筑类型到参数表key"""
        mapping = {
            "office": "other_civil",
            "shop": "other_civil",
            "school": "school",
            "hospital": "hospital",
            "nursery": "nursery_kindergarten_elderly",
            "kindergarten": "nursery_kindergarten_elderly",
            "elderly": "nursery_kindergarten_elderly",
            "entertainment": "entertainment",
            "residential": "other_civil",
        }
        return mapping.get(building_type, "other_civil")

    # ---------- 4. 安全出口数量校验 ----------

    def check_exits(
        self,
        exits: List[Exit],
        total_occupants: int,
        fire_zone_area: float = 0,
    ) -> List[CalculationResult]:
        """校验安全出口数量、间距、最小宽度"""
        results = []
        exit_data = self.params.get("min_exit_count", {})

        # 4a. 出口数量
        min_exits = exit_data.get("fire_zone_min", 2)
        actual_exits = len(exits)

        # 特殊条件：可设1个出口
        if actual_exits == 1:
            if fire_zone_area > 0 and fire_zone_area <= 200 and total_occupants <= 50:
                min_exits = 1
            elif fire_zone_area > 0 and fire_zone_area <= 50 and total_occupants <= 15:
                min_exits = 1

        results.append(CalculationResult(
            item="安全出口数量",
            calculated_value=actual_exits,
            required_value=min_exits,
            unit="个",
            compliant=actual_exits >= min_exits,
            detail=f"实际{actual_exits}个出口；规范要求≥{min_exits}个",
            code_reference="GB 50016 5.5.15",
        ))

        # 4b. 出口间距（如有2个以上出口，检查间距 - 需要额外信息）
        # 此项需要平面图坐标信息，此处仅提示
        if actual_exits >= 2:
            min_spacing = exit_data.get("exit_spacing_min_m", 5)
            results.append(CalculationResult(
                item="安全出口间距",
                calculated_value=0,  # 需要从平面图测量
                required_value=min_spacing,
                unit="m",
                compliant=True,  # 默认合规，需用户确认
                detail=f"需确认：相邻出口最近边缘间距≥{min_spacing}m（请从平面图测量）",
                code_reference="GB 55037 7.1.2",
            ))

        # 4c. 出口最小宽度
        min_width_data = self.params.get("min_width", {})
        min_door_width = min_width_data.get("evacuation_door_public", 0.90)

        for exit_info in exits:
            compliant = exit_info.width_m >= min_door_width
            results.append(CalculationResult(
                item=f"出口{exit_info.id}宽度",
                calculated_value=exit_info.width_m,
                required_value=min_door_width,
                unit="m",
                compliant=compliant,
                detail=f"实际{exit_info.width_m}m；最小要求{min_door_width}m",
                code_reference="GB 50016 5.5.18",
            ))

        return results

    # ---------- 综合分析 ----------

    def full_analysis(
        self,
        building_type: str,
        fire_resistance: str,
        floor: str,
        has_sprinkler: bool,
        rooms: List[Dict],
        exits: List[Dict],
        travel_distances: List[Dict],
        fire_zone_area: float = 0,
    ) -> AnalysisReport:
        """执行完整疏散分析"""

        # 转换数据
        room_objects = [Room(**r) for r in rooms]
        exit_objects = [Exit(**e) for e in exits]
        td_objects = []
        for td in travel_distances:
            td_objects.append(TravelDistance(
                from_point=td.get("from", td.get("from_point", "")),
                to_exit=td.get("to", td.get("to_exit", "")),
                distance_m=td.get("distance_m", 0),
                path_type=td.get("path_type", "between_exits"),
            ))

        report = AnalysisReport(
            building_type=building_type,
            fire_resistance=fire_resistance,
            floor=floor,
            has_sprinkler=has_sprinkler,
        )

        # 1. 疏散人数
        total_occupants, occupant_details = self.calc_occupants(room_objects, building_type)
        report.total_occupants = total_occupants

        report.results.append(CalculationResult(
            item="疏散人数",
            calculated_value=total_occupants,
            required_value=0,
            unit="人",
            compliant=True,
            detail="\n".join(occupant_details) if occupant_details else "无计算房间",
            code_reference="GB 50016 5.5.21 / 表5.5.20-2",
        ))

        # 2. 疏散宽度
        width_result = self.calc_evacuation_width(
            total_occupants, building_type, floor, exit_objects
        )
        report.results.append(width_result)

        # 3. 疏散距离
        distance_results = self.check_travel_distance(
            td_objects, building_type, fire_resistance, has_sprinkler
        )
        report.results.extend(distance_results)

        # 4. 安全出口
        exit_results = self.check_exits(exit_objects, total_occupants, fire_zone_area)
        report.results.extend(exit_results)

        # 汇总不合规项
        for r in report.results:
            if not r.compliant:
                report.non_compliant.append(f"{r.item}: 计算{r.calculated_value}{r.unit} < 限值{r.required_value}{r.unit}")

        return report


# ============================================================
# DXF解析模块（可选）
# ============================================================

def parse_dxf(dxf_path: str) -> Dict:
    """解析DXF文件，提取房间面积、门宽度等信息"""
    try:
        import ezdxf
    except ImportError:
        return {"error": "ezdxf not installed. Run: pip install ezdxf"}

    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    rooms = []
    doors = []
    texts = []

    for entity in msp:
        if entity.dxftype() == "LWPOLYLINE":
            if entity.closed:
                # 计算闭合多段线面积
                points = [(p[0], p[1]) for p in entity.get_points()]
                area = abs(polygon_area(points))
                rooms.append({
                    "area_m2": round(area, 2),
                    "points": points,
                })

        elif entity.dxftype() == "INSERT":
            # 门图块 - 尝试提取宽度
            block_name = entity.dxf.name
            doors.append({
                "block_name": block_name,
                "insert_point": (entity.dxf.insert.x, entity.dxf.insert.y),
            })

        elif entity.dxftype() == "TEXT":
            texts.append({
                "text": entity.dxf.text,
                "position": (entity.dxf.insert.x, entity.dxf.insert.y),
            })

    return {
        "rooms": rooms,
        "doors": doors,
        "texts": texts,
        "room_count": len(rooms),
        "door_count": len(doors),
    }


def polygon_area(points):
    """使用鞋带公式计算多边形面积"""
    n = len(points)
    if n < 3:
        return 0
    area = 0
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    return area / 2


# ============================================================
# HTML报告生成
# ============================================================

def generate_html_report(report: AnalysisReport, output_path: str, plan_image: str = None):
    """生成HTML合规报告"""
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>消防疏散分析报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: "Microsoft YaHei", "Segoe UI", sans-serif; background: #f5f5f5; color: #333; line-height: 1.6; }}
        .container {{ max-width: 960px; margin: 20px auto; background: #fff; padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }}
        h1 {{ font-size: 22px; color: #1a1a2e; border-bottom: 3px solid #e94560; padding-bottom: 12px; margin-bottom: 24px; }}
        h2 {{ font-size: 16px; color: #16213e; margin: 24px 0 12px; padding-left: 12px; border-left: 4px solid #e94560; }}
        .info-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 24px; }}
        .info-item {{ background: #f8f9fa; padding: 10px 16px; border-radius: 6px; }}
        .info-item .label {{ color: #6c757d; font-size: 13px; }}
        .info-item .value {{ font-weight: 600; font-size: 15px; color: #16213e; }}
        table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
        th {{ background: #16213e; color: #fff; padding: 10px 12px; text-align: left; font-size: 13px; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #dee2e6; font-size: 13px; }}
        tr:hover {{ background: #f8f9fa; }}
        .pass {{ color: #28a745; font-weight: 600; }}
        .fail {{ color: #dc3545; font-weight: 600; }}
        .badge-pass {{ background: #d4edda; color: #155724; padding: 2px 10px; border-radius: 12px; font-size: 12px; }}
        .badge-fail {{ background: #f8d7da; color: #721c24; padding: 2px 10px; border-radius: 12px; font-size: 12px; }}
        .detail {{ color: #6c757d; font-size: 12px; margin-top: 4px; }}
        .code-ref {{ color: #007bff; font-size: 12px; }}
        .summary-box {{ padding: 16px 20px; border-radius: 8px; margin: 16px 0; }}
        .summary-all-pass {{ background: #d4edda; border: 1px solid #c3e6cb; }}
        .summary-has-fail {{ background: #f8d7da; border: 1px solid #f5c6cb; }}
        .footer {{ margin-top: 40px; padding-top: 16px; border-top: 1px solid #dee2e6; color: #6c757d; font-size: 12px; }}
        .plan-image {{ max-width: 100%; border: 1px solid #dee2e6; border-radius: 8px; margin: 12px 0; }}
    </style>
</head>
<body>
<div class="container">
    <h1>消防疏散分析报告</h1>

    <h2>项目概况</h2>
    <div class="info-grid">
        <div class="info-item"><span class="label">建筑类型</span><br><span class="value">{report.building_type}</span></div>
        <div class="info-item"><span class="label">耐火等级</span><br><span class="value">{report.fire_resistance}</span></div>
        <div class="info-item"><span class="label">楼层位置</span><br><span class="value">{report.floor}</span></div>
        <div class="info-item"><span class="label">自动喷淋系统</span><br><span class="value">{'设' if report.has_sprinkler else '未设'}</span></div>
        <div class="info-item"><span class="label">疏散总人数</span><br><span class="value">{report.total_occupants} 人</span></div>
        <div class="info-item"><span class="label">校验项目数</span><br><span class="value">{len(report.results)} 项</span></div>
    </div>
"""

    if plan_image and os.path.exists(plan_image):
        html += f"""
    <h2>平面图</h2>
    <img src="{plan_image}" alt="平面布置图" class="plan-image">
"""

    html += """
    <h2>疏散计算结果</h2>
    <table>
        <thead>
            <tr>
                <th>校验项</th>
                <th>计算值</th>
                <th>限值/要求</th>
                <th>判定</th>
                <th>条文依据</th>
            </tr>
        </thead>
        <tbody>
"""
    for r in report.results:
        status_class = "pass" if r.compliant else "fail"
        badge = '<span class="badge-pass">合规</span>' if r.compliant else '<span class="badge-fail">不合规</span>'
        html += f"""
            <tr>
                <td>{r.item}<div class="detail">{r.detail}</div></td>
                <td class="{status_class}">{r.calculated_value} {r.unit}</td>
                <td>{r.required_value} {r.unit}</td>
                <td>{badge}</td>
                <td class="code-ref">{r.code_reference}</td>
            </tr>
"""

    html += """
        </tbody>
    </table>
"""

    if report.non_compliant:
        html += """
    <div class="summary-box summary-has-fail">
        <strong>不合规项汇总</strong>
        <ul>
"""
        for item in report.non_compliant:
            html += f"            <li>{item}</li>\n"
        html += """
        </ul>
        <p style="margin-top:8px;color:#721c24;">建议针对不合规项进行整改，调整出口位置、宽度或疏散路径后重新校验。</p>
    </div>
"""
    else:
        html += """
    <div class="summary-box summary-all-pass">
        <strong>所有校验项均合规</strong>
        <p>本次消防疏散分析各项指标均满足规范要求。</p>
    </div>
"""

    html += """
    <h2>规范依据</h2>
    <table>
        <tr><th>规范</th><th>条文</th><th>用途</th></tr>
        <tr><td>GB 55037-2022 建筑防火通用规范</td><td>第7章 安全疏散</td><td>强制性原则要求</td></tr>
        <tr><td>GB 50016-2014(2018版) 建筑设计防火规范</td><td>第5.5章 安全疏散</td><td>量化计算参数</td></tr>
        <tr><td>GB 50222-2017 建筑内部装修设计防火规范</td><td>—</td><td>装修材料防火</td></tr>
    </table>

    <div class="footer">
        <p>本报告由消防疏散分析系统自动生成，仅供参考。正式设计应以规范原文为准，建议由注册消防工程师审核。</p>
        <p>生成时间: """ + __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
    </div>
</div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path


# ============================================================
# 命令行入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="消防疏散计算引擎")
    parser.add_argument("--params", default="evacuation_params.json", help="参数数据库JSON路径")
    parser.add_argument("--building-type", default="office", help="建筑类型")
    parser.add_argument("--fire-resistance", default="class_1_2", help="耐火等级")
    parser.add_argument("--floor", default="ground_2", help="楼层")
    parser.add_argument("--has-sprinkler", action="store_true", help="是否设自动喷淋")
    parser.add_argument("--fire-zone-area", type=float, default=0, help="防火分区面积(㎡)")
    parser.add_argument("--rooms", default="[]", help="房间JSON数组")
    parser.add_argument("--exits", default="[]", help="出口JSON数组")
    parser.add_argument("--travel-distances", default="[]", help="疏散距离JSON数组")
    parser.add_argument("--dxf", help="DXF文件路径（可选，自动提取空间信息）")
    parser.add_argument("--output", help="HTML报告输出路径")
    parser.add_argument("--plan-image", help="平面图图片路径（嵌入报告）")

    args = parser.parse_args()

    # 初始化计算器
    calc = EvacuationCalculator(args.params)

    # 解析DXF（如提供）
    if args.dxf:
        dxf_data = parse_dxf(args.dxf)
        if "error" not in dxf_data:
            print(f"DXF解析: {dxf_data['room_count']}个房间, {dxf_data['door_count']}个门")
            # 此处可进一步将DXF数据映射为rooms/exits格式

    # 解析JSON参数
    rooms = json.loads(args.rooms)
    exits_list = json.loads(args.exits)
    travel_distances = json.loads(args.travel_distances)

    # 执行分析
    report = calc.full_analysis(
        building_type=args.building_type,
        fire_resistance=args.fire_resistance,
        floor=args.floor,
        has_sprinkler=args.has_sprinkler,
        rooms=rooms,
        exits=exits_list,
        travel_distances=travel_distances,
        fire_zone_area=args.fire_zone_area,
    )

    # 输出文本报告
    print(report.summary())

    # 生成HTML报告（如指定输出路径）
    if args.output:
        html_path = generate_html_report(report, args.output, args.plan_image)
        print(f"\nHTML报告已生成: {html_path}")


if __name__ == "__main__":
    main()
