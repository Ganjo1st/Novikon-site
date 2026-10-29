import os
import sys
from telethon import TelegramClient, errors

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
PHONE = os.environ.get("PHONE_NUMBER", "")
CODE = os.environ.get("CODE", "").strip()
PASSWORD = os.environ.get("PASSWORD", "").strip()

if not API_ID or not API_HASH or not PHONE:
    print("❌ Ошибка: не заданы API_ID, API_HASH или PHONE_NUMBER")
    sys.exit(1)

print("🚀 Создание сессии через GitHub...")
print(f"📱 Номер: {PHONE[:4]}***{PHONE[-2:]}")

client = TelegramClient("session", API_ID, API_HASH)
client.connect()

if client.is_user_authorized():
    print("✅ Клиент уже авторизован (сессия уже существует).")
else:
    print("✅ Подключено к Telegram")
    try:
        sent = client.send_code_request(PHONE)
        print("📨 Код подтверждения отправлен в Telegram")
    except Exception as e:
        print(f"❌ Ошибка при запросе кода: {e}")
        client.disconnect()
        sys.exit(1)

    # Проверяем, передан ли код, уже ПОСЛЕ запроса
    if not CODE:
        print("⚠️ Код не передан.")
        print("1. Проверьте Telegram — там код подтверждения")
        print("2. Запустите workflow СНОВА и укажите этот код в поле 'code'")
        client.disconnect()
        sys.exit(0)  # Завершаем с успехом, чтобы не было красного крестика в Actions

    try:
        client.sign_in(PHONE, CODE, phone_code_hash=sent.phone_code_hash)
        print("✅ Успешный вход по коду!")
    except errors.SessionPasswordNeededError:
        if not PASSWORD:
            print("❌ Требуется пароль 2FA, но переменная PASSWORD не задана.")
            client.disconnect()
            sys.exit(1)
        try:
            client.sign_in(password=PASSWORD)
            print("✅ Успешный вход по паролю 2FA!")
        except Exception as e:
            print(f"❌ Ошибка 2FA: {e}")
            client.disconnect()
            sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка входа: {e}")
        client.disconnect()
        sys.exit(1)

if not client.is_user_authorized():
    print("❌ Сессия НЕ авторизована после всех шагов.")
    client.disconnect()
    sys.exit(1)

me = client.get_me()
print(f"✅ Авторизован как: {me.first_name} (ID: {me.id})")

client.disconnect()
print("✅ Готово! Файл session.session создан и валиден.")
