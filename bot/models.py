from datetime import datetime, time

from django.db import models
from django.utils.timezone import make_aware, now


class OrderStatus(models.TextChoices):
    PROGRESS = 'progress', 'Jarayonda'
    CALLING = 'calling', 'Qo‘ng‘iroq qilinmoqda'
    COMPLETE = 'complete', 'Bajarildi'
    CANCEL = 'cancel', 'Bekor qilindi'


class BotUser(models.Model):
    chat_id = models.CharField(max_length=20)
    full_name = models.CharField(max_length=500)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    cash = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status  = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.full_name} | {self.cash} so'm"

    @classmethod
    async def new_user(cls, chat_id, full_name, phone=None, cash=0, status=False):
        await cls.objects.acreate(
            chat_id=chat_id,
            full_name=full_name,
            phone=phone,
            cash=cash,
            status=status
        )

    @classmethod
    async def exists_user(cls, chat_id: int) -> bool:
        return await cls.objects.filter(chat_id=chat_id).aexists()

    @classmethod
    async def get_user(cls, chat_id: int):
        return await cls.objects.filter(chat_id=chat_id).afirst()


class PrivateGroup(models.Model):
    chat_id = models.CharField(max_length=20)
    title = models.CharField(max_length=100)

    @classmethod
    async def get_group(cls):
        return await cls.objects.afirst()


class Order(models.Model):
    group_chat_id = models.BigIntegerField("Guruh chat ID", null=True, blank=True)
    group_message_id = models.IntegerField("Guruhdagi xabar ID", null=True, blank=True)

    c_chat_id = models.BigIntegerField("Mijoz Telegram ID")
    c_name = models.CharField("Mijoz ismi", max_length=100)
    c_username = models.CharField("Mijoz username", max_length=100, null=True, blank=True)
    c_count = models.IntegerField("Yo‘lovchilar soni", null=True, blank=True)
    c_phone = models.CharField("Mijoz telefoni", max_length=20, null=True, blank=True)
    c_direction = models.CharField("Yo'nalishi", max_length=255, null=True, blank=True)

    d_name = models.CharField("Haydovchi ismi", max_length=100, null=True, blank=True)
    d_phone = models.CharField("Haydovchi telefoni", max_length=20, null=True, blank=True)
    d_id = models.BigIntegerField("Haydovchi Telegram ID", null=True, blank=True)

    status = models.CharField("Holati", max_length=10, choices=OrderStatus.choices, default=OrderStatus.PROGRESS)  # progress, calling, complete, cancel

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.c_name} → {self.c_direction}"

    @classmethod
    async def get_order(cls, order_id):
        try:
            return await cls.objects.aget(id=order_id)
        except:
            return None

    @classmethod
    async def check_limit(cls, direction: str, d_chat_id: int):
        """Bugun bir yo'nalish va bir haydovchiga tegishli buyurtmalar sonini hisoblash"""
        today_start = make_aware(datetime.combine(now().date(), time.min))
        today_end = make_aware(datetime.combine(now().date(), time.max))

        count = await cls.objects.filter(
            d_id=d_chat_id,
            c_direction=direction,
            created_at__range=(today_start, today_end),
        ).acount()

        return count


class OrderHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="history")
    doer = models.CharField("Bajaruvchi", max_length=200)  # yoki ForeignKey(BotUser) bo‘lishi mumkin
    status = models.CharField("Holat", max_length=20)  # True = olgan, False = bekor qilgan
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.order.id} | User: {self.doer} | Status: {self.status}"
