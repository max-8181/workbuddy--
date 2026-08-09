#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将DWG通过AutoCAD Plot对象导出为图片
"""
import win32com.client
import pythoncom
import os
import time

DWG_PATH = r"J:\测试\新块.dwg"
OUTPUT_DIR = r"C:\Users\panshunkang\WorkBuddy\ima室内规范库"
OUTPUT_PNG = os.path.join(OUTPUT_DIR, "平面图_export.png")
OUTPUT_BMP = os.path.join(OUTPUT_DIR, "平面图_export.bmp")

pythoncom.CoInitialize()

try:
    acad = win32com.client.GetActiveObject("AutoCAD.Application")
except:
    acad = win32com.client.Dispatch("AutoCAD.Application")
    acad.Visible = True

print(f"AutoCAD: {acad.Caption}")

# 找到文档
doc = None
for d in acad.Documents:
    if d.FullName and d.FullName.upper() == DWG_PATH.upper():
        doc = d
        break

if doc is None:
    doc = acad.Documents.Open(DWG_PATH)

print(f"文档: {doc.Name}")

# Zoom extents to show everything
acad.ZoomExtents()
acad.ZoomScaled(0.95, 1)  # zoom out 5% for margin

# Try BMPOUT command (available since early AutoCAD versions)
try:
    import subprocess
    # SendCommand is async, let's use it and wait
    doc.SendCommand(f'(command "_BMPOUT" "{OUTPUT_BMP}" "_ALL" "") ')
    print("BMPOUT命令已发送，等待生成...")
    time.sleep(3)
    
    if os.path.exists(OUTPUT_BMP):
        # Convert BMP to PNG using Python
        from PIL import Image
        img = Image.open(OUTPUT_BMP)
        img.save(OUTPUT_PNG, "PNG")
        print(f"PNG已保存: {OUTPUT_PNG} ({img.size})")
        os.remove(OUTPUT_BMP)
    else:
        print("BMP文件未生成，尝试其他方法...")
        
        # Try using plot
        layout = doc.ActiveLayout
        print(f"布局: {layout.Name}")
        
        # Configure plot
        layout.ConfigName = "DWG To PDF.pc3"
        layout.PlotType = 1  # acExtents
        layout.StandardScale = 0  # acScaleToFit
        layout.CenterPlot = True
        
        # Try plotting to file
        pdf_path = os.path.join(OUTPUT_DIR, "平面图_temp.pdf")
        plot_result = doc.Plot.DisplayPlotPreview(0)  # acFullPreview
        print(f"预览结果: {plot_result}")
        
except Exception as e:
    print(f"导出失败: {e}")
    import traceback
    traceback.print_exc()

doc.Close(False)
pythoncom.CoUninitialize()
print("完成")
