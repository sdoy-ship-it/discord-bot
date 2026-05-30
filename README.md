# 🔍 Luau Deobfuscator Discord Bot

Roblox Luauスクリプトの難読化を解析するDiscord Botです。

## ✅ 機能

| 機能 | 説明 |
|------|------|
| GUIツリー生成 | ScreenGui/Frame/TextLabel等のGUI要素を検出・ツリー化 |
| ScreenGui解析 | ScreenGui の構造を解析 |
| RemoteEvent解析 | FireServer/InvokeServer等のリモート通信を検出 |
| ModuleScript解析 | require() によるモジュール参照を検出 |
| loadstring先取得 | 動的コード実行を検出 |
| require解析 | モジュール依存関係を解析 |
| AST変換 | 16進文字列・難読化変数を変換 |
| StyLua自動整形 | StyLuaでコードを整形（インストール時） |
| 可読化コード返却 | 整形済み `.lua` ファイルを返信 |
| Web Dashboard | ブラウザで解析履歴・統計を確認 |
| Discord Slash Commands | `/set` `/status` `/unset` |
| 難読化スコア表示 | 0〜100のスコアで危険度を可視化 |
| AIレポートPDF生成 | OpenAI APIによる解析レポートをPDFで返却 |

## 🚀 セットアップ

### 1. リポジトリをクローン

```bash
git clone https://github.com/あなたのユーザー名/luau-deobfuscator-bot.git
cd luau-deobfuscator-bot
```

### 2. Python 仮想環境を作成（推奨）

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

StyLua（任意・コード整形）:
```bash
# Windows: https://github.com/JohnnyMorganz/StyLua/releases からDL
# Mac:
brew install stylua
```

### 4. `.env` ファイルを作成

```bash
cp .env.example .env
```

`.env` を開いて以下を記入:

```env
DISCORD_TOKEN=あなたのDiscordBotトークン
OPENAI_API_KEY=あなたのOpenAI APIキー
DASHBOARD_PORT=8080
```

### 5. Discord Bot の設定

Discord Developer Portal (https://discord.com/developers/applications) で:

1. アプリケーションを作成 → **Bot** タブ → **Token** をコピーして `.env` に記入
2. **Privileged Gateway Intents** で以下を有効化:
   - `MESSAGE CONTENT INTENT` ✅
   - `SERVER MEMBERS INTENT` ✅
3. **OAuth2 → URL Generator** で以下を選択:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Send Messages`, `Read Messages/View Channels`, `Attach Files`, `Read Message History`
4. 生成されたURLでBotをサーバーに招待

### 6. Bot を起動

```bash
python bot.py
```

VSCode からの起動:
- `bot.py` を開いて `F5` キー、または
- ターミナルで `python bot.py`

Web Dashboard: http://localhost:8080

## 📖 使い方

### コマンド一覧

| コマンド | 説明 | 権限 |
|---------|------|------|
| `/set` | 現在のチャンネルを解析チャンネルとして設定 | 管理者 |
| `/status` | 現在の設定チャンネルを確認 | 全員 |
| `/unset` | 設定を解除 | 管理者 |

### 解析の使い方

1. `/set` で解析チャンネルを設定
2. そのチャンネルに `.lua` または `.txt` ファイルを送信
3. Botが自動で解析を実行し、以下を返信:
   - 📊 埋め込みメッセージ（スコア・チェック項目・AIレポート）
   - 📄 可読化済み `.lua` ファイル
   - 📋 PDF解析レポート

## 📁 ファイル構成

```
luau-deobfuscator-bot/
├── bot.py                    # メインBot（ここを起動）
├── requirements.txt          # 依存パッケージ
├── .env.example              # 環境変数テンプレート
├── .env                      # 実際の環境変数（gitignore済）
├── analyzer/
│   ├── deobfuscator.py       # メイン解析エンジン
│   ├── luau_parser.py        # Luauコード解析
│   ├── stylua_formatter.py   # StyLuaフォーマット
│   └── report.py             # PDF生成
└── dashboard/
    ├── app.py                # Flask Webサーバー
    └── templates/
        └── index.html        # ダッシュボード画面
```

## 🔒 セキュリティ

- `.env` は `.gitignore` に含まれているため、GitHubにはアップロードされません
- APIキーやトークンを `.env` 以外の場所に書かないでください

## 📄 ライセンス

MIT License
