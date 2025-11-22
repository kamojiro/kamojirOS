# ADR-0014: CLI フレームワーク (Typer)

- 日付: 2025-11-22
- ステータス: 承認
- レイヤ: apps / interface
- 種別: ライブラリ選定
- 関連コンポーネント: src/kamojiros/cli

---

## 1. 背景 / コンテキスト

Kamojiros は多くの機能を CLI ツールとして提供します（レポート作成、検索、統計など）。
使いやすく、開発しやすい CLI フレームワークが必要です。

---

## 2. 決定

**Typer** を採用します。

- **Type Hints**: Python の型ヒントを使って引数やオプションを定義できる。
- **Completion**: シェル補完をサポートしている。
- **Subcommands**: `kamojiros create`, `kamojiros list` のようなサブコマンド構成が容易。

---

## 3. 選択肢と評価

### 採用案 (Typer)

- メリット:
  - **開発体験**: 型ヒントを書くだけで CLI が定義でき、コード量が減る。
  - **Click ベース**: 内部は Click なので、必要なら Click の機能も使える。
- デメリット:
  - 特になし。

### 代替案 A (Argparse)

- 概要: 標準ライブラリ。
- 採用しなかった理由:
  - 記述が冗長。型チェックとの連携が弱い。

### 代替案 B (Click)

- 概要: Typer の基盤。デコレータベース。
- 採用しなかった理由:
  - Typer の方が型ヒントを活用でき、よりモダンに書ける。

---

## 4. 根拠（評価軸と判断）

- **Productivity**: CLI ツールを素早く量産する必要があるため、ボイラープレートの少なさを重視しました。
- **Consistency**: Pydantic と同様に「型ヒント中心」の設計思想で統一するため。

---

## 5. 影響範囲

- **CLI**: `src/kamojiros/cli/` 配下にコマンドを実装。
- **Entrypoint**: `pyproject.toml` の `[project.scripts]` に `kamojiros` コマンドを登録。

---

## 6. 関連 ADR

- ADR-0009: Python バージョン (型ヒント活用)
