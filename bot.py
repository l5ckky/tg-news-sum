import datetime
import logging

import aiogram.exceptions
import os
import db

import asyncio
from aiogram import Bot, Dispatcher, types, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaDocument, FSInputFile
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
# channels = []
# words = []


# words = [i[0] for i in db.DB().select("SELECT * FROM words")]
# channels = [i[0] for i in db.DB().select("SELECT * FROM channels")]

def human_read_format(size):
    if size < 1024:
        return f"{size}Б"
    elif size < 1024 * 1024:
        return f"{round(size / 1024)}КБ"
    elif size < 1024 * 1024 * 1024:
        return f"{round(size / (1024 * 1024))}МБ"
    else:
        return f"{round(size / (1024 * 1024 * 1024))}ГБ"


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
async def cmd_start(message: types.Message, back: None | types.Message = None):
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
    keyboard.row(
        InlineKeyboardButton(text="📢 Каналы", callback_data="channels"),
        InlineKeyboardButton(text="📝 Слова", callback_data="words"))
    keyboard.row(InlineKeyboardButton(text="📡 Логи", callback_data="logs"))

    if back:
        domsg = back.edit_text
    else:
        domsg = message.answer

    await domsg(f"⚙️ {html.bold('Главное меню')}",
                reply_markup=keyboard.as_markup())


# Обработка кнопки Каналы
@dp.callback_query(F.data == "channels")
async def channels_list(callback: types.CallbackQuery):
    channels = [i[0] for i in db.DB().select("SELECT * FROM channels")]
    await callback.message.edit_text(
        f"{html.bold('📢 Список каналов')}\n{html.italic('Нажмите на элемент для подробностей') if channels else html.italic('Кажется, здесь пусто... Добавьте первый канал!')}",
        reply_markup=build_keyboard(channels, "channel", "main_menu")
    )


# Обработка кнопки Слова
@dp.callback_query(F.data == "words")
async def words_list(callback: types.CallbackQuery):
    words = [i[0] for i in db.DB().select("SELECT * FROM words")]
    await callback.message.edit_text(
        f"{html.bold('📝 Список слов')}\n{html.italic('Нажмите на элемент для подробностей') if words else html.italic('Кажется, здесь пусто... Добавьте первое слово!')}",
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
    try:
        if prefix == "channel":
            db.DB().delete("channels", [item])
            await channels_list(callback)
        else:
            db.DB().delete("words", [item])
            await words_list(callback)
    except Exception as e:
        await callback.message.answer(
            f"{html.bold('Произошла ошибка при удалении из Базы Данных:')}\n{html.blockquote(e)}")
        await back_to_main(callback)


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

    await bot.delete_message(message.chat.id, message.message_id - 1)

    channel_name = ''
    bad_request = False
    try:
        if prefix == "channel":
            try:
                if item.startswith("@"):
                    item = item[1:]
                channel_name = (await (bot.get_chat("@" + item))).title
                db.DB().insert("channels", [item])
            except aiogram.exceptions.TelegramBadRequest:
                bad_request = True
        else:
            db.DB().insert("words", [item])
    except Exception as e:
        await message.answer(
            f"{html.bold('Произошла ошибка при добавлении в Базу Данных:')}\n{html.blockquote(e)}")
        await cmd_start(message, message)

    if bad_request:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"{prefix}s"
        ), InlineKeyboardButton(
            text="➕ Добавить другой",
            callback_data=f"{prefix}-add"))
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
    await cmd_start(callback.message, callback.message)


# Обработка кнопки Логи
@dp.callback_query(F.data == "logs")
async def logs_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🗓 Лог за сегодня",
        callback_data='logs-log-today',
    ))
    builder.row(InlineKeyboardButton(
        text="🗓 Лог за вчера",
        callback_data='logs-log-yesterday',
    ))
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data='main_menu',
    ), InlineKeyboardButton(
        text="🗂 Другое",
        callback_data='logs-other',
    )
        # , InlineKeyboardButton(
        # text=f"📥 Скачать все логи ({human_read_format(os.path.getsize("logs/main_log.log"))})",
        # callback_data='logs-download-main',)
    )
    try:
        await callback.message.edit_text(
            f"{html.bold('📡 Меню управления логами')}\n{html.italic('Выберите действие')}",
            reply_markup=builder.as_markup()
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            f"{html.bold('📡 Меню управления логами')}\n{html.italic('Выберите действие')}",
            reply_markup=builder.as_markup()
        )


@dp.callback_query(F.data == "logs-other")
async def logs_menu_other(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data='logs',
    ), InlineKeyboardButton(
        text="Выбрать дату",
        callback_data='logs-select-date',
    ))
    builder.row(InlineKeyboardButton(
        text="Выбрать кол-во строк",
        callback_data='logs-select-lines',
    ))
    builder.row(InlineKeyboardButton(
        text=f"📥 Скачать все логи ({human_read_format(os.path.getsize('logs/main_log.log'))})",
        callback_data='logs-action-download-main'))
    builder.row()
    await callback.message.edit_text(
        f"{html.bold('📡 Меню управления логами: Другое')}\n{html.italic('Выберите действие...')}",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("logs-log-"))
async def logs_log(callback: types.CallbackQuery):
    pr = callback.data.split("-", maxsplit=2)[-1]

    if pr == 'today':
        day = datetime.datetime.today().date()
        day_word = 'сегодня'
    elif pr == 'yesterday':
        day = (datetime.datetime.today() - datetime.timedelta(days=1)).date()
        day_word = 'вчера'
    else:
        day = datetime.datetime.strptime(pr, "%d_%m_%Y").date()
        day_word = day.strftime("%d.%m.%Y")

    count_lines = 0
    day_log = ''
    file = f"logs/daily/log_{day.strftime('%d_%m_%Y')}.log"
    if os.path.exists(file):
        day_log = file
        with open(day_log, 'r', encoding="utf-8") as f:
            count_lines = len(f.readlines())

    if not day_log:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="Нет логов",
            callback_data='dummy',
        ))
        builder.row(InlineKeyboardButton(
            text=f"⬅️ К меню логов",
            callback_data='logs',
        ))
        format = "%d.%m.%Y"
        await callback.message.edit_text(
            f"{html.bold(f'📡 Логи за {day_word} не найдены!')}\n{html.italic(f'{day.strftime(format)} нет логов!')}",
            reply_markup=builder.as_markup()
        )
        return

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=f"Просмотр ({str(count_lines)} строк)",
        callback_data=f'logs-action-show-{day_log}',
    ))
    builder.row(InlineKeyboardButton(
        text=f"Скачать файл ({human_read_format(os.path.getsize(f'{day_log}'))})",
        callback_data=f'logs-action-download-{day_log}',
    ))
    builder.row(InlineKeyboardButton(
        text=f"⬅️ К меню логов",
        callback_data='logs'))
    a = f"({day.strftime('%d.%m.%Y')})"
    t = 'today'
    y = "yesterday"
    s = ''
    try:
        await callback.message.edit_text(
            f"{html.bold(f'📡 Лог за {day_word} {a if pr in (t, y) else s}')}\n{html.italic('Выберите действие...')}",
            reply_markup=builder.as_markup()
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            f"{html.bold(f'📡 Лог за {day_word} {a if pr in (t, y) else s}')}\n{html.italic('Выберите действие...')}",
            reply_markup=builder.as_markup()
        )


@dp.callback_query(F.data == "logs-select-date")
async def logs_select_date(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="Открыть календарь",
        callback_data='logs-select-date-calendar',
    ))
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data='logs-other',
    ), InlineKeyboardButton(
        text=f"Вручную",
        callback_data='logs-select-date-manual'))
    await callback.message.edit_text(
        f"{html.bold('📡 Меню управления логами: Выбрать дату')}\n{html.italic('🛠 В разработке...')}",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data.startswith("logs-action-"))
async def logs_actions(callback: types.CallbackQuery):
    pr = callback.data.split("-", maxsplit=3)[2]
    r = "reload" in callback.data.split(":", maxsplit=1)
    file = callback.data.split("-", maxsplit=3)[3] if not r else callback.data.split("-", maxsplit=3)[3].split(':')[0]

    if file == "main":
        file = "logs/main_log.log"
        day = None
    else:
        day = datetime.datetime.strptime(file.split("/")[-1].split(".")[0].split("_", maxsplit=1)[1], "%d_%m_%Y").date()

    if pr == 'download':
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"logs{('-log-' + day.strftime('%d_%m_%Y')) if day else ''}",
        ))
        media = FSInputFile(file)
        await callback.message.edit_media(InputMediaDocument(media=media), reply_markup=builder.as_markup())
    elif pr == 'show':
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"logs{('-log-' + day.strftime('%d_%m_%Y')) if day else ''}",
        ), InlineKeyboardButton(
            text="Обновить",
            callback_data=callback.data + (":reload" if not r else ''),
        ))
        with open(file, 'r', encoding="utf-8") as f:
            lines = [i.strip() for i in f.readlines()]
            log = '\n\n'.join(lines)
            msg = (callback.message.html_text if not r else "\n".join(
                callback.message.html_text.split('\n', maxsplit=2)[:2])) + f"\n{html.expandable_blockquote(log)}"
            if len(msg) > 4096:
                builder.row(InlineKeyboardButton(
                    text=f"Скачать файл ({human_read_format(os.path.getsize(f'{file}'))})",
                    callback_data=f'logs-action-download-{file}',
                ))
                a = '\n\n'
                msg = (callback.message.html_text if not r else "\n".join(
                    callback.message.html_text.split('\n', maxsplit=2)[
                    :2])) + f"\n{html.blockquote(a.join(lines[-5:]))}\n{html.italic('Выведены только последние 5 строк. Чтобы скачать файл всего лога, нажмите кнопку ниже...')}"
        try:
            await callback.message.edit_text(msg, reply_markup=builder.as_markup())
        except aiogram.exceptions.TelegramBadRequest as e:
            if "message is not modified" in e.message:
                await callback.answer()


@dp.callback_query(F.data == "dummy")
async def dummy(callback: types.CallbackQuery):
    await callback.answer()


# Кнопка, чтобы уйти
@dp.callback_query(F.data == "leave")
async def leave_scene(callback: types.CallbackQuery):
    await callback.message.edit_text("Пока!")
    await (await bot.get_chat(callback.message.chat.id)).delete_message(callback.message.message_id - 1)
    await asyncio.sleep(2)
    await callback.message.delete()


if __name__ == "__main__":
    dp.run_polling(bot)
