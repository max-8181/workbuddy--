#!/bin/bash
# ============================================================
# WorkBuddy 跨设备同步脚本
# 用法:
#   ./sync_configs.sh push   — 将本地配置推送到仓库（当前电脑）
#   ./sync_configs.sh pull   — 从仓库拉取配置到本地（新电脑）
# ============================================================

set -e

# PortableGit 的系统级 credential.helper=helper-selector 会让 git push 永久挂起，全程禁用
export GIT_CONFIG_NOSYSTEM=1
# github.com 本机直连不通，默认走本机代理；可用 WB_SYNC_PROXY 环境变量覆盖
SYNC_PROXY="${WB_SYNC_PROXY:-http://localhost:15236}"

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIGS_DIR="$REPO_DIR/workbuddy-configs"
WB_HOME="$HOME/.workbuddy"

# 需要同步的配置文件列表
CONFIG_FILES="SOUL.md IDENTITY.md USER.md settings.json mcp-approvals.json"

echo "=========================================="
echo "  WorkBuddy 跨设备同步工具"
echo "=========================================="
echo ""

case "$1" in
  push)
    echo "[推送模式] 将本地 ~/.workbuddy 配置同步到仓库"
    echo ""

    # 同步 skills 目录
    # 注：用合并复制（cp -r 到已存在目录），不用 rm -rf —— 避免误删与权限拦截。
    # 本地回滚备份目录（形如 .xxx.bak-*）会一并复制进来，但 .gitignore 已排除，不会提交。
    if [ -d "$WB_HOME/skills" ]; then
      echo "→ 同步 skills/ ..."
      mkdir -p "$CONFIGS_DIR/skills"
      cp -r "$WB_HOME/skills/." "$CONFIGS_DIR/skills/"
      echo "  完成: $(find "$CONFIGS_DIR/skills" -type f | wc -l) 个文件（备份目录已由 .gitignore 排除）"
    fi

    # 项目续接笔记放 workbuddy-configs/notes/，在 workbuddy-configs 下会自动纳入提交

    # 同步配置文件
    for f in $CONFIG_FILES; do
      if [ -f "$WB_HOME/$f" ]; then
        cp "$WB_HOME/$f" "$CONFIGS_DIR/$f"
        echo "→ 已同步: $f"
      fi
    done

    echo ""
    echo "✅ 推送完成！现在可以 git commit && git push"
    echo ""

    # 自动提交 + 推送
    # 本机（2026-10 实测）三个必踩的坑，已全部内置处理：
    #   1) github.com 直连不通（curl 20s 超时），必须走本机代理；代理端口可用 WB_SYNC_PROXY 覆盖
    #   2) PortableGit 的系统级 credential.helper=helper-selector 会让 push 永久挂起 → GIT_CONFIG_NOSYSTEM=1
    #   3) schannel: CRYPT_E_REVOCATION_OFFLINE → http.schannelCheckRevoke=false
    cd "$REPO_DIR"
    GITCMD="git -c http.proxy=$SYNC_PROXY -c https.proxy=$SYNC_PROXY -c http.schannelCheckRevoke=false"
    echo "→ 代理: $SYNC_PROXY"
    $GITCMD add workbuddy-configs/
    $GITCMD commit -m "sync: update workbuddy configs $(date '+%Y-%m-%d %H:%M')" || echo "(无变更需要提交)"
    $GITCMD push || echo "⚠️  push 失败：若代理不通，改用 WB_SYNC_PROXY=http://<host>:<port> ./sync_configs.sh push"
    ;;

  pull)
    echo "[拉取模式] 从仓库恢复配置到 ~/.workbuddy"
    echo ""

    # 确保目标目录存在
    mkdir -p "$WB_HOME"

    # 恢复 skills 目录（覆盖前先把本机的备份一份，避免丢自有的技能）
    if [ -d "$CONFIGS_DIR/skills" ]; then
      if [ -d "$WB_HOME/skills" ]; then
        mv "$WB_HOME/skills" "$WB_HOME/.skills.local-$(date '+%Y%m%d-%H%M%S')"
        echo "→ 本机原有 skills 已备份为 ~/.workbuddy/.skills.local-*"
      fi
      echo "→ 恢复 skills/ ..."
      cp -r "$CONFIGS_DIR/skills" "$WB_HOME/skills"
      echo "  完成: $(find "$WB_HOME/skills" -type f | wc -l) 个文件"
    fi

    # 恢复配置文件
    for f in $CONFIG_FILES; do
      if [ -f "$CONFIGS_DIR/$f" ]; then
        cp "$CONFIGS_DIR/$f" "$WB_HOME/$f"
        echo "→ 已恢复: $f"
      fi
    done

    echo ""
    echo "✅ 拉取完成！"
    echo ""
    echo "⚠️  注意事项："
    echo "   1. MCP 连接器（如 ima-mcp）需要在 WorkBuddy 界面中重新连接"
    echo "   2. Python venv 需要重新创建（见 README.md）"
    echo "   3. AutoCAD COM 自动化需要本机安装 AutoCAD"
    echo "   4. upload_creds.json 含 COS 密钥，未同步，需要重新获取"
    ;;

  *)
    echo "用法:"
    echo "  ./sync_configs.sh push   — 当前电脑：推送配置到仓库"
    echo "  ./sync_configs.sh pull   — 新电脑：从仓库拉取配置"
    ;;
esac

echo ""
echo "==========================================