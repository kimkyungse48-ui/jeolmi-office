#!/usr/bin/env bash
# Jeolmi Office — GitHub Pages(gh-pages 브랜치) 배포 스크립트
#
#   ./scripts/deploy_pages.sh                              # 기본 저장소로 배포
#   ./scripts/deploy_pages.sh git@github.com:내계정/저장소.git   # 다른 저장소로 배포
#   DRY_RUN=1 ./scripts/deploy_pages.sh                    # 푸시 없이 결과만 확인
#
# 전제: PC에 git이 있고, GitHub에 저장소가 이미 만들어져 있어야 한다.
#       (저장소는 github.com/new 에서 먼저 만든 뒤 실행)
set -euo pipefail

REPO="${1:-git@github.com:kimkyungse48-ui/jeolmi-office.git}"
BRANCH="gh-pages"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE_URL="$REPO"
if [ -d "$REPO" ]; then
  REMOTE_URL="$(cd "$REPO" && pwd)"
fi

echo "▶ 소스 폴더 : $SRC_DIR"
echo "▶ 배포 대상 : $REPO ($BRANCH 브랜치)"

for f in index.html styles.css app.js manifest.webmanifest sw.js; do
  [ -f "$SRC_DIR/$f" ] || { echo "✖ $f 파일이 없어요. 앱 폴더에서 다시 실행해 주세요."; exit 1; }
done
[ -d "$SRC_DIR/assets" ] || { echo "✖ assets 폴더가 없어요."; exit 1; }

WORK_DIR="$(mktemp -d)"
KEEP_DIR=""
cleanup() { rm -rf "$WORK_DIR"; [ -n "$KEEP_DIR" ] && rm -rf "$KEEP_DIR"; }
trap cleanup EXIT

SITE="$WORK_DIR/site"
mkdir -p "$SITE/assets"

# 배포에 필요한 파일만 복사 (미리보기 이미지·스크립트는 제외)
cp "$SRC_DIR/index.html" "$SRC_DIR/styles.css" "$SRC_DIR/app.js" \
   "$SRC_DIR/manifest.webmanifest" "$SRC_DIR/sw.js" "$SITE/"
cp "$SRC_DIR/assets/office-bg.png" "$SRC_DIR/assets/office-bg.jpg" \
   "$SRC_DIR/assets/office-bg-night.png" "$SRC_DIR/assets/office-bg-night.jpg" \
   "$SRC_DIR/assets/icon-192.png" "$SRC_DIR/assets/icon-512.png" "$SITE/assets/" 2>/dev/null || true
# GitHub Pages 에서 Jekyll 처리를 건너뛰게 함
touch "$SITE/.nojekyll"

cd "$SITE"
git init -q
git checkout -q -b "$BRANCH"
git add -A

if git -c user.name="Jeolmi" -c user.email="jeolmi@users.noreply.github.com" \
     commit -q -m "deploy: Jeolmi Office $(date '+%Y-%m-%d %H:%M')" ; then
  :
else
  echo "• 바뀐 내용이 없어 배포를 건너뜁니다."
  exit 0
fi

if [ "${DRY_RUN:-0}" = "1" ]; then
  echo "▶ DRY_RUN — 푸시하지 않고 배포본만 확인합니다."
  git --no-pager log --oneline -1
  git --no-pager show --stat --oneline HEAD | head -20
  exit 0
fi

git remote add origin "$REMOTE_URL"
echo "▶ gh-pages 브랜치를 푸시합니다…"
git push -f origin "$BRANCH"

echo "✔ 배포 완료!"
echo "  저장소가 kimkyungse48-ui/jeolmi-office 라면 주소는"
echo "  https://kimkyungse48-ui.github.io/jeolmi-office/"
echo "  (Settings → Pages 에서 Source = Deploy from a branch, Branch = gh-pages /root 로 한 번만 설정)"
