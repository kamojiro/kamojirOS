# ADR-0020: フィードバックシグナルモデル (FeedbackSignal)

- 日付: 2025-11-22
- ステータス: 提案中
- レイヤ: core
- 種別: ドメインモデル
- 関連コンポーネント: core.models.Feedback

---

## 1. 背景 / コンテキスト

エージェントが生成したレポートや、提案したテーマが「ユーザーにとって有用だったか」を定量的に評価し、次のアクションに活かす仕組みが必要です。
単純な「いいね」だけでなく、閲覧時間、引用回数、Misskey でのリアクションなど、多様なシグナルを統一的に扱いたいと考えています。

---

## 2. 決定

**FeedbackSignal** モデルを定義し、あらゆるフィードバックを「誰が」「何に対して」「どんな強さで」行ったかのイベントとして記録します。

```python
class FeedbackSignal(BaseModel):
    id: str
    target_id: str  # Report ID or Theme ID
    source: str     # "user", "misskey", "system"
    type: str       # "rating", "reaction", "click", "citation"
    score: float    # -1.0 to 1.0 (normalized usefulness)
    raw_data: dict  # Original event data
    created_at: datetime
```

---

## 3. 選択肢と評価

### 採用案 (Event Sourcing like Signal)

- メリット:
  - **柔軟性**: 新しい種類のフィードバック（例: 脳波センサ）が増えても `type` を増やすだけで対応できる。
  - **時系列解析**: 「最初は評価が低かったが、後から評価された」といった推移を追える。
- デメリット:
  - データ量が増える（集計が必要）。

### 代替案 A (Report モデルに直接埋め込む)

- 概要: `Report.rating` フィールドを持たせる。
- 採用しなかった理由:
  - 複数のソースからの評価（Misskey のリアクション + ユーザーの直接評価）が競合する。
  - 履歴が残らない。

---

## 4. 根拠（評価軸と判断）

- **Extensibility**: 将来的にどのようなフィードバックが得られるか未知数であるため、最も汎用的なイベントモデルを採用します。
- **Analytics**: エージェントの学習（強化学習的なアプローチ）に使うための教師データとして適しています。

---

## 5. 影響範囲

- **Core**: `FeedbackSignal` モデルの追加。
- **Infrastructure**: フィードバックを保存するストア（当面はファイル追記 or SQLite）。

---

## 6. 関連 ADR

- ADR-0006: コアドメインモデル
