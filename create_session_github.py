import os
import sys
import asyncio
from telethon import TelegramClient, errors
from telethon.network.connection import ConnectionTcpFull
from python_socks import ProxyType

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
    
    # Очищаем старую базу, чтобы избежать "database is locked"
    for f in ["session.session", "session.session-journal"]:
        if os.path.exists(f):
            os.remove(f)
            print(f"🧹 Удалён старый файл: {f}")

    # Список бесплатных SOCKS5 прокси (актуальны на момент написания)
    PROXIES = [
        {"proxy_type": ProxyType.SOCKS5, "addr": "185.130.104.180", "port": 1080},
        {"proxy_type": ProxyType.SOCKS5, "addr": "194.58.103.212", "port": 1080},
        {"proxy_type": ProxyType.SOCKS5, "addr": "45.94.31.77", "port": 1080},
        {"proxy_type": ProxyType.SOCKS5, "addr": "176.113.73.55", "port": 1080},
        {"proxy_type": ProxyType.SOCKS5, "addr": "37.18.73.60", "port": 1080},
    ]

    client = None
    for p in PROXIES:
        try:
            print(f"🌐 Пробуем SOCKS5 {p['addr']}:{p['port']}...")
            client = TelegramClient(
                "session", API_ID, API_HASH,
                connection=ConnectionTcpFull,
                proxy=(p["proxy_type"], p["addr"], p["port"], True, None, None)
            )
            await client.connect()
            print(f"✅ Подключились через {p['addr']}")
            break
        except Exception as e:
            print(f"⚠️ Прокси {p['addr']} не сработал: {e}")
            client = None
            # чистим базу после неудачной попытки
            for f in ["session.session", "session.session-journal"]:
                if os.path.exists(f):
                    os.remove(f)

    if client is None:
        print("❌ Не удалось подключиться ни через один прокси.")
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
            await client.send_code_request(PHONE)
            print("✅ Код отправлен. Проверьте Telegram (чат 'Telegram' или '777000').")
            print("⚠️ Запустите workflow СНОВА, вставив код в поле 'code'.")
        except Exception as e:
            print(f"❌ Ошибка при запросе кода: {e}")
        await client.disconnect()
        sys.exit(0)
    
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
    print("✅ Готово! Файл session.session создан.")

if __name__ == "__main__":
    asyncio.run(main())
