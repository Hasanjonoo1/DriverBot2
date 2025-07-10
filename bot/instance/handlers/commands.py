from aiogram.types import Message
from aiogram import Bot
from aiogram.utils.markdown import hbold

from bot.instance.handlers.keyboards import *
from bot.models import BotUser

async def start(message: Message, bot: Bot):
    if message.chat.type != 'private':
        await message.reply("Bot bu buyruqga faqat shaxsiy xabarlarda ishlaydi")

    await message.answer(
        "👋 Assalomu alaykum!\n\n🚖 Haydovchilar uchun taksi bot tizimiga xush kelibsiz!\n\n/info - Ma'lumot uchun",
    )

    chat_id = message.chat.id

    if not await BotUser.exists_user(chat_id=chat_id):
        await message.reply("Raqam yuboring", reply_markup=ask_phone_b)
    return

async def get_id(message: Message, bot: Bot):
    await message.answer(
        f"chatID: <code>{message.chat.id}</code>\n"
             f"Full name: <code>{message.chat.full_name}</code>",
             parse_mode="html"
    )
    return

async def profile(message: Message, bot: Bot):
    chat_id = str(message.chat.id)

    try:
        user = await BotUser.objects.aget(chat_id=chat_id)
    except BotUser.DoesNotExist:
        await message.answer("🚫 Siz ro‘yxatdan o‘tmagansiz. Iltimos, avval /start buyrug'ini yuboring.")
        return

    text = (
        f"{hbold('👤 Profil maʼlumotlari')}\n"
        f"{hbold('Ism:')} {user.full_name}\n"
        f"{hbold('Telefon:')} {user.phone or '–'}\n"
        f"{hbold('Balans:')} {user.cash} so'm\n"
        f"{hbold('Holat:')} {'✅ Faol' if user.status else '⛔️ Nofaol'}"
    )

    await message.answer(text, parse_mode="html")