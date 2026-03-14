from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from asgiref.sync import sync_to_async, async_to_sync
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, PrivateGroup
from django.conf import settings
from aiogram import Bot


@receiver(post_save, sender=Order)
def send_order_to_group(sender, instance, created, **kwargs):
    if created:
        # ✅ asyncio.run() emas, async_to_sync ishlatamiz
        async_to_sync(send_to_group)(instance)


<<<<<<< HEAD
from aiogram.client.default import DefaultBotProperties

async def send_to_group(order: Order):
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(protect_content=True))  # ✅ ichkarida yaratamiz
=======
async def send_to_group(order: Order):
    bot = Bot(token=settings.BOT_TOKEN)  # ✅ ichkarida yaratamiz
>>>>>>> ebb601a9a4d30196f2fec478b305776cf8b130af

    group = await PrivateGroup.get_group()
    if not group:
        return

    c_count = order.c_count if order.c_count > 0 else "Pochta"

    text = (
        f"📦 <b>Yangi buyurtma</b> #{order.pk}\n"
        f"📍 Ism: {order.c_name or 'Nomaʼlum'}\n"
        f"📍 Yo'nalish: {order.c_direction or 'Nomaʼlum'}\n"
        f"👥 Yo‘lovchilar soni: {c_count or 'Nomaʼlum'}\n\n"
        f"Buyurtmani olish uchun tugmani bosing 👇"
    )

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚕 Buyurtmani olish", callback_data=f"take_order:{order.id}")]
    ])

    msg = await bot.send_message(
        chat_id=group.chat_id,
        text=text,
        reply_markup=markup,
        parse_mode="HTML"
    )

    order.group_chat_id = group.chat_id
    order.group_message_id = msg.message_id
    await sync_to_async(order.save)()

    await bot.session.close()  # ✅ sessionni yoping
