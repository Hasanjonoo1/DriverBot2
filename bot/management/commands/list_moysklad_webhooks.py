import requests
from django.core.management.base import BaseCommand
from config import settings

MS_TOKEN = f"Bearer {settings.MOYSKLAD_TOKEN}"

class Command(BaseCommand):
    help = 'MoySklad’dagi mavjud webhook’larni ro‘yxatini chiqaradi'

    def handle(self, *args, **options):

        headers = {
            "Authorization": MS_TOKEN,
            "Accept": "application/json;charset=utf-8"
        }

        url = "https://api.moysklad.ru/api/remap/1.2/entity/webhook"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            webhooks = data.get("rows", [])
            if not webhooks:
                self.stdout.write("ℹ️ Hech qanday webhook topilmadi.")
                return

            self.stdout.write(self.style.SUCCESS("📄 Mavjud webhooklar:\n"))
            for w in webhooks:
                print(f"🔗 ID: {w.get('id')}")
                print(f"🌐 URL: {w.get('url')}")
                print(f"📦 Entity: {w.get('entityType')} | 🔁 Action: {w.get('action')}")
                print("-" * 40)

        else:
            self.stdout.write(self.style.ERROR(f"❌ Xatolik: {response.status_code}"))
            print(response.text)
