#!/bin/bash
# GitHub リポジトリへのアップロードスクリプト
# 使い方: bash setup_github.sh

set -e

echo "=== Luau Deobfuscator Bot — GitHub セットアップ ==="
echo ""

# Git の確認
if ! command -v git &> /dev/null; then
    echo "❌ git がインストールされていません"
    exit 1
fi

# 初期化
if [ ! -d ".git" ]; then
    git init
    echo "✅ git init 完了"
fi

# .env が .gitignore に含まれているか確認
if ! grep -q "^.env$" .gitignore 2>/dev/null; then
    echo ".env" >> .gitignore
fi

# ステージング
git add .
git commit -m "feat: initial Luau deobfuscator Discord bot" 2>/dev/null || echo "（変更なし）"

echo ""
echo "GitHubリポジトリのURLを入力してください:"
echo "例: https://github.com/yourname/luau-deobfuscator-bot.git"
read -r REPO_URL

if [ -z "$REPO_URL" ]; then
    echo "❌ URLが入力されていません"
    exit 1
fi

# リモートの設定
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL"

# ブランチ名の確認・設定
git branch -M main 2>/dev/null || true

# プッシュ
echo ""
echo "GitHubにプッシュします..."
echo "※ ユーザー名とPersonal Access Tokenの入力が求められます"
git push -u origin main

echo ""
echo "✅ GitHubへのアップロードが完了しました！"
echo "   $REPO_URL"
