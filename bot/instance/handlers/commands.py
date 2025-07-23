from django.utils import timezone  # muhim
from aiogram.types import Message
from aiogram import Bot
from aiogram.utils.markdown import hbold

from bot.instance.handlers.keyboards import *
from bot.models import Driver, Ticket, TicketStatus, TicketDetail


async def start(message: Message, bot: Bot):
    if message.chat.type != 'private':
        await message.reply("Bot bu buyruqga faqat shaxsiy xabarlarda ishlaydi")
        return

    await message.answer(
        "👋 Assalomu alaykum!\n\n🚖 Haydovchilar uchun taksi bot tizimiga xush kelibsiz!\n\n/info - Ma'lumot uchun",
        reply_markup=target
    )

    chat_id = message.chat.id

    if not await Driver.exists_user(chat_id=chat_id):
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
    if message.chat.type != 'private':
        await message.reply("Bot bu buyruqga faqat shaxsiy xabarlarda ishlaydi")
        return

    try:
        user = await Driver.objects.aget(chat_id=chat_id)
    except Driver.DoesNotExist:
        await message.answer("🚫 Siz ro‘yxatdan o‘tmagansiz. Iltimos, avval /start buyrug'ini yuboring.")
        return

    now = timezone.now()

    # Bloklanganlik statusi aniqlanadi
    if user.is_blocked:
        if user.blocked_until and user.blocked_until > now:
            blocked_status = f"🚫 Bloklangan (gacha: {user.blocked_until.strftime('%d.%m.%Y %H:%M')})"
        else:
            blocked_status = "⚠️ Bloklangan (muddati tugagan)"
    else:
        blocked_status = "✅ Bloklanmagan"

    # Umumiy profil matni
    text = (
        f"{hbold('👤 Profil maʼlumotlari')}\n"
        f"{hbold('Ism:')} {user.full_name}\n"
        f"{hbold('Telefon:')} {user.phone or '–'}\n"
        f"{hbold('Balans:')} {user.cash} so'm\n"
        f"{hbold('Holat:')} {'✅ Faol' if user.status else '⛔️ Nofaol'}\n"
        f"{hbold('Bloklanganlik:')} {blocked_status}\n\n"
        f"{hbold('🔢 Limitlar:')}\n"
        f"• Yo‘nalish limiti (24soat ichida): {user.limit_target_per_24hours} ta\n"
        f"• Yo'lovchi limiti (har bir yo'nalish uchun): {user.limit_count_per_target} ta\n"
        f"{hbold('🕒 Ro‘yxatdan o‘tgan sana:')} {user.created_at.strftime('%d.%m.%Y %H:%M')}"
    )

    await message.answer(
        text,
        parse_mode="html",
        reply_markup=target
    )

async def ticket(message: Message, bot: Bot):
    if message.chat.type != 'private':
        await message.reply("Bot bu buyruqga faqat shaxsiy xabarlarda ishlaydi")
        return
    chat_id = str(message.chat.id)

    try:
        user = await Driver.objects.aget(chat_id=chat_id)
    except Driver.DoesNotExist:
        await message.answer("🚫 Siz ro‘yxatdan o‘tmagansiz. Iltimos, avval /start buyrug'ini yuboring.")
        return

    ticket = await Ticket.objects \
        .filter(driver=user) \
        .prefetch_related('details') \
        .alast()

    if not ticket:
        await message.answer(
            text="📭 Sizda hozircha ochiq ticket yo‘q.",
            reply_markup=await close_ticket(ticket_id=None, status=None)
        )
        return

    # Yo‘lovchi detallari
    details = ticket.details.all()
    total_passengers = sum(d.count or 0 for d in details)

    text = (
        f"🎫 <b>Ma’lumotlar:</b>\n"
        f"🛣 <b>Yo‘nalish:</b> {ticket.get_direction_display()}\n"
        f"📅 <b>Status:</b> {ticket.status}\n"
        f"👥 <b>Yo‘lovchilar:</b>\n"
    )

    if details:
        for i, d in enumerate(details, 1):
            text += (
                f"\n<b>{i}.</b> {d.full_name} | {d.phone} | Son: {d.count or 0}"
            )
        text += f"\n\n🔢 <b>Jami yo‘lovchilar soni:</b> {total_passengers}"
    else:
        text += "\n🚫 Yo‘lovchilar hali qo‘shilmagan."

    # Ticket vaqtlari (ochilgan / yopilgan)
    text += (
        f"\n\n🕒 <b>Ochilgan vaqti:</b> {ticket.created_at.strftime('%Y-%m-%d %H:%M')}"
    )
    if ticket.updated_at:
        text += f"\n🕘 <b>Oxirgi o'zgartirish vaqti:</b> {ticket.updated_at.strftime('%Y-%m-%d %H:%M')}"



    await message.answer(text, reply_markup=await close_ticket(ticket_id=ticket.pk, status=ticket.status), parse_mode="HTML")
