from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from bot.models import DirectionStatus

ask_phone_b = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

target = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧭 Yo‘nalish tanlash")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder="Quyidagi tugmani bosing"
)

async def targets():
    keyboard = []

    for direction in DirectionStatus:
        keyboard.append(
            InlineKeyboardButton(
                text= direction.label,
                callback_data= f"ticket_create:{direction.value}"
            )
        )

    return InlineKeyboardMarkup(inline_keyboard=[keyboard])

async def order_private_ik(order_id):
    # Inline tugmalar
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"accept_order:{order_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_order:{order_id}")
        ]
    ])

async def get_order_ik(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🚕 Buyurtmani olish", callback_data=f"take_order:{order_id}")]
            ])

async def close_ticket(ticket_id, status):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Ticketni yangilash", callback_data="ticket_refresh")]

    ])