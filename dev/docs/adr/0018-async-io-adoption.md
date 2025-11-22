# ADR-0018: 非同期処理の採用 (asyncio)

- 日付: 2025-11-22
- ステータス: 承認
- レイヤ: core / infrastructure
- 種別: アーキテクチャ
- 関連コンポーネント: infrastructure.misskey, infrastructure.llm

---

## 1. 背景 / コンテキスト

Kamojiros は、Misskey API へのアクセス、LLM の推論待ち、Git 操作など、I/O 待ちが発生する処理を多く含みます。
これらを効率的に実行するためには、非同期処理の導入が検討されます。

---

## 2. 決定

**asyncio** を全面的に採用します。
I/O バウンドな処理（API クライアント、DB アクセス）はすべて非同期関数（`async def`）として実装します。

- **HTTP Client**: `httpx` (AsyncClient)
- **File I/O**: 必要に応じて `aiofiles` または `anyio`（ただしローカルファイル操作は同期でも許容する場合あり）。
- **Framework**: Pydantic AI も非同期サポートがあるため、整合性が取れる。

---

## 3. 選択肢と評価

### 採用案 (asyncio)

- メリット:
  - **並行性**: 複数の LLM リクエストや API コールを並列に投げられるため、全体の処理時間を大幅に短縮できる。
  - **エコシステム**: 現代の Python ライブラリ（FastAPI, Pydantic AI, LangChain 等）は asyncio 前提のものが多い。
- デメリット:
  - 同期コードと非同期コードの混在（Function Coloring Problem）が面倒。
  - デバッグが少し難しくなる。

### 代替案 A (Threading)

- 概要: `concurrent.futures.ThreadPoolExecutor` を使う。
- 採用しなかった理由:
  - スレッドセーフの管理が難しい。
  - コンテキストスイッチのオーバーヘッドがある。

---

## 4. 根拠（評価軸と判断）

- **Performance**: エージェントの応答速度（スループット）を最大化するため。
- **Modernity**: 今後の Python エコシステムの主流に合わせるため。

---

## 5. 影響範囲

- **Codebase**: 基本的に `async def` で書くことになる。CLI エントリポイント（Typer）は `anyio.run` 等で非同期関数を呼ぶ必要がある。

---

## 6. 関連 ADR

- ADR-0004: エージェントフレームワーク
