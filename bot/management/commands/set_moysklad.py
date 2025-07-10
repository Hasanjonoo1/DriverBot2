import requests
from django.core.management.base import BaseCommand
from config import settings

MS_TOKEN = f"Bearer {settings.MOYSKLAD_TOKEN}"

class Command(BaseCommand):
    help = 'Create a webhook in MoySklad for otgruzka (demand) creation'

    def handle(self, *args, **options):
        WEBHOOK_URL = f"{settings.BOT_HOST}/bot/webhook/otgruzka" 

        headers = {
            "Authorization": MS_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json;charset=utf-8"
        }

        data = {
            "url": WEBHOOK_URL,
            "action": "CREATE",       
            "entityType": "demand" 
        }

        print("⏳ Webhook yaratilyapti...")

        response = requests.post(
            "https://api.moysklad.ru/api/remap/1.2/entity/webhook",
            json=data,
            headers=headers
        )

        if response.status_code in [200, 201]:
            self.stdout.write(self.style.SUCCESS("✅ Webhook muvaffaqiyatli yaratildi."))
        else:
            self.stdout.write(self.style.ERROR(f"❌ Xatolik: {response.status_code}"))
            print(response.text)
