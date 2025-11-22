# ADR-0010: リンターとフォーマッター (Ruff)

- 日付: 2025-11-22
- ステータス: 承認
- レイヤ: dev-experience
- 種別: ツール選定
- 関連コンポーネント: pyproject.toml

---

## 1. 背景 / コンテキスト

Python のコード品質を保つために、リンターとフォーマッターが必要です。
従来は `flake8`, `isort`, `black`, `pydocstyle` などを組み合わせて使っていましたが、設定が分散し、実行速度も遅いという課題がありました。

---

## 2. 決定

**Ruff** を全面的に採用し、リンターとフォーマッターを統一します。

- **Linter**: `ruff check`
- **Formatter**: `ruff format`
- **Import Sorting**: Ruff の `isort` 互換機能を使用。

---

## 3. 選択肢と評価

### 採用案 (Ruff)

- メリット:
  - **速度**: Rust 製で極めて高速。
  - **統合**: 多数のプラグイン（flake8, isort, pydocstyle, pyupgrade 等）が 1 つのツールにまとまっている。
  - **設定**: `pyproject.toml` 一箇所で完結する。
- デメリット:
  - まだ発展途上で、稀に挙動が変わることがある（許容範囲）。

### 代替案 A (Flake8 + Black + Isort)

- 概要: 従来の構成。
- 採用しなかった理由:
  - 遅い。設定ファイルが増える。

---

## 4. 根拠（評価軸と判断）

- **Speed**: CI やローカルでのフィードバックループを短くするため。
- **Simplicity**: ツールチェーンを簡素化するため。

---

## 5. 影響範囲

- **Editor**: VS Code の拡張機能として `charliermarsh.ruff` を推奨。
- **CI**: `ruff check` と `ruff format --check` を実行。

---

## 6. 関連 ADR

- ADR-0009: Python バージョンとパッケージ管理
