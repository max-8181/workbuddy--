#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DWG平面图数据提取脚本
使用AutoCAD COM接口解析DWG文件，提取空间信息用于消防疏散分析
"""
import win32com.client
from win32com.client import Dispatch
import json
import math
import pythoncom

DWG_PATH = r"J:\测试\新块.dwg"
OUTPUT_JSON = r"C:\Users\panshunkang\WorkBuddy\ima室内规范库\dwg_data.json"

def connect_autocad():
    """连接AutoCAD"""
    try:
        acad = win32com.client.GetActiveObject("AutoCAD.Application")
        print("已连接到运行中的AutoCAD实例")
    except:
        acad = win32com.client.Dispatch("AutoCAD.Application")
        print("已启动AutoCAD（后台模式）")
    return acad

def extract_polyline_area(entity):
    """提取闭合多段线面积（mm²→m²）"""
    try:
        if entity.Closed:
            area_mm2 = entity.Area
            area_m2 = round(area_mm2 / 1000000, 2)
            return area_m2
    except:
        pass
    return None

def extract_polyline_vertices(entity):
    """提取多段线顶点坐标"""
    try:
        coords = list(entity.Coordinates)
        points = []
        for i in range(0, len(coords), 2):
            points.append((coords[i], coords[i+1]))
        return points
    except:
        return []

def get_entity_bounds(entity):
    """获取实体包围盒"""
    try:
        min_pt = entity.GetBoundingBox(None, None)
        max_pt = entity.GetBoundingBox(None, None)
        # GetBoundingBox with win32com special handling
        import win32com.client
        min_v = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [0.0, 0.0, 0.0])
        max_v = win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, [0.0, 0.0, 0.0])
        entity.GetBoundingBox(min_v, max_v)
        min_arr = min_v.value
        max_arr = max_v.value
        return {
            "min": (min_arr[0], min_arr[1]),
            "max": (max_arr[0], max_arr[1]),
            "center": ((min_arr[0]+max_arr[0])/2, (min_arr[1]+max_arr[1])/2)
        }
    except:
        return None

def main():
    print("=" * 60)
    print("DWG 平面图数据提取")
    print("=" * 60)
    
    pythoncom.CoInitialize()
    
    try:
        acad = connect_autocad()
        print(f"AutoCAD版本: {acad.Version}")
        print(f"产品: {acad.Caption}")
        
        # 尝试找到文档 - 可能文件已经在CAD中打开
        doc = None
        for d in acad.Documents:
            if d.FullName and d.FullName.upper() == DWG_PATH.upper():
                doc = d
                print(f"文件已在AutoCAD中打开: {d.Name}")
                break
        
        if doc is None:
            print(f"正在打开文件: {DWG_PATH}")
            doc = acad.Documents.Open(DWG_PATH)
            print(f"已打开: {doc.Name}")
        
        msp = doc.ModelSpace
        print(f"模型空间实体总数: {msp.Count}")
        
    except Exception as e:
        print(f"连接AutoCAD失败: {e}")
        import traceback
        traceback.print_exc()
        pythoncom.CoUninitialize()
        return
    
    # 分类存储提取结果
    closed_polylines = []
    open_polylines = []
    texts = []
    mtexts = []
    blocks = []
    dimensions = []
    circles = []
    arcs = []
    
    entity_types = {}
    
    print("\n正在遍历实体...")
    
    try:
        for i in range(msp.Count):
            entity = msp.Item(i)
            try:
                ename = entity.EntityName if hasattr(entity, 'EntityName') else str(entity.ObjectName)
                entity_types[ename] = entity_types.get(ename, 0) + 1
                
                if ename in ('AcDbPolyline', 'AcDb2dPolyline'):
                    try:
                        is_closed = entity.Closed
                        layer = entity.Layer if hasattr(entity, 'Layer') else "?"
                        
                        if is_closed:
                            area_m2 = extract_polyline_area(entity)
                            bounds = get_entity_bounds(entity)
                            closed_polylines.append({
                                "index": i,
                                "area_m2": area_m2,
                                "layer": layer,
                                "bounds": bounds,
                            })
                        else:
                            open_polylines.append({
                                "index": i,
                                "layer": layer,
                            })
                    except:
                        pass
                
                elif ename == 'AcDbText':
                    try:
                        texts.append({
                            "index": i,
                            "text": str(entity.TextString),
                            "x": entity.InsertionPoint[0],
                            "y": entity.InsertionPoint[1],
                            "height": entity.Height,
                            "layer": entity.Layer,
                        })
                    except:
                        pass
                
                elif ename == 'AcDbMText':
                    try:
                        mtexts.append({
                            "index": i,
                            "text": str(entity.TextString),
                            "x": entity.InsertionPoint[0],
                            "y": entity.InsertionPoint[1],
                            "layer": entity.Layer,
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
                        blocks.append({
                            "index": i,
                            "name": str(name),
                            "x": entity.InsertionPoint[0],
                            "y": entity.InsertionPoint[1],
                            "layer": entity.Layer,
                        })
                    except:
                        pass
                
                elif 'Dimension' in ename:
                    try:
                        dim = {"index": i, "type": ename, "layer": entity.Layer}
                        try:
                            dim["measurement"] = entity.Measurement
                        except:
                            pass
                        try:
                            dim["text"] = str(entity.TextOverride)
                        except:
                            pass
                        dimensions.append(dim)
                    except:
                        pass
                
                elif ename == 'AcDbCircle':
                    try:
                        circles.append({
                            "index": i,
                            "x": entity.Center[0],
                            "y": entity.Center[1],
                            "radius": entity.Radius,
                            "layer": entity.Layer,
                        })
                    except:
                        pass
                
                elif ename == 'AcDbArc':
                    try:
                        arcs.append({
                            "index": i,
                            "x": entity.Center[0],
                            "y": entity.Center[1],
                            "radius": entity.Radius,
                            "layer": entity.Layer,
                        })
                    except:
                        pass
                    
            except Exception as e:
                continue
        
        # 处理进度
        if i % 500 == 0:
            print(f"  已处理 {i+1}/{msp.Count} 个实体...")
        
    finally:
        # 关闭文档（不保存）
        try:
            doc.Close(False)
        except:
            pass
        pythoncom.CoUninitialize()
    
    # 按面积排序
    closed_polylines.sort(key=lambda x: x.get("area_m2", 0) or 0, reverse=True)
    
    print(f"\n实体统计:")
    for etype, count in sorted(entity_types.items()):
        print(f"  {etype}: {count}")
    
    print(f"\n闭合多段线(潜在房间): {len(closed_polylines)} 个")
    for cp in closed_polylines[:30]:
        area = cp.get("area_m2") or "N/A"
        layer = cp.get("layer", "?")
        bounds = cp.get("bounds")
        center_str = ""
        if bounds and bounds.get("center"):
            c = bounds["center"]
            center_str = f" 中心=({c[0]:.0f}, {c[1]:.0f})"
        print(f"    #{cp['index']}: {area} ㎡, 图层={layer}{center_str}")
    
    print(f"\n文字标注: {len(texts)} 条")
    for t in texts[:50]:
        print(f"    #{t['index']}: \"{t['text']}\" @ ({t['x']:.0f}, {t['y']:.0f}) [{t['layer']}]")
    
    if mtexts:
        print(f"\n多行文字: {len(mtexts)} 条")
        for mt in mtexts[:20]:
            print(f"    #{mt['index']}: \"{mt['text'][:80]}\"")
    
    print(f"\n图块引用: {len(blocks)} 个")
    block_names = {}
    for b in blocks:
        name = b['name']
        block_names[name] = block_names.get(name, 0) + 1
    for name, count in sorted(block_names.items(), key=lambda x: -x[1]):
        print(f"    {name}: {count}个")
    
    # 保存JSON
    data = {
        "file": DWG_PATH,
        "entity_counts": entity_types,
        "closed_polylines": closed_polylines,
        "texts": texts,
        "mtexts": mtexts,
        "blocks": blocks,
        "dimensions": dimensions,
        "circles": circles,
        "arcs": arcs,
    }
    
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n数据已保存到: {OUTPUT_JSON}")
    print("=" * 60)

if __name__ == "__main__":
    main()
