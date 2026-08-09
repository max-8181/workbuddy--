# ima 室内规范库 — 跨设备同步仓库

本仓库用于在多台电脑之间同步 WorkBuddy 工作环境，包括规范库文件、脚本、技能和配置。

## 仓库结构

```
├── workbuddy-configs/        # WorkBuddy 全局配置（~/.workbuddy/ 的镜像）
│   ├── skills/               # 已安装的技能包
│   ├── SOUL.md               # AI 性格定义
│   ├── IDENTITY.md           # AI 身份信息
│   ├── USER.md               # 用户信息
│   ├── settings.json         # 全局设置
│   └── mcp-approvals.json    # MCP 审批记录
├── 规范库/                    # 30部建筑规范 PDF + 索引
├── 条文摘要/                  # 15部规范的条文级摘要
├── 规范全文/                  # 提取的 Markdown 全文
├── .workbuddy/memory/        # 项目记忆（日志 + 长期记忆）
├── *.py                      # Python 脚本（PDF转换、消防疏散计算等）
├── *.json                    # 数据文件（参数库、DWG数据等）
├── *.html                    # 检索报告
├── *.svg                     # 平面图
├── sync_configs.sh           # 配置同步脚本
└── .gitignore
```

## 新电脑恢复步骤

### 1. 克隆仓库

```bash
git clone https://github.com/max-8181/workbuddy--.git
```

### 2. 恢复 WorkBuddy 配置

```bash
cd workbuddy--
chmod +x sync_configs.sh
./sync_configs.sh pull
```

这会将 `workbuddy-configs/` 下的技能和配置文件复制到 `~/.workbuddy/`。

### 3. 重新连接 MCP 服务

打开 WorkBuddy → 「专家·技能·连接器」→「连接器」，重新连接以下服务：
- **ima 知识库**（ima-mcp）— 登录同一账号即可访问云端的「设计工程规范库」

### 4. 创建 Python 虚拟环境（如需运行脚本）

```bash
# 使用 WorkBuddy 自带的 Python
python -m venv ~/.workbuddy/binaries/python/envs/default

# 激活并安装依赖
source ~/.workbuddy/binaries/python/envs/default/bin/activate  # Linux/Mac
# 或 Windows: ~/.workbuddy/binaries/python/envs/default/Scripts/activate

pip install pymupdf ezdxf numpy pywin32 cos-python-sdk-v5
```

### 5. 重新获取 COS 上传凭证

`upload_creds.json` 含腾讯云密钥，未纳入版本控制。
如需上传新规范到 IMA，需要重新运行上传流程获取凭证。

## 日常同步

### 当前电脑推送更新

```bash
./sync_configs.sh push
```

这会自动将最新的配置推送到仓库并 git push。

### 新电脑拉取更新

```bash
git pull
./sync_configs.sh pull
```

## 云端自动同步（无需手动操作）

以下内容存储在云端，登录同一账号自动同步：
- **IMA 知识库内容**（规范 PDF + 条文摘要）
- **WorkBuddy 对话记录**
- **WorkBuddy 个人画像**

## 注意事项

- `upload_creds.json` 被排除在版本控制之外（含 COS 密钥）
- Python venv 不同步（各电脑需独立创建）
- AutoCAD COM 自动化需要本机安装 AutoCAD
- Windows 定时任务不会迁移，需要在新电脑重新创建
