# ADR-0013: 設定管理 (Pydantic Settings)

- 日付: 2025-11-22
- ステータス: 承認
- レイヤ: core / infrastructure
- 種別: 設定管理
- 関連コンポーネント: src/kamojiros/config/base_settings.py

---

## 1. 背景 / コンテキスト

アプリケーションの設定（API キー、パス、フラグ等）を環境変数や `.env` ファイルから読み込み、型安全に扱う必要があります。

---

## 2. 決定

**Pydantic Settings** を採用します。
設定クラスは `BaseSettings` を継承し、環境変数プレフィックス `KAMOJIROS_` を使用します。

- **Source**: 環境変数 > `.env` ファイル > デフォルト値
- **Type Safety**: Pydantic によるバリデーションと型変換。

---

## 3. 選択肢と評価

### 採用案 (Pydantic Settings)

- メリット:
  - **型安全**: 設定値が正しい型であることを保証できる。
  - **統合**: Pydantic エコシステムの一部であり、バリデーションロジックを再利用できる。
  - **12-Factor App**: 環境変数ベースの設定管理を容易に実現できる。
- デメリット:
  - 特になし。

### 代替案 A (python-dotenv + os.environ)

- 概要: 生の環境変数を読む。
- 採用しなかった理由:
  - 型変換やバリデーションを自前で書く必要がある。

---

## 4. 根拠（評価軸と判断）

- **Robustness**: 設定ミスによる実行時エラーを早期（起動時）に検知するため。
- **Developer Experience**: `.env` ファイルのサポートにより、ローカル開発が容易になるため。

---

## 5. 影響範囲

- **Codebase**: `src/kamojiros/config/` 配下に設定定義を集約する。
- **Deployment**: デプロイ時は環境変数を注入するだけで動作する。

---

## 6. 関連 ADR

- ADR-0006: コアドメインモデル (Pydantic 採用)
