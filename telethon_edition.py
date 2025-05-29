import asyncio
import os
import string

import telethon.types
from telethon import TelegramClient, events
from telethon.tl.types import Channel, PeerChannel
from pymystem3 import Mystem
from loguru import logger
import datetime
from text_format import words_separator, word_filter, text_msg, text_ch

import config
import db
import stats as st

logger.add('logs/main_log.log', level='DEBUG', format="{time} {level} {message}", rotation="50 MB")
logger.add(f'logs/daily/log_{datetime.date.today().strftime("%d_%m_%Y")}.log',
           level='DEBUG',
           format="{time:DD.MM.YYYY-HH:mm:ss.SSS} | {level} | {message}",
           rotation=datetime.time(hour=0, minute=0, second=0))


api_hash = config.api_hash
api_id = config.api_id

stem = Mystem()

commands = {'канал': 'channels', 'слово': 'words', 'пользователь': 'users'}

stats = st.Statistics()

class Params:
    words = []
    channels = []
    forward_target = []

    async def get_attrs(self, client):
        self.words = []
        self.channels = []
        self.forward_target = []

        self.words = [i[0] for i in db.DB().select("SELECT * FROM words")]

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

        self.forward_target = [i[0] for i in db.DB().select("SELECT * FROM users")]


client = TelegramClient('my_account', api_id, api_hash)


@client.on(events.NewMessage(chats=config.notifications))
async def control_channel_handler(event):
    await client.forward_messages(PeerChannel(config.control_chanel_id), event.message)
    logger.info(f'Техническое оповещение {text_msg(event.message)} переслано в канал сводки')


@client.on(events.NewMessage(func=lambda e: e.is_channel))
async def channel_message_handler(event):
    params = Params()
    await params.get_attrs(client)

    message: telethon.types.Message = event.message
    text = message.message or ""
    if message.peer_id.channel_id in params.channels:
        logger.debug(
            f'В канале {await text_ch(client, message.peer_id.channel_id)} появился новый пост {text_msg(message)}')
        a = word_filter(params.words, text)
        if a:
            word, lemtext = a
            try:
                await client.forward_messages(config.control_chanel_id, message)
                logger.info(
                    f'Пост {text_msg(message)} канала {await text_ch(client, message.peer_id.channel_id)} содержит '
                    + f'слово \"{word}\" и переслан в канал сводки')
                stats.record(word, (await client.get_entity(message.peer_id.channel_id)).username)
            except telethon.errors.ChatForwardsRestrictedError:
                await client.send_message(
                    config.control_chanel_id,
                    f"Обнаружено сообщение от "
                    + f"{await text_ch(client, message.peer_id.channel_id, add_id=False)}\n"
                    + f"{words_separator(word, message.message, lemtext)}\n"
                    + f"(канал запретил пересылку, посмотрите по <a href=\"https://t.me/c/{message.peer_id.channel_id}/"
                    + f"{message.id}\">ссылке</a>)",
                    parse_mode='html')
                logger.info(
                    f'Пост {text_msg(message)} запрещающего пересылку канала '
                    + f'{await text_ch(client, message.peer_id.channel_id)} содержит '
                    + f'слово \"{word}\" и отправлен в канал сводки')


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
