import asyncio
import os
import string

import telethon.types
from telethon import TelegramClient, events
from telethon.tl.types import Channel
from pymystem3 import Mystem
from loguru import logger

from text_format import words_separator, word_filter

import config
import db

logger.add('main_log.log', level='DEBUG', format="{time} {level} {message}", rotation="10 MB")

api_hash = config.api_hash
api_id = config.api_id

stem = Mystem()

commands = {'канал': 'channels', 'слово': 'words', 'пользователь': 'users'}


class Params:
    words = []
    channels = []
    forward_target = []

    async def get_attrs(self, client):
        self.words = []
        self.channels = []
        self.forward_target = []

        words = db.DB().select("SELECT * FROM words")
        for item in words:
            self.words.append(item[0])

        tmp = db.DB().select("SELECT * FROM channels")
        for item in tmp:
            try:
                ite = int(item[0])
            except Exception:
                ite = item[0]
            try:
                chat = await client.get_entity(ite)
                if isinstance(chat, Channel):
                    self.channels.append(chat.id)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error getting chat {item[0]}: {e}")

        forward_target = db.DB().select("SELECT * FROM users")
        for item in forward_target:
            self.forward_target.append(item[0])


client = TelegramClient('my_account', api_id, api_hash)

# def word_filter(words, t):
#     if not t:
#         return False
#     stext = t[:]
#     text = t.lower()
#     text = ''.join([i for i in text if i.isalpha() or i in string.punctuation])
#     text_array = stem.lemmatize(" ".join(words))
#     for word in text.split():
#         if word in text_array:
#             index = stext.index(word)
#             logger.info(f'Совпадение слова {word} со списком на индексе {index}')
#             return index
#     return False


# @client.on(events.NewMessage(chats=config.control_chanel_id))
# async def control_channel_handler(event):
#     await Params().get_attrs(client)
#     message = event.message
#     text = message.text.lower() if message.text else ""
#     text_array = text.split(' ')


@client.on(events.NewMessage(func=lambda e: e.is_channel))
async def channel_message_handler(event):
    params = Params()
    await params.get_attrs(client)

    message: telethon.types.Message = event.message
    print(message)
    text = message.message or ""
    if message.peer_id.channel_id in params.channels:
        logger.debug(f'Канал {message.peer_id.channel_id} есть в списке')
        word, lemtext = word_filter(params.words, text)
        if word:
            logger.info(f'Переслал сообщение в управляющий канал')
            await client.forward_messages(config.control_chanel_id, message)
            # Альтернативный вариант с кастомным сообщением:
            chat = await client.get_entity(message.peer_id.channel_id)
            # await client.send_message(
            #     config.control_chanel_id,
            #     f"<strong>{word}</strong>\nСообщение: <a href=\"https://t.me/c/{chat.id}/{message.id}\">{chat.title}</a>\n{words_separator(word, message.message, lemtext)}",
            #     parse_mode='html')
            # await client.send_message(target, f">Циатата", parse_mode="md")


if __name__ == '__main__':
    try:
        with client:
            print("запуск бота...")
            client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Error: {e}")
        if os.path.exists('my_account.session'):
            os.remove('my_account.session')
        with client:
            client.run_until_disconnected()