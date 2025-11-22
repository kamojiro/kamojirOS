# ADR-0017: エラーハンドリング方針 (独自例外)

- 日付: 2025-11-22
- ステータス: 承認
- レイヤ: core
- 種別: 設計方針
- 関連コンポーネント: core.exceptions

---

## 1. 背景 / コンテキスト

アプリケーション内で発生するエラーを適切に捕捉し、ユーザーに分かりやすいメッセージを表示したり、リトライ処理を行ったりする必要があります。
Python 標準の例外をそのまま投げるだけでは、エラーの意図や発生源が不明確になりがちです。

---

## 2. 決定

**ドメイン固有の例外階層** を定義して使用します。
`KamojirosError` を基底クラスとし、各コンポーネントやエラー種別ごとにサブクラスを定義します。

```python
class KamojirosError(Exception):
    """Base exception for Kamojiros."""

class ResourceNotFoundError(KamojirosError):
    """Resource not found."""

class ExternalApiError(KamojirosError):
    """Error from external API (Misskey, OpenAI, etc)."""
```

---

## 3. 選択肢と評価

### 採用案 (Custom Exception Hierarchy)

- メリット:
  - **捕捉の粒度**: `try: ... except KamojirosError:` でアプリ固有のエラーだけをまとめて捕捉できる。
  - **意味の付与**: `ValueError` よりも `InvalidReportFormatError` の方が何が起きたか明白。
- デメリット:
  - 定義する手間がかかる。

### 代替案 A (Built-in Exceptions Only)

- 概要: `ValueError`, `RuntimeError` などをそのまま使う。
- 採用しなかった理由:
  - ライブラリが投げる例外と区別がつかなくなる。

---

## 4. 根拠（評価軸と判断）

- **Robustness**: エラーハンドリングの漏れを防ぎ、予期せぬクラッシュを減らすため。
- **User Experience**: CLI で「内部エラーが発生しました」ではなく「設定ファイルが見つかりません」と具体的に伝えるため。

---

## 5. 影響範囲

- **Core**: `core/exceptions.py` (仮) に例外クラスを集約。
- **Apps**: 外部ライブラリの例外をキャッチして、ドメイン例外にラップして投げ直す（Translation）。

---

## 6. 関連 ADR

- ADR-0006: コアドメインモデル
