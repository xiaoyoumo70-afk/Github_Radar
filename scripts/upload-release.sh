#!/usr/bin/env bash
set -euo pipefail

REPO="xiaoyoumo70-afk/Github_Radar"
TAG="v0.1.0"
ROOT="/home/drawbridge/.openclaw/workspace/github-radar"
RELEASE_DIR="$ROOT/release"

echo "=== 步骤 1/3: 推送 tag ==="
cd "$ROOT"
git tag -f "$TAG"
git push origin "$TAG" --force

echo ""
echo "=== 步骤 2/3: 创建 GitHub Release ==="
gh release create "$TAG" \
  --repo "$REPO" \
  --title "$TAG — GitHub Radar 发布" \
  --notes "## 🚀 $TAG

### 下载

| 平台 | 文件 | 说明 |
|------|------|------|
| 🐧 Linux | github-radar-0.1.0-linux-x64.tar.gz | 便携包 |
| 🐧 Linux | github-radar-0.1.0-linux-x64-bundled.tar.gz | 自包含 |
| 🐧 Linux | GitHub-Radar-0.1.0.AppImage | 桌面 |
| 🐧 Linux | github-radar-0.1.0.tar.gz | 桌面 tar |
| 🐧 Linux | github-radar-cli | CLI |
| 🪟 Windows | github-radar-0.1.0-windows-x64.zip | 便携包 |

### 使用
\`\`\`bash
tar xzf github-radar-*-linux-x64.tar.gz
cd github-radar-*
cp .env.example .env  # 编辑配置
./GitHub-Radar.sh      # 打开 http://localhost:4420
\`\`\`" \
  --verify-tag 2>/dev/null || true

echo ""
echo "=== 步骤 3/3: 上传文件 ==="
gh release upload "$TAG" \
  "$RELEASE_DIR/linux/"* \
  "$RELEASE_DIR/windows/"* \
  --repo "$REPO" \
  --clobber

echo ""
echo "📦 Release: https://github.com/$REPO/releases/tag/$TAG"
