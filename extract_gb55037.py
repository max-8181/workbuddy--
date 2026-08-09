import json
import re

file_path = r"C:\Users\panshunkang\.workbuddy\projects\c-Users-panshunkang-WorkBuddy-ima室内规范库\04abacd2-4d78-4337-8ee6-25cb8ab2271a\tool-results\mcp-connector-proxy-ima-mcp_fetch_media_content-1785995646528-6b4db8.txt"

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

content = ""
if isinstance(data, dict):
    for key in ['content', 'text', 'result', 'data']:
        if key in data:
            content = str(data[key])
            break
    if not content:
        content = json.dumps(data, ensure_ascii=False)
elif isinstance(data, str):
    content = data

# Extract key sections by keywords
keywords = [
    "耐火等级", "防火分区", "安全疏散", "疏散宽度", "疏散距离",
    "内部装修", "外部装修", "建筑保温", "防火门", "防火窗",
    "防火墙", "幕墙", "管道井", "竖井", "消防电梯",
    "消防救援口", "避难", "楼梯间", "防火分隔",
    "6.5", "6.6", "7.", "8.", "室内装修",
    "装修材料", "燃烧性能", "A级", "B1级",
    "排烟", "火灾自动报警", "消火栓", "自动灭火"
]

# Split content into sections by looking for chapter/section markers
lines = content.split('\n')
output_lines = []
current_section = ""

for i, line in enumerate(lines):
    line_stripped = line.strip()
    # Include lines that match keywords
    for kw in keywords:
        if kw in line_stripped:
            # Get surrounding context (2 lines before and after)
            start = max(0, i - 1)
            end = min(len(lines), i + 2)
            for j in range(start, end):
                if lines[j].strip() and lines[j] not in output_lines:
                    output_lines.append(f"[L{j}] {lines[j]}")
            break

# Print unique lines
seen = set()
for line in output_lines:
    if line not in seen:
        seen.add(line)
        print(line)
