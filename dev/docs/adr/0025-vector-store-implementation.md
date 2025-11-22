# ADR-0025: ベクトルストア実装 (Supabase pgvector)

- 日付: 2025-11-22
- ステータス: 提案中
- レイヤ: infrastructure
- 種別: データストア
- 関連コンポーネント: infrastructure.vector_store

---

## 1. 背景 / コンテキスト

ADR-0007 で決定した検索インデックス戦略（Activity / Notes 分離）を実現するための具体的な技術選定が必要です。
個人開発の規模感で、コストパフォーマンスと機能のバランスが良いものが求められます。

---

## 2. 決定

**Supabase (PostgreSQL + pgvector)** を採用します。
無料枠が充実しており、SQL とベクトル検索を組み合わせて利用できる点が強みです。

- **Library**: `vecs` (Supabase 公式の Python クライアント) または `SQLAlchemy` + `pgvector` 拡張。
- **Deployment**: クラウド（Supabase Managed）を利用。

---

## 3. 選択肢と評価

### 採用案 (Supabase pgvector)

- メリット:
  - **コスト**: 無料枠で 500MB 程度まで使える（テキスト埋め込みなら十分）。
  - **SQL**: メタデータフィルタリング（`WHERE author = 'user'` 等）が強力。
  - **管理**: Web UI でデータを確認しやすい。
- デメリット:
  - 外部サービスへの依存。

### 代替案 A (Chroma / FAISS - Local)

- 概要: ローカルファイルベースのベクトルストア。
- 採用しなかった理由:
  - 永続化ファイルの管理が面倒（Git に入れるには大きすぎる）。
  - 複数エージェントからの同時アクセス（ロック制御）が難しい。

### 代替案 B (Pinecone / Weaviate)

- 概要: 専用ベクトルDB。
- 採用しなかった理由:
  - 無料枠の制限が厳しい、または期間制限がある場合が多い。
  - RDB としての機能（リレーショナルな結合など）が弱い。

---

## 4. 根拠（評価軸と判断）

- **Cost**: ランニングコストをゼロに近づけるため。
- **Flexibility**: 将来的にリレーショナルなデータ（Task, Feedback）も同じ DB に入れたくなる可能性が高いため、Postgres ベースが有利。

---

## 5. 影響範囲

- **Infrastructure**: Supabase の接続情報（URL, Key）を環境変数に追加。
- **Dependencies**: `vecs` または `psycopg` などのドライバを追加。

---

## 6. 関連 ADR

- ADR-0007: 検索インデックス戦略
