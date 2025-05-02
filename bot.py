import logging

import asyncio
from aiogram import Bot, Dispatcher, types, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import config

# Настройка логгирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=config.manage_bot_token, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# "База данных"
channels = []
words = []

admins_list = config.admin_chats_list


# Состояния FSM
class AddStates(StatesGroup):
    waiting_channel = State()
    waiting_word = State()


# Генератор клавиатуры
def build_keyboard(items, prefix, back_handler):
    builder = InlineKeyboardBuilder()

    # Добавляем элементы в две колонки
    for i in range(0, len(items), 2):
        row = items[i:i + 2]
        for item in row:
            builder.add(InlineKeyboardButton(
                text=item,
                callback_data=f"{prefix}-item-{item}"
            ))
        builder.adjust(2)

    # Если нечетное количество, последний элемент на всю ширину
    # if len(items) % 2 != 0:
    #     builder.row(InlineKeyboardButton(
    #         text=items[-1],
    #         callback_data=f"{prefix}_item_{items[-1]}"
    #     ), width=1)

    # Кнопки управления
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=back_handler),
        InlineKeyboardButton(text="➕ Добавить", callback_data=f"{prefix}-add")
    )
    return builder.as_markup()


# Главное меню
@dp.message(Command("start"))
async def cmd_start(message: types.Message, back: None | types.CallbackQuery = None):
    if message.chat.id not in admins_list:
        print(message.chat.id)
        keyboard = InlineKeyboardBuilder()
        keyboard.add(
            InlineKeyboardButton(text="😔 Уйти", callback_data="leave")
        )
        await message.answer(
            f"😔 {html.bold('Вас нет в списке!')}\n{html.italic('Кажется, вы не тот, кого я так жду...')}",
            reply_markup=keyboard.as_markup()
        )
        return
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(text="📢 Каналы", callback_data="channels"),
        InlineKeyboardButton(text="📝 Слова", callback_data="words")
    )
    if back:
        await back.message.edit_text(
            f"⚙️ {html.bold('Главное меню')}",
            reply_markup=keyboard.as_markup()
        )
    else:
        await message.answer(
            f"⚙️ {html.bold('Главное меню')}",
            reply_markup=keyboard.as_markup()
        )


# Обработка кнопки Каналы
@dp.callback_query(F.data == "channels")
async def channels_list(callback: types.CallbackQuery):
    await callback.message.edit_text(
        f"{html.bold('Список каналов')}\n{html.italic('Нажмите на элемент для подробностей') if channels else html.italic('Кажется, здесь пусто... Добавьте первый канал!')}",
        reply_markup=build_keyboard(channels, "channel", "main_menu")
    )


# Обработка кнопки Слова
@dp.callback_query(F.data == "words")
async def words_list(callback: types.CallbackQuery):
    await callback.message.edit_text(
        f"{html.bold('Список слов')}\n{html.italic('Нажмите на элемент для подробностей') if words else html.italic('Кажется, здесь пусто... Добавьте первое слово!')}",
        reply_markup=build_keyboard(words, "word", "main_menu")
    )


# Обработка элементов
@dp.callback_query(F.data.startswith(("channel-item-", "word-item-")))
async def handle_item(callback: types.CallbackQuery):
    prefix = "channel" if callback.data.startswith('channel') else "word"
    item = callback.data.split("-", maxsplit=2)[2]

    channel_url = item

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=(await (bot.get_chat("@" + item))).title if prefix == "channel" else item,
        url=f"t.me/{channel_url}" if prefix == "channel" else None,
        callback_data=f"dummy" if prefix == "word" else None,
    ), width=1)
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data=prefix + "s"
    ), InlineKeyboardButton(
        text="❌ Удалить",
        callback_data=f"{prefix}-delete-{item}"
    ), width=2)

    await callback.message.edit_text(
        f"{html.bold('Меню управления элементом')}\n{html.italic('Вы, что, хотите удалить его?..')}",
        reply_markup=builder.as_markup()
    )


# Обработка удаления
@dp.callback_query(F.data.startswith(("channel-delete-", "word-delete-")))
async def delete_item(callback: types.CallbackQuery):
    prefix = "channel" if "channel" in callback.data else "word"
    item = callback.data.split("-", maxsplit=2)[2]

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"{prefix}-confirm-{item}"),
        InlineKeyboardButton(text="❌ Отменить", callback_data=f"{prefix}s")
    )
    await callback.message.edit_text(
        f"{html.bold(f'Вы действительно хотите удалить «{item}»?')}\n{html.italic('Чтобы отменить нажмите «Отменить».')}",
        reply_markup=builder.as_markup()
    )


# Подтверждение удаления
@dp.callback_query(F.data.startswith(("channel-confirm-", "word-confirm-")))
async def confirm_delete(callback: types.CallbackQuery):
    prefix = "channel" if "channel" in callback.data else "word"
    item = callback.data.split("-", maxsplit=2)[2]

    if prefix == "channel":
        channels.remove(item)
        await channels_list(callback)
    else:
        words.remove(item)
        await words_list(callback)


# Обработка добавления
@dp.callback_query(F.data.endswith("-add"))
async def add_item(callback: types.CallbackQuery, state: FSMContext):
    prefix = callback.data.split("-")[0]

    await state.set_state(AddStates.waiting_channel if prefix == "channel" else AddStates.waiting_word)
    await state.update_data(prefix=prefix)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="❌ Отмена",
        callback_data=f"{prefix}s"
    ))

    await callback.message.edit_text(
        f"{html.bold('Введите тег канала...')}\n{html.italic('К примеру, @amsu_online')}" if prefix == "channel" else
        f"{html.bold('Введите слово в начальной форме...')}\n{html.italic('К примеру: проиграл – проиграть, зонтики – зонтик')}",
        reply_markup=builder.as_markup()
    )


# Обработка ввода данных
@dp.message(AddStates.waiting_channel)
@dp.message(AddStates.waiting_word)
async def process_item(message: types.Message, state: FSMContext):
    data = await state.get_data()
    prefix = data.get("prefix")
    item = message.text.lower()

    await (await bot.get_chat(message.chat.id)).delete_message(message.message_id - 1)

    channel_name = ''
    bad_request = False
    if prefix == "channel":
        if item.startswith("@"):
            item = item[1:]
        try:
            channel_name = (await (bot.get_chat("@" + item))).title
            channels.append(item)
        except Exception as e:
            bad_request = True
    else:
        words.append(item)

    if bad_request:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"{prefix}s"
        ), InlineKeyboardButton(
            text="➕ Добавить другой",
            callback_data=f"{prefix}-add"
        ))
        await message.delete()
        await message.answer(
            f"{html.bold('Канал не найден!')}\n{html.italic(f'Тег @{item} не существует!')}",
            reply_markup=builder.as_markup()
        )
        await state.clear()
    else:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"{prefix}s"
        ), InlineKeyboardButton(
            text="➕ Добавить ещё",
            callback_data=f"{prefix}-add"
        ))
        await message.answer(
            f"{html.bold('Успешно добавлено!')}\n{html.italic(f'Канал «{channel_name}» добавлен!')}" if prefix == 'channel' else
            f"{html.bold('Успешно добавлено!')}\n{html.italic(f'Слово «{item}» добавлено!')}",
            reply_markup=builder.as_markup()
        )
        await state.clear()


# Возврат в главное меню
@dp.callback_query(F.data == "main_menu")
async def back_to_main(callback: types.CallbackQuery):
    await cmd_start(callback.message, callback)


# Кнопка, чтобы уйти
@dp.callback_query(F.data == "leave")
async def leave_scene(callback: types.CallbackQuery):
    await callback.message.edit_text("Пока!")
    await (await bot.get_chat(callback.message.chat.id)).delete_message(callback.message.message_id - 1)
    await asyncio.sleep(2)
    await callback.message.delete()


if __name__ == "__main__":
    dp.run_polling(bot)
