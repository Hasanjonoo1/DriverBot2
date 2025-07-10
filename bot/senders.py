from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from django.conf import settings
from asgiref.sync import sync_to_async
from .models import Order, PrivateGroup

bot = Bot(token=settings.BOT_TOKEN)

async def send_to_group(order_id: int):
    order = await Order.get_order(order_id)
    if not order:
        return

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
