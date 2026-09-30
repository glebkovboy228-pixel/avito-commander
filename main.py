import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database import init_db, add_or_update_user, get_user
from shield import router as shield_router

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()
dp.include_router(shield_router)


def main_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="🛡 Щит — ответы на отзывы", callback_data="shield")
    kb.button(text="👁 Глаз — алерты (скоро)", callback_data="coming_soon")
    kb.button(text="📊 Прайс — цены (скоро)", callback_data="coming_soon")
    kb.button(text="💎 Подписка", callback_data="subscribe")
    kb.adjust(1)
    return kb.as_markup()


def subscribe_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Базовый — 499 ₽/мес", callback_data="sub_basic")
    kb.button(text="Про — 999 ₽/мес", callback_data="sub_pro")
    kb.button(text="🔙 Назад", callback_data="back_to_menu")
    kb.adjust(1)
    return kb.as_markup()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    add_or_update_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.full_name or "",
    )
    text = (
        "🤖 <b>Авито-Командир</b>\n\n"
        "Ваш помощник для работы с Авито и отзывами.\n\n"
        "Выберите раздел:"
    )
    await message.answer(text, reply_markup=main_keyboard())


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🤖 <b>Авито-Командир</b>\n\nВыберите раздел:",
        reply_markup=main_keyboard(),
    )
    await callback.answer()


@dp.callback_query(F.data == "coming_soon")
async def coming_soon(callback: CallbackQuery):
    await callback.answer("Этот модуль в разработке 🚧", show_alert=True)


@dp.callback_query(F.data == "subscribe")
async def show_subscribe(callback: CallbackQuery):
    text = (
        "💎 <b>Подписка Авито-Командир</b>\n\n"
        "<b>Базовый — 499 ₽/мес</b>\n"
        "• Безлимит ответов на отзывы\n"
        "• 10 фильтров для алертов\n"
        "• 20 товаров для мониторинга цен\n\n"
        "<b>Про — 999 ₽/мес</b>\n"
        "• Всё из Базового\n"
        "• Безлимит фильтров и товаров\n"
        "• Проверка каждые 30 секунд\n"
        "• Авто-постинг ответов\n\n"
        "Оплата: перевод на карту / ЮMoney.\n"
        "После оплаты напишите админу."
    )
    await callback.message.edit_text(text, reply_markup=subscribe_keyboard())
    await callback.answer()


@dp.callback_query(F.data.startswith("sub_"))
async def handle_sub(callback: CallbackQuery):
    sub_type = callback.data.split("_", 1)[1]
    price = 499 if sub_type == "basic" else 999
    await callback.answer(
        f"Для оформления подписки ({price} ₽) напишите админу.",
        show_alert=True,
    )


async def main():
    init_db()
    logging.info("Бот запущен! Нажмите Ctrl+C для остановки.")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
