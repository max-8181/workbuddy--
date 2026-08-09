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
elif isinstance(data, str):
    content = data

# Find the main body of the standard (after the preface/announcement section)
# Look for "2基本规定" or "2 基本规定" or "# 2"
idx = content.find("2基本规定")
if idx < 0:
    idx = content.find("2 基本规定")
if idx < 0:
    idx = content.find("# 2")
if idx < 0:
    idx = content.find("2.1")

if idx > 0:
    # Extract a large chunk of the main content
    main_content = content[idx:idx+15000]
    print(main_content)
else:
    # Just print from position 5000 onwards
    print(content[5000:20000])
