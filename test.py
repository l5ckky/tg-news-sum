from pyrogram import Client
import config

api_hash = config.api_hash  # Получаем api из конфига
api_id = config.api_id
app = Client(name="my_account", api_hash=api_hash, api_id=api_id)


async def main():
    async with app:
        async for dialog in app.get_dialogs():
            if dialog.chat.title == "Новости":
                try:
                    print(dialog.chat.title, dialog.chat.id, dialog.chat.username)
                except Exception:
                    pass


app.run(main())
