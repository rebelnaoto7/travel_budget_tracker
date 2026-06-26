from django.contrib import admin

from .models import Budget, Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("date", "user", "item", "category", "amount_local", "currency", "rate_to_jpy", "amount_jpy")
    list_filter = ("user", "category", "currency", "date")
    search_fields = ("item", "memo")
    date_hierarchy = "date"


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("user", "total_budget_jpy", "updated_at")
    list_filter = ("user",)
