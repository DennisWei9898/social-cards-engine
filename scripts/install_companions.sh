#!/usr/bin/env bash
# 安裝 social-cards-engine 的「伴生 skill」到 ~/.claude/skills/
#
# 重要：這個腳本**不散布別人的作品**——它只是從各 skill 的**官方 repo** 幫你 clone 下來，
# 你是直接向原作者取得、依原作者的授權使用。social-cards-engine 本身不打包這些 skill。
#
# 伴生 skill（皆為選用，裝了引擎自動借力；沒裝引擎也能獨立跑）：
#   • huashu-design (by alchaincyf/花叔) —— 前置設計對焦 + 後段版面 QA
#       ⚠️ 授權＝Personal Use License：個人免費；公司/團隊/工作室/客戶交付/商用
#          須先向作者取得書面授權（見其 repo 的 LICENSE）。
#   • claude-skill-social-post (by Hao0321) —— 演算法擴散權重 + 半自動發文
#
# 用法：
#   bash scripts/install_companions.sh            # 裝全部（已存在則跳過）
#   bash scripts/install_companions.sh huashu     # 只裝 huashu-design
#   bash scripts/install_companions.sh --update    # 已存在的改跑 git pull 更新
set -euo pipefail

SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
UPDATE=0
ONLY=""
for arg in "$@"; do
  case "$arg" in
    --update) UPDATE=1 ;;
    huashu|huashu-design) ONLY="huashu-design" ;;
    social|social-post) ONLY="social-post" ;;
    *) echo "未知參數：$arg" >&2 ;;
  esac
done

command -v git >/dev/null 2>&1 || { echo "✗ 需要 git，請先安裝。" >&2; exit 1; }
mkdir -p "$SKILLS_DIR"
echo "→ 安裝目錄：$SKILLS_DIR"
echo

# install_skill <資料夾名> <官方 git url> <一句說明>
install_skill() {
  local name="$1" url="$2" note="$3"
  [ -n "$ONLY" ] && [ "$ONLY" != "$name" ] && return 0
  local dest="$SKILLS_DIR/$name"
  if [ -d "$dest/.git" ]; then
    if [ "$UPDATE" -eq 1 ]; then
      echo "↻ 更新 $name（git pull）…"
      git -C "$dest" pull --ff-only || echo "  ⚠️ $name 更新失敗（可能有本地修改），略過。"
    else
      echo "✓ $name 已存在，跳過（要更新加 --update）。"
    fi
  elif [ -e "$dest" ]; then
    echo "⚠️ $dest 已存在但不是 git repo，未動它。請自行確認。"
  else
    echo "⇩ 安裝 $name —— $note"
    echo "   來源（官方）：$url"
    git clone --depth 1 "$url" "$dest" && echo "✓ $name 裝好了。"
  fi
  echo
}

install_skill "huashu-design" "https://github.com/alchaincyf/huashu-design.git" \
  "前置設計對焦 + 後段版面 QA（by alchaincyf/花叔）"

# 提醒：huashu-design 為個人使用授權，商用/客戶案須另外取得授權
if [ -z "$ONLY" ] || [ "$ONLY" = "huashu-design" ]; then
  echo "⚠️  huashu-design 授權提醒：Personal Use License（作者 alchaincyf/花叔）。"
  echo "    個人免費；公司/團隊/客戶交付/商用須先向作者取得書面授權（見其 LICENSE）。"
  echo "    social-cards-engine（MIT）不改變其授權；商用請自行確認。"
  echo
fi

install_skill "social-post" "https://github.com/Hao0321/claude-skill-social-post.git" \
  "演算法擴散權重 + 半自動發文（by Hao0321）"

echo "完成。這些 skill 皆為選用——沒裝，引擎會走內建 fallback（設計對焦用引擎渲一張真封面卡）。"
