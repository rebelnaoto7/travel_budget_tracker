"""データモデル定義。

元の Streamlit 版では expenses.csv / budget.json にファイル保存していたが、
Django 版では SQLite（本番は PostgreSQL 推奨）に保存する。
"""
from django.conf import settings
from django.db import models

# 元アプリと同じ分類・通貨の定義
CATEGORIES = ["食費", "交通", "宿泊", "買い物", "観光", "その他"]
CURRENCIES = ["JPY", "USD", "EUR", "THB", "KRW", "TWD", "GBP", "AUD", "CAD"]

CATEGORY_CHOICES = [(c, c) for c in CATEGORIES]
CURRENCY_CHOICES = [(c, c) for c in CURRENCIES]


def default_category_budgets():
    """budget.json の category_budgets と同じ初期値。"""
    return {
        "食費": 20000,
        "交通": 10000,
        "宿泊": 40000,
        "買い物": 15000,
        "観光": 10000,
        "その他": 5000,
    }


class Budget(models.Model):
    """予算設定（ユーザーごとに1レコード）。"""

    # ユーザーごとに1件の予算を持つ（データ分離の要）
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="budget",
        verbose_name="ユーザー",
    )
    total_budget_jpy = models.PositiveIntegerField("総予算（円）", default=100000)
    # budget.json の構造をそのまま JSONField で保持
    category_budgets = models.JSONField("カテゴリ別予算", default=default_category_budgets)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    class Meta:
        verbose_name = "予算"
        verbose_name_plural = "予算"

    def __str__(self):
        return f"{self.user} の総予算 {self.total_budget_jpy:,} 円"

    @classmethod
    def get_for_user(cls, user):
        """指定ユーザーの予算を取得。なければ初期値で作成。"""
        obj, _ = cls.objects.get_or_create(
            user=user,
            defaults={
                "total_budget_jpy": 100000,
                "category_budgets": default_category_budgets(),
            },
        )
        # 後から追加されたカテゴリの取りこぼしを補完
        changed = False
        defaults = default_category_budgets()
        if not isinstance(obj.category_budgets, dict):
            obj.category_budgets = defaults
            changed = True
        for cat in CATEGORIES:
            if cat not in obj.category_budgets:
                obj.category_budgets[cat] = defaults[cat]
                changed = True
        if changed:
            obj.save()
        return obj


class Expense(models.Model):
    """支出 1 件。expenses.csv の 1 行に相当。"""

    # 支出の所有者（データ分離の要）
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="expenses",
        verbose_name="ユーザー",
    )
    date = models.DateField("日付")
    item = models.CharField("内容", max_length=200)
    category = models.CharField("カテゴリ", max_length=20, choices=CATEGORY_CHOICES)
    amount_local = models.FloatField("金額（現地通貨）")
    currency = models.CharField("通貨", max_length=3, choices=CURRENCY_CHOICES)
    rate_to_jpy = models.FloatField("為替レート（1通貨=何円）")
    amount_jpy = models.FloatField("金額（円）", default=0)
    memo = models.CharField("メモ", max_length=500, blank=True)
    created_at = models.DateTimeField("登録日時", auto_now_add=True)

    class Meta:
        verbose_name = "支出"
        verbose_name_plural = "支出"
        ordering = ["-date", "-id"]

    def save(self, *args, **kwargs):
        # convert_to_jpy 相当：保存時に円換算額を自動計算
        self.amount_jpy = (self.amount_local or 0) * (self.rate_to_jpy or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} {self.item} / {self.amount_jpy:,.0f} 円"
