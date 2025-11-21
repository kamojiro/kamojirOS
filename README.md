# Kamojiros

個人研究エージェントシステム

## セットアップ

```bash
# 依存関係のインストール
uv sync

# 環境変数の設定
cp .env.example .env
# .env を編集して KAMOJIROS_NOTES__REPO_ROOT を設定
```

## CLI コマンド

### レポート作成

新しいレポートを作成します。

```bash
# インタラクティブモード（デフォルト）
uv run kamojiros create

# コマンドライン引数で指定
uv run kamojiros create \
  --title "新しい技術メモ" \
  --type tech \
  --tags "python,cli" \
  --body "# メモの内容\n\n詳細な説明..."

# インタラクティブモードを無効化
uv run kamojiros create -I --title "タイトル" --type tech --body "内容"
```

**オプション:**
- `--title, -t`: レポートのタイトル
- `--type`: レポートの種類 (`tech`, `paper`, `life`, `meta`)
- `--tags`: カンマ区切りのタグ
- `--body, -b`: Markdown形式の本文
- `--interactive, -i` / `--no-interactive, -I`: インタラクティブモードの有効/無効

### レポート一覧表示

既存のレポートを一覧表示します。

```bash
# デフォルト（最新10件）
uv run kamojiros list

# 表示件数を指定
uv run kamojiros list --limit 20

# 日付でフィルタ
uv run kamojiros list --since 2025-11-01

# タイプでフィルタ
uv run kamojiros list --type tech

# タグでフィルタ
uv run kamojiros list --tags "python,agent"

# JSON形式で出力
uv run kamojiros list --json

# 本文のプレビューを表示
uv run kamojiros list --show-body
```

### レポート検索

キーワードでレポートを検索します。

```bash
# 全体から検索
uv run kamojiros search "キーワード"

# タイトルのみ検索
uv run kamojiros search "キーワード" --title-only

# 本文のみ検索
uv run kamojiros search "キーワード" --body-only

# タグのみ検索
uv run kamojiros search "キーワード" --tags-only
```

### 統計情報表示

レポートの統計情報を表示します。

```bash
# デフォルト（過去30日間）
uv run kamojiros stats

# 期間を指定
uv run kamojiros stats --since 2025-11-01
```

## アプリケーション

### Self Observer

過去24時間のレポートを集計し、日次レポートを自動生成します。

```bash
uv run python -m kamojiros.apps.self_observer.main
```

## 開発

### テスト実行

```bash
# すべてのテスト + Lint + Type Check
uv run nox

# テストのみ
uv run pytest
```

### コード整形

```bash
# 自動修正
uv run ruff check --fix src tests

# フォーマット
uv run ruff format src tests
```

### cspell

```bash
# 不要な cspell.json の要素を削除する
npx cspell-check-unused-words@latest --fix
```