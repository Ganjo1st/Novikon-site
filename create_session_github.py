import os
import sys
import asyncio
from telethon import TelegramClient, errors
from telethon.network.connection import ConnectionTcpMTProxyRandomizedIntermediate

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
PHONE = os.environ.get("PHONE_NUMBER", "")
CODE = os.environ.get("CODE", "").strip()
PASSWORD = os.environ.get("PASSWORD", "").strip()

if not API_ID or not API_HASH or not PHONE:
    print("❌ Ошибка: не заданы API_ID, API_HASH или PHONE_NUMBER")
    sys.exit(1)

async def main():
    print("🚀 Подключение через MTProxy (обход блокировки Azure)...")
    
    # Очищаем старую базу, чтобы избежать "database is locked"
    for f in ["session.session", "session.session-journal"]:
        if os.path.exists(f):
            os.remove(f)
            print(f"🧹 Удалён старый файл: {f}")

    # Рабочие MTProxy серверы Telegram
    # Если один не работает, пробуем другой.
    PROXIES = [
        ("mtproxy.dark-purple.ru", 443, "dd00000000000000000000000000000000"),
        ("proxy.mtproxy.org", 443, "dd00000000000000000000000000000000"),
        ("mtp.stel.com", 443, "ee00000000000000000000000000000000"),
        ("tg.sakha.tv", 443, "dd00000000000000000000000000000000"),
        ("91.221.60.10", 443, "ee00000000000000000000000000000000"),
        ("139.59.238.238", 443, "dd00000000000000000000000000000000"),
    ]

    client = None
    for host, port, secret in PROXIES:
        try:
            print(f"🌐 Пробуем MTProxy {host}:{port}...")
            client = TelegramClient(
                "session", API_ID, API_HASH,
                connection=ConnectionTcpMTProxyRandomizedIntermediate,
                proxy=(host, port, secret)
            )
            await client.connect()
            print(f"✅ Успешно подключились через {host}")
            break
        except Exception as e:
            print(f"⚠️ Прокси {host} не сработал: {e}")
            client = None
            # чистим базу после неудачной попытки
            for f in ["session.session", "session.session-journal"]:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except:
                        pass

    if client is None:
        print("❌ Не удалось подключиться ни через один прокси.")
        print("Попробуйте позже или используйте другой способ.")
        sys.exit(1)

    if await client.is_user_authorized():
        print("✅ Клиент уже авторизован (сессия существует).")
        me = await client.get_me()
        print(f"✅ Вы вошли как: {me.first_name} (ID: {me.id})")
        await client.disconnect()
        return

    if not CODE:
        print("📨 Отправка кода...")
        try:
            sent = await client.send_code_request(PHONE)
            print("✅ Код отправлен. Проверьте Telegram (чат 'Telegram' или '777000').")
            print("⚠️ Запустите workflow СНОВА, вставив код в поле 'code'.")
        except Exception as e:
            print(f"❌ Ошибка при запросе кода: {e}")
        await client.disconnect()
        sys.exit(0)
    
    # Если код передан, пробуем войти
    try:
        await client.sign_in(PHONE, CODE)
        print("✅ Вход по коду успешен!")
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
    await client.disconnect()
    print("✅ Готово! Файл session.session создан и валиден.")

if __name__ == "__main__":
    asyncio.run(main())
