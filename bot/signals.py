import asyncio
from asgiref.sync import sync_to_async
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from .senders import send_to_group  # asinxron funksiya alohida faylda bo'lsin

@receiver(post_save, sender=Order)
def send_order_to_group(sender, instance, created, **kwargs):
    if created:
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(send_to_group(instance.id))
        except RuntimeError:
            # signaldan tashqarida (masalan manage.py createsuperuser) - pass
            pass
