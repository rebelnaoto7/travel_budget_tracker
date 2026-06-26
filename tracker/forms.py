"""フォーム定義。元 Streamlit 版のバリデーションをサーバ側で再現。"""
from datetime import date

from django import forms

from .models import Expense, CATEGORIES


class ExpenseForm(forms.ModelForm):
    """支出登録フォーム。"""

    class Meta:
        model = Expense
        fields = ["date", "item", "category", "amount_local", "currency", "rate_to_jpy", "memo"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "inp"}),
            "item": forms.TextInput(attrs={"class": "inp", "placeholder": "例：ランチ、タクシー、ホテル"}),
            "category": forms.Select(attrs={"class": "inp"}),
            "amount_local": forms.NumberInput(attrs={"class": "inp", "step": "1", "min": "0"}),
            "currency": forms.Select(attrs={"class": "inp"}),
            "rate_to_jpy": forms.NumberInput(attrs={"class": "inp", "step": "0.1", "min": "0"}),
            "memo": forms.TextInput(attrs={"class": "inp", "placeholder": "任意"}),
        }
        labels = {
            "date": "日付",
            "item": "内容",
            "category": "カテゴリ",
            "amount_local": "金額（現地通貨）",
            "currency": "通貨",
            "rate_to_jpy": "為替レート（1通貨=何円）",
            "memo": "メモ",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound and not self.initial.get("date"):
            self.fields["date"].initial = date.today()
        self.fields["rate_to_jpy"].initial = 1.0
        self.fields["memo"].required = False

    def clean_item(self):
        item = (self.cleaned_data.get("item") or "").strip()
        if item == "":
            raise forms.ValidationError("内容を入力してください。")
        return item

    def clean_amount_local(self):
        amount = self.cleaned_data.get("amount_local")
        if amount is None or amount <= 0:
            raise forms.ValidationError("金額は0より大きくしてください。")
        return amount

    def clean_rate_to_jpy(self):
        rate = self.cleaned_data.get("rate_to_jpy")
        if rate is None or rate <= 0:
            raise forms.ValidationError("為替レートは0より大きくしてください。")
        return rate


class BudgetForm(forms.Form):
    """予算設定フォーム。total + カテゴリ別予算（動的フィールド）。"""

    total_budget_jpy = forms.IntegerField(
        label="総予算（円）",
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "inp", "step": "1000", "min": "0"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        initial = kwargs.get("initial", {}) or {}
        cat_init = initial.get("category_budgets", {})
        # 日本語カテゴリ名はフィールド名に使いにくいので index で管理
        for i, cat in enumerate(CATEGORIES):
            self.fields[f"cat_{i}"] = forms.IntegerField(
                label=f"{cat}予算",
                min_value=0,
                initial=cat_init.get(cat, 0),
                widget=forms.NumberInput(attrs={"class": "inp", "step": "1000", "min": "0"}),
            )

    def category_fields(self):
        """テンプレートで (カテゴリ名, BoundField) を回すためのヘルパ。"""
        for i, cat in enumerate(CATEGORIES):
            yield cat, self[f"cat_{i}"]

    def category_budgets(self):
        """cleaned_data から {カテゴリ名: 金額} を組み立てる。"""
        result = {}
        for i, cat in enumerate(CATEGORIES):
            result[cat] = self.cleaned_data.get(f"cat_{i}", 0)
        return result
