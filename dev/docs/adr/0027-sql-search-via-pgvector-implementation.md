# ADR-0027: SQL Search via pgvector Implementation

- 日付: 2025-12-14
- ステータス: 承認
- レイヤ: infrastructure / services
- 種別: データストア / エージェント統合
- 関連コンポーネント: infrastructure.rag.activity_index_query_repository / activity_bootstrap / services.rag.activity_retrieve_service / services.qa_service

---

## 1. 背景 / コンテキスト

この ADR で「何を」「なぜ」決めるのかを、プロジェクト文脈で書く。

- 目的・解決したいこと:
  - pgvector で管理される `activity_index` テーブルに対する直接的なSQLクエリ機能を提供し、ベクトル検索のオーバーヘッドなしに日付範囲フィルタリングなどの柔軟な検索を可能にする。
- 前提・制約:
  - `activity_index` テーブルは主に pgvector で管理されている。
- この ADR がカバーする範囲:
  - `activity_index` に対する直接SQLクエリの実装、共有 `AsyncEngine` の利用、サービスへの統合、およびエージェントツールとしての提供。

---

## 2. 決定

`activity_index` テーブルに対して直接SQLクエリを実行するための `ActivityIndexQueryRepository` を実装し、共有 `AsyncEngine` を用いてデータベース接続を効率化し、関連サービスに統合する。これにより、ベクトル検索とは独立した柔軟な検索機能を提供する。QAサービスのエージェントは、特定の期間検索のためにこの機能をツールとして利用する。

---

## 3. 選択肢と評価

検討した選択肢と、その評価を軽くまとめる。

### 採用案（本 ADR の決定）

- 概要:
  - `ActivityIndexQueryRepositoryImpl` を作成し、`src/kamojiros/infrastructure/rag/activity_index_query_repository.py` に配置。
  - `sqlalchemy` Core を使用して SELECT ステートメントを構築し、結果を `Activity` Pydantic モデルにマッピング。`metadata` JSONB カラムの抽出もハンドリングする。
  - `src/kamojiros/activity_bootstrap.py` で `AsyncEngine` を明示的に作成し、`langchain-postgres` の VectorStore と `ActivityIndexQueryRepositoryImpl` で共有。
  - `src/kamojiros/services/rag/activity_retrieve_service.py` に `list_between_activity` メソッドを追加し、`query_repo` に処理を委譲。
  - `src/kamojiros/services/qa_service.py` に `list_between` ツールを追加し、`QA_SYSTEM_PROMPT` を更新してエージェントが特定の期間検索（例: "last week"）に利用するように誘導。
- メリット:
  - 日付範囲フィルタリングなど、ベクトル検索では難しい厳密かつ柔軟なクエリが可能になる。
  - ベクトル検索のオーバーヘッドなしに、特定の条件での検索パフォーマンスを向上できる。
  - データベース接続エンジンを共有することで、リソース効率が向上し、管理が簡素化される。
- デメリット / リスク:
  - 直接SQLクエリのロジックと、Pydantic モデルへのマッピングロジックを独自に管理する必要がある。これにより、実装と保守の複雑さが増す可能性がある。

### 代替案 A: ベクトル検索のみを使用

- 概要:
  - `activity_index` テーブルに対する検索は、常にベクトル検索のみを使用し、キーワードや日付によるフィルタリングはベクトル空間内での類似度検索に依存する。
- 採用しなかった理由:
  - 日付範囲フィルタリングのような厳密な検索条件に正確に対応することが難しく、ユーザーの意図に沿わない検索結果を返す可能性があるため。また、特定のメタデータに基づくフィルタリングには不向き。

---

## 4. 根拠（評価軸と判断）

どんな観点で比較して、この決定になったかを書く。

- ビジョンとの整合:
  - ユーザーの多様な検索ニーズに応え、より正確で柔軟な情報取得を可能にするシステムを目指すプロジェクト方針に合致する。特に、特定の日付範囲におけるアクティビティの取得は、エージェントの利用価値を高める。
- 非機能要件:
  - パフォーマンスと柔軟性を両立させるための選択。厳密な条件での高速な検索を可能にし、ベクトル検索が最適でないシナリオを補完する。共有 `AsyncEngine` は、リソース利用の最適化に貢献する。
- チーム / 自分のスキル・運用コスト:
  - SQLAlchemy Core の利用は既存のPythonスキルセットで管理可能であり、大規模な追加学習コストは発生しない。データベースアクセスパターンを明示的に制御できるため、将来的な最適化やデバッグが容易になる。

---

## 5. 影響範囲

この決定が影響するものを列挙する。

- コード / ディレクトリ構成:
  - `src/kamojiros/infrastructure/rag/activity_index_query_repository.py` の新規作成。
  - `src/kamojiros/activity_bootstrap.py` のデータベースエンジン初期化ロジックの変更。
  - `src/kamojiros/services/rag/activity_retrieve_service.py` に新しい検索メソッドの追加。
  - `src/kamojiros/services/qa_service.py` に新しいエージェントツールの追加とプロンプトの更新。
- 既存・将来のコンポーネント:
  - `langchain-postgres` の VectorStore が `AsyncEngine` を共有するようになる。
  - QAサービスのエージェントは、日付範囲によるアクティビティ検索のための新しい `list_between` ツールを利用可能になる。

---

## 6. ロールアウト / 移行方針

フェーズ付きの計画に沿って、「いつ・どう適用するか」を簡単に書く。

- 既に実装・検証済みであり、システムに統合されている。
- 既存のベクトル検索機能と並行して動作し、大きな移行作業は不要。

---

## 7. オープンな論点 / フォローアップ

この ADR では決めきらなかった点や、別 ADR に切り出す前提をメモしておく。

- open question:
  - `list_between` クエリのパフォーマンスをさらに最適化するための PostgreSQL インデックス戦略の適用。具体的には、`created_at` カラムや `source` と `created_at` の複合インデックス（例: `CREATE INDEX CONCURRENTLY idx_activity_created_at ON activity_index (created_at DESC);`）の導入を検討する必要がある。

---

## 8. 関連 ADR

- ADR-0025: Vector Store Implementation (pgvector の採用を決定した ADR)
