# ADR-0026: 自己観察集計戦略 (Self-Observation)

- 日付: 2025-11-22
- ステータス: 提案中
- レイヤ: apps
- 種別: ロジック
- 関連コンポーネント: apps.self_observer

---

## 1. 背景 / コンテキスト

`SelfObserver` エージェントは、日々の活動（Activity）や生成されたレポート（Report）を振り返り、メタレポート（日報・週報）を作成します。
どのような粒度・トリガーで集計を行うかを決める必要があります。

---

## 2. 決定

**定期実行（Cron / Scheduler）** による **日次・週次集計** を基本とします。

1.  **Daily Review**:
    - トリガー: 毎日 0:00 (JST)
    - 対象: 前日 0:00 〜 23:59 の Activity と Report
    - 出力: `docs/journal/YYYY/MM/DD/daily-review.md`
2.  **Weekly Review**:
    - トリガー: 毎週月曜 0:00 (JST)
    - 対象: 過去7日間の Daily Review + 主要な Report
    - 出力: `docs/journal/YYYY/MM/DD/weekly-review.md`

---

## 3. 選択肢と評価

### 採用案 (Scheduled Aggregation)

- メリット:
  - **リズム**: 人間の生活リズム（1日、1週間）に合わせることで、振り返りの習慣がつきやすい。
  - **処理負荷**: まとめて処理するため、LLM のコンテキスト効率が良い（リアルタイムに毎回要約するより安い）。
- デメリット:
  - リアルタイムなフィードバック（「今使いすぎ！」など）はできない。

### 代替案 A (Real-time / Stream Processing)

- 概要: Activity が発生するたびに要約を更新する。
- 採用しなかった理由:
  - LLM API コストが跳ね上がる。
  - 「1日のまとめ」としての俯瞰的な視点が持ちにくい。

---

## 4. 根拠（評価軸と判断）

- **Cost**: LLM のトークン消費を抑えるため。
- **Context**: 「1日」という単位で区切ることで、意味のある物語（ナラティブ）を生成しやすくするため。

---

## 5. 影響範囲

- **Infrastructure**: 定期実行の仕組み（GitLab CI Schedules, GitHub Actions Schedule, または常駐プロセスのスケジューラ）が必要。
- **Apps**: `SelfObserver` に `run_daily_review(date)` メソッドを実装。

---

## 6. 関連 ADR

- ADR-0006: コアドメインモデル (ReportType.META)
