import streamlit as st
import pandas as pd
import os
from datetime import date

st.title("Travel Budget Tracker")

DATA_FILE = "expenses.csv"

# 初期CSV作成
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=[
        "date", "item", "category", "amount_local", "currency", "rate_to_jpy", "amount_jpy"
    ])
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

# CSV読み込み
df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")

st.subheader("支出登録")

with st.form("expense_form"):
    col1, col2 = st.columns(2)

    with col1:
        expense_date = st.date_input("日付", value=date.today())
        item = st.text_input("内容")
        category = st.selectbox("カテゴリ", ["食費", "交通", "宿泊", "買い物", "その他"])

    with col2:
        amount_local = st.number_input("金額（現地通貨）", min_value=0.0, step=1.0)
        currency = st.selectbox("通貨", ["JPY", "USD", "EUR", "THB", "KRW"])
        rate_to_jpy = st.number_input("為替レート（1通貨=何円）", min_value=0.0, value=1.0)

    submitted = st.form_submit_button("追加")

    if submitted:
        if item.strip() == "" or amount_local <= 0 or rate_to_jpy <= 0:
            st.warning("入力内容を確認してください")
        else:
            amount_jpy = amount_local * rate_to_jpy
            new_row = {
                "date": expense_date.strftime("%Y-%m-%d"),
                "item": item,
                "category": category,
                "amount_local": amount_local,
                "currency": currency,
                "rate_to_jpy": rate_to_jpy,
                "amount_jpy": amount_jpy
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
            st.success("支出を追加しました")
            st.rerun()

st.subheader("支出一覧（円換算）")

if df.empty:
    st.info("まだ支出がありません")
else:
    st.dataframe(df)