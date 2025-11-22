# ADR-0021: タスク管理モデル (Task)

- 日付: 2025-11-22
- ステータス: 提案中
- レイヤ: core
- 種別: ドメインモデル
- 関連コンポーネント: core.models.Task, apps.task_planner

---

## 1. 背景 / コンテキスト

エージェントは「興味」や「フィードバック」に基づいて、次に何をするか（調査、実験、まとめ記事作成など）を計画する必要があります。
これを実行可能な単位として管理するためのモデルが必要です。

---

## 2. 決定

**Task** モデルを定義し、ステータス、優先度、実行に必要なコンテキスト（関連テーマ、期限など）を管理します。

```python
class TaskStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class Task(BaseModel):
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: int
    related_theme_id: str | None
    created_at: datetime
    due_date: datetime | None
    result_report_id: str | None  # 完了時に生成されたレポート
```

---

## 3. 選択肢と評価

### 採用案 (Simple Task Model)

- メリット:
  - **自律性**: エージェント自身がタスクを生成・消化するループを作りやすい。
  - **可視化**: 人間が「今エージェントが何をしようとしているか」を確認できる。
- デメリット:
  - 既存のタスク管理ツール（Todoist, GitHub Issues）と重複する可能性がある。

### 代替案 A (GitHub Issues 連携)

- 概要: タスクをすべて GitHub Issues として管理する。
- 採用しなかった理由:
  - API レート制限や、大量の微細なタスク（「検索して要約する」レベル）によるノイズが懸念される。
  - 内部的な思考プロセスとしてのタスクは内部DBで完結させたい。

---

## 4. 根拠（評価軸と判断）

- **Autonomy**: エージェントが外部サービスに依存せず、自律的に思考・行動サイクルを回せるようにするため。
- **Traceability**: 「なぜそのレポートが書かれたのか」という動機（タスク）を追跡可能にするため。

---

## 5. 影響範囲

- **Apps**: `TaskPlanner` がタスクを生成し、`Executor` が消化するアーキテクチャになる。

---

## 6. 関連 ADR

- ADR-0006: コアドメインモデル
