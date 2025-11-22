# ADR-0022: Misskey 収集戦略 (Streaming vs Polling)

- 日付: 2025-11-22
- ステータス: 提案中
- レイヤ: infrastructure
- 種別: データ収集
- 関連コンポーネント: apps.misskey_ingestor

---

## 1. 背景 / コンテキスト

Kamojiros はユーザーの活動（Activity）の主要なソースとして Misskey を利用します。
リアルタイム性を重視するか、確実性を重視するかによって収集方式が異なります。

---

## 2. 決定

**Polling (REST API)** を基本とし、補助的に **Streaming (WebSocket)** を使用するハイブリッド構成を提案します。
初期フェーズでは **Polling のみ** で実装します。

- **Polling**: 定期的（例: 10分ごと）に `notes/timeline` 等を取得。
- **Streaming**: 将来的に「即座に反応するエージェント」を作る場合に導入。

---

## 3. 選択肢と評価

### 採用案 (Polling First)

- メリット:
  - **堅牢性**: ネットワーク切断やサーバー再起動に強い。再開時に「前回の取得地点」から取り直せば漏れがない。
  - **実装難易度**: WebSocket より簡単。
- デメリット:
  - リアルタイム性に劣る。

### 代替案 A (Streaming Only)

- 概要: WebSocket で常時接続。
- 採用しなかった理由:
  - 切断時の再接続ロジックや、切断中のデータ欠損の補完（結局 Polling が必要になる）が複雑。

---

## 4. 根拠（評価軸と判断）

- **Reliability**: データの取りこぼしを防ぐことを最優先しました。
- **Simplicity**: まずは確実に動くものを作るため。

---

## 5. 影響範囲

- **Infrastructure**: `MisskeyClient` に `fetch_notes(since_id, until_id)` のようなメソッドが必要。
- **State Management**: 「どこまで読んだか」を保存するカーソル管理が必要。

---

## 6. 関連 ADR

- ADR-0006: コアドメインモデル (Activity)
