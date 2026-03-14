from datetime import timedelta
from pprint import pprint

from aiogram import Bot
from aiogram.types import CallbackQuery
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.utils.timezone import localtime

from bot.models import Order, OrderStatus, Driver, OrderHistory, Ticket, TicketStatus, TicketDetail


@sync_to_async
def create_order_history(order, doer, status):
    return OrderHistory.objects.create(order=order, doer=doer, status=status)

import asyncio
import threading
from aiogram.client.default import DefaultBotProperties
from config import settings

async def execute_auto_reject(order_id: int, driver_id: int, driver_name: str):
    order = await Order.get_order(order_id=order_id)
    # Faqat "CALLING" holatida bo'lsa va int() orqali to'g'ri tekshiramiz
    if not order or order.status != OrderStatus.CALLING or order.d_id != int(driver_id):
        return
        
    order.d_name = None
    order.d_phone = None
    order.d_id = None
    order.status = OrderStatus.PROGRESS
    await sync_to_async(order.save)()
    
    # 30 soniyalik cheklov qo'shish
    try:
        driver = await Driver.get_user(chat_id=driver_id)
        if driver:
            driver.blocked_until = timezone.now() + timedelta(seconds=30)
            await sync_to_async(driver.save)()
    except Exception as e:
        print(f"Driver block error: {e}")
        
    await create_order_history(
        order=order,
        doer=f"{driver_name} (Avto Rad etish)",
        status="reject"
    )
    
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(protect_content=True))
    try:
        from bot.instance.handlers import get_order_ik
        
        # Haydovchidagi eski buyurtma xabarini o'chirish
        if order.user_message_id and order.user_chat_id:
            try:
                await bot.delete_message(chat_id=order.user_chat_id, message_id=order.user_message_id)
            except Exception:
                pass  # Xabar allaqachon o'chirilgan bo'lishi mumkin

        history_qs = await sync_to_async(list)(order.history.order_by("created_at").all())
        history_text = ""
        n = 1
        for hist in history_qs:
            action = dict(OrderStatus.choices).get(hist.status, hist.status)
            history_text += f"\n {n}. {hist.doer} — {action} ({localtime(hist.created_at).strftime('%H:%M:%S')})"
            n += 1
            
        c_count = order.c_count if order.c_count > 0 else "Pochta"
        
        if hasattr(order, "group_chat_id") and hasattr(order, "group_message_id"):
            await bot.edit_message_text(
                chat_id=order.group_chat_id,
                message_id=order.group_message_id,
                text=(
                    f"<b>Yangi buyurtma</b>  #{order.pk}\n"
                    f"📍 Ism: {order.c_name or 'Nomaʼlum'}\n"
                    f"📍 Yo'nalish: {order.c_direction or 'Nomaʼlum'}\n"
                    f"👥 Yo'lovchilar soni: {c_count or 'Nomaʼlum'}\n\n"
                    f"<b>📜 Tarix:</b>{history_text or '\n— Tarix mavjud emas —'}\n\n"
                    f"Buyurtmani olish uchun tugmani bosing 👇"
                ),
                parse_mode="HTML",
                reply_markup=await get_order_ik(order_id)
            )
            
        await bot.send_message(
            chat_id=driver_id,
            text=f"⏳ <b>Vaqt tugadi!</b>\n\nBuyurtma #{order.pk} ga 5 daqiqa davomida javob bermaganingiz uchun u avtomatik tarzda bekor qilindi.",
            parse_mode="HTML",
            protect_content=True
        )
    except Exception as e:
        print(f"Avto reject error: {e}")
    finally:
        await bot.session.close()


def schedule_auto_reject(order_id, driver_id, driver_name):
    """ Webhookni to'xtatib qo'ymaslik uchun maxsus thread orqali taymerni ishlatamiz """
    def run_coro():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(execute_auto_reject(order_id, driver_id, driver_name))
        loop.close()
        
    t = threading.Timer(300, run_coro) # 300 soniya = 5 daqiqa
    t.start()


async def take_order(callback: CallbackQuery, bot: Bot):
    try:
        order_id = int(callback.data.split(":")[1])
        user = callback.from_user

        driver = await Driver.get_user(chat_id=user.id)
        if not driver or not driver.status:
            await callback.answer("❌ Sizning hisobingiz faol emas.", show_alert=True)
            return

        # Muzlatish (block) tekshiruvi
        if driver.blocked_until and driver.blocked_until > timezone.now():
            diff = (driver.blocked_until - timezone.now()).seconds
            await callback.answer(f"⏳ Siz vaqtinchalik cheklovdasiz! \nIltimos, {diff} soniyadan keyin urinib ko'ring.", show_alert=True)
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

        # Check active ticket
        ticket = await Ticket.get_active_ticket(driver.chat_id)
        if not ticket:
            await callback.answer("❌ Avval yo‘nalish tanlab ticket yarating: /ticket", show_alert=True)
            return

        if ticket.direction != order.c_direction:
            await callback.answer("❌ Siz tanlagan yo‘nalish bu buyurtmaga mos emas!", show_alert=True)
            return


        if order.status == OrderStatus.PROGRESS:
            # 2. Faol chiptadagi yo‘lovchilar sonini hisoblaymiz
            details = await sync_to_async(list)(ticket.details.all())
            current_passenger_count = sum(d.count or 0 for d in details)

            # 3. Yangi buyurtma yo‘lovchilari sonini qo‘shamiz
            new_passenger_count = order.c_count or 0
            total_passengers = current_passenger_count + new_passenger_count

            if total_passengers > driver.limit_count_per_target:
                await callback.answer("❌ Bu yo‘nalish bo‘yicha yo‘lovchilar limiti to‘ldi", show_alert=True)
                return

            if await Order.check_calling(driver.chat_id):
                await callback.answer("❌ Sizda yakunlanmagan buyurtma bor", show_alert=True)
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
                f"🚖 <b>Yangi buyurtma</b>  #{order.pk}\n\n"
                f"👤 <b>Mijoz:</b> <a href='tg://user?id={order.c_chat_id}'>{order.c_name}</a>\n"
                f"📞 <b>Telefon:</b> {order.c_phone or 'Nomaʼlum'}\n"
                f"🧑‍<b>Yo‘lovchilar:</b> {c_count or 'Nomaʼlum'}\n"
                f"📍 <b>Yo‘nalish:</b> {order.c_direction or 'Ko‘rsatilmagan'}\n"
                f"{f'📬 <b>Username:</b> @{order.c_username}' if order.c_username else ''}"
                f"\n\n5 daqiqa ichida mijoz bilan bog‘lanib, pastdagi kerakli tugmani bosing"
            )

            from bot.instance.handlers import order_private_ik
            sent_msg = await callback.bot.send_message(
                chat_id=driver.chat_id,
                text=order_text,
                parse_mode="html",
                reply_markup=await order_private_ik(order.id),
                protect_content=True
            )

            # Haydovchiga yuborilgan xabar ID sini saqlaymiz (avto reject uchun)
            order.user_chat_id = int(driver.chat_id)
            order.user_message_id = sent_msg.message_id
            await sync_to_async(order.save)()

            # Guruhdagi xabarni tahrirlash
            if hasattr(order, "group_chat_id") and hasattr(order, "group_message_id"):
                try:
                    history_qs = await sync_to_async(list)(order.history.order_by("created_at").all())

                    history_text = ""
                    n = 1
                    for hist in history_qs:
                        action = dict(OrderStatus.choices).get(hist.status, hist.status)
                        history_text += f"\n {n}. {hist.doer} — {action} ({localtime(hist.created_at).strftime('%H:%M:%S')})"
                        n += 1

                    # Yuborilayotgan xabarga qo‘shamiz
                    await callback.bot.edit_message_text(
                        chat_id=order.group_chat_id,
                        message_id=order.group_message_id,
                        text=(
                            f"<b>Yangi buyurtma</b>  #{order.pk}\n"
                            f"📍 Ism: {order.c_name or 'Nomaʼlum'}\n"
                            f"📍 Yo'nalish: {order.c_direction or 'Nomaʼlum'}\n"
                            f"👥 Yo‘lovchilar soni: {c_count or 'Nomaʼlum'}\n\n"
                            f"🚖 Buyurtmaga qo‘ng‘iroq qilinmoqda...\n"
                            f"👨‍✈️ Haydovchi: {driver.full_name}\n"
                            f"\n\n<b>📜 Tarix:</b>{history_text or '\n— Tarix mavjud emas —'}"
                        ),
                        parse_mode="html"
                    )

                except Exception as e:
                    print(f"Error take order: {e}")
                    await callback.message.answer("⚠️ Guruhdagi xabarni yangilab bo‘lmadi.")

            # AVTO REJECT TASK CHAQIRISH:
            schedule_auto_reject(order.id, driver.chat_id, driver.full_name)
    except Exception as e:
        print(f"errorrrrrr: {e}")

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

        history_qs = await sync_to_async(list)(order.history.order_by("created_at").all())

        history_text = ""
        n = 1
        for hist in history_qs:
            action = dict(OrderStatus.choices).get(hist.status, hist.status)
            history_text += f"\n {n}. {hist.doer} — {action} ({localtime(hist.created_at).strftime('%H:%M:%S')})"
            n += 1

        await bot.edit_message_text(
            chat_id=order.group_chat_id,
            message_id=order.group_message_id,
            text=(
                f"<b>Yangi buyurtma</b>  #{order.pk}\n"
                f"📍 Ism: {order.c_name or 'Nomaʼlum'}\n"
                f"📍 Yo'nalish: {order.c_direction or 'Nomaʼlum'}\n"
                f"👥 Yo‘lovchilar soni: {c_count or 'Nomaʼlum'}\n\n"
                f"<b>📜 Tarix:</b>{history_text or '\n— Tarix mavjud emas —'}\n\n"
                f"Buyurtmani olish uchun tugmani bosing 👇"
            ),
            parse_mode="HTML",
            reply_markup=await get_order_ik(order_id)
        )

        order_text = (
            f"🚖 *Yangi buyurtma:*  #{order.pk}\n\n"
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

    driver = await Driver.get_user(chat_id=user.id)
    if not driver or not driver.status:
        await callback.answer("❌ Sizning hisobingiz faol emas.", show_alert=True)
        return

    order = await Order.get_order(order_id=order_id)
    if not order:
        await callback.answer("❌ Buyurtma topilmadi.")
        return

    if order.d_id != callback.from_user.id:
        await callback.answer("❌ Siz bu buyurtmaga biriktirilmagansiz.")
        return

    # Avval faol ticketni olish
    ticket = await Ticket.get_active_ticket(chat_id=user.id)
    if not ticket:
        await callback.answer("❌ Sizda faol chipta mavjud emas!", show_alert=True)
        return

    # Yo'nalish mosligini tekshirish
    if ticket.direction != order.c_direction:
        await callback.answer("❌ Buyurtma yo'nalishi chiptadagi yo‘nalish bilan mos emas!", show_alert=True)
        return

    # Limitni tekshirish (chiptadagi yo‘lovchilar + yangi orderdagi yo‘lovchilar)
    ticket_passenger_count = await sync_to_async(
        lambda: sum([d.count for d in ticket.details.all()])
    )()
    total_after = ticket_passenger_count + (order.c_count or 0)
    if total_after > driver.limit_count_per_target:
        await callback.answer("❌ Limitdan oshib ketdi!", show_alert=True)
        return

    # ✅ Darhol javob
    await callback.answer("✅ Buyurtma qabul qilindi", show_alert=True)

    # Holatni yangilash
    order.status = OrderStatus.COMPLETE
    await sync_to_async(order.save)()

    # Tarixga yozish
    await create_order_history(
        order=order,
        doer=callback.from_user.full_name,
        status="accept"
    )

    # TicketDetail yaratish
    await sync_to_async(TicketDetail.objects.create)(
        ticket=ticket,
        order=order,
        full_name=order.c_name or "",
        phone=order.c_phone or "",
        count=order.c_count or 0
    )
    await ticket.asave()

    # Guruhdagi xabarni yangilash
    try:
        from bot.instance.handlers import get_order_ik

        history_qs = await sync_to_async(list)(order.history.order_by("created_at").all())
        history_text = ""
        for idx, hist in enumerate(history_qs, start=1):
            action = dict(OrderStatus.choices).get(hist.status, hist.status)
            history_text += f"\n {idx}. {hist.doer} — {action} ({localtime(hist.created_at).strftime('%H:%M:%S')})"

        c_count = order.c_count if order.c_count > 0 else "Pochta"

        await bot.edit_message_text(
            chat_id=order.group_chat_id,
            message_id=order.group_message_id,
            text=(
                f"<b>Yangi buyurtma</b>  #{order.pk}\n"
                f"📍 Ism: {order.c_name or 'Nomaʼlum'}\n"
                f"📍 Yo'nalish: {order.c_direction or 'Nomaʼlum'}\n"
                f"👥 Yo‘lovchilar soni: {c_count or 'Nomaʼlum'}\n\n"
                f"🚖 Buyurtma olindi\n"
                f"👨‍✈️ Haydovchi: {driver.full_name}\n\n"
                f"<b>📜 Tarix:</b>{history_text or '\n— Tarix mavjud emas —'}\n\n"
            ),
            parse_mode="HTML"
        )

        order_text = (
            f"🚖 <b>Yangi buyurtma</b>  #{order.pk}\n\n"
            f"👤 <b>Mijoz:</b> <a href='tg://user?id={order.c_chat_id}'>{order.c_name}</a>\n"
            f"📞 <b>Telefon:</b> {order.c_phone or 'Nomaʼlum'}\n"
            f"🧑‍<b>Yo‘lovchilar:</b> {c_count or 'Nomaʼlum'}\n"
            f"📍 <b>Yo‘nalish:</b> {order.c_direction or 'Ko‘rsatilmagan'}\n"
            f"{f'📬 <b>Username:</b> @{order.c_username}' if order.c_username else ''}"
            f"\n\nBuyurtmani qabul qildingiz"
        )
        await callback.message.edit_text(
            order_text,
            parse_mode='HTML'
        )

    except Exception as e:
        print(f"⚠️ Guruhdagi xabarni yangilab bo‘lmadi.\n{e}")


async def ticket_close(callback: CallbackQuery, bot: Bot):
    ticket_id = int(callback.data.split(":")[1])
    chat_id = str(callback.from_user.id)

    # Har doim darhol javob beramiz — kechikishni oldini olish uchun
    try:
        await callback.answer("⏳ Tekshirilmoqda...")
    except:
        pass

    try:
        user = await Driver.objects.aget(chat_id=chat_id)
        ticket = await Ticket.objects.aget(id=ticket_id, driver=user)
    except (Driver.DoesNotExist, Ticket.DoesNotExist):
        await callback.message.edit_text("❌ Ticket topilmadi.")
        return

    if ticket.status != TicketStatus.OPEN:
        await callback.message.edit_text("❌ Bu ticket allaqachon yopilgan.")
        return

    ticket.status = TicketStatus.CLOSED
    ticket.updated_at = timezone.now()
    await sync_to_async(ticket.save)()

    await callback.message.edit_text(
        "✅ Ticket yopildi.\n\n"
        "📂 /ticket - Ticketlaringizni ko‘rish"
    )

from django.utils.timezone import now, localtime
from datetime import timedelta

async def ticket_create(callback: CallbackQuery, bot: Bot):
    try:
        direction_code = callback.data.split(":")[1]
        chat_id = str(callback.from_user.id)

        try:
            user = await Driver.objects.aget(chat_id=chat_id)
        except Driver.DoesNotExist:
            await callback.answer("❌ Siz ro‘yxatdan o‘tmagansiz.", show_alert=True)
            await callback.message.delete()
            return

        # Oxirgi yopilgan yoki to'lgan ticket dan 5 soat o'tganmi?
        five_hours_ago = now() - timedelta(hours=3)
        last_ticket = await Ticket.objects \
            .filter(driver=user) \
            .order_by('-updated_at') \
            .afirst()

        if last_ticket and last_ticket.updated_at > five_hours_ago:
            soat_farqi = (now() - last_ticket.updated_at).seconds // 3600
            daqiqa_farqi = ((now() - last_ticket.updated_at).seconds % 3600) // 60
            await callback.answer(
                f"⏳ Oxirgi klientni olganingizdan beri hali 3 soat o'tmagan.",
                show_alert=True
            )
            await callback.message.edit_text(
                f"⏳ Oxirgi yo'nalishingiz: {last_ticket.get_direction_display()}\n"
                f"🕓 So‘nggi o‘zgarish: {localtime(last_ticket.updated_at).strftime('%Y-%m-%d %H:%M')}\n"
                f"⏱ O‘tgan vaqt: {soat_farqi} soat {daqiqa_farqi} daqiqa\n\n"
                f"Kamida 3 soat kutishingiz kerak!\n\n"
                f"/ticket - Ma'lumotlarni ko‘rish"
            )
            return

        # 24 soatda ochilgan ticketlar soni limitdan oshmasligi kerak
        day_ago = now() - timedelta(hours=24)
        direction_count = await Ticket.objects.filter(
            driver=user,
            created_at__gte=day_ago
        ).acount()

        if direction_count >= user.limit_target_per_24hours:
            await callback.answer(
                f"🚫 24 soat ichida {user.limit_target_per_24hours} tadan ortiq yo'nalishni almashtirolmaysiz.",
                show_alert=True
            )
            await callback.message.edit_text(
                f"🚫 24 soat ichida {user.limit_target_per_24hours} tadan ortiq yo'nalishni almashtirolmaysiz.\n\n"
                f"/ticket - Klientlarni ko‘rish"
            )
            return


        # 4. Ticket yaratish
        await Ticket.objects.filter(driver=user, status=True).aupdate(status=False)
        ticket = Ticket(
            driver=user,
            direction=direction_code,
            created_at=now(),
            updated_at=now()
        )
        await sync_to_async(ticket.save)()

        from bot.instance.handlers import ticket as ticket_handler
        # Yangilangan ticket handleri o'zi eski xabarlarni o'chirib yangisini yuboradi
        await ticket_handler(callback.message, bot, show_keyboard=True, clean=True)

    except Exception as e:
        print(f"Ticket create ERROR: {e}")
        await callback.message.edit_text(
            "⚠️ Nimadir xato ketdi!\n\n"
            "🎫 /ticket — Ma’lumotlarini ko‘rish"
        )


async def ticket_refresh(callback: CallbackQuery, bot: Bot):
    from bot.instance.handlers import ticket
    # Yangilangan ticket handleri o'zi eski xabarlarni o'chirib yangisini yuboradi
    await ticket(callback.message, bot, show_keyboard=True, clean=True)
