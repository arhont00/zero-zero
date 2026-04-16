"""
Профиль пользователя — заказы, баланс, стрик, свой камень.
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from src.database.db import db
from src.database.models import UserModel

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "profile")
async def profile_show(callback: CallbackQuery):
    """Профиль пользователя."""
    user_id = callback.from_user.id
    user = UserModel.get(user_id)

    if not user:
        await callback.answer("Профиль не найден", show_alert=True)
        return

    name = user.get('first_name') or user.get('username') or f"ID{user_id}"

    # Баланс бонусов
    bonus = UserModel.get_bonus_balance(user_id)

    # Заказы
    with db.cursor() as c:
        c.execute("SELECT COUNT(*) as cnt FROM orders WHERE user_id = ? AND status = 'paid'", (user_id,))
        orders_count = c.fetchone()['cnt'] or 0

        c.execute("SELECT SUM(total_price) as total FROM orders WHERE user_id = ? AND status = 'paid'", (user_id,))
        row = c.fetchone()
        total_spent = int(row['total'] or 0)

    text = (
        f"👤 *МОЙ ПРОФИЛЬ*\n\n"
        f"*{name}*\n\n"
        f"📦 *Заказов:* {orders_count} (на {total_spent} ₽)\n"
        f"💰 *Бонусы:* {int(bonus)} ₽\n\n"
    )

    buttons = [
        [InlineKeyboardButton(text="📦 МОИ ЗАКАЗЫ", callback_data="my_orders")],
        [InlineKeyboardButton(text="🤝 РЕФЕРАЛЫ", callback_data="referral")],
    ]

    buttons.append([InlineKeyboardButton(text="← МЕНЮ", callback_data="menu")])

    await callback.message.edit_text(
        text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()
