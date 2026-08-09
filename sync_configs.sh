#!/bin/bash
# ============================================================
# WorkBuddy 跨设备同步脚本
# 用法:
#   ./sync_configs.sh push   — 将本地配置推送到仓库（当前电脑）
#   ./sync_configs.sh pull   — 从仓库拉取配置到本地（新电脑）
# ============================================================

set -e

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
    if [ -d "$WB_HOME/skills" ]; then
      echo "→ 同步 skills/ ..."
      rm -rf "$CONFIGS_DIR/skills"
      cp -r "$WB_HOME/skills" "$CONFIGS_DIR/skills"
      echo "  完成: $(find "$CONFIGS_DIR/skills" -type f | wc -l) 个文件"
    fi

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

    # 自动提交
    cd "$REPO_DIR"
    git add workbuddy-configs/
    git commit -m "sync: update workbuddy configs $(date '+%Y-%m-%d %H:%M')" || echo "(无变更需要提交)"
    git push || echo "⚠️  push 失败，请检查网络或仓库权限后手动 git push"
    ;;

  pull)
    echo "[拉取模式] 从仓库恢复配置到 ~/.workbuddy"
    echo ""

    # 确保目标目录存在
    mkdir -p "$WB_HOME"

    # 恢复 skills 目录
    if [ -d "$CONFIGS_DIR/skills" ]; then
      echo "→ 恢复 skills/ ..."
      rm -rf "$WB_HOME/skills"
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