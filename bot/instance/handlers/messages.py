from aiogram import Bot
from aiogram.types import Message, ReplyKeyboardRemove

from bot.instance.handlers import targets
from bot.models import Driver, Order
from django.utils import timezone

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

    msg_text = "🧭 Iltimos, yo‘nalishni tanlang."

    await message.answer(msg_text, reply_markup=await targets())