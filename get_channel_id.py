import argparse
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError
import config


def get_channel_id(client, channel_name):
    try:
        entity = client.get_entity(channel_name)
        print(f"Название: {entity.title}")
        print(f"ID: {entity.id}")
        print(f"Username: @{entity.username}" if entity.username else "Username: None")
    except Exception as e:
        print(f"Ошибка: {e}")


def main():
    parser = argparse.ArgumentParser(description='Получение ID канала Telegram по его названию')
    parser.add_argument('channel_name', help='Название канала')

    api_hash = config.api_hash
    api_id = config.api_id

    args = parser.parse_args()

    client = TelegramClient('my_account', api_id, api_hash)

    try:
        client.connect()
        if not client.is_user_authorized():
            client.send_code_request(args.phone)
            client.sign_in(args.phone, input('Введите код: '))
        get_channel_id(client, args.channel_name)
    except SessionPasswordNeededError:
        client.sign_in(password=input('Введите пароль: '))
        get_channel_id(client, args.channel_name)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        client.disconnect()


if __name__ == '__main__':
    main()
