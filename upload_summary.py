from qcloud_cos import CosConfig, CosS3Client

secret_id = "AKIDwKLLnw9pf3kx1TNv3OPXGwziWB6ZRPSP2R7nIvW_cg2Y2OLmftSIMscAxFc-r3de"
secret_key = "YCcCNXZ+kgmSythyvHi5Fmi9SFIsTrLlLo9M+4zHN2Q="
token = "a7DawfCGVeC9UwsudJgpSTOONKu7BJ4a9dadd60327d440873299d31709c6e439jdJa501ueNt5mGNL9BfHBmFvlYBPYKRTOiZKIn-SpiyYR-6-dPl-_EAEsqXSPpdGx48ihWBJWScxqRwl5cthflddT50dOx0RTRKr9IkORSue8rcyNnuRSx_6GFzmV0LAejk0RQ2IJ5Ugr1llwhL6705RnuAjsph2WJMmAiZHSpa5-57nPagOX0VxqXBN1wSY03popCiBJmq5rTKR_8d4EikOgv5_q8MMYGvqmobuaqU2xzfGXmQj8VshrFSY3eX3k2kDKajIprpy3EuIrp4tC1eutyqtbtiywaa_xQMMDv26SzfgfhIJzDFgLaz8-RdujMH2MWgiLp_no3jKV24VQzyy7C-Wvfe4B5dmMhQzYwLadqebDnsDZ8jo7su7yW6AwzEt6cRmVe4jgzfRNs3OGfNVb2j7ct7o25XwnEgxO73IFsDh3aRYJ0AFYNwTI1pj6CPrVRm9zW86BNGscvptQXntaMwpkD-uP3_dyl6Hq977U8qteGkvzLpbTeD8__kiOkiL5mLQ5rcB4YH4EYyTI8Dt_DO21U5ogh945wrmbEPHMMGgv3RQcV6J6wLtD5fAdN9OrgbEYJWBehrQ0kmBGVAhPb7cRWfCh03NztsveAY6wwTf6f85AugG82dudp-BihAYinDfPkuUGBzp2xprPz13olaL_lAj1gd5G7zODIFoDqgOSlr_eft5fNg-LFlUrB3vHSiAIjfDjttCpYvJeDsxJx1kYUXJbwL4kqTf-aHINHF0Bza9LulqBNQUmMH8Of9i_QuWEAWgKZMhmkaH1POxfi0JMnUrAV1sF8f_R7M"

region = "ap-shanghai"
bucket = "ima-share-kb-1258344701"
cos_key = "5/TvkbCO8AxJZziiqOrG9G8B/file_manager/019fd5b0bed2738d836e1a74ee5657cf.md"
local_file = r"C:\Users\panshunkang\WorkBuddy\ima室内规范库\条文摘要\GB55019-2021_建筑与市政工程无障碍通用规范_条文摘要.md"

config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token, Scheme='https')
client = CosS3Client(config)

response = client.upload_file(
    Bucket=bucket,
    Key=cos_key,
    LocalFilePath=local_file,
    EnableMD5=True,
    ContentType='text/markdown'
)

print(f"Upload successful! ETag: {response.get('ETag', 'N/A')}")
