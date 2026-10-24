---
name: github-repo-skill-installer
description: "从任意 GitHub 仓库安装 SKILL.md 格式的技能到 WorkBuddy：含安全审计（网络调用/eval/subprocess 扫描）、git clone 被网络策略阻断时的下载降级方案、WorkBuddy 路径与托管 venv 适配补丁。当用户提供 GitHub 仓库链接要求安装 skill、或说'帮我装这个 skill 仓库'时使用。"
---

# GitHub 仓库技能安装器（含安全审计）

## 适用场景
用户给出 GitHub 仓库 URL，要求把其中的 skill 装进 WorkBuddy（`~/.workbuddy/skills/<skill-name>/`）。

## 流程

### 1. 了解仓库
用 WebFetch 读仓库首页 README，或用 GitHub MCP `get_file_contents`（owner/repo/path）拉文件列表与 SKILL.md。

### 2. 安全审计（强制，安装前完成）
- 逐个读 SKILL.md 和所有可执行代码（scripts/、包目录、tools/）。
- 扫描模式（在解压后的本地目录执行 grep）：
  - 网络调用：`requests\.|urllib\.request|socket\.|httpx|urlopen`
  - 危险执行：`eval\(|exec\(|os\.system|shell=True|base64\.b64decode`
  - subprocess 使用：逐个确认是固定命令 + 列表参数（非 shell=True 拼接）。
- pip install 行为：确认只装固定白名单包、默认 ask 模式需确认。
- 有 P0/P1 风险 → 强烈警告并要求用户明确确认后才可安装。

### 3. 下载（git clone 失败的降级链）
本机常见故障：`schannel: CRYPT_E_REVOCATION_OFFLINE`；本机**没有 `gh` CLI**（查仓库信息一律用 `curl --noproxy '*' https://api.github.com/...`）。降级顺序：
1. `git -c http.schannelCheckRevoke=false clone` （多数情况无效）
2. `curl -sL --ssl-no-revoke -o <abs-path>.zip https://codeload.github.com/<owner>/<repo>/zip/refs/heads/<branch>`
   - **`-o` 必须写 Windows 风格绝对路径**（如工作区目录下）。实测 `-o /tmp/x.zip` 在 Git Bash 下返回 HTTP 200 但 **size_download=0**，静默下载空文件——务必用 `-w "HTTP:%{http_code} SIZE:%{size_download}"` 确认字节数。
   - **先查默认分支**：`curl -s --ssl-no-revoke https://api.github.com/repos/<owner>/<repo> | grep default_branch`——拼错分支名会得到 404 文本文件而非 zip。
   - 解压用托管 python 最稳（Git Bash 常无 `unzip`）：
     `<venv>/Scripts/python.exe -c "import zipfile; zipfile.ZipFile('<abs>.zip').extractall('.')"`
3. MCP `get_file_contents` 逐文件拼装（最后手段，慢）。

### 4. 安装
- 目标：`~/.workbuddy/skills/<skill-name>/`（用户级）。
- **覆盖前先备份**：`cp -r <skill-dir> .<skill-name>.bak-$(date +%Y%m%d-%H%M%S)`，失败可回滚。已装过同名技能时，先问用户是「更新到最新 / 保持现状 / 重装 release」，别默认覆盖。
- 只拷贝运行所需：SKILL.md、代码目录、tools/、LICENSE、中文 README；排除 docs/、tests/、.github/、evals 素材。
- SKILL.md 大小应与审计时一致（wc -c 核对）。

### 5. WorkBuddy 适配补丁（按需）
- 若 SKILL.md 里有脚本查找路径列表（CANDIDATES 之类），把 `~/.workbuddy/skills/<skill-name>/...` 加为第一候选。
- 若涉及 Python：优先托管 venv：
  `~/.workbuddy/binaries/python/envs/default/Scripts/python.exe`（Windows）/ `bin/python`（Unix）。
- Git Bash 调 Windows python.exe 传路径参数需 `cygpath -w` 转换，否则报 `c:\c\Users\...`。

### 6. 依赖与验证
- Python 依赖装进托管 venv（`<venv>/Scripts/python.exe -m pip install <pkg>`），绝不全局 pip。
- **跑 `--check` 必须用托管 venv 的 python**。用裸 interpreter 跑会把 venv 里已装的包全报成缺失（误判）——book-to-skill 就踩过：裸 python 报 pypdf/pdfminer/ebooklib/trafilatura 全缺，换 venv 后全 ready。
- 能 `--check`/`--help` 的工具跑一次验证；再拿仓库自带文件做一次真实端到端跑通（比只跑 --help 有说服力）。
- 收尾清掉 `__pycache__` 和临时下载目录。
- 重依赖（如 docling 带 torch）默认不装，说明即可。

### 7. 收尾
- 报告：审计结论、安装位置、适配补丁、使用方法、缺什么依赖。
- 写工作区 memory 日志。
