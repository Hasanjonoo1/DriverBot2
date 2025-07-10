from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

ask_phone_b = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


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