from datetime import datetime, time

from asgiref.sync import sync_to_async
from django.db import models
from django.utils.timezone import make_aware, now


class OrderStatus(models.TextChoices):
    PROGRESS = 'progress', 'Jarayonda'
    CALLING = 'calling', 'Qo‘ng‘iroq qilinmoqda'
    COMPLETE = 'accept', 'Bajarildi'
    CANCEL = 'reject', 'Bekor qilindi'


class DirectionStatus(models.TextChoices):
    FERGANA_TO_TASHKENT = '🚖 Beshariqdan Toshkentga', "🚖 Beshariqdan Toshkentga"
    TASHKENT_TO_FERGANA = '🚖 Toshkentdan Beshariqga', "🚖 Toshkentdan Beshariqga"


class TicketStatus(models.TextChoices):
    OPEN = 'open', "Ochiq"
    FULL = 'full', "To‘lgan"
    CLOSED = 'closed', "Yopilgan"


class Driver(models.Model):
    chat_id = models.CharField("Chat ID", max_length=20)
    full_name = models.CharField("To‘liq ism", max_length=500)
    phone = models.CharField("Telefon raqam", max_length=20, unique=True, null=True, blank=True)
    cash = models.DecimalField("Balans", max_digits=10, decimal_places=2, default=0)
    limit_count_per_target = models.IntegerField("Yo‘lovchi limiti", default=4)
    limit_target_per_24hours = models.IntegerField("Yo'nalish limiti", default=2)
    status  = models.BooleanField("Faol", default=False)
    is_blocked  = models.BooleanField("Blok", default=False)
    blocked_until = models.DateTimeField("Cheklov davomiyligi", null=True, blank=True)
    last_ticket_msg_id = models.IntegerField("Oxirgi ticket xabari ID", null=True, blank=True)
    last_reply_msg_id = models.IntegerField("Oxirgi reply klaviatura ID", null=True, blank=True)
    created_at = models.DateTimeField("Ro‘yxatdan o‘tgan vaqt", auto_now_add=True, null=True)

    class Meta:
        verbose_name = "Haydovchi"
        verbose_name_plural = "Haydovchilar"

    def __str__(self):
        return f"{self.full_name} | {self.phone}"

    def __str__(self):
        return f"{self.full_name} | {self.cash} so'm"

    @classmethod
    async def new_user(cls, chat_id, full_name, phone=None, cash=0, status=True):
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
    user_chat_id = models.BigIntegerField("Foydalanuvchi chat ID", null=True, blank=True)
    user_message_id = models.IntegerField("Foydalanuvchi xabar ID", null=True, blank=True)

    c_chat_id = models.BigIntegerField("Mijoz Telegram ID")
    c_name = models.CharField("Mijoz ismi", max_length=255)
    c_username = models.CharField("Mijoz username", max_length=100, null=True, blank=True)
    c_count = models.IntegerField("Yo‘lovchilar soni", null=True, blank=True, default=0)
    c_phone = models.CharField("Mijoz telefoni", max_length=100, null=True, blank=True)
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
        today_start = make_aware(datetime.combine(now().date(), time.min))
        today_end = make_aware(datetime.combine(now().date(), time.max))

        count = await cls.objects.filter(
            d_id=d_chat_id,
            c_direction=direction,
            created_at__range=(today_start, today_end),
        ).acount()

        return count

    @classmethod
    async def check_calling(cls, d_chat_id: int):
        return await cls.objects.filter(d_id=d_chat_id, status=OrderStatus.CALLING).aexists()


class OrderHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="history")
    doer = models.CharField("Bajaruvchi", max_length=200)  # yoki ForeignKey(BotUser) bo‘lishi mumkin
    status = models.CharField("Holat", max_length=20)  # True = olgan, False = bekor qilgan
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.order.id} | User: {self.doer} | Status: {self.status}"


class Ticket(models.Model):
    driver = models.ForeignKey(
        'Driver',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Haydovchi"
    )
    direction = models.CharField(
        max_length=50,
        choices=DirectionStatus.choices,
        verbose_name="Yo‘nalish"
    )
    status = models.BooleanField(
        default=True,
        verbose_name="Holat"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqti")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Yangilangan vaqti")

    class Meta:
        verbose_name = "Chiptalar"
        verbose_name_plural = "Chiptalar ro'yxati"

    def __str__(self):
        return f"{self.driver} | {self.get_direction_display()} | {self.status} | {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    @classmethod
    async def get_active_ticket(cls, chat_id):
        return await sync_to_async(cls.objects.filter(driver__chat_id=chat_id, status=True).last)()


class TicketDetail(models.Model):
    ticket = models.ForeignKey(
        'Ticket',
        on_delete=models.CASCADE,
        related_name='details',
        verbose_name="Chipta"
    )
    order = models.ForeignKey(
        'Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Buyurtma"
    )
    full_name = models.CharField(max_length=255, verbose_name="Yo‘lovchi F.I.Sh.")
    phone = models.CharField(max_length=255, verbose_name="Telefon raqam")
    count = models.IntegerField("Yo‘lovchilar soni", null=True, blank=True, default=0)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Qo‘shilgan vaqti")

    class Meta:
        unique_together = ('ticket', 'order')
        verbose_name = "Chiptadagi buyurtma"
        verbose_name_plural = "Chiptadagi buyurtmalar"

    def __str__(self):
        return f"{self.full_name} | {self.ticket}"
