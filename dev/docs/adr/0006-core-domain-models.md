# ADR-0006: コアドメインモデル（Report / Activity）

- 日付: 2025-11-22
- ステータス: 承認
- レイヤ: core
- 種別: ドメインモデル
- 関連コンポーネント: core.models

---

## 1. 背景 / コンテキスト

Kamojiros は「自己観察」と「技術調査」を行うエージェントシステムです。
システム内で扱う主要なデータの概念（モデル）を定義し、コンポーネント間の共通言語とする必要があります。

- 目的・解決したいこと:
  - 「レポート」と「外部からの入力（アクティビティ）」を明確に区別したい。
  - 将来的な拡張（Feedback, Interest, Task）に耐えうる基盤を作りたい。
  - Python の型システムで厳密に定義したい。

---

## 2. 決定

以下の主要モデルを定義します。

1.  **Report**: システム内で生成された知識・記録。
    - `meta`: メタデータ（ID, タイトル, 日時, タグ, 著者, 種別）。
    - `body_markdown`: 本文。
2.  **Activity**: 外部サービス（Misskey, Discord 等）から収集した生のログ。
    - `id`, `type`, `content`, `created_at`, `source_url`, `raw_data`。
3.  **ReportType**: レポートの分類（`tech`, `paper`, `life`, `meta`）。
4.  **ReportAuthor**: レポートの作成者（`user`, `agent:self_observer` 等）。

---

## 3. 選択肢と評価

### 採用案（Report と Activity の分離）

- 概要:
  - 外部入力は `Activity` として保存（Immutable）。
  - 内部生成物は `Report` として保存（Mutable / Versioned）。
- メリット:
  - 入力と出力の責務が明確になる。
  - `Activity` は「事実」として変更不可にできる。
  - `Report` は編集・推敲されるものとして設計できる。

### 代替案 A (すべて Note として扱う)

- 概要: 入力も出力もすべて `Note` という単一モデルで扱う。
- 採用しなかった理由:
  - 外部データ（Misskey ノート）と内部データ（調査レポート）では、必要なメタデータやライフサイクルが大きく異なるため、単一モデルにするとフィールドが nullable だらけになる。

---

## 4. 根拠（評価軸と判断）

- **ドメインの明瞭さ**: 「収集フェーズ」と「生成フェーズ」を明確に分けるアーキテクチャ（Ingestor -> Activity -> Agent -> Report）を採用したため、モデルもそれに合わせました。
- **型安全性**: Pydantic を用いて定義することで、バリデーションとシリアライズを容易にしました。

---

## 5. 影響範囲

- **Core**: `core/models.py` に定義が集約される。
- **Apps**: 全てのアプリケーションは、このモデルを入出力の基本単位とする。

---

## 6. ロールアウト / 移行方針

- フェーズ1（完了）:
  - `Report`, `ReportMeta`, `Activity` の定義完了。
- フェーズ2以降:
  - `InterestSnapshot`, `Feedback`, `Task` などのモデルを追加予定。

---

## 7. オープンな論点 / フォローアップ

- **Report の昇格**: `journal`（日報的なログ）から `note`（体系的な知識）への昇格をどうモデルで表現するか。現在はディレクトリの違いで表現しているが、モデル上に `status` や `promoted_at` を持つべきかもしれない。
- **Activity の詳細化**: 現在は汎用的な `Activity` だが、`MisskeyNoteActivity`, `GitHubCommitActivity` のようにサブクラス化（または Discriminated Union）するかどうか。

---

## 8. 関連 ADR

- ADR-0005: レポート保存形式
- ADR-0001: システムアーキテクチャ概観
- ADR-0002: レイヤードアーキテクチャ戦略
