from pprint import pprint

from aiogram import Bot
from aiogram.types import CallbackQuery
from asgiref.sync import sync_to_async

from bot.models import Order, OrderStatus, BotUser, OrderHistory


@sync_to_async
def create_order_history(order, doer, status):
    return OrderHistory.objects.create(order=order, doer=doer, status=status)

async def take_order(callback: CallbackQuery, bot: Bot):
    order_id = int(callback.data.split(":")[1])
    user = callback.from_user

    driver = await BotUser.get_user(chat_id=user.id)
    if not driver or not driver.status:
        await callback.answer("❌ Sizning hisobingiz faol emas.", show_alert=True)
        return

    order = await Order.get_order(order_id=order_id)
    if not order:
        await callback.answer("❌ Buyurtma topilmadi.", show_alert=True)
        return

    if order.status == OrderStatus.CALLING:
        await callback.answer("🚕 Bu buyurtma boshqa haydovchi tomonidan olingan.", show_alert=True)
        return

    if order.status == OrderStatus.COMPLETE:
        await callback.answer("✅ Bu buyurtma allaqachon bajarilgan.", show_alert=True)
        return

    if order.status == OrderStatus.CANCEL:
        await callback.answer("❌ Bu buyurtma bekor qilingan.", show_alert=True)
        return

    if order.status == OrderStatus.PROGRESS:
        count = await Order.check_limit(order.c_direction, driver.chat_id)
        if order.c_count + count > 4:
            await callback.answer("❌ Limit to'ldi", show_alert=True)
            return

        order.d_name = driver.full_name
        order.d_phone = driver.phone
        order.d_id = driver.chat_id
        order.status = OrderStatus.CALLING
        await sync_to_async(order.save)()

        await create_order_history(order=order, doer=driver.full_name, status=OrderStatus.CALLING)
        await callback.answer("✅ Buyurtma sizga biriktirildi.", show_alert=True)

        c_count = order.c_count if order.c_count > 0 else "Pochta"
        order_text = (
            f"🚖 *Yangi buyurtma ma'lumotlari:*\n\n"
            f"👤 *Mijoz:* {order.c_name}\n"
            f"📞 *Telefon:* {order.c_phone or 'Nomaʼlum'}\n"
            f"🧑‍🤝‍🧑 *Yo‘lovchilar:* {c_count or 'Nomaʼlum'}\n"
            f"📍 *Yo‘nalish:* {order.c_direction or 'Ko‘rsatilmagan'}\n"
            f"{f'📬 *Username:* @{order.c_username}' if order.c_username else ''}"
            f"\n\n5 daqiqa ichida mijoz bilan bog'lanib, pastdagi kerakli tugmani bosing"
        )

        from bot.instance.handlers import order_private_ik
        await callback.bot.send_message(
            chat_id=driver.chat_id,
            text=order_text,
            parse_mode="Markdown",
            reply_markup=await order_private_ik(order.id)
        )

        # Guruhdagi xabarni tahrirlash
        if hasattr(order, "group_chat_id") and hasattr(order, "group_message_id"):
            try:
                await callback.bot.edit_message_text(
                    chat_id=order.group_chat_id,
                    message_id=order.group_message_id,
                    text=(
                        f"<b>Yangi buyurtma</b>\n"
                        f"📍 Ism: {order.c_name or 'Nomaʼlum'}\n"
                        f"📍 Yo'nalish: {order.c_direction or 'Nomaʼlum'}\n"
                        f"👥 Yo‘lovchilar soni: {c_count or 'Nomaʼlum'}\n\n"
                        f"🚖 Buyurtmaga qo'ng'iroq qilinmoqda...\n"
                        f"👨‍✈️ Haydovchi: {driver.full_name}\n"
                    ),
                    parse_mode="html"
                )
            except Exception:
                await callback.message.answer("⚠️ Guruhdagi xabarni yangilab bo‘lmadi.")

    # TODO: balans tekshirish va boshqa shartlar

    # order = await Order.objects.aget(id=order_id)
    # order.d_id = user.id
    # order.d_name = user.full_name
    # order.d_phone = ""
    # await order.asave()
    #
    # await callback.message.edit_text(f"✅ Buyurtma qabul qilindi: {user.full_name}")


async def reject(callback: CallbackQuery, bot: Bot):
    try:
        order_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("❌ Noto‘g‘ri buyurtma ID")
        return

    order = await Order.get_order(order_id=order_id)
    if not order:
        await callback.answer("❌ Buyurtma topilmadi.")
        return

    # Faqat o‘ziga biriktirilgan haydovchi rad qila oladi
    if order.d_id != callback.from_user.id:
        await callback.answer("❌ Siz bu buyurtmaga biriktirilmagansiz.")
        return

    # ✅ Javob darhol yuboriladi (2.5 soniyadan oldin!)
    await callback.answer("❌ Buyurtma rad etildi.", show_alert=True)



    # 👇 Og‘ir ishlar endi boshlanadi
    # Holatni tiklash
    order.d_name = None
    order.d_phone = None
    order.d_id = None
    order.status = OrderStatus.PROGRESS
    await sync_to_async(order.save)()

    # Tarixga yozish
    await create_order_history(
        order=order,
        doer=callback.from_user.full_name,
        status="reject"
    )
    c_count = order.c_count if order.c_count > 0 else "Pochta"

    # Guruhdagi xabarni yangilash
    try:
        from bot.instance.handlers import get_order_ik
        await bot.edit_message_text(
            chat_id=order.group_chat_id,
            message_id=order.group_message_id,
            text=(
                f"<b>Yangi buyurtma</b>\n"
                f"📍 Yo'nalish: {order.c_direction or 'Nomaʼlum'}\n"
                f"👥 Yo‘lovchilar soni: {c_count or 'Nomaʼlum'}\n\n"
                f"Buyurtmani olish uchun tugmani bosing 👇"
            ),
            parse_mode="HTML",
            reply_markup=await get_order_ik(order_id)
        )

        order_text = (
            f"🚖 *Yangi buyurtma ma'lumotlari:*\n\n"
            f"👤 *Mijoz:* {order.c_name}\n"
            f"🧑‍🤝‍🧑 *Yo‘lovchilar:* {c_count or 'Nomaʼlum'}\n"
            f"📍 *Yo‘nalish:* {order.c_direction or 'Ko‘rsatilmagan'}\n"
            f"\n\nBuyurtmani rad etdingiz!"
        )
        await callback.message.edit_text(
            order_text,
            parse_mode='markdown'
        )

    except Exception as e:
        print(f"⚠️ Guruhdagi xabarni yangilab bo‘lmadi.\n{e}")


async def accept(callback: CallbackQuery, bot: Bot):
    try:
        order_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("❌ Noto‘g‘ri buyurtma ID")
        return

    user = callback.from_user

    driver = await BotUser.get_user(chat_id=user.id)
    if not driver or not driver.status:
        await callback.answer("❌ Sizning hisobingiz faol emas.", show_alert=True)
        return

    order = await Order.get_order(order_id=order_id)
    if not order:
        await callback.answer("❌ Buyurtma topilmadi.")
        return

    # Faqat o‘ziga biriktirilgan haydovchi rad qila oladi
    if order.d_id != callback.from_user.id:
        await callback.answer("❌ Siz bu buyurtmaga biriktirilmagansiz.")
        return

    # ✅ Javob darhol yuboriladi (2.5 soniyadan oldin!)
    await callback.answer("✅ Buyurtma qabul qilindi", show_alert=True)

    # 👇 Og‘ir ishlar endi boshlanadi
    # Holatni yangilash
    order.status = OrderStatus.COMPLETE
    await sync_to_async(order.save)()

    # Tarixga yozish
    await create_order_history(
        order=order,
        doer=callback.from_user.full_name,
        status="accept"
    )
    c_count = order.c_count if order.c_count > 0 else "Pochta"

    # Guruhdagi xabarni yangilash
    try:
        from bot.instance.handlers import get_order_ik
        await bot.edit_message_text(
            chat_id=order.group_chat_id,
            message_id=order.group_message_id,
            text=(
                f"<b>Yangi buyurtma</b>\n"
                f"📍 Ism: {order.c_name or 'Nomaʼlum'}\n"
                f"📍 Yo'nalish: {order.c_direction or 'Nomaʼlum'}\n"
                f"👥 Yo‘lovchilar soni: {c_count or 'Nomaʼlum'}\n\n"
                f"🚖 Buyurtma olindi\n"
                f"👨‍✈️ Haydovchi: {driver.full_name}\n"
            ),
            parse_mode="HTML"
        )

        order_text = (
            f"🚖 *Yangi buyurtma ma'lumotlari:*\n\n"
            f"👤 *Mijoz:* {order.c_name}\n"
            f"🧑‍🤝‍🧑 *Yo‘lovchilar:* {c_count or 'Nomaʼlum'}\n"
            f"📍 *Yo‘nalish:* {order.c_direction or 'Ko‘rsatilmagan'}\n"
            f"\n\nBuyurtmani qabul qildingiz"
        )
        await callback.message.edit_text(
            order_text,
            parse_mode='markdown'
        )

    except Exception as e:
        print(f"⚠️ Guruhdagi xabarni yangilab bo‘lmadi.\n{e}")
