import os
import sys
import asyncio
from telethon import TelegramClient, errors

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
PHONE = os.environ.get("PHONE_NUMBER", "")
CODE = os.environ.get("CODE", "").strip()
PASSWORD = os.environ.get("PASSWORD", "").strip()

if not API_ID or not API_HASH or not PHONE:
    print("❌ Ошибка: не заданы API_ID, API_HASH или PHONE_NUMBER")
    sys.exit(1)

async def main():
    print("🚀 Создание сессии через GitHub...")
    print(f"📱 Номер: {PHONE[:4]}***{PHONE[-2:]}")
    
    # ВАЖНО: создаём клиент, но не подключаемся здесь, а используем контекстный менеджер
    client = TelegramClient("session", API_ID, API_HASH)
    
    await client.connect()
    
    if await client.is_user_authorized():
        print("✅ Клиент уже авторизован (сессия уже существует).")
    else:
        print("✅ Подключено к Telegram")
        try:
            sent = await client.send_code_request(PHONE)
            print("📨 Код подтверждения отправлен в Telegram")
        except Exception as e:
            print(f"❌ Ошибка при запросе кода: {e}")
            await client.disconnect()
            sys.exit(1)

        if not CODE:
            print("⚠️ Код не передан.")
            print("1. Проверьте Telegram — там код подтверждения")
            print("2. Запустите workflow СНОВА и укажите этот код в поле 'code'")
            await client.disconnect()
            sys.exit(0)

        try:
            await client.sign_in(PHONE, CODE, phone_code_hash=sent.phone_code_hash)
            print("✅ Успешный вход по коду!")
        except errors.SessionPasswordNeededError:
            if not PASSWORD:
                print("❌ Требуется пароль 2FA, но переменная PASSWORD не задана.")
                await client.disconnect()
                sys.exit(1)
            try:
                await client.sign_in(password=PASSWORD)
                print("✅ Успешный вход по паролю 2FA!")
            except Exception as e:
                print(f"❌ Ошибка 2FA: {e}")
                await client.disconnect()
                sys.exit(1)
        except Exception as e:
            print(f"❌ Ошибка входа: {e}")
            await client.disconnect()
            sys.exit(1)

    if not await client.is_user_authorized():
        print("❌ Сессия НЕ авторизована после всех шагов.")
        await client.disconnect()
        sys.exit(1)

    me = await client.get_me()
    print(f"✅ Авторизован как: {me.first_name} (ID: {me.id})")
    
    await client.disconnect()
    print("✅ Готово! Файл session.session создан и валиден.")

if __name__ == "__main__":
    asyncio.run(main())
