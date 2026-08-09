#!/usr/bin/env python3
"""Upload 19 regulation PDFs to Tencent COS for IMA knowledge base."""
import json, os, sys, time
from qcloud_cos import CosConfig, CosS3Client

BUCKET = "ima-share-kb-1258344701"
REGION = "ap-shanghai"
BASE_DIR = r"C:\Users\panshunkang\WorkBuddy\ima室内规范库\规范库"

with open(r"C:\Users\panshunkang\WorkBuddy\ima室内规范库\upload_creds.json", "r", encoding="utf-8") as f:
    files = json.load(f)

success = []
failed = []

for i, item in enumerate(files, 1):
    file_path = os.path.join(BASE_DIR, item["f"].replace("/", os.sep))
    name = os.path.basename(item["f"])
    print(f"\n[{i}/{len(files)}] Uploading: {name}")
    
    if not os.path.exists(file_path):
        print(f"  ERROR: File not found: {file_path}")
        failed.append(item)
        continue
    
    file_size = os.path.getsize(file_path)
    print(f"  Size: {file_size / 1024 / 1024:.1f} MB")
    
    try:
        config = CosConfig(
            Region=REGION,
            SecretId=item["si"],
            SecretKey=item["sk"],
            Token=item["t"],
            Scheme="https"
        )
        client = CosS3Client(config)
        
        # Upload with EnableMD5=True for integrity check
        response = client.upload_file(
            Bucket=BUCKET,
            Key=item["k"],
            LocalFilePath=file_path,
            EnableMD5=True
        )
        print(f"  OK - ETag: {response.get('ETag', 'N/A')}")
        success.append(item)
    except Exception as e:
        print(f"  FAILED: {e}")
        failed.append(item)

print(f"\n=== RESULT ===")
print(f"Success: {len(success)}/{len(files)}")
print(f"Failed: {len(failed)}")

if failed:
    print("\nFailed files:")
    for item in failed:
        print(f"  - {item['f']}")
        print(f"    media_id: {item['m']}")

# Output media_ids for successful uploads
if success:
    print("\n=== MEDIA_IDS (for add_knowledge) ===")
    for item in success:
        print(item["m"])
