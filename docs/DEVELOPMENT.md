# 開発メモ（旅行予算管理アプリ）

README から分けた、開発者向けの補足です。使い方は [README](../README.md) を参照してください。

## 構成

```text
ブラウザ
    │ GET /、POST /（form_type=budget または expense）
    │ POST /expense/<id>/delete/、/signup/、/accounts/login/、/accounts/logout/
    ▼
myproject/urls.py → tracker/urls.py → tracker/views.py
    ├─ index()           予算・支出の保存（PRG）と、集計・グラフ用データの計算
    ├─ delete_expense()  本人の支出だけを削除（POST のみ）
    └─ signup()          UserCreationForm で登録し、そのままログイン
    │ Django ORM（すべて user=request.user で絞り込み）
    ▼
Budget（ユーザーごとに 1 件）／ Expense（支出）
    SQLite（db.sqlite3）
```

## Streamlit 版との対応表

| Streamlit 版（`app.py`） | Django 版 | 補足 |
| --- | --- | --- |
| `expenses.csv` に保存 | `Expense` モデル | ユーザーごとに DB に保存します |
| `budget.json` に保存 | `Budget` モデル | ユーザーごとに 1 件。カテゴリ別の予算は JSONField で同じ形のまま持ちます |
| （認証なし） | ログイン必須とユーザーごとのデータ分離 | `django.contrib.auth` を使います |
| サイドバーの予算設定（`st.sidebar.form`） | 左側の予算設定パネル（`BudgetForm`） | |
| 支出登録（`st.form`） | 支出登録フォーム（`ExpenseForm`） | 入力チェックはサーバー側で行います |
| `st.rerun()` | PRG（Post/Redirect/Get）パターン | 保存に成功したらリダイレクトします |
| `st.success`・`st.warning`・`st.error` | Django の messages フレームワークとアラート表示 | |
| `st.tabs`（4 タブ） | 1 ページ内のタブ（CSS・JavaScript） | |
| matplotlib（棒グラフ・円グラフの画像） | Canvas API による自前の描画 | 外部ライブラリが不要で、オフラインでも表示できます |
| `convert_to_jpy()` | `Expense.save()` | 保存時に `amount_jpy` を計算します |
| `summarize_by_category()`・`summarize_by_currency()` | `_category_summary()`・`_currency_summary()` | ORM の集計（`Sum`）で計算します |
| （なし） | 支出の削除 | POST のみ。本人の支出だけが対象です |

アラートの基準（総予算の 80%・100%、カテゴリ別の 80%・100%）と、通貨別・カテゴリ別の集計は Streamlit 版と同じです。

## データモデル

### Expense（支出）

| フィールド | 型 | 説明 |
| --- | --- | --- |
| `user` | ForeignKey（ユーザー） | 支出の持ち主 |
| `date` | DateField | 日付 |
| `item` | CharField（200 文字） | 内容 |
| `category` | CharField（選択式） | 食費・交通・宿泊・買い物・観光・その他 |
| `amount_local` | FloatField | 金額（現地通貨） |
| `currency` | CharField（選択式） | JPY・USD・EUR・THB・KRW・TWD・GBP・AUD・CAD |
| `rate_to_jpy` | FloatField | 為替レート（1 通貨が何円か） |
| `amount_jpy` | FloatField | 円換算額（`save()` で自動計算） |
| `memo` | CharField（500 文字） | メモ（任意） |
| `created_at` | DateTimeField | 登録日時（自動） |

並び順は、日付の新しい順（同じ日付なら登録の新しい順）です。

### Budget（予算。ユーザーごとに 1 件）

| フィールド | 型 | 説明 |
| --- | --- | --- |
| `user` | OneToOneField（ユーザー） | 予算の持ち主 |
| `total_budget_jpy` | PositiveIntegerField | 総予算（円。初期値 100,000） |
| `category_budgets` | JSONField | `{カテゴリ名: 金額}`。`budget.json` の `category_budgets` と同じ形 |
| `updated_at` | DateTimeField | 更新日時（自動） |

カテゴリ別の予算の初期値は、食費 20,000 円・交通 10,000 円・宿泊 40,000 円・買い物 15,000 円・観光 10,000 円・その他 5,000 円です。`Budget.get_for_user()` は、予算がなければ初期値で作り、足りないカテゴリがあれば初期値で補います。

## URL

| URL | 処理 | 内容 |
| --- | --- | --- |
| `/` | `index` | メイン画面（ログイン必須）。POST の `form_type` が `budget` なら予算、`expense` なら支出を保存します |
| `/signup/` | `signup` | 新規登録。ログイン済みなら `/` に移動します |
| `/expense/<id>/delete/` | `delete_expense` | 支出の削除（POST のみ。GET では `/` に戻るだけです） |
| `/accounts/login/` | Django 標準 | ログイン（テンプレートは `registration/login.html`） |
| `/accounts/logout/` | Django 標準 | ログアウト（POST のみ） |
| `/admin/` | Django admin | 管理画面 |

`/accounts/` には Django 標準の認証 URL（`django.contrib.auth.urls`）をまとめて登録しています。パスワード変更・再設定の URL もありますが、このアプリ用の画面は用意していません。

## 開発用のコマンド

```bash
python manage.py check                   # 設定の確認（問題なし）
python manage.py makemigrations --check  # モデルとマイグレーションの差分確認（No changes detected）
python manage.py test                    # 自動テストは 0 件（NO TESTS RAN）
```

括弧内は、Windows 11 / Python 3.13 / Django 6.1.2 で実行したときの結果です（2026 年 11 月）。
