import os
import json
from datetime import date

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="旅行予算管理アプリ", layout="wide")

# =========================
# ファイル設定
# =========================
EXPENSES_FILE = "expenses.csv"
BUDGET_FILE = "budget.json"

CATEGORIES = ["食費", "交通", "宿泊", "買い物", "観光", "その他"]
CURRENCIES = ["JPY", "USD", "EUR", "THB", "KRW", "TWD", "GBP", "AUD", "CAD"]

# matplotlib 日本語フォント対策（Windows想定）
plt.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "MS Gothic", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False


# =========================
# 初期データ
# =========================
def get_default_budget():
    return {
        "total_budget_jpy": 100000,
        "category_budgets": {
            "食費": 20000,
            "交通": 10000,
            "宿泊": 40000,
            "買い物": 15000,
            "観光": 10000,
            "その他": 5000
        }
    }


# =========================
# 初期ファイル作成
# =========================
def init_files():
    if not os.path.exists(EXPENSES_FILE):
        df = pd.DataFrame(columns=[
            "date",
            "item",
            "category",
            "amount_local",
            "currency",
            "rate_to_jpy",
            "amount_jpy",
            "memo"
        ])
        df.to_csv(EXPENSES_FILE, index=False, encoding="utf-8-sig")

    if not os.path.exists(BUDGET_FILE):
        default_budget = get_default_budget()
        with open(BUDGET_FILE, "w", encoding="utf-8") as f:
            json.dump(default_budget, f, ensure_ascii=False, indent=2)


# =========================
# データ読み書き
# =========================
def load_expenses():
    expected_cols = [
        "date", "item", "category", "amount_local",
        "currency", "rate_to_jpy", "amount_jpy", "memo"
    ]

    if not os.path.exists(EXPENSES_FILE):
        df = pd.DataFrame(columns=expected_cols)
        df.to_csv(EXPENSES_FILE, index=False, encoding="utf-8-sig")
        return df

    if os.path.getsize(EXPENSES_FILE) == 0:
        df = pd.DataFrame(columns=expected_cols)
        df.to_csv(EXPENSES_FILE, index=False, encoding="utf-8-sig")
        return df

    try:
        df = pd.read_csv(EXPENSES_FILE, encoding="utf-8-sig")
    except Exception:
        df = pd.DataFrame(columns=expected_cols)
        df.to_csv(EXPENSES_FILE, index=False, encoding="utf-8-sig")
        return df

    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    if not df.empty:
        df["amount_local"] = pd.to_numeric(df["amount_local"], errors="coerce").fillna(0.0)
        df["rate_to_jpy"] = pd.to_numeric(df["rate_to_jpy"], errors="coerce").fillna(0.0)
        df["amount_jpy"] = pd.to_numeric(df["amount_jpy"], errors="coerce").fillna(0.0)

    return df[expected_cols]


def save_expense(expense_dict):
    df = load_expenses()
    new_row = pd.DataFrame([expense_dict])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(EXPENSES_FILE, index=False, encoding="utf-8-sig")


def load_budget():
    default_budget = get_default_budget()

    if not os.path.exists(BUDGET_FILE):
        with open(BUDGET_FILE, "w", encoding="utf-8") as f:
            json.dump(default_budget, f, ensure_ascii=False, indent=2)
        return default_budget

    if os.path.getsize(BUDGET_FILE) == 0:
        with open(BUDGET_FILE, "w", encoding="utf-8") as f:
            json.dump(default_budget, f, ensure_ascii=False, indent=2)
        return default_budget

    try:
        with open(BUDGET_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "total_budget_jpy" not in data:
            data["total_budget_jpy"] = default_budget["total_budget_jpy"]

        if "category_budgets" not in data or not isinstance(data["category_budgets"], dict):
            data["category_budgets"] = default_budget["category_budgets"]

        for cat in CATEGORIES:
            if cat not in data["category_budgets"]:
                data["category_budgets"][cat] = default_budget["category_budgets"][cat]

        return data

    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        with open(BUDGET_FILE, "w", encoding="utf-8") as f:
            json.dump(default_budget, f, ensure_ascii=False, indent=2)
        return default_budget


def save_budget(budget_dict):
    with open(BUDGET_FILE, "w", encoding="utf-8") as f:
        json.dump(budget_dict, f, ensure_ascii=False, indent=2)


# =========================
# 計算処理
# =========================
def convert_to_jpy(amount_local, rate_to_jpy):
    return amount_local * rate_to_jpy


def summarize_by_category(df):
    if df.empty:
        return pd.DataFrame(columns=["category", "amount_jpy"])

    summary = df.groupby("category", as_index=False)["amount_jpy"].sum()
    summary = summary.sort_values(by="amount_jpy", ascending=False)
    return summary


def summarize_by_currency(df):
    if df.empty:
        return pd.DataFrame(columns=["currency", "amount_local"])

    summary = df.groupby("currency", as_index=False)["amount_local"].sum()
    summary = summary.sort_values(by="amount_local", ascending=False)
    return summary


def format_expense_display(row):
    return f'{row["amount_local"]:.2f} {row["currency"]} / {row["amount_jpy"]:,.0f} 円'


# =========================
# 初期化
# =========================
init_files()
expenses_df = load_expenses()
budget_data = load_budget()

# =========================
# タイトル
# =========================
st.title("旅行予算管理アプリ")
st.caption("海外旅行中の支出を現地通貨と円換算の両方で管理し、予算超過を防ぐアプリ")


# =========================
# サイドバー：予算設定
# =========================
st.sidebar.header("予算設定")

with st.sidebar.form("budget_form"):
    total_budget_jpy = st.number_input(
        "総予算（円）",
        min_value=0,
        value=int(budget_data.get("total_budget_jpy", 100000)),
        step=1000
    )

    st.markdown("### カテゴリ別予算（円）")
    category_budgets = {}
    existing_category_budgets = budget_data.get("category_budgets", {})

    for cat in CATEGORIES:
        category_budgets[cat] = st.number_input(
            f"{cat}予算",
            min_value=0,
            value=int(existing_category_budgets.get(cat, 0)),
            step=1000,
            key=f"budget_{cat}"
        )

    save_budget_clicked = st.form_submit_button("予算を保存")

    if save_budget_clicked:
        new_budget = {
            "total_budget_jpy": total_budget_jpy,
            "category_budgets": category_budgets
        }
        save_budget(new_budget)
        budget_data = new_budget
        st.sidebar.success("予算を保存しました")
        st.rerun()


# =========================
# 支出登録フォーム
# =========================
st.subheader("支出登録")

with st.form("expense_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        expense_date = st.date_input("日付", value=date.today())
        item = st.text_input("内容", placeholder="例：ランチ、タクシー、ホテル")

    with col2:
        category = st.selectbox("カテゴリ", CATEGORIES)
        currency = st.selectbox("通貨", CURRENCIES)

    with col3:
        amount_local = st.number_input("金額（現地通貨）", min_value=0.0, value=0.0, step=1.0)
        rate_to_jpy = st.number_input("為替レート（1通貨 = 何円）", min_value=0.0, value=1.0, step=0.1)

    memo = st.text_input("メモ", placeholder="任意")
    submitted = st.form_submit_button("支出を追加")

    if submitted:
        if item.strip() == "":
            st.warning("内容を入力してください。")
        elif amount_local <= 0:
            st.warning("金額は0より大きくしてください。")
        elif rate_to_jpy <= 0:
            st.warning("為替レートは0より大きくしてください。")
        else:
            amount_jpy = convert_to_jpy(amount_local, rate_to_jpy)

            expense = {
                "date": expense_date.strftime("%Y-%m-%d"),
                "item": item,
                "category": category,
                "amount_local": amount_local,
                "currency": currency,
                "rate_to_jpy": rate_to_jpy,
                "amount_jpy": amount_jpy,
                "memo": memo
            }

            save_expense(expense)
            st.success(f"支出を追加しました：{amount_local:.2f} {currency} / {amount_jpy:,.0f} 円")
            st.rerun()


# =========================
# 予算サマリー
# =========================
st.subheader("予算サマリー")

total_spent_jpy = expenses_df["amount_jpy"].sum() if not expenses_df.empty else 0
total_budget = budget_data.get("total_budget_jpy", 0)
remaining_budget = total_budget - total_spent_jpy
usage_rate = (total_spent_jpy / total_budget * 100) if total_budget > 0 else 0

m1, m2, m3 = st.columns(3)
m1.metric("総支出（円）", f"{total_spent_jpy:,.0f} 円")
m2.metric("残予算（円）", f"{remaining_budget:,.0f} 円")
m3.metric("予算消化率", f"{usage_rate:.1f}%")

if total_budget > 0 and total_spent_jpy > total_budget:
    st.error("総予算を超過しています。")
elif total_budget > 0 and usage_rate >= 80:
    st.warning("予算消化率が80%を超えています。")


# =========================
# タブ表示
# =========================
tab1, tab2, tab3, tab4 = st.tabs([
    "支出一覧（円換算）",
    "通貨別集計",
    "カテゴリ別集計",
    "グラフ"
])

with tab1:
    st.subheader("支出一覧（円換算）")

    if expenses_df.empty:
        st.info("まだ支出データがありません。")
    else:
        display_df = expenses_df.copy()
        display_df["金額表示"] = display_df.apply(format_expense_display, axis=1)
        display_df = display_df.rename(columns={
            "date": "日付",
            "item": "内容",
            "category": "カテゴリ",
            "rate_to_jpy": "為替レート",
            "memo": "メモ"
        })

        st.dataframe(
            display_df[["日付", "内容", "カテゴリ", "金額表示", "為替レート", "メモ"]],
            use_container_width=True
        )

with tab2:
    st.subheader("通貨別集計（現地通貨ベース）")

    currency_summary = summarize_by_currency(expenses_df)
    if currency_summary.empty:
        st.info("通貨別集計データがありません。")
    else:
        currency_summary = currency_summary.rename(columns={
            "currency": "通貨",
            "amount_local": "合計金額（現地通貨）"
        })
        st.dataframe(currency_summary, use_container_width=True)

with tab3:
    st.subheader("カテゴリ別集計（円ベース）")

    category_summary = summarize_by_category(expenses_df)
    if category_summary.empty:
        st.info("カテゴリ別集計データがありません。")
    else:
        category_summary = category_summary.rename(columns={
            "category": "カテゴリ",
            "amount_jpy": "合計金額（円）"
        })
        st.dataframe(category_summary, use_container_width=True)

        st.markdown("### カテゴリ別予算チェック")
        category_budget_dict = budget_data.get("category_budgets", {})

        for _, row in category_summary.iterrows():
            cat = row["カテゴリ"]
            spent = row["合計金額（円）"]
            cat_budget = category_budget_dict.get(cat, 0)

            if cat_budget > 0:
                if spent > cat_budget:
                    st.error(f"{cat}：予算超過（支出 {spent:,.0f} 円 / 予算 {cat_budget:,.0f} 円）")
                elif spent >= cat_budget * 0.8:
                    st.warning(f"{cat}：予算の80%超（支出 {spent:,.0f} 円 / 予算 {cat_budget:,.0f} 円）")
                else:
                    st.success(f"{cat}：予算内（支出 {spent:,.0f} 円 / 予算 {cat_budget:,.0f} 円）")

with tab4:
    st.subheader("グラフ")

    category_summary = summarize_by_category(expenses_df)

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("### カテゴリ別支出（棒グラフ）")
        if not category_summary.empty:
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(category_summary["category"], category_summary["amount_jpy"])
            ax.set_xlabel("カテゴリ")
            ax.set_ylabel("支出額（円）")
            ax.set_title("カテゴリ別支出")
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.info("カテゴリ別グラフ表示用データがありません。")

    with col_chart2:
        st.markdown("### カテゴリ別支出割合（円グラフ）")
        if not category_summary.empty:
            fig2, ax2 = plt.subplots(figsize=(6, 6))
            ax2.pie(
                category_summary["amount_jpy"],
                labels=category_summary["category"],
                autopct="%1.1f%%",
                startangle=90
            )
            ax2.set_title("カテゴリ別支出割合")
            st.pyplot(fig2)
        else:
            st.info("円グラフ表示用データがありません。")