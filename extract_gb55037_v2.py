import json

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

# Find sections by chapter markers
import re

# Look for chapter/section patterns
patterns = [
    (r'6\.5[\.\s].*?(?=6\.6[\.\s]|第7章|7\s)', "6.5 内部和外部装修"),
    (r'6\.4[\.\s].*?(?=6\.5[\.\s])', "6.4 防火门窗卷帘"),
    (r'6\.1[\.\s].*?(?=6\.2[\.\s])', "6.1 防火墙"),
    (r'6\.3[\.\s].*?(?=6\.4[\.\s])', "6.3 竖井管线防火"),
    (r'6\.6[\.\s].*?(?=6\.7[\.\s]|第7章|7\s)', "6.6 建筑保温"),
    (r'7\.[\d].*?(?=第8章|8\.\d)', "7 安全疏散"),
    (r'3\.[\d].*?(?=第4章|4\.\d)', "3 建筑高度与耐火等级"),
    (r'4\.[\d].*?(?=第5章|5\.\d)', "4 建筑平面布置与防火分隔"),
    (r'8\.[\d].*?(?=第9章|9\.\d)', "8 消防设施"),
]

for pat, name in patterns:
    matches = list(re.finditer(pat, content, re.DOTALL))
    if matches:
        text = matches[0].group()[:3000]  # Limit to 3000 chars
        print(f"\n{'='*60}")
        print(f"SECTION: {name}")
        print(f"{'='*60}")
        print(text)
    else:
        print(f"\n[NOT FOUND] {name}")

# Also search for specific key terms
print("\n\n" + "="*60)
print("KEY TERM SEARCH RESULTS")
print("="*60)

key_terms = [
    "室内装修",
    "装修材料",
    "燃烧性能",
    "消防电梯",
    "消防救援口",
    "避难层",
    "疏散楼梯",
    "防火门",
    "防火分区",
    "耐火等级",
]

for term in key_terms:
    idx = content.find(term)
    if idx >= 0:
        start = max(0, idx - 100)
        end = min(len(content), idx + 500)
        snippet = content[start:end].replace('\n', ' ')
        print(f"\n[{term}] ...{snippet}...")
