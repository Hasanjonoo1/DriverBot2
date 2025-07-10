import requests
from django.core.management.base import BaseCommand
from config import settings

MS_TOKEN = f"Bearer {settings.MOYSKLAD_TOKEN}"

class Command(BaseCommand):
    help = 'MoySklad webhook’ni o‘chirish'

    def add_arguments(self, parser):
        parser.add_argument('--id', type=str, help='Webhook ID ni bu yerda kiriting')

    def handle(self, *args, **options):
        webhook_id = options['id']

        if not webhook_id:
            self.stdout.write(self.style.ERROR("❗ Iltimos, --id argument orqali webhook ID kiriting."))
            return

        headers = {
            "Authorization": MS_TOKEN,
            "Accept": "application/json;charset=utf-8"
        }

        url = f"https://api.moysklad.ru/api/remap/1.2/entity/webhook/{webhook_id}"
        print(f"⏳ Webhook o‘chirilmoqda: {webhook_id}")

        response = requests.delete(url, headers=headers)

        if response.status_code == 200:
            self.stdout.write(self.style.SUCCESS("✅ Webhook muvaffaqiyatli o‘chirildi."))
        else:
            self.stdout.write(self.style.ERROR(f"❌ O‘chirishda xatolik: {response.status_code}"))
            print(response.text)
