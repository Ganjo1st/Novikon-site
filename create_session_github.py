import os
import sys
import asyncio
from telethon import TelegramClient, errors
from telethon.sessions import StringSession

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
PHONE = os.environ.get("PHONE_NUMBER", "")
CODE = os.environ.get("CODE", "").strip()
PASSWORD = os.environ.get("PASSWORD", "").strip()

if not API_ID or not API_HASH or not PHONE:
    print("❌ Ошибка: не заданы API_ID, API_HASH или PHONE_NUMBER")
    sys.exit(1)

async def main():
    print("🚀 Создание StringSession через GitHub Actions...")
    
    # Удаляем старые файлы, чтобы не было блокировок
    for f in ["session.session", "session.session-journal"]:
        if os.path.exists(f):
            os.remove(f)

    # Используем StringSession вместо файла
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()

    if await client.is_user_authorized():
        print("✅ Уже авторизован!")
        print("=== ВАША STRINGSESSION ===")
        print(client.session.save())
        print("==========================")
        await client.disconnect()
        return

    if not CODE:
        print("📨 Запрос кода (придет в приложение Telegram, не по SMS)...")
        try:
            # force_sms=False заставляет Telegram отправить код в приложение
            sent = await client.send_code_request(PHONE, force_sms=False)
            print("✅ Код отправлен в приложение Telegram (чат 'Telegram' или '777000').")
            print("⚠️ Запустите workflow СНОВА, вставив код в поле 'code'.")
        except Exception as e:
            print(f"❌ Ошибка при запросе кода: {e}")
        await client.disconnect()
        sys.exit(0)

    try:
        await client.sign_in(PHONE, CODE)
        print("✅ Вход успешен!")
    except errors.SessionPasswordNeededError:
        if not PASSWORD:
            print("❌ Нужен 2FA пароль.")
            await client.disconnect()
            sys.exit(1)
        await client.sign_in(password=PASSWORD)
        print("✅ Вход по 2FA успешен!")
    except Exception as e:
        print(f"❌ Ошибка входа: {e}")
        await client.disconnect()
        sys.exit(1)

    me = await client.get_me()
    print(f"✅ Авторизован как: {me.first_name} (ID: {me.id})")
    
    # ВЫВОДИМ STRINGSESSION В ЛОГИ
    session_string = client.session.save()
    print("\n\n=== ВАША STRINGSESSION (СКОПИРУЙТЕ ЕЁ) ===")
    print(session_string)
    print("=========================================\n\n")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
