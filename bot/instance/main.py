from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from bot.instance.handlers import start, handle_contact, profile, get_id, take_order, reject, accept, ticket, \
    ticket_close, ticket_create, ticket_refresh, select_target

webhook_dp = Dispatcher()

webhook_dp.message.register(start, CommandStart())
webhook_dp.message.register(profile, Command('profile'))
webhook_dp.message.register(get_id, Command('id'))
webhook_dp.message.register(ticket, Command('ticket'))
webhook_dp.message.register(handle_contact, F.contact)
webhook_dp.message.register(select_target, F.text == "🧭 Yo‘nalish tanlash")

webhook_dp.callback_query.register(take_order, F.data.startswith("take_order:"))
webhook_dp.callback_query.register(reject, F.data.startswith("reject_order:"))
webhook_dp.callback_query.register(accept, F.data.startswith("accept_order:"))
webhook_dp.callback_query.register(ticket_close, F.data.startswith("ticket_close:"))
webhook_dp.callback_query.register(ticket_create, F.data.startswith("ticket_create"))
webhook_dp.callback_query.register(ticket_refresh, F.data.startswith("ticket_refresh"))


async def feed_update(token: str, update: dict):
    try:
        webhook_book = Bot(token=token)
        aiogram_update = types.Update(**update)
        await webhook_dp.feed_update(bot=webhook_book, update=aiogram_update)
    finally:
        await webhook_book.session.close()