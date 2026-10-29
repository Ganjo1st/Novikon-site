import os
import sys
import asyncio
from telethon import TelegramClient, errors
from telethon.tl.functions.auth import ResendCodeRequest

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
PHONE = os.environ.get("PHONE_NUMBER", "")
CODE = os.environ.get("CODE", "").strip()
PASSWORD = os.environ.get("PASSWORD", "").strip()

if not API_ID or not API_HASH or not PHONE:
    print("❌ Ошибка: не заданы API_ID, API_HASH или PHONE_NUMBER")
    sys.exit(1)

async def main():
    print("🚀 Подключение...")
    client = TelegramClient("session", API_ID, API_HASH)
    await client.connect()
    
    if await client.is_user_authorized():
        print("✅ Клиент уже авторизован (сессия существует).")
        me = await client.get_me()
        print(f"✅ Вы вошли как: {me.first_name} (ID: {me.id})")
        await client.disconnect()
        return

    if not CODE:
        print("📨 Отправка кода (SMS)...")
        sent = await client.send_code_request(PHONE)
        print("✅ Код отправлен. Проверьте Telegram (в том числе чат 'Telegram' или '777000').")
        print("⚠️ Если код не пришёл в течение 1-2 минут, Telegram заблокировал SMS для этого IP.")
        print("В таком случае попробуйте следующий запуск с параметром phone_code, но без запроса.")
        await client.disconnect()
        sys.exit(0)
    
    # Если код УЖЕ передан, пробуем войти без запроса нового кода
    try:
        # Пытаемся войти с тем кодом, который ввели (чтобы не терять hash)
        await client.sign_in(PHONE, CODE)
        print("✅ Вход по коду успешен!")
    except errors.SessionPasswordNeededError:
        if not PASSWORD:
            print("❌ Нужен 2FA пароль, но он не передан.")
            await client.disconnect()
            sys.exit(1)
        try:
            await client.sign_in(password=PASSWORD)
            print("✅ Вход по 2FA успешен!")
        except Exception as e:
            print(f"❌ Ошибка 2FA: {e}")
            await client.disconnect()
            sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка входа: {e}")
        print("⚠️ Код мог истечь. Попробуйте запросить код заново (очистив поле), и затем сразу ввести.")
        await client.disconnect()
        sys.exit(1)

    me = await client.get_me()
    print(f"✅ Авторизован как: {me.first_name} (ID: {me.id})")
    await client.disconnect()
    print("✅ Готово! Файл session.session создан и валиден.")

if __name__ == "__main__":
    asyncio.run(main())
