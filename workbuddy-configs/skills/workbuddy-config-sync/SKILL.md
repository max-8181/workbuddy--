---
name: workbuddy-config-sync
description: "WorkBuddy 跨设备同步：把本机技能库与配置推送到 max-8181/workbuddy-- 仓库，或从仓库拉取到其他客户端继续项目；含续接笔记（notes/）撰写约定与本机 git 推送三个必踩坑的绕过方案。当用户说'同步到其他客户端''别的电脑也能看到''换台机器继续这个项目''sync_configs'时使用。"
agent_created: true
---

# WorkBuddy 跨设备同步

## 仓库与脚本

| 项 | 值 |
|---|---|
| 远程 | `https://github.com/max-8181/workbuddy--.git` |
| 本地副本 | `C:/Users/Administrator/WorkBuddy/2026-08-09-10-17-35` |
| 脚本 | `./sync_configs.sh push`（本机→仓库）／`./sync_configs.sh pull`（仓库→本机） |
| 同步内容 | `workbuddy-configs/`（skills + SOUL/IDENTITY/USER/settings/mcp-approvals + notes） |

## 流程

### 推送（当前电脑）

```bash
cd C:/Users/Administrator/WorkBuddy/2026-08-09-10-17-35
./sync_configs.sh push
```

脚本已内置三个坑的处理。若卡住，用排查表（见下）。

### 拉取（其他客户端）

```bash
git clone https://github.com/max-8181/workbuddy--.git     # 新机器
git pull                                                  # 已有副本
./sync_configs.sh pull                                    # 恢复到 ~/.workbuddy
```

pull 会先把本机现有 skills 备份为 `~/.workbuddy/.skills.local-<时间戳>`，不会直接覆盖丢失。

### 写续接笔记（关键步骤，别省）

光同步技能不够——**对话上下文不会同步**。会话结束前必须写一份续接笔记：

`workbuddy-configs/notes/YYYY-MM-DD-<主题>.md`，必含四块：
1. **本次变更**：改了哪些技能／文件，体量变化，备份位置
2. **结论**：分析或产出的核心结论（数据基准日、关键数字、判断）
3. **待办**：未完成项、缺什么数据、精度限制
4. **其他客户端怎么继续**：拉取命令、依赖环境、源文件路径是否可得

同目录可附 `YYYY-MM-DD-原始工作日志.md`（当天工作区 memory 的副本，保留踩坑细节）。

> 与 `<工作区>/.workbuddy/memory/` 的区别：memory 的工作区路径**每台机器都不同**（`WorkBuddy/<时间戳>/`），同步不了；notes/ 在仓库里，全设备可见。

## 本机 git 三个必踩坑

| 症状 | 原因 | 处理 |
|---|---|---|
| push 永久挂起、无报错 | PortableGit 系统级 `credential.helper=helper-selector` | `GIT_CONFIG_NOSYSTEM=1` |
| 连接超时（curl 20s 返回 000） | **github.com 直连不通**，必须走代理 | `http.proxy=http://localhost:15236`（端口变了用 `WB_SYNC_PROXY` 覆盖） |
| `CRYPT_E_REVOCATION_OFFLINE` | schannel 吊销检查离线 | `http.schannelCheckRevoke=false` |

一键可用命令：

```bash
GIT_CONFIG_NOSYSTEM=1 git -c http.proxy=http://localhost:15236 \
  -c https.proxy=http://localhost:15236 \
  -c http.schannelCheckRevoke=false push origin HEAD
```

**注意：`api.github.com` 直连可达（200）但 `github.com` 不可达**——别用前者判断网络，会误判。10808 那个代理不可用，`--noproxy '*'` 只对 api.github.com 有效。

凭据问题：`~/.gitconfig` 的 credential.helper 曾指向失效的 `~/.workbuddy/vendor/PortableGit/.../git-credential-manager.exe`，正确路径是 `C:/Program Files/Git/mingw64/bin/git-credential-manager.exe`。Windows 凭据管理器里存有 GitHub 凭据（用户 max-8181），可用 `git credential fill` 验证。

## 安全与卫生

- **不要在同步目录里用 `rm -rf`**：会触发安全策略被拒。`sync_configs.sh` 已改为**合并复制**（`cp -r src/. dst/`），不做删除。
- 本地回滚备份目录（`.xxx.bak-<时间戳>`）由 `.gitignore` 的 `workbuddy-configs/skills/.*.bak-*/` 排除，不进仓库。
- `upload_creds.json`、`*.key`、`*.pem` 已在 .gitignore 中，勿强推。

## 验证

推送后用 API 核验（api.github.com 直连可达，无需代理）：

```bash
curl --noproxy '*' -s https://api.github.com/repos/max-8181/workbuddy--/contents/workbuddy-configs/skills | grep -o '"name": "[^"]*"'
```

确认新技能在其中，再抽查 `contents/workbuddy-configs/skills/<skill>/chapters` 的文件数。
