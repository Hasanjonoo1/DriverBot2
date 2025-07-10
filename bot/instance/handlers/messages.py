from aiogram.types import Message, ReplyKeyboardRemove
from bot.models import BotUser

async def handle_contact(message: Message, bot):
    contact = message.contact
    chat_id = message.chat.id
    full_name = f"{contact.first_name or ''} {contact.last_name or ''}".strip()
    phone = contact.phone_number

    # Foydalanuvchi mavjudligini tekshiramiz
    is_exists = await BotUser.exists_user(chat_id)

    if is_exists:
        await message.answer(
            "✅ Siz allaqachon ro'yxatdan o'tgansiz.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # Yangi foydalanuvchini saqlaymiz
    await BotUser.new_user(
        chat_id=str(chat_id),
        full_name=full_name,
        phone=phone
    )

    await message.answer(
        "✅ Raqamingiz saqlandi.\n\n/profile - Profile ma'lumotlaringiz",
        reply_markup=ReplyKeyboardRemove()
    )
