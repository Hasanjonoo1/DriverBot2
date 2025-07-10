from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from asgiref.sync import sync_to_async, async_to_sync
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, PrivateGroup
from django.conf import settings
from aiogram import Bot

bot = Bot(token=settings.BOT_TOKEN)

@receiver(post_save, sender=Order)
def send_order_to_group(sender, instance, created, **kwargs):
    if created:
        # asyncio.run() o‘rniga async_to_sync ishlatilmoqda
        async_to_sync(send_to_group)(instance)


async def send_to_group(order: Order):
    group = await PrivateGroup.get_group()
    if not group:
        return

    text = (
        f"📦 <b>Yangi buyurtma</b>\n"
        f"📍 Ism: {order.c_name or 'Nomaʼlum'}\n"
        f"📍 Yo'nalish: {order.c_direction or 'Nomaʼlum'}\n"
        f"👥 Yo‘lovchilar soni: {order.c_count or 'Nomaʼlum'}\n\n"
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
