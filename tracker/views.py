"""ビュー。元 Streamlit 版の 1 ページ構成を Django で再現する。

Streamlit の st.rerun() による再描画を、Django では PRG
(Post / Redirect / Get) パターンで置き換えている。
"""
from collections import OrderedDict

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum
from django.shortcuts import redirect, render

from .forms import BudgetForm, ExpenseForm
from .models import Budget, Expense, CATEGORIES


def _category_summary(expenses):
    """カテゴリ別の円合計（降順）。summarize_by_category 相当。"""
    rows = (
        expenses.values("category")
        .annotate(total=Sum("amount_jpy"))
        .order_by("-total")
    )
    return [{"category": r["category"], "amount_jpy": r["total"] or 0} for r in rows]


def _currency_summary(expenses):
    """通貨別の現地通貨合計（降順）。summarize_by_currency 相当。"""
    rows = (
        expenses.values("currency")
        .annotate(total=Sum("amount_local"))
        .order_by("-total")
    )
    return [{"currency": r["currency"], "amount_local": r["total"] or 0} for r in rows]


@login_required
def index(request):
    budget = Budget.get_for_user(request.user)

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        # --- 予算保存フォーム ---
        if form_type == "budget":
            budget_form = BudgetForm(request.POST)
            expense_form = ExpenseForm()
            if budget_form.is_valid():
                budget.total_budget_jpy = budget_form.cleaned_data["total_budget_jpy"]
                budget.category_budgets = budget_form.category_budgets()
                budget.save()
                messages.success(request, "予算を保存しました")
                return redirect("index")

        # --- 支出登録フォーム ---
        elif form_type == "expense":
            expense_form = ExpenseForm(request.POST)
            budget_form = BudgetForm(
                initial={
                    "total_budget_jpy": budget.total_budget_jpy,
                    "category_budgets": budget.category_budgets,
                }
            )
            if expense_form.is_valid():
                obj = expense_form.save(commit=False)
                obj.user = request.user  # ログインユーザーを所有者に設定
                obj.save()  # save() 内で円換算を自動計算
                messages.success(
                    request,
                    f"支出を追加しました：{obj.amount_local:.2f} {obj.currency} / {obj.amount_jpy:,.0f} 円",
                )
                return redirect("index")
        else:
            budget_form = BudgetForm(
                initial={
                    "total_budget_jpy": budget.total_budget_jpy,
                    "category_budgets": budget.category_budgets,
                }
            )
            expense_form = ExpenseForm()
    else:
        budget_form = BudgetForm(
            initial={
                "total_budget_jpy": budget.total_budget_jpy,
                "category_budgets": budget.category_budgets,
            }
        )
        expense_form = ExpenseForm()

    # ===== サマリー計算（ログインユーザーの支出のみ） =====
    expenses = Expense.objects.filter(user=request.user)
    total_spent_jpy = expenses.aggregate(s=Sum("amount_jpy"))["s"] or 0
    total_budget = budget.total_budget_jpy or 0
    remaining_budget = total_budget - total_spent_jpy
    usage_rate = (total_spent_jpy / total_budget * 100) if total_budget > 0 else 0

    if total_budget > 0 and total_spent_jpy > total_budget:
        alert_level, alert_msg = "error", "総予算を超過しています。"
    elif total_budget > 0 and usage_rate >= 80:
        alert_level, alert_msg = "warning", "予算消化率が80%を超えています。"
    else:
        alert_level, alert_msg = "ok", ""

    # ===== 集計 =====
    cat_summary = _category_summary(expenses)
    cur_summary = _currency_summary(expenses)

    # カテゴリ別予算チェック
    cat_budget_dict = budget.category_budgets or {}
    cat_checks = []
    for row in cat_summary:
        cat = row["category"]
        spent = row["amount_jpy"]
        cat_budget = cat_budget_dict.get(cat, 0) or 0
        if cat_budget > 0:
            if spent > cat_budget:
                level = "error"
            elif spent >= cat_budget * 0.8:
                level = "warning"
            else:
                level = "ok"
            cat_checks.append(
                {"category": cat, "spent": spent, "budget": cat_budget, "level": level}
            )

    # Chart.js 用データ（カテゴリ順を固定）
    ordered = OrderedDict((c, 0) for c in CATEGORIES)
    for row in cat_summary:
        ordered[row["category"]] = row["amount_jpy"]
    chart_labels = [c for c in CATEGORIES if ordered[c] > 0]
    chart_values = [ordered[c] for c in chart_labels]

    context = {
        "budget_form": budget_form,
        "expense_form": expense_form,
        "expenses": expenses,
        "total_spent_jpy": total_spent_jpy,
        "remaining_budget": remaining_budget,
        "usage_rate": usage_rate,
        "total_budget": total_budget,
        "alert_level": alert_level,
        "alert_msg": alert_msg,
        "cat_summary": cat_summary,
        "cur_summary": cur_summary,
        "cat_checks": cat_checks,
        "chart_labels": chart_labels,
        "chart_values": chart_values,
    }
    return render(request, "tracker/index.html", context)


@login_required
def delete_expense(request, pk):
    """支出の削除。他人のデータは削除できないよう user で絞り込む。"""
    if request.method == "POST":
        # user=request.user で絞ることで他人の支出は削除対象外になる
        deleted, _ = Expense.objects.filter(pk=pk, user=request.user).delete()
        if deleted:
            messages.success(request, "支出を削除しました")
        else:
            messages.error(request, "対象の支出が見つかりません")
    return redirect("index")


def signup(request):
    """新規登録。成功したらそのままログインして index へ。"""
    if request.user.is_authenticated:
        return redirect("index")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # 登録後そのままログイン
            messages.success(request, "アカウントを作成しました")
            return redirect("index")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})
