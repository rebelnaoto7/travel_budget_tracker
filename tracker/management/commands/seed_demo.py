"""サンプルデータ投入コマンド。

元アプリの expenses.csv / budget.json を、デモユーザーに紐付けて DB に取り込む。
    python manage.py seed_demo
    python manage.py seed_demo --user alice   # 任意のユーザーに投入
    python manage.py seed_demo --reset        # 対象ユーザーの支出を消してから投入
"""
import csv
import json
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from tracker.models import Budget, Expense, default_category_budgets

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo12345"


class Command(BaseCommand):
    help = "sample_data/ の expenses.csv と budget.json をデモユーザーに紐付けて取り込みます。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user",
            default=DEMO_USERNAME,
            help=f"取り込み先のユーザー名（既定: {DEMO_USERNAME}）。存在しなければ作成します。",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="対象ユーザーの支出を全削除してから取り込みます。",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        username = options["user"]

        # --- 取り込み先ユーザーを用意 ---
        user, created_user = User.objects.get_or_create(username=username)
        if created_user:
            user.set_password(DEMO_PASSWORD)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"デモユーザーを作成しました: ユーザー名={username} / パスワード={DEMO_PASSWORD}"
                )
            )
        else:
            self.stdout.write(self.style.NOTICE(f"既存ユーザー {username} に取り込みます。"))

        base = Path(settings.BASE_DIR) / "sample_data"
        budget_file = base / "budget.json"
        expenses_file = base / "expenses.csv"

        # --- 予算 ---
        budget = Budget.get_for_user(user)
        if budget_file.exists():
            data = json.loads(budget_file.read_text(encoding="utf-8"))
            budget.total_budget_jpy = data.get("total_budget_jpy", 100000)
            budget.category_budgets = data.get("category_budgets", default_category_budgets())
            budget.save()
            self.stdout.write(self.style.SUCCESS(f"予算を取り込みました: 総予算 {budget.total_budget_jpy:,} 円"))

        # --- 支出 ---
        if options["reset"]:
            count = Expense.objects.filter(user=user).count()
            Expense.objects.filter(user=user).delete()
            self.stdout.write(self.style.WARNING(f"{username} の既存支出 {count} 件を削除しました。"))

        if expenses_file.exists():
            created = 0
            with expenses_file.open(encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not (row.get("item") or "").strip():
                        continue
                    Expense.objects.create(
                        user=user,
                        date=row["date"],
                        item=row["item"],
                        category=row["category"],
                        amount_local=float(row["amount_local"] or 0),
                        currency=row["currency"],
                        rate_to_jpy=float(row["rate_to_jpy"] or 0),
                        memo=(row.get("memo") or "").strip(),
                    )
                    created += 1
            self.stdout.write(self.style.SUCCESS(f"支出を {created} 件取り込みました。"))
        else:
            self.stdout.write(self.style.NOTICE("sample_data/expenses.csv が見つかりません。"))
