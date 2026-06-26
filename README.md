# 🌏 旅行予算管理アプリ（Django版）

海外旅行中の支出を **現地通貨 × 円換算** でリアルタイム管理する Web アプリ。
Streamlit 版（`app.py`）を **Django 5.2 / 6.0** に移植したものです。
9通貨対応・カテゴリ別予算管理・超過アラート機能付き。

---

## 移植の対応表（Streamlit → Django）

| Streamlit（元） | Django（移植後） |
|---|---|
| `expenses.csv`（CSV保存） | `Expense` モデル（DB保存・ユーザー別） |
| `budget.json`（JSON保存） | `Budget` モデル（`JSONField`・ユーザー別） |
| matplotlib（棒・円グラフ画像） | **自前Canvas描画**（外部ライブラリ不要・オフライン動作） |
| （認証なし） | **ログイン認証＋ユーザー別データ分離**（`django.contrib.auth`） |
| `st.tabs` 4タブ | 1ページ内タブ（CSS/JS） |
| `st.form` ×2（予算・支出） | `BudgetForm` / `ExpenseForm`（サーバ側バリデーション） |
| `st.rerun()` | PRG（Post/Redirect/Get）パターン |
| サイドバー予算設定 | 左パネルの予算設定フォーム |

> 元の機能（80%警告 / 100%超過エラー、カテゴリ別予算チェック、通貨別・カテゴリ別集計）はすべて再現済み。
> Web運用向けに **支出の削除** 機能を追加しています。

---

## セットアップ手順（PowerShell想定）

```powershell
# 1. プロジェクトへ移動
cd .\travel_budget

# 2. 仮想環境の作成・有効化
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. 依存パッケージのインストール
pip install -r requirements.txt

# 4. マイグレーション（DB作成）
python manage.py migrate

# 5. サンプルデータの投入（任意：元の expenses.csv / budget.json を取り込む）
python manage.py seed_demo

# 6. 管理者ユーザー作成（任意：/admin を使う場合）
python manage.py createsuperuser

# 7. 開発サーバー起動
python manage.py runserver
```

ブラウザで <http://127.0.0.1:8000/> を開く。
管理画面は <http://127.0.0.1:8000/admin/>。

---

## 🔐 認証とユーザー別データ分離

このアプリは **ログイン必須** で、データはユーザーごとに完全分離されます。

### 仕組み

| 項目 | 実装 |
|---|---|
| ログイン状態の判定 | 全ビューに `@login_required`。未ログインは `/accounts/login/` へ自動リダイレクト |
| 支出のデータ分離 | `Expense.user`（外部キー）。一覧・集計は `filter(user=request.user)` で本人分のみ |
| 予算のデータ分離 | `Budget.user`（OneToOne）。`Budget.get_for_user(user)` で本人の予算を取得 |
| 他人データの保護 | 削除は `filter(pk=pk, user=request.user)`。他人の支出は削除不可 |
| 認証URL | `django.contrib.auth.urls`（login / logout / password_change 等） |
| 新規登録 | 自作 `signup` ビュー（`UserCreationForm`）。登録後そのままログイン |

### 画面

| URL | 内容 |
|---|---|
| `/accounts/login/` | ログイン |
| `/signup/` | 新規登録 |
| `/` | メイン（要ログイン）。右上にユーザー名＋ログアウト |

### デモ用アカウント

`python manage.py seed_demo` 実行時に自動作成されます。

```
ユーザー名: demo
パスワード: demo12345
```

> 発表会で複数人に試してもらう場合は、各自 `/signup/` から登録すれば、
> それぞれ独立した予算・支出データを持てます。

### 検証済みのデータ分離（自動テストで確認）

- ✅ 未ログインでトップ → ログイン画面へリダイレクト
- ✅ alice の画面に bob のデータは表示されない
- ✅ alice は bob の支出を削除できない
- ✅ 予算もユーザーごとに独立
- ✅ ログアウト後はトップにアクセス不可

---

## VS Code で開いて実行する

このプロジェクトには `.vscode/` 設定が同梱されています。

### 初回だけ行うこと

1. **フォルダを開く**：VS Code で `ファイル → フォルダーを開く` → `travel_budget` フォルダを選択。
2. **推奨拡張機能を入れる**：右下に「推奨拡張機能をインストールしますか？」と出るので **インストール**。
   （Python / Python Debugger / Django の3つ。手動なら拡張機能パネルで検索）
3. **仮想環境を作る**：ターミナル（`Ctrl + @`）で
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
   > `Activate.ps1` でエラーが出たら、管理者PowerShellで一度だけ
   > `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned`
4. **インタープリタを選ぶ**：`Ctrl + Shift + P` → `Python: Select Interpreter` → `.venv` を選択。
   （`.vscode/settings.json` で自動的に `.venv` を指すよう設定済み）
5. **DB作成とデータ投入**：
   ```powershell
   python manage.py migrate
   python manage.py seed_demo
   ```

### 2回目以降の実行

- **`F5` キー** を押すと「Django: runserver」が起動し、デバッグ実行できます。
  （`.vscode/launch.json` で設定済み。ブレークポイントも使えます）
- デバッグ不要なら、ターミナルで `python manage.py runserver`。
- ブラウザで <http://127.0.0.1:8000/> を開く。

### 同梱した .vscode 設定

| ファイル | 役割 |
|---|---|
| `launch.json` | `F5` で Django をデバッグ起動 |
| `settings.json` | `.venv` を既定インタープリタに／Djangoテンプレート色分け／UTF-8固定 |
| `extensions.json` | 推奨拡張機能（Python・Debugpy・Django） |
| `tasks.json` | migrate / seed_demo / runserver をタスクから実行 |

---

## ディレクトリ構成

```
travel_budget/
├── .vscode/                    # VS Code 設定（launch/settings/extensions/tasks）
├── manage.py
├── requirements.txt
├── db.sqlite3                  # migrate 後に自動生成（.gitignore対象）
├── sample_data/
│   ├── budget.json             # 元データ（seed_demo で取込）
│   └── expenses.csv            # 元データ（seed_demo で取込）
├── travelbudget/               # プロジェクト設定
│   ├── settings.py             # TIME_ZONE=Asia/Tokyo, LANGUAGE_CODE=ja
│   └── urls.py
└── tracker/                    # アプリ本体
    ├── models.py               # Budget / Expense
    ├── forms.py                # BudgetForm / ExpenseForm
    ├── views.py                # index（PRG）/ delete_expense
    ├── urls.py
    ├── admin.py
    ├── management/commands/seed_demo.py
    └── templates/tracker/index.html
```

---

## データモデル

### Expense（支出）
| フィールド | 型 | 説明 |
|---|---|---|
| date | DateField | 日付 |
| item | CharField | 内容 |
| category | CharField(choices) | 食費/交通/宿泊/買い物/観光/その他 |
| amount_local | FloatField | 金額（現地通貨） |
| currency | CharField(choices) | JPY/USD/EUR/THB/KRW/TWD/GBP/AUD/CAD |
| rate_to_jpy | FloatField | 為替レート（1通貨=何円） |
| amount_jpy | FloatField | 円換算額（`save()` で自動計算） |
| memo | CharField | メモ（任意） |

### Budget（予算・単一レコード pk=1）
| フィールド | 型 | 説明 |
|---|---|---|
| total_budget_jpy | PositiveIntegerField | 総予算（円） |
| category_budgets | JSONField | `{カテゴリ名: 金額}`（budget.json と同構造） |

---

## 今後の改善案（一般公開を見据えて）

1. ~~**認証の追加**~~ — ✅ 実装済み（ログイン必須化＋ユーザー別データ分離）。
2. **為替レートの自動取得** — 手入力の `rate_to_jpy` を外部API（為替レート）で補完。
3. **本番DB** — Azure App Service 等では SQLite はファイルが揮発するため **PostgreSQL** を推奨。
4. **静的ファイル配信** — 本番は `collectstatic` + WhiteNoise もしくは CDN。
5. **テスト** — `tests.py` に集計・バリデーションの自動テストを追加。
