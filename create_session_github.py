import os
import asyncio
import sys
import base64
from telethon import TelegramClient
from telethon.errors import PhoneCodeInvalidError, SessionPasswordNeededError

API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
PHONE = os.getenv('PHONE', '')
CODE = os.getenv('CODE', '')
PASSWORD = os.getenv('PASSWORD', '')  # для 2FA

if not API_ID or not API_HASH:
    print("❌ API_ID или API_HASH не установлены")
    sys.exit(1)

if not PHONE:
    print("❌ PHONE не установлен")
    sys.exit(1)

async def create_session():
    print("🚀 Создание сессии через GitHub...")
    print(f"📱 Номер: {PHONE}")
    
    client = TelegramClient('session', API_ID, API_HASH)
    
    try:
        await client.connect()
        print("✅ Подключено к Telegram")
        
        if await client.is_user_authorized():
            print("✅ Сессия уже существует и активна")
            me = await client.get_me()
            print(f"👤 Авторизован: {me.first_name}")
            await client.disconnect()
            return
        
        # Отправляем запрос на код
        await client.send_code_request(PHONE)
        print("📨 Код подтверждения отправлен в Telegram")
        
        if not CODE:
            print("")
            print("⚠️ Код не передан.")
            print("1. Проверьте Telegram — там код подтверждения")
            print("2. Запустите workflow СНОВА и укажите этот код в поле 'phone_code'")
            await client.disconnect()
            return
        
        print(f"🔑 Используем код: {CODE}")
        
        try:
            await client.sign_in(PHONE, CODE)
        except SessionPasswordNeededError:
            if not PASSWORD:
                print("❌ Требуется пароль 2FA. Добавьте секрет PASSWORD.")
                await client.disconnect()
                return
            await client.sign_in(password=PASSWORD)
        
        print("✅ Сессия создана успешно!")
        me = await client.get_me()
        print(f"👤 Авторизован: {me.first_name}")
        
    except PhoneCodeInvalidError:
        print("❌ Неверный код! Запустите workflow снова с правильным кодом.")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.disconnect()
        print("✅ Готово!")

if __name__ == '__main__':
    asyncio.run(create_session())
