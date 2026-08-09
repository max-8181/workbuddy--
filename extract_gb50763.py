import json
import re

file_path = r"C:\Users\panshunkang\.workbuddy\projects\c-Users-panshunkang-WorkBuddy-ima室内规范库\04abacd2-4d78-4337-8ee6-25cb8ab2271a\tool-results\call_ba3c79f15f334a7db648b2cd.txt"

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get content field
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

print(f"Total content length: {len(content)}")
print("=" * 80)

# Extract key sections by chapter markers
chapters = re.split(r'(\d+\s*[\u4e00-\u9fff]+)', content)

# Find强制性条文
mandatory_patterns = [
    r'强制性条文',
    r'必须严格执行',
    r'不应低于',
    r'不应小于',
    r'不应大于',
    r'不应超过',
    r'必须',
]

# Search for key terms
key_terms = [
    '轮椅坡道', '盲道', '缘石坡道', '无障碍出入口', '无障碍通道',
    '无障碍电梯', '无障碍厕所', '无障碍浴室', '无障碍客房',
    '无障碍住房', '轮椅席位', '无障碍停车位', '低位服务',
    '无障碍标识', '居住区', '居住建筑', '公共建筑',
    '办公建筑', '商业建筑', '医疗建筑', '教育建筑',
    '强制性条文', '必须严格执行',
    '坡度', '宽度', '高度', '扶手', '回转空间',
    '3.7', '4.4', '6.2', '8.1',  # mandatory clause numbers
]

# Print first 2000 chars to understand structure
print("=== FIRST 2000 CHARS ===")
print(content[:2000])
print("=" * 80)

# Print content around each key term (first occurrence)
found_sections = set()
for term in key_terms:
    idx = content.find(term)
    if idx >= 0:
        start = max(0, idx - 200)
        end = min(len(content), idx + 500)
        section_key = (start // 500)
        if section_key not in found_sections:
            found_sections.add(section_key)
            print(f"\n--- Found '{term}' at position {idx} ---")
            print(content[start:end])
            print("---")
