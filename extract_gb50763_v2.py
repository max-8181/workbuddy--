import json

file_path = r"C:\Users\panshunkang\.workbuddy\projects\c-Users-panshunkang-WorkBuddy-ima室内规范库\04abacd2-4d78-4337-8ee6-25cb8ab2271a\tool-results\call_ba3c79f15f334a7db648b2cd.txt"

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

# Print from position 2000 onwards (after TOC)
print(content[2000:8000])
print("\n" + "=" * 80)
print("=== SECTION 8000-14000 ===")
print(content[8000:14000])
print("\n" + "=" * 80)
print("=== SECTION 14000-20000 ===")
print(content[14000:20000])
print("\n" + "=" * 80)
print("=== SECTION 20000-26000 ===")
print(content[20000:26000])
print("\n" + "=" * 80)
print("=== SECTION 26000-32000 ===")
print(content[26000:32000])
print("\n" + "=" * 80)
print("=== SECTION 32000-38000 ===")
print(content[32000:38000])
print("\n" + "=" * 80)
print("=== SECTION 38000-44000 ===")
print(content[38000:44000])
print("\n" + "=" * 80)
print("=== SECTION 44000-52000 ===")
print(content[44000:])
