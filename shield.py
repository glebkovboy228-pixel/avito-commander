from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import (
    check_limit, log_usage, get_user, set_user_style,
    get_today_usage_count,
)
from llm import generate_review_response

router = Router()

STYLE_LABELS = {
    "polite": "Вежливый",
    "confident": "Уверенный",
    "apologetic": "С извинением",
    "neutral": "Нейтральный",
}

user_states = {}


def style_keyboard():
    kb = InlineKeyboardBuilder()
    for key, label in STYLE_LABELS.items():
        kb.button(text=label, callback_data=f"style_{key}")
    kb.button(text="🔙 Назад", callback_data="back_to_menu")
    kb.adjust(2)
    return kb.as_markup()


def shield_menu_keyboard(selected_style: str = None):
    kb = InlineKeyboardBuilder()
    style_label = STYLE_LABELS.get(selected_style, "Вежливый")
    kb.button(text=f"Стиль: {style_label}", callback_data="choose_style")
    kb.button(text="✍️ Отправить отзыв", callback_data="send_review")
    kb.button(text="🔙 Назад в меню", callback_data="back_to_menu")
    kb.adjust(1)
    return kb.as_markup()


@router.callback_query(F.data == "shield")
async def shield_entry(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    selected_style = user["selected_style"] if user else "polite"
    user_states[callback.from_user.id] = {"module": "shield"}
    text = (
        "🛡 <b>Щит — ответы на отзывы</b>\n\n"
        "Отправьте текст отзыва — получите готовый ответ для публикации.\n\n"
        f"Текущий стиль: <b>{STYLE_LABELS.get(selected_style, 'Вежливый')}</b>\n"
    )
    await callback.message.edit_text(text, reply_markup=shield_menu_keyboard(selected_style))
    await callback.answer()


@router.callback_query(F.data == "choose_style")
async def choose_style(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выберите стиль ответа:",
        reply_markup=style_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("style_"))
async def set_style(callback: CallbackQuery):
    style_key = callback.data.split("_", 1)[1]
    set_user_style(callback.from_user.id, style_key)
    user_states[callback.from_user.id] = {"module": "shield"}
    await callback.message.edit_text(
        f"✅ Стиль изменён на: <b>{STYLE_LABELS[style_key]}</b>\n\n"
        "Отправьте текст отзыва — получите готовый ответ.",
        reply_markup=shield_menu_keyboard(style_key),
    )
    await callback.answer()


@router.callback_query(F.data == "send_review")
async def send_review_prompt(callback: CallbackQuery):
    user_states[callback.from_user.id] = {"module": "shield", "waiting": True}
    await callback.message.edit_text(
        "✍️ Отправьте текст отзыва следующим сообщением.\n"
        "Просто скопируйте и вставьте сюда отзыв клиента.\n\n"
        "Для отмены нажмите /cancel"
    )
    await callback.answer()


@router.message(Command("cancel"))
async def cancel_action(message: Message):
    user_states.pop(message.from_user.id, None)
    await message.answer("Действие отменено. Напишите /start для меню.")


@router.message()
async def handle_review(message: Message):
    state = user_states.get(message.from_user.id)
    if not state or not state.get("waiting"):
        return

    user_states[message.from_user.id] = {"module": "shield"}

    if not check_limit(message.from_user.id, "shield"):
        kb = InlineKeyboardBuilder()
        kb.button(text="💎 Оформить подписку", callback_data="subscribe")
        kb.button(text="🔙 Назад", callback_data="shield")
        kb.adjust(1)
        await message.answer(
            "⚠️ <b>Дневной лимит исчерпан (5 ответов)</b>\n\n"
            "Оформите подписку для безлимитных ответов:",
            reply_markup=kb.as_markup(),
        )
        return

    user = get_user(message.from_user.id)
    style = user["selected_style"] if user else "polite"

    await message.answer("⏳ Генерирую ответ...")

    response = generate_review_response(message.text, style)
    log_usage(message.from_user.id, "shield")

    remaining = 5 - get_today_usage_count(message.from_user.id, "shield")
    remaining_text = (
        f"\n\n📊 Осталось сегодня: {remaining}"
        if (user and user["subscription"] == "free")
        else ""
    )

    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Другой стиль", callback_data="choose_style")
    kb.button(text="🛡 Новый отзыв", callback_data="send_review")
    kb.button(text="🔙 В меню", callback_data="back_to_menu")
    kb.adjust(2, 1)

    await message.answer(
        f"<b>Готовый ответ:</b>\n\n{response}{remaining_text}",
        reply_markup=kb.as_markup(),
    )
