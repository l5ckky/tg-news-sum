import asyncio
import os

import pyrogram.enums

import config
import db
try:
    from loguru import logger
    from pyrogram import Client, filters
    from pyrogram.types import Message
    from pymystem3 import Mystem
except ImportError:
    os.system('python -m pip install -r requirements.txt')
    from loguru import logger
    from pyrogram import Client, filters
    from pyrogram.types import Message
    from pymystem3 import Mystem


logger.add('main_log.log', level='DEBUG', format="{time} {level} {message}", rotation="10 MB")  # Логгирование


api_hash = config.api_hash  # Получаем api из конфига
api_id = config.api_id

stem = Mystem()  # Это морфологический модуль

commands = {'канал': 'channels', 'слово': 'words', 'пользователь': 'users'}  # Связь между командой и именем таблицы в БД


class Params:  # Класс для удобного хранения и получения данных из бд в реальном времени

    words = []
    channels = []
    forward_target = []

    async def get_attrs(self):  # Загружаем данные из БД в переменные
        words = db.DB().select("SELECT * FROM words")
        for item in words:
            self.words.append(item[0])
        tmp = db.DB().select("SELECT * FROM channels")
        for item in tmp:
            chat = await client.get_chat(item[0])  # переводит имя в ID
            self.channels.append(chat.id)
            await asyncio.sleep(0.1)
        forward_target = db.DB().select("SELECT * FROM users")
        for item in forward_target:
            self.forward_target.append(item[0])


client = Client(name="my_account", api_hash=api_hash, api_id=api_id)


# Функция прооверяет есть ли совпадение слов
def word_filter(words, t):
    text = t.lower()  # Получаем текст сообщения
    text_array = stem.lemmatize(text)  # Разбиваем текст на массив слов и приводим все слова к начальной форме
    for word in words:
        if word in text_array:  # Если слово есть в массиве слов
            logger.info(f'Совпадение слова {word} со списком')
            return True
    return False


# Функция срабатывает при получении любого сообщения
@client.on_message(filters=filters.channel)
async def echo(client_object, message: Message):
    await Params().get_attrs()  # Сразу же поддтягиваем всё из БД в переменные
    test = 1
    if message.chat.id == config.control_chanel_id:
        logger.info(f"Получено сообщение от управляющего канала {message.chat.id}: {message.text}")
        text = message.text.lower()  # Получаем текст сообщения
        text_array = text.split(' ')  # Разбиваем текст на массив слов

        try:  # Эта конструкция проверяет на правильность принятой команды
            if text_array[0] == 'добавить':

                if text_array[1] == 'слово' or text_array[1] == 'канал' or text_array[1] == 'пользователь':

                    if text_array[1] == 'канал':

                        try:  # Крайне простая проверка на правильность имени канала
                            await client.get_chat(text_array[2])
                        except Exception:
                            await client_object.send_message(message.chat.id, f"{text_array[2]} Несуществующий канал или ошибка в имени")
                            test = 0

                    if test:
                        db.DB().insert(commands[text_array[1]], [text_array[2]])
                        await client_object.send_message(message.chat.id, f"{text_array[1]} добавил")
                else:
                    await client_object.send_message(message.chat.id, f"{text_array[1]} не найдено в списке команд")

            elif text_array[0] == 'удалить':

                if text_array[1] == 'слово' or text_array[1] == 'канал':
                    db.DB().delete(commands[text_array[1]], [text_array[2]])
                    await client_object.send_message(message.chat.id, f"{text_array[1]} удалил")
                else:
                    await client_object.send_message(message.chat.id, f"{text_array[1]} не найдено в списке команд")
            elif text_array[0] == 'список':
                result = f'{text_array[1]}:\n'
                for item in db.DB().select(f"""SELECT * FROM {commands[text_array[1]]}"""):
                    result += item[0] + '\n'

                await client_object.send_message(message.chat.id, result)
            elif text_array[0] == 'помощь':
                await client_object.send_message(message.chat.id, config.help_message)
            else:
                await client_object.send_message(message.chat.id, f'Неверная команда, попробуйте написать "помощь"')

        except IndexError:
            await client_object.send_message(message.chat.id, f'Неверная команда, попробуйте написать "помощь"')
    else:
        print(message)
        if message.text:
            text = message.text
        elif message.caption:
            text = message.caption
        logger.debug(f"Получено сообщение от канала {message.chat.id}: {text}")
        if message.chat.id in Params.channels:  # Основная логика
            logger.debug(f'Канал {message.chat.id} есть в списке')
            if word_filter(Params.words, text):
                forward_target = Params.forward_target
                if len(forward_target) == 0:
                    forward_target.append(config.control_chanel_id)
                for target in forward_target:
                    logger.info(f'Переслал сообщение пользователю {target}')
                    await message.forward(target)
                    #await client.send_message(target,
                    #                          f"[{message.chat.title}]({message.link})\n\n>{text}",
                    #                          parse_mode=pyrogram.enums.ParseMode.MARKDOWN)


if __name__ == '__main__':
    try:
        client.run()
    except Exception:
        os.remove('my_account.session')
        client.run()
