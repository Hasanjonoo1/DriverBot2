from aiogram import Bot
from aiogram.types import Message, ReplyKeyboardRemove

from bot.instance.handlers import targets
from bot.models import Driver, Order
from django.utils import timezone
from django.utils.timezone import localtime
from asgiref.sync import sync_to_async

async def handle_contact(message: Message, bot):
    contact = message.contact
    chat_id = message.chat.id
    full_name = f"{contact.first_name or ''} {contact.last_name or ''}".strip()
    phone = contact.phone_number

    # Foydalanuvchi mavjudligini tekshiramiz
    is_exists = await Driver.exists_user(chat_id)

    if is_exists:
        await message.answer(
            "✅ Siz allaqachon ro'yxatdan o'tgansiz.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # Yangi foydalanuvchini saqlaymiz
    await Driver.new_user(
        chat_id=str(chat_id),
        full_name=full_name,
        phone=phone
    )

    await message.answer(
        "✅ Raqamingiz saqlandi.\n\n/profile - Profile ma'lumotlaringiz",
        reply_markup=ReplyKeyboardRemove()
    )


async def select_target(message: Message, bot: Bot):
    chat_id = str(message.chat.id)

    try:
        user = await Driver.objects.aget(chat_id=chat_id)
    except Driver.DoesNotExist:
        return

    # 1. Eski xabarlarni o'chirish
    if user.last_ticket_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=user.last_ticket_msg_id)
        except:
            pass
    if user.last_reply_msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=user.last_reply_msg_id)
        except:
            pass

    msg_text = "🧭 Iltimos, yo‘nalishni tanlang."
    msg_reply = await message.answer(msg_text, reply_markup=await targets())

    # 2. ID larni saqlash
    user.last_ticket_msg_id = None
    user.last_reply_msg_id = msg_reply.message_id
    await sync_to_async(user.save)()