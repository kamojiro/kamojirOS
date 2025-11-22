# ADR-0019: CI/CD パイプライン (GitLab CI + Local Runner)

- 日付: 2025-11-22
- ステータス: 承認
- レイヤ: infrastructure / devops
- 種別: CI/CD
- 関連コンポーネント: .gitlab-ci.yml

---

## 1. 背景 / コンテキスト

コードの品質担保（テスト、Lint）と、成果物（レポートサイト）のデプロイを自動化したい。
ただし、個人開発であり、クラウドのリソース（GitLab Shared Runners のクレジット）を節約したい。

---

## 2. 決定

**GitLab CI** を使用し、実行環境として **Local Runner (Shell or Docker executor)** を採用します。

- **Trigger**: `git push`
- **Jobs**:
  - `test`: `nox -s test`
  - `lint`: `nox -s lint`
  - `pages`: `mkdocs build` -> GitLab Pages へデプロイ

---

## 3. 選択肢と評価

### 採用案 (GitLab CI + Local Runner)

- メリット:
  - **コスト**: 自前の PC リソースを使うため無料。
  - **速度**: ローカルのキャッシュやスペックを活かせるため、Shared Runner より速い場合が多い。
  - **統合**: GitLab Pages との連携がスムーズ。
- デメリット:
  - ローカル PC を起動しておく必要がある（常時稼働サーバーがない場合）。

### 代替案 A (GitHub Actions)

- 概要: GitHub にミラーリングして Actions を回す。
- 採用しなかった理由:
  - メインリポジトリが GitLab であるため（ADR-0003 参照）。

---

## 4. 根拠（評価軸と判断）

- **Cost Efficiency**: 個人プロジェクトとして持続可能なコスト構造にするため。
- **Simplicity**: 既存の GitLab エコシステムで完結させるため。

---

## 5. 影響範囲

- **Environment**: ローカルマシンに `gitlab-runner` をインストール・登録する必要がある。

---

## 6. 関連 ADR

- ADR-0003: レポートホスティング戦略
