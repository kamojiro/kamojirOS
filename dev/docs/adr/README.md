# Architecture Decision Records (ADR)

Kamojiros プロジェクトのアーキテクチャ決定記録です。

## 全体像 (High-Level Architecture)

システム全体の設計思想や構造については、まず以下を参照してください。

- [ADR-0001: システムアーキテクチャ概観 (Second Brain)](0001-system-architecture-overview.md)
- [ADR-0002: レイヤードアーキテクチャ戦略](0002-layered-architecture-strategy.md)

## インデックス

### 1. Core / Domain (ドメインモデル・ルール)

- [ADR-0006: コアドメインモデル (Report / Activity)](0006-core-domain-models.md)
- [ADR-0017: エラーハンドリング方針](0017-error-handling-policy.md)
- [ADR-0020: フィードバックシグナルモデル (提案中)](0020-feedback-signal-model.md)
- [ADR-0021: タスク管理モデル (提案中)](0021-task-management-model.md)

### 2. Infrastructure (基盤・データストア)

- [ADR-0003: レポートホスティング戦略 (GitLab Pages)](0003-report-hosting-strategy.md)
- [ADR-0005: レポート保存形式 (Markdown)](0005-report-storage-format.md)
- [ADR-0007: 検索インデックス戦略](0007-search-index-strategy.md)
- [ADR-0008: 興味プロファイル管理](0008-interest-profile-management.md)
- [ADR-0016: ログ出力戦略](0016-logging-strategy.md)
- [ADR-0018: 非同期処理の採用 (asyncio)](0018-async-io-adoption.md)
- [ADR-0019: CI/CD パイプライン](0019-ci-cd-pipeline.md)
- [ADR-0022: Misskey 収集戦略 (提案中)](0022-misskey-ingestion-strategy.md)
- [ADR-0025: ベクトルストア実装 (提案中)](0025-vector-store-implementation.md)

### 3. Apps / Agents (アプリケーション・エージェント)

- [ADR-0004: エージェントフレームワーク採用方針 (Pydantic AI)](0004-agent-framework-adoption.md)
- [ADR-0023: テーマ生成ロジック (提案中)](0023-theme-generation-logic.md)
- [ADR-0024: レポート昇格ワークフロー (提案中)](0024-report-promotion-workflow.md)
- [ADR-0026: 自己観察集計戦略 (提案中)](0026-self-observation-aggregation-strategy.md)

### 4. Dev Experience / Tools (開発環境・ツール)

- [ADR-0009: Python バージョンとパッケージ管理 (uv)](0009-python-version-and-package-manager.md)
- [ADR-0010: リンターとフォーマッター (Ruff)](0010-linter-and-formatter.md)
- [ADR-0011: 型チェック方針 (Pyright)](0011-type-checking-policy.md)
- [ADR-0012: テストフレームワーク (pytest + nox)](0012-testing-framework.md)
- [ADR-0013: 設定管理 (Pydantic Settings)](0013-configuration-management.md)
- [ADR-0014: CLI フレームワーク (Typer)](0014-cli-framework.md)
- [ADR-0015: プロジェクト構成 (src layout)](0015-project-structure.md)
