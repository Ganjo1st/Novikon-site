import os
import asyncio
import sys
from telethon import TelegramClient
from telethon.errors import PhoneCodeInvalidError

API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
PHONE = os.getenv('PHONE', '')
CODE = os.getenv('CODE', '')

if not API_ID or not API_HASH:
    print("❌ API_ID или API_HASH не установлены")
    sys.exit(1)

if not PHONE:
    print("❌ PHONE_NUMBER не установлен")
    sys.exit(1)

async def create_session():
    print("🚀 Создание сессии через GitHub...")
    print(f"📱 Номер: {PHONE}")
    
    client = TelegramClient('session', API_ID, API_HASH)
    
    try:
        await client.connect()
        print("✅ Подключено к Telegram")
        
        # Проверяем, не авторизованы ли уже
        if await client.is_user_authorized():
            print("✅ Сессия уже существует и активна")
            me = await client.get_me()
            print(f"👤 Авторизован: {me.first_name}")
            return
        
        # Отправляем запрос на код
        await client.send_code_request(PHONE)
        print("📨 Код подтверждения отправлен в Telegram")
        
        # Если код передан через input
        if CODE:
            print(f"🔑 Используем код: {CODE}")
            try:
                await client.sign_in(PHONE, CODE)
                print("✅ Сессия создана успешно!")
                me = await client.get_me()
                print(f"👤 Авторизован: {me.first_name}")
                return
            except PhoneCodeInvalidError:
                print("❌ Неверный код! Запустите workflow снова с правильным кодом.")
                return
        
        # Если код не передан, просим ввести вручную
        print("\n⚠️ Введите код подтверждения из Telegram:")
        print("1. Перейдите в Telegram")
        print("2. Найдите код в сообщении")
        print("3. Введите его ниже")
        
        # Ждем ввода кода (работает только в интерактивном режиме)
        code = input("Код: ").strip()
        
        if code:
            try:
                await client.sign_in(PHONE, code)
                print("✅ Сессия создана успешно!")
                me = await client.get_me()
                print(f"👤 Авторизован: {me.first_name}")
            except PhoneCodeInvalidError:
                print("❌ Неверный код! Попробуйте снова.")
        else:
            print("❌ Код не введен")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.disconnect()
        print("✅ Готово!")

if __name__ == '__main__':
    asyncio.run(create_session())
