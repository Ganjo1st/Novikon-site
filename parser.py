import os
import json
import asyncio
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import shutil
import html as html_module
import re

# Получение данных из секретов
API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', '')
API_BACKEND_URL = os.getenv('API_BACKEND_URL', 'https://your-backend.koyeb.app')

if not API_ID or not API_HASH:
    print("❌ Ошибка: API_ID или API_HASH не установлены")
    exit(1)

if not CHANNEL_ID:
    print("❌ Ошибка: TELEGRAM_CHANNEL_ID не установлен")
    exit(1)

client = TelegramClient('session', API_ID, API_HASH)
LOGO_FILE = 'logo_H.png'

def clean_title(title):
    if not title:
        return ''
    title = re.sub(r'^\*\*\s*', '', title)
    title = re.sub(r'\s*\*\*$', '', title)
    title = re.sub(r'\*\*', '', title)
    title = ' '.join(title.split())
    return title

def clean_text(text):
    if not text:
        return ''
    text = re.sub(r'\*\*', '', text)
    text = ' '.join(text.split())
    return text

async def parse_channel():
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            print("❌ Сессия не авторизована!")
            return
        
        print("✅ Пользователь авторизован")
        
        try:
            if CHANNEL_ID.startswith('@'):
                entity = await client.get_entity(CHANNEL_ID)
            else:
                try:
                    entity = await client.get_entity(int(CHANNEL_ID))
                except ValueError:
                    entity = await client.get_entity(CHANNEL_ID)
        except Exception as e:
            print(f"❌ Не удалось найти канал: {e}")
            return
        
        print(f"📡 Подключен к каналу: {entity.title if hasattr(entity, 'title') else CHANNEL_ID}")
        
        posts = []
        limit = 200  # Загружаем 200, но на сайте показываем по лимиту
        count = 0
        
        os.makedirs('assets', exist_ok=True)
        os.makedirs('posts', exist_ok=True)
        
        print("📥 Получение истории сообщений...")
        async for message in client.iter_messages(entity, limit=limit):
            if message.text and message.text.startswith('/'):
                continue
            
            if not message.text and not message.media:
                continue
                
            post = {
                'id': message.id,
                'date': message.date.isoformat(),
                'text': message.text or '',
                'image_url': None
            }
            
            if message.media:
                try:
                    path = await client.download_media(message.media, file=f'temp_{message.id}.jpg')
                    if path:
                        new_path = f'assets/post_{message.id}.jpg'
                        shutil.move(path, new_path)
                        post['image_url'] = new_path
                        print(f"📸 Загружено медиа: {new_path}")
                except Exception as e:
                    print(f"⚠️ Ошибка загрузки медиа для {message.id}: {e}")
            
            posts.append(post)
            count += 1
            if count % 10 == 0:
                print(f"✅ Обработано {count} постов...")
        
        print(f"📊 Всего обработано {len(posts)} постов")
        
        with open('posts.json', 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        print("💾 Сохранен posts.json")
        
        print("📝 Генерация HTML страниц...")
        generate_html(posts, API_BACKEND_URL)
        generate_post_pages(posts, API_BACKEND_URL)
        
        posts_files = os.listdir('posts')
        print(f"📁 В папке posts создано {len(posts_files)} файлов")
        
        await client.disconnect()
        print("✅ Парсинг завершен успешно!")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        await client.disconnect()

def generate_html(posts, api_url):
    # Передаём только первые 42 статьи в HTML (для бесплатных)
    # Остальные будут загружаться через API для подписчиков
    posts_json = json.dumps(posts[:42], ensure_ascii=False)
    total_posts = len(posts)
    
    html_output = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Новикон - Новости</title>
    <link rel="icon" href="''' + LOGO_FILE + '''" type="image/png">
    <style>
        :root {
            --bg: #f5f5f5;
            --text: #333;
            --card-bg: white;
            --header-bg: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --shadow: 0 4px 15px rgba(0,0,0,0.08);
            --border: #e0e0e0;
            --accent: #667eea;
            --favorite: #ffc107;
            --unread: #ff4757;
            --premium: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        [data-theme="dark"] {
            --bg: #1a1a2e;
            --text: #e0e0e0;
            --card-bg: #16213e;
            --header-bg: linear-gradient(135deg, #0f3460 0%, #1a1a2e 100%);
            --shadow: 0 4px 15px rgba(0,0,0,0.3);
            --border: #2a2a4a;
            --accent: #7b8cde;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            transition: background 0.4s, color 0.4s;
        }
        header {
            background: var(--header-bg);
            color: white;
            padding: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: background 0.4s;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        .logo-container {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .logo-container img {
            height: 50px;
            width: auto;
            border-radius: 8px;
        }
        .site-title {
            font-size: 28px;
            font-weight: 700;
            color: white;
            text-decoration: none;
        }
        .site-subtitle {
            color: rgba(255,255,255,0.9);
            font-size: 14px;
        }
        .header-controls {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }
        .control-btn {
            background: rgba(255,255,255,0.2);
            border: 2px solid rgba(255,255,255,0.3);
            color: white;
            padding: 8px 14px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
            white-space: nowrap;
            position: relative;
        }
        .control-btn:hover {
            background: rgba(255,255,255,0.3);
            transform: scale(1.05);
        }
        .control-btn.active {
            background: rgba(255,255,255,0.4);
            border-color: white;
        }
        .control-btn.premium {
            background: var(--premium);
            border-color: rgba(255,255,255,0.5);
            font-weight: 600;
        }
        .control-btn.premium:hover {
            box-shadow: 0 0 20px rgba(245, 87, 108, 0.6);
        }
        .badge {
            position: absolute;
            top: -5px;
            right: -5px;
            background: var(--unread);
            color: white;
            border-radius: 50%;
            min-width: 20px;
            height: 20px;
            font-size: 11px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            padding: 0 4px;
        }
        
        .search-bar {
            max-width: 1200px;
            margin: 20px auto 0;
            padding: 0 20px;
            display: none;
        }
        .search-bar.active {
            display: block;
            animation: slideDown 0.3s ease;
        }
        .search-bar input {
            width: 100%;
            padding: 15px 20px;
            border: 2px solid var(--border);
            border-radius: 12px;
            background: var(--card-bg);
            color: var(--text);
            font-size: 16px;
            transition: all 0.3s;
        }
        .search-bar input:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .filter-bar {
            display: flex;
            gap: 10px;
            padding: 15px 0;
            flex-wrap: wrap;
            justify-content: center;
        }
        .filter-btn {
            padding: 8px 20px;
            border: 2px solid var(--border);
            background: var(--card-bg);
            color: var(--text);
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }
        .filter-btn:hover {
            border-color: var(--accent);
        }
        .filter-btn.active {
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }
        
        /* Premium banner */
        .premium-banner {
            background: var(--premium);
            color: white;
            padding: 20px 30px;
            border-radius: 16px;
            margin: 20px 0;
            display: none;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
            box-shadow: 0 8px 30px rgba(245, 87, 108, 0.3);
            animation: fadeIn 0.5s ease;
        }
        .premium-banner.show {
            display: flex;
        }
        .premium-banner h3 {
            font-size: 20px;
            margin-bottom: 5px;
        }
        .premium-banner p {
            opacity: 0.95;
            font-size: 14px;
        }
        .premium-banner button {
            background: white;
            color: #f5576c;
            border: none;
            padding: 12px 28px;
            border-radius: 25px;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            transition: transform 0.3s;
        }
        .premium-banner button:hover {
            transform: scale(1.05);
        }
        
        .news-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
            padding: 30px 0;
        }
        .news-card {
            background: var(--card-bg);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: var(--shadow);
            transition: transform 0.3s ease, box-shadow 0.3s ease, background 0.4s;
            cursor: pointer;
            text-decoration: none;
            color: inherit;
            display: block;
            position: relative;
            animation: fadeIn 0.5s ease forwards;
            opacity: 0;
        }
        .news-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        .news-card img {
            width: 100%;
            height: 220px;
            object-fit: cover;
            background: #e0e0e0;
            transition: transform 0.5s ease;
        }
        .news-card:hover img {
            transform: scale(1.05);
        }
        .news-content { padding: 20px; }
        .news-date { color: #888; font-size: 13px; margin-bottom: 10px; }
        .news-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 12px;
            line-height: 1.4;
            color: var(--text);
        }
        .news-text {
            color: var(--text);
            font-size: 15px;
            opacity: 0.8;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        .no-image {
            height: 220px;
            background: var(--header-bg);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 48px;
        }
        
        .card-actions {
            position: absolute;
            top: 10px;
            right: 10px;
            display: flex;
            gap: 8px;
            z-index: 10;
        }
        .action-btn {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            border: none;
            background: rgba(255,255,255,0.9);
            color: #333;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            transition: all 0.3s;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }
        .action-btn:hover {
            transform: scale(1.15);
            background: white;
        }
        .action-btn.favorite.active {
            background: var(--favorite);
            color: white;
        }
        
        /* Заблокированная карточка */
        .news-card.locked {
            position: relative;
            overflow: hidden;
        }
        .news-card.locked::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(240, 147, 251, 0.95) 0%, rgba(245, 87, 108, 0.95) 100%);
            backdrop-filter: blur(10px);
            z-index: 5;
        }
        .news-card.locked .lock-content {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 6;
            text-align: center;
            color: white;
            padding: 20px;
        }
        .news-card.locked .lock-content .lock-icon {
            font-size: 48px;
            margin-bottom: 10px;
        }
        .news-card.locked .lock-content h3 {
            font-size: 18px;
            margin-bottom: 10px;
        }
        .news-card.locked .lock-content p {
            font-size: 14px;
            opacity: 0.95;
            margin-bottom: 15px;
        }
        .news-card.locked .lock-content button {
            background: white;
            color: #f5576c;
            border: none;
            padding: 10px 24px;
            border-radius: 25px;
            font-weight: 700;
            cursor: pointer;
            transition: transform 0.3s;
        }
        .news-card.locked .lock-content button:hover {
            transform: scale(1.05);
        }
        
        .footer {
            text-align: center;
            padding: 30px 0;
            color: #888;
            font-size: 14px;
            border-top: 1px solid var(--border);
            margin-top: 20px;
            transition: border-color 0.4s;
        }
        .read-more {
            display: inline-block;
            margin-top: 12px;
            color: var(--accent);
            font-weight: 600;
            text-decoration: none;
        }
        
        .no-results {
            text-align: center;
            padding: 60px 20px;
            color: #888;
            font-size: 18px;
            grid-column: 1 / -1;
        }
        
        .toast-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .toast {
            background: var(--card-bg);
            color: var(--text);
            padding: 15px 20px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            border-left: 4px solid var(--accent);
            min-width: 280px;
            max-width: 400px;
            animation: slideInRight 0.4s ease;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .toast.favorite {
            border-left-color: var(--favorite);
        }
        .toast.success {
            border-left-color: #10b981;
        }
        .toast.error {
            border-left-color: #ef4444;
        }
        .toast-icon {
            font-size: 24px;
        }
        .toast-content {
            flex: 1;
            font-size: 14px;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(100px); }
            to { opacity: 1; transform: translateX(0); }
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        .badge.pulse {
            animation: pulse 1s ease infinite;
        }
        
        .progress-bar {
            position: fixed;
            top: 0;
            left: 0;
            height: 3px;
            background: var(--accent);
            width: 0%;
            z-index: 9999;
            transition: width 0.3s;
        }
        
        .lang-dropdown {
            position: relative;
            display: inline-block;
        }
        .lang-menu {
            display: none;
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 8px;
            background: var(--card-bg);
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            overflow: hidden;
            min-width: 150px;
            z-index: 200;
        }
        .lang-menu.active {
            display: block;
            animation: slideDown 0.3s ease;
        }
        .lang-option {
            padding: 12px 20px;
            cursor: pointer;
            transition: background 0.2s;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            color: var(--text);
        }
        .lang-option:hover {
            background: rgba(102, 126, 234, 0.1);
        }
        .lang-option.active {
            background: rgba(102, 126, 234, 0.15);
            font-weight: 600;
        }
        
        /* Модальные окна */
        .modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 2000;
            animation: fadeIn 0.3s;
            padding: 20px;
        }
        .modal.active {
            display: flex;
        }
        .modal-content {
            background: var(--card-bg);
            border-radius: 16px;
            padding: 40px;
            max-width: 420px;
            width: 100%;
            position: relative;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            animation: slideDown 0.3s;
            max-height: 90vh;
            overflow-y: auto;
        }
        .modal-close {
            position: absolute;
            top: 15px;
            right: 20px;
            font-size: 28px;
            cursor: pointer;
            color: #888;
            transition: color 0.3s;
            background: none;
            border: none;
            line-height: 1;
        }
        .modal-close:hover {
            color: var(--text);
        }
        .modal-content h2 {
            margin-bottom: 20px;
            text-align: center;
            color: var(--text);
        }
        .modal-content input {
            width: 100%;
            padding: 14px 18px;
            margin-bottom: 15px;
            border: 2px solid var(--border);
            border-radius: 10px;
            background: var(--bg);
            color: var(--text);
            font-size: 15px;
            transition: border-color 0.3s;
            font-family: inherit;
        }
        .modal-content input:focus {
            outline: none;
            border-color: var(--accent);
        }
        .modal-content button[type="submit"],
        .modal-content .primary-btn {
            width: 100%;
            padding: 14px;
            background: var(--header-bg);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s;
            font-family: inherit;
        }
        .modal-content button[type="submit"]:hover,
        .modal-content .primary-btn:hover {
            transform: scale(1.02);
        }
        .modal-content button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .switch-mode {
            text-align: center;
            margin-top: 15px;
            color: #888;
            font-size: 14px;
        }
        .switch-mode a {
            color: var(--accent);
            text-decoration: none;
            font-weight: 600;
        }
        
        .plans {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 20px;
        }
        .plan {
            padding: 25px 15px;
            border: 2px solid var(--border);
            border-radius: 12px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            position: relative;
        }
        .plan:hover {
            border-color: var(--accent);
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
        }
        .plan.recommended {
            border-color: #f5576c;
            background: linear-gradient(135deg, rgba(240, 147, 251, 0.05) 0%, rgba(245, 87, 108, 0.05) 100%);
        }
        .plan.recommended::before {
            content: 'ВЫГОДНО';
            position: absolute;
            top: -10px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--premium);
            color: white;
            font-size: 10px;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 10px;
            letter-spacing: 1px;
        }
        .plan h3 {
            font-size: 16px;
            margin-bottom: 10px;
            color: var(--text);
        }
        .plan .price {
            font-size: 32px;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 5px;
        }
        .plan.recommended .price {
            color: #f5576c;
        }
        .plan p {
            font-size: 13px;
            color: #888;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 10px;
            color: white;
            padding: 8px 14px;
            background: rgba(255,255,255,0.15);
            border-radius: 25px;
            font-size: 14px;
            cursor: pointer;
            transition: background 0.3s;
        }
        .user-info:hover {
            background: rgba(255,255,255,0.25);
        }
        .user-info .user-avatar {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: var(--premium);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: 700;
        }
        .user-info .user-status {
            font-size: 11px;
            opacity: 0.85;
        }
        
        @media (max-width: 768px) {
            .news-grid {
                grid-template-columns: 1fr;
                padding: 15px 0;
            }
            .logo-container img {
                height: 40px;
            }
            .site-title {
                font-size: 22px;
            }
            .header-content {
                flex-direction: column;
                gap: 10px;
                text-align: center;
            }
            .header-controls {
                justify-content: center;
            }
            .control-btn {
                font-size: 13px;
                padding: 7px 12px;
            }
            .modal-content {
                padding: 30px 20px;
            }
            .plans {
                grid-template-columns: 1fr;
            }
            .premium-banner {
                flex-direction: column;
                text-align: center;
            }
        }
    </style>
</head>
<body>
    <div class="progress-bar" id="progressBar"></div>
    
    <header>
        <div class="container">
            <div class="header-content">
                <div class="logo-container">
                    <a href="/Novikon-site/" style="text-decoration: none; display: flex; align-items: center; gap: 15px;">
                        <img src="''' + LOGO_FILE + '''" alt="Новикон Логотип">
                        <div>
                            <div class="site-title">Новикон</div>
                            <div class="site-subtitle" data-i18n="subtitle">Актуальные новости и события</div>
                        </div>
                    </a>
                </div>
                <div class="header-controls">
                    <button class="control-btn" onclick="toggleSearch()" title="Поиск">
                        🔍 <span data-i18n="search">Поиск</span>
                    </button>
                    <button class="control-btn" onclick="toggleFavorites()" id="favBtn" title="Избранное">
                        ⭐ <span data-i18n="favorites">Избранное</span>
                        <span class="badge" id="favBadge" style="display:none">0</span>
                    </button>
                    <button class="control-btn" id="unreadBtn" title="Непрочитанные">
                        📬 <span data-i18n="unread">Новые</span>
                        <span class="badge" id="unreadBadge" style="display:none">0</span>
                    </button>
                    <div class="lang-dropdown">
                        <button class="control-btn" onclick="toggleLangMenu()" title="Язык">
                            🌐 <span id="currentLang">RU</span>
                        </button>
                        <div class="lang-menu" id="langMenu">
                            <div class="lang-option active" onclick="setLanguage('ru')">🇷🇺 Русский</div>
                            <div class="lang-option" onclick="setLanguage('en')">🇬🇧 English</div>
                            <div class="lang-option" onclick="setLanguage('de')">🇩🇪 Deutsch</div>
                            <div class="lang-option" onclick="setLanguage('es')">🇪🇸 Español</div>
                        </div>
                    </div>
                    <button class="control-btn" onclick="toggleTheme()" id="themeBtn">🌙 <span data-i18n="theme">Тема</span></button>
                    <button class="control-btn premium" onclick="openSubscriptionModal()" id="premiumBtn">
                        ⭐ <span data-i18n="premium">Подписка</span>
                    </button>
                    <button class="control-btn" onclick="toggleAuthModal()" id="authBtn">👤 <span data-i18n="login">Войти</span></button>
                </div>
            </div>
        </div>
    </header>
    
    <div class="search-bar" id="searchBar">
        <div class="container" style="padding: 0;">
            <input type="text" id="searchInput" placeholder="Поиск по новостям..." oninput="performSearch()">
        </div>
    </div>
    
    <div class="container">
        <div class="premium-banner" id="premiumBanner">
            <div>
                <h3>⭐ Откройте все 200 статей</h3>
                <p>Подписка за 149 ₽/мес — доступ к полной ленте новостей</p>
            </div>
            <button onclick="openSubscriptionModal()">Оформить подписку</button>
        </div>
        
        <div class="filter-bar">
            <button class="filter-btn active" onclick="filterPosts('all', this)" data-i18n="all">Все</button>
            <button class="filter-btn" onclick="filterPosts('favorites', this)" data-i18n="filterFav">⭐ Избранные</button>
            <button class="filter-btn" onclick="filterPosts('unread', this)" data-i18n="filterUnread">📬 Непрочитанные</button>
            <button class="filter-btn" onclick="filterPosts('read', this)" data-i18n="filterRead">✅ Прочитанные</button>
        </div>
        
        <div class="news-grid" id="newsGrid">
'''

    for post in posts:
        text_lines = post['text'].split('\n')
        raw_title = text_lines[0] if text_lines else ''
        title = clean_title(raw_title)
        
        preview_text = ''
        for line in text_lines[1:]:
            clean_line = clean_text(line)
            if clean_line:
                if preview_text:
                    preview_text += ' ' + clean_line                else:
                    preview_text = clean_line
                if len(preview_text) > 200:
                    break
        
        if len(preview_text) < 20 and len(text_lines) > 1:
            preview_text = clean_text(text_lines[1])[:200]
        
        if not preview_text:
            preview_text = clean_text(post['text'])[:200]
        
        if len(preview_text) > 200:
            preview_text = preview_text[:200] + '...'
        
        date_obj = datetime.fromisoformat(post['date'])
        date_str = date_obj.strftime('%d.%m.%Y %H:%M')
        
        if post.get('image_url'):
            img_html = f'<img src="{post["image_url"]}" alt="News image" loading="lazy">'
        else:
            img_html = '<div class="no-image">📄</div>'
        
        title_for_search = json.dumps(title.lower(), ensure_ascii=False)
        text_for_search = json.dumps(preview_text.lower(), ensure_ascii=False)
        
        html_output += f'''
            <div class="news-card" data-post-id="{post["id"]}" data-title={title_for_search} data-text={text_for_search}>
                <div class="card-actions">
                    <button class="action-btn favorite" onclick="event.preventDefault(); event.stopPropagation(); toggleFavorite({post["id"]}, this)" title="В избранное">⭐</button>
                    <button class="action-btn read-toggle" onclick="event.preventDefault(); event.stopPropagation(); toggleRead({post["id"]}, this)" title="Отметить прочитанным">👁️</button>
                </div>
                <a href="/Novikon-site/posts/post_{post["id"]}.html" style="text-decoration: none; color: inherit;" onclick="markAsRead({post["id"]})">
                    {img_html}
                    <div class="news-content">
                        <div class="news-date">{date_str}</div>
                        <div class="news-title">{html_module.escape(title)}</div>
                        <div class="news-text">{html_module.escape(preview_text)}</div>
                        <span class="read-more" data-i18n="readMore">Читать далее →</span>
                    </div>
                </a>
            </div>
'''

    html_output += f'''
        </div>
        <div class="no-results" id="noResults" style="display:none;">
            <p data-i18n="noResults">😔 Ничего не найдено</p>
        </div>
    </div>
    
    <!-- Заблокированные статьи для подписчиков -->
    <div class="container" id="lockedSection" style="display:none;">
        <div class="news-grid" id="lockedGrid"></div>
    </div>
    
    <div class="footer">
        <div class="container">
            <p>© 2026 Новикон</p>
        </div>
    </div>
    
    <div class="toast-container" id="toastContainer"></div>
    
    <!-- Модальное окно авторизации -->
    <div class="modal" id="authModal">
        <div class="modal-content">
            <button class="modal-close" onclick="toggleAuthModal()">&times;</button>
            <h2 id="authTitle">Вход</h2>
            <form id="authForm" onsubmit="handleAuth(event)">
                <input type="email" id="authEmail" placeholder="Email" required autocomplete="email">
                <input type="password" id="authPassword" placeholder="Пароль" required autocomplete="current-password" minlength="6">
                <button type="submit" id="authSubmitBtn">Войти</button>
            </form>
            <p class="switch-mode">
                <a href="#" onclick="toggleAuthMode(event)">
                    <span id="authSwitchText">Нет аккаунта? Зарегистрироваться</span>
                </a>
            </p>
        </div>
    </div>
    
    <!-- Модальное окно подписки -->
    <div class="modal" id="subscriptionModal">
        <div class="modal-content">
            <button class="modal-close" onclick="closeSubscriptionModal()">&times;</button>
            <h2>⭐ Подписка Новикон</h2>
            <p style="text-align:center; color:#888; margin: 15px 0;">
                Получите доступ к 200 статьям вместо 42
            </p>
            <div class="plans">
                <div class="plan" onclick="subscribe('monthly')">
                    <h3>Месяц</h3>
                    <div class="price">149 ₽</div>
                    <p>в месяц</p>
                </div>
                <div class="plan recommended" onclick="subscribe('yearly')">
                    <h3>Год</h3>
                    <div class="price">1 490 ₽</div>
                    <p>скидка 17%</p>
                </div>
            </div>
            <p style="text-align:center; color:#888; font-size:12px; margin-top:15px;">
                Оплата через ЮKassa. Отмена в любой момент.
            </p>
        </div>
    </div>
    
    <script>
        // ============ КОНФИГУРАЦИЯ ============
        const API_URL = '{api_url}';
        const TOTAL_ARTICLES = {total_posts};
        const FREE_LIMIT = 42;
        
        // ============ ДАННЫЕ ============
        const postsData = ''' + posts_json + ''';
        
        // ============ ПЕРЕВОДЫ ============
        const translations = {{
            ru: {{
                subtitle: 'Актуальные новости и события',
                search: 'Поиск',
                favorites: 'Избранное',
                unread: 'Новые',
                theme: 'Тема',
                premium: 'Подписка',
                login: 'Войти',
                all: 'Все',
                filterFav: '⭐ Избранные',
                filterUnread: '📬 Непрочитанные',
                filterRead: '✅ Прочитанные',
                searchPlaceholder: 'Поиск по новостям...',
                readMore: 'Читать далее →',
                noResults: '😔 Ничего не найдено',
                addedToFav: 'Добавлено в избранное',
                removedFromFav: 'Удалено из избранного',
                newArticles: 'новых статей',
                premiumTitle: '⭐ Подписка Новикон',
                premiumText: 'Откройте все 200 статей'
            }},
            en: {{
                subtitle: 'Latest news and events',
                search: 'Search',
                favorites: 'Favorites',
                unread: 'New',
                theme: 'Theme',
                premium: 'Premium',
                login: 'Login',
                all: 'All',
                filterFav: '⭐ Favorites',
                filterUnread: '📬 Unread',
                filterRead: '✅ Read',
                searchPlaceholder: 'Search news...',
                readMore: 'Read more →',
                noResults: '😔 Nothing found',
                addedToFav: 'Added to favorites',
                removedFromFav: 'Removed from favorites',
                newArticles: 'new articles',
                premiumTitle: '⭐ Novikon Premium',
                premiumText: 'Unlock all 200 articles'
            }},
            de: {{
                subtitle: 'Aktuelle Nachrichten und Ereignisse',
                search: 'Suche',
                favorites: 'Favoriten',
                unread: 'Neu',
                theme: 'Thema',
                premium: 'Premium',
                login: 'Anmelden',
                all: 'Alle',
                filterFav: '⭐ Favoriten',
                filterUnread: '📬 Ungelesen',
                filterRead: '✅ Gelesen',
                searchPlaceholder: 'Nachrichten durchsuchen...',
                readMore: 'Weiterlesen →',
                noResults: '😔 Nichts gefunden',
                addedToFav: 'Zu Favoriten hinzugefügt',
                removedFromFav: 'Aus Favoriten entfernt',
                newArticles: 'neue Artikel',
                premiumTitle: '⭐ Novikon Premium',
                premiumText: 'Alle 200 Artikel freischalten'
            }},
            es: {{
                subtitle: 'Últimas noticias y eventos',
                search: 'Buscar',
                favorites: 'Favoritos',
                unread: 'Nuevo',
                theme: 'Tema',
                premium: 'Premium',
                login: 'Entrar',
                all: 'Todos',
                filterFav: '⭐ Favoritos',
                filterUnread: '📬 No leídos',
                filterRead: '✅ Leídos',
                searchPlaceholder: 'Buscar noticias...',
                readMore: 'Leer más →',
                noResults: '😔 Nada encontrado',
                addedToFav: 'Añadido a favoritos',
                removedFromFav: 'Eliminado de favoritos',
                newArticles: 'nuevos artículos',
                premiumTitle: '⭐ Novikon Premium',
                premiumText: 'Desbloquea los 200 artículos'
            }}
        }};
        
        let currentLang = localStorage.getItem('lang') || 'ru';
        let currentFilter = 'all';
        let currentUser = null;
        let authMode = 'login';
        let originalTexts = new Map();
        let allPosts = [...postsData]; // локальные 42 + подгруженные
        
        // ============ API ============
        async function apiRequest(endpoint, options = {{}}) {{
            const token = localStorage.getItem('token');
            const headers = {{
                'Content-Type': 'application/json',
                ...(options.headers || {{}})
            }};
            if (token) {{
                headers['Authorization'] = 'Bearer ' + token;
            }}
            
            const response = await fetch(API_URL + endpoint, {{
                ...options,
                headers
            }});
            
            if (!response.ok) {{
                const error = await response.json().catch(() => ({{ detail: 'Ошибка сервера' }}));
                throw new Error(error.detail || 'Ошибка');
            }}
            
            return response.json();
        }}
        
        // ============ АВТОРИЗАЦИЯ ============
        function toggleAuthModal() {{
            const modal = document.getElementById('authModal');
            modal.classList.toggle('active');
        }}
        
        function toggleAuthMode(e) {{
            e.preventDefault();
            authMode = authMode === 'login' ? 'register' : 'login';
            document.getElementById('authTitle').textContent = authMode === 'login' ? 'Вход' : 'Регистрация';
            document.getElementById('authSubmitBtn').textContent = authMode === 'login' ? 'Войти' : 'Зарегистрироваться';
            document.getElementById('authSwitchText').textContent = authMode === 'login' 
                ? 'Нет аккаунта? Зарегистрироваться' 
                : 'Уже есть аккаунт? Войти';
            document.getElementById('authPassword').autocomplete = authMode === 'login' ? 'current-password' : 'new-password';
        }}
        
        async function handleAuth(e) {{
            e.preventDefault();
            const email = document.getElementById('authEmail').value.trim();
            const password = document.getElementById('authPassword').value;
            const submitBtn = document.getElementById('authSubmitBtn');
            
            submitBtn.disabled = true;
            submitBtn.textContent = 'Подождите...';
            
            try {{
                const data = await apiRequest('/api/auth/' + authMode, {{
                    method: 'POST',
                    body: JSON.stringify({{ email, password }})
                }});
                
                localStorage.setItem('token', data.access_token);
                currentUser = data.user;
                
                toggleAuthModal();
                updateAuthUI();
                showToast('✅', 'Добро пожаловать, ' + data.user.email + '!', 'success');
                
                // Если подписчик - показываем все статьи
                if (data.user.is_subscriber) {{
                    await loadAllArticles();
                }} else {{
                    showLockedArticles();
                }}
                
            }} catch (error) {{
                showToast('❌', error.message, 'error');
            }} finally {{
                submitBtn.disabled = false;
                submitBtn.textContent = authMode === 'login' ? 'Войти' : 'Зарегистрироваться';
            }}
        }}
        
        function updateAuthUI() {{
            const authBtn = document.getElementById('authBtn');
            const t = translations[currentLang];
            
            if (currentUser) {{
                const initial = currentUser.email.charAt(0).toUpperCase();
                const status = currentUser.is_subscriber ? '⭐ Premium' : 'Free';
                authBtn.innerHTML = `<span class="user-avatar">${{initial}}</span> <span>${{currentUser.email.split('@')[0]}}</span> <span class="user-status">${{status}}</span>`;
                authBtn.onclick = () => logout();
                authBtn.title = 'Выйти';
                
                if (currentUser.is_subscriber) {{
                    document.getElementById('premiumBanner').classList.remove('show');
                    document.getElementById('premiumBtn').style.display = 'none';
                }} else {{
                    document.getElementById('premiumBanner').classList.add('show');
                }}
            }} else {{
                authBtn.innerHTML = '👤 <span>' + t.login + '</span>';
                authBtn.onclick = () => toggleAuthModal();
                document.getElementById('premiumBanner').classList.add('show');
                document.getElementById('premiumBtn').style.display = 'block';
            }}
        }}
        
        function logout() {{
            if (confirm('Выйти из аккаунта?')) {{
                localStorage.removeItem('token');
                currentUser = null;
                updateAuthUI();
                showToast('👋', 'Вы вышли из аккаунта');
                location.reload();
            }}
        }}
        
        async function loadUserData() {{
            const token = localStorage.getItem('token');
            if (!token) {{
                showLockedArticles();
                return;
            }}
            
            try {{
                currentUser = await apiRequest('/api/auth/me');
                updateAuthUI();
                
                if (currentUser.is_subscriber) {{
                    await loadAllArticles();
                }} else {{
                    showLockedArticles();
                }}
            }} catch (e) {{
                localStorage.removeItem('token');
                showLockedArticles();
            }}
        }}
        
        // ============ ПОДПИСКА ============
        function openSubscriptionModal() {{
            if (!currentUser) {{
                showToast('⚠️', 'Сначала войдите в аккаунт');
                toggleAuthModal();
                return;
            }}
            
            if (currentUser.is_subscriber) {{
                showToast('⭐', 'У вас уже есть подписка!');
                return;
            }}
            
            document.getElementById('subscriptionModal').classList.add('active');
        }}
        
        function closeSubscriptionModal() {{
            document.getElementById('subscriptionModal').classList.remove('active');
        }}
        
        async function subscribe(plan) {{
            try {{
                const data = await apiRequest('/api/payments/create', {{
                    method: 'POST',
                    body: JSON.stringify({{ plan }})
                }});
                
                // Перенаправляем на оплату
                window.location.href = data.confirmation_url;
                
            }} catch (error) {{
                showToast('❌', error.message, 'error');
            }}
        }}
        
        async function checkPaymentReturn() {{
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('payment') === 'success') {{
                // Тестовое подтверждение (в продакшене убираем)
                try {{
                    const plan = urlParams.get('plan') || 'monthly';
                    await apiRequest('/api/payments/confirm-test?plan=' + plan, {{ method: 'POST' }});
                    showToast('✅', 'Оплата успешна! Подписка активирована.', 'success');
                    await loadUserData();
                }} catch (e) {{
                    showToast('⚠️', 'Не удалось активировать подписку');
                }}
                window.history.replaceState({{}}, '', window.location.pathname);
            }}
        }}
        
        // ============ ЗАГРУЗКА СТАТЕЙ ДЛЯ ПОДПИСЧИКОВ ============
        async function loadAllArticles() {{
            try {{
                const data = await apiRequest('/api/articles?limit=200');
                allPosts = data.articles;
                
                // Добавляем недостающие статьи
                const existingIds = new Set(postsData.map(p => p.id));
                const missingPosts = allPosts.filter(p => !existingIds.has(p.id));
                
                if (missingPosts.length > 0) {{
                    addArticlesToGrid(missingPosts);
                }}
                
                document.getElementById('lockedSection').style.display = 'none';
                showToast('⭐', 'Открыт доступ ко всем 200 статьям!', 'success');
                
            }} catch (e) {{
                console.error('Ошибка загрузки статей:', e);
                showLockedArticles();
            }}
        }}
        
        function addArticlesToGrid(posts) {{
            const grid = document.getElementById('newsGrid');
            
            posts.forEach((post, index) => {{
                const textLines = post.text.split('\\n');
                const title = textLines[0] ? textLines[0].replace(/\\*\\*/g, '').trim() : '';
                
                let preview = '';
                for (let i = 1; i < textLines.length; i++) {{
                    const line = textLines[i].replace(/\\*\\*/g, '').trim();
                    if (line) {{
                        preview += (preview ? ' ' : '') + line;
                        if (preview.length > 200) break;
                    }}
                }}
                if (preview.length > 200) preview = preview.substring(0, 200) + '...';
                
                const date = new Date(post.date);
                const dateStr = date.toLocaleDateString('ru-RU', {{ day: '2-digit', month: '2-digit', year: 'numeric' }}) + ' ' + 
                                date.toLocaleTimeString('ru-RU', {{ hour: '2-digit', minute: '2-digit' }});
                
                const imgHtml = post.image_url 
                    ? `<img src="${{post.image_url}}" alt="News image" loading="lazy">`
                    : '<div class="no-image">📄</div>';
                
                const card = document.createElement('div');
                card.className = 'news-card';
                card.setAttribute('data-post-id', post.id);
                card.setAttribute('data-title', title.toLowerCase());
                card.setAttribute('data-text', preview.toLowerCase());
                card.style.animationDelay = (index * 0.05) + 's';
                
                card.innerHTML = `
                    <div class="card-actions">
                        <button class="action-btn favorite" onclick="event.preventDefault(); event.stopPropagation(); toggleFavorite(${{post.id}}, this)" title="В избранное">⭐</button>
                        <button class="action-btn read-toggle" onclick="event.preventDefault(); event.stopPropagation(); toggleRead(${{post.id}}, this)" title="Отметить прочитанным">👁️</button>
                    </div>
                    <a href="/Novikon-site/posts/post_${{post.id}}.html" style="text-decoration: none; color: inherit;" onclick="markAsRead(${{post.id}})">
                        ${{imgHtml}}
                        <div class="news-content">
                            <div class="news-date">${{dateStr}}</div>
                            <div class="news-title">${{escapeHtml(title)}}</div>
                            <div class="news-text">${{escapeHtml(preview)}}</div>
                            <span class="read-more">Читать далее →</span>
                        </div>
                    </a>
                `;
                
                grid.appendChild(card);
            }});
            
            // Обновляем избранное и прочитанные
            updateAllCardsState();
        }}
        
        // ============ ЗАБЛОКИРОВАННЫЕ СТАТЬИ ============
        async function showLockedArticles() {{
            // Показываем 3-5 заблокированных карточек как превью
            const lockedGrid = document.getElementById('lockedGrid');
            const lockedSection = document.getElementById('lockedSection');
            
            lockedGrid.innerHTML = '';
            
            // Создаём 3 заглушки для демонстрации
            for (let i = 0; i < 3; i++) {{
                const card = document.createElement('div');
                card.className = 'news-card locked';
                card.innerHTML = `
                    <div class="no-image">🔒</div>
                    <div class="lock-content">
                        <div class="lock-icon">🔒</div>
                        <h3>Статья доступна по подписке</h3>
                        <p>Оформите подписку за 149 ₽/мес</p>
                        <button onclick="openSubscriptionModal()">Открыть</button>
                    </div>
                `;
                lockedGrid.appendChild(card);
            }}
            
            lockedSection.style.display = 'block';
        }}
        
        // ============ ВСПОМОГАТЕЛЬНЫЕ ============
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}
        
        function updateAllCardsState() {{
            const favorites = getFavorites();
            const readPosts = getReadPosts();
            
            document.querySelectorAll('.news-card').forEach(card => {{
                const postId = parseInt(card.getAttribute('data-post-id'));
                const favBtn = card.querySelector('.favorite');
                if (favorites.includes(postId) && favBtn) favBtn.classList.add('active');
            }});
            
            updateFavBadge();
            updateUnreadBadge();
        }}
        
        // ============ ПЕРЕВОД СТАТЕЙ ============
        async function translateText(text, targetLang) {{
            if (targetLang === 'ru') return text;
            if (!text || text.trim().length === 0) return text;
            
            try {{
                const url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=ru&tl=' + targetLang + '&dt=t&q=' + encodeURIComponent(text.substring(0, 1500));
                const response = await fetch(url);
                const data = await response.json();
                
                if (data && data[0]) {{
                    return data[0].map(item => item[0]).join('');
                }}
                return text;
            }} catch (e) {{
                return text;
            }}
        }}
        
        async function translateAllPosts(targetLang) {{
            const cards = document.querySelectorAll('.news-card:not(.locked)');
            showToast('🌐', 'Перевод статей...');
            
            for (const card of cards) {{
                const titleEl = card.querySelector('.news-title');
                const textEl = card.querySelector('.news-text');
                
                if (!titleEl || !textEl) continue;
                
                if (!originalTexts.has(card)) {{
                    originalTexts.set(card, {{
                        title: titleEl.textContent,
                        text: textEl.textContent
                    }});
                }}
                
                const original = originalTexts.get(card);
                
                if (targetLang === 'ru') {{
                    titleEl.textContent = original.title;
                    textEl.textContent = original.text;
                }} else {{
                    const [translatedTitle, translatedText] = await Promise.all([
                        translateText(original.title, targetLang),
                        translateText(original.text, targetLang)
                    ]);
                    titleEl.textContent = translatedTitle;
                    textEl.textContent = translatedText;
                    card.setAttribute('data-title', translatedTitle.toLowerCase());
                    card.setAttribute('data-text', translatedText.toLowerCase());
                }}
                
                await new Promise(r => setTimeout(r, 100));
            }}
            
            showToast('✅', 'Перевод завершён!', 'success');
        }}
        
        // ============ ТЕМА ============
        function toggleTheme() {{
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeButton(newTheme);
        }}
        
        function updateThemeButton(theme) {{
            const btn = document.getElementById('themeBtn');
            const t = translations[currentLang];
            btn.innerHTML = theme === 'dark' ? '☀️ <span>' + t.theme + '</span>' : '🌙 <span>' + t.theme + '</span>';
        }}
        
        // ============ ЯЗЫК ============
        function toggleLangMenu() {{
            document.getElementById('langMenu').classList.toggle('active');
        }}
        
        async function setLanguage(lang) {{
            currentLang = lang;
            localStorage.setItem('lang', lang);
            
            document.querySelectorAll('.lang-option').forEach(el => el.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('currentLang').textContent = lang.toUpperCase();
            
            document.querySelectorAll('[data-i18n]').forEach(el => {{
                const key = el.getAttribute('data-i18n');
                if (translations[lang][key]) el.textContent = translations[lang][key];
            }});
            
            document.getElementById('searchInput').placeholder = translations[lang].searchPlaceholder;
            updateThemeButton(document.documentElement.getAttribute('data-theme') || 'light');
            updateAuthUI();
            document.getElementById('langMenu').classList.remove('active');
            
            await translateAllPosts(lang);
        }}
        
        // ============ ИЗБРАННОЕ ============
        function getFavorites() {{
            return JSON.parse(localStorage.getItem('favorites') || '[]');
        }}
        
        function toggleFavorite(postId, btn) {{
            let favorites = getFavorites();
            const index = favorites.indexOf(postId);
            
            if (index > -1) {{
                favorites.splice(index, 1);
                if (btn) btn.classList.remove('active');
                showToast('💔', translations[currentLang].removedFromFav);
            }} else {{
                favorites.push(postId);
                if (btn) btn.classList.add('active');
                showToast('⭐', translations[currentLang].addedToFav, 'favorite');
            }}
            
            localStorage.setItem('favorites', JSON.stringify(favorites));
            updateFavBadge();
            if (currentFilter === 'favorites') filterPosts('favorites');
        }}
        
        function updateFavBadge() {{
            const favorites = getFavorites();
            const badge = document.getElementById('favBadge');
            if (favorites.length > 0) {{
                badge.textContent = favorites.length;
                badge.style.display = 'flex';
            }} else {{
                badge.style.display = 'none';
            }}
        }}
        
        function toggleFavorites() {{
            const btn = document.getElementById('favBtn');
            btn.classList.toggle('active');
            filterPosts(btn.classList.contains('active') ? 'favorites' : 'all');
        }}
        
        // ============ ПРОЧИТАННЫЕ ============
        function getReadPosts() {{
            return JSON.parse(localStorage.getItem('readPosts') || '[]');
        }}
        
        function markAsRead(postId) {{
            let readPosts = getReadPosts();
            if (!readPosts.includes(postId)) {{
                readPosts.push(postId);
                localStorage.setItem('readPosts', JSON.stringify(readPosts));
                updateUnreadBadge();
            }}
        }}
        
        function toggleRead(postId, btn) {{
            let readPosts = getReadPosts();
            const index = readPosts.indexOf(postId);
            
            if (index > -1) {{
                readPosts.splice(index, 1);
                showToast('📬', 'Отмечено как непрочитанное');
            }} else {{
                readPosts.push(postId);
                showToast('✅', 'Отмечено как прочитанное');
            }}
            
            localStorage.setItem('readPosts', JSON.stringify(readPosts));
            updateUnreadBadge();
            if (currentFilter === 'unread' || currentFilter === 'read') filterPosts(currentFilter);
        }}
        
        function updateUnreadBadge() {{
            const readPosts = getReadPosts();
            const unreadCount = allPosts.length - readPosts.length;
            const badge = document.getElementById('unreadBadge');
            
            if (unreadCount > 0) {{
                badge.textContent = unreadCount;
                badge.style.display = 'flex';
                badge.classList.add('pulse');
                setTimeout(() => badge.classList.remove('pulse'), 2000);
            }} else {{
                badge.style.display = 'none';
            }}
        }}
        
        // ============ ПОИСК ============
        function toggleSearch() {{
            const searchBar = document.getElementById('searchBar');
            searchBar.classList.toggle('active');
            
            if (searchBar.classList.contains('active')) {{
                setTimeout(() => document.getElementById('searchInput').focus(), 100);
            }} else {{
                document.getElementById('searchInput').value = '';
                performSearch();
            }}
        }}
        
        function performSearch() {{
            const query = document.getElementById('searchInput').value.toLowerCase().trim();
            const cards = document.querySelectorAll('.news-card:not(.locked)');
            let visibleCount = 0;
            
            cards.forEach(card => {{
                const title = card.getAttribute('data-title') || '';
                const text = card.getAttribute('data-text') || '';
                
                if (!query || title.includes(query) || text.includes(query)) {{
                    card.style.display = '';
                    visibleCount++;
                }} else {{
                    card.style.display = 'none';
                }}
            }});
            
            document.getElementById('noResults').style.display = visibleCount === 0 ? 'block' : 'none';
        }}
        
        // ============ ФИЛЬТРЫ ============
        function filterPosts(filter, btn) {{
            currentFilter = filter;
            
            if (btn) {{
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            }}
            
            const favorites = getFavorites();
            const readPosts = getReadPosts();
            const cards = document.querySelectorAll('.news-card:not(.locked)');
            let visibleCount = 0;
            
            cards.forEach(card => {{
                const postId = parseInt(card.getAttribute('data-post-id'));
                let show = true;
                
                if (filter === 'favorites') show = favorites.includes(postId);
                else if (filter === 'unread') show = !readPosts.includes(postId);
                else if (filter === 'read') show = readPosts.includes(postId);
                
                card.style.display = show ? '' : 'none';
                if (show) visibleCount++;
            }});
            
            document.getElementById('noResults').style.display = visibleCount === 0 ? 'block' : 'none';
            
            const favBtn = document.getElementById('favBtn');
            favBtn.classList.toggle('active', filter === 'favorites');
        }}
        
        // ============ УВЕДОМЛЕНИЯ ============
        function showToast(icon, message, type = '') {{
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = 'toast ' + type;
            toast.innerHTML = `<div class="toast-icon">${{icon}}</div><div class="toast-content">${{message}}</div>`;
            container.appendChild(toast);
            
            setTimeout(() => {{
                toast.style.animation = 'slideInRight 0.4s ease reverse';
                setTimeout(() => toast.remove(), 400);
            }}, 3000);
        }}
        
        // ============ ПРОГРЕСС-БАР ============
        window.addEventListener('scroll', () => {{
            const scrollTop = window.pageYOffset;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            const scrollPercent = (scrollTop / docHeight) * 100;
            document.getElementById('progressBar').style.width = scrollPercent + '%';
        }});
        
        // ============ ЗАГРУЗКА ============
        document.addEventListener('DOMContentLoaded', async function() {{
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-theme', savedTheme);
            updateThemeButton(savedTheme);
            
            document.getElementById('currentLang').textContent = currentLang.toUpperCase();
            document.querySelectorAll('.lang-option').forEach(el => {{
                el.classList.remove('active');
                if (el.textContent.includes(currentLang === 'ru' ? 'Русский' : currentLang === 'en' ? 'English' : currentLang === 'de' ? 'Deutsch' : 'Español')) {{
                    el.classList.add('active');
                }}
            }});
            
            document.querySelectorAll('[data-i18n]').forEach(el => {{
                const key = el.getAttribute('data-i18n');
                if (translations[currentLang][key]) el.textContent = translations[currentLang][key];
            }});
            document.getElementById('searchInput').placeholder = translations[currentLang].searchPlaceholder;
            
            // Инициализация избранного
            const favorites = getFavorites();
            document.querySelectorAll('.news-card').forEach(card => {{
                const postId = parseInt(card.getAttribute('data-post-id'));
                const favBtn = card.querySelector('.favorite');
                if (favorites.includes(postId) && favBtn) favBtn.classList.add('active');
            }});
            updateFavBadge();
            updateUnreadBadge();
            
            // Анимация
            document.querySelectorAll('.news-card').forEach((card, index) => {{
                card.style.animationDelay = (index * 0.05) + 's';
            }});
            
            // Проверка платежа
            await checkPaymentReturn();
            
            // Загрузка данных пользователя
            await loadUserData();
            
            // Закрытие меню языка
            document.addEventListener('click', function(e) {{
                const langDropdown = document.querySelector('.lang-dropdown');
                if (langDropdown && !langDropdown.contains(e.target)) {{
                    document.getElementById('langMenu').classList.remove('active');
                }}
            }});
            
            // Перевод при загрузке
            if (currentLang !== 'ru') {{
                setTimeout(() => translateAllPosts(currentLang), 500);
            }}
        }});
    </script>
</body>
</html>
'''
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_output)
    print("🌐 Сгенерирован index.html с подпиской")

def generate_post_pages(posts, api_url):
    os.makedirs('posts', exist_ok=True)
    
    print(f"📝 Генерация {len(posts)} страниц постов...")
    
    for i, post in enumerate(posts):
        try:
            text_lines = post['text'].split('\n')
            raw_title = text_lines[0] if text_lines else ''
            title = clean_title(raw_title)
            
            date_obj = datetime.fromisoformat(post['date'])
            date_str = date_obj.strftime('%d.%m.%Y %H:%M')
            
            full_text_lines = []
            for line in text_lines[1:]:
                clean_line = clean_text(line)
                if clean_line:
                    full_text_lines.append(clean_line)
            
            full_text = '<br>'.join(full_text_lines) if full_text_lines else clean_text(post['text'])
            if not full_text:
                full_text = title
            
            if post.get('image_url'):
                img_html = f'<img src="../{post["image_url"]}" alt="News image" style="display: block; max-width: 100%; border-radius: 12px; margin: 20px auto;">'
            else:
                img_html = ''
            
            title_json = json.dumps(title, ensure_ascii=False)
            full_text_json = json.dumps(full_text, ensure_ascii=False)
            
            html_output = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html_module.escape(title)} - Новикон</title>
    <link rel="icon" href="../{LOGO_FILE}" type="image/png">
    <style>
        :root {{
            --bg: #f5f5f5;
            --text: #333;
            --card-bg: white;
            --header-bg: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --shadow: 0 4px 15px rgba(0,0,0,0.08);
            --border: #e0e0e0;
            --accent: #667eea;
            --favorite: #ffc107;
        }}
        [data-theme="dark"] {{
            --bg: #1a1a2e;
            --text: #e0e0e0;
            --card-bg: #16213e;
            --header-bg: linear-gradient(135deg, #0f3460 0%, #1a1a2e 100%);
            --shadow: 0 4px 15px rgba(0,0,0,0.3);
            --border: #2a2a4a;
            --accent: #7b8cde;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.8;
            transition: background 0.4s, color 0.4s;
        }}
        header {{
            background: var(--header-bg);
            color: white;
            padding: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: background 0.4s;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        .header-content {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .logo-link {{
            display: flex;
            align-items: center;
            gap: 12px;
            color: white;
            text-decoration: none;
        }}
        .logo-link img {{
            height: 40px;
            width: auto;
            border-radius: 6px;
        }}
        .logo-link .site-title {{
            font-size: 22px;
            font-weight: 700;
        }}
        .header-btns {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .control-btn {{
            background: rgba(255,255,255,0.2);
            border: 2px solid rgba(255,255,255,0.3);
            color: white;
            padding: 8px 14px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }}
        .control-btn:hover {{
            background: rgba(255,255,255,0.3);
            transform: scale(1.05);
        }}
        .control-btn.favorite.active {{
            background: var(--favorite);
            border-color: var(--favorite);
            color: white;
        }}
        .lang-dropdown {{
            position: relative;
            display: inline-block;
        }}
        .lang-menu {{
            display: none;
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 8px;
            background: var(--card-bg);
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            overflow: hidden;
            min-width: 150px;
            z-index: 200;
        }}
        .lang-menu.active {{ display: block; }}
        .lang-option {{
            padding: 12px 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            color: var(--text);
        }}
        .lang-option:hover {{ background: rgba(102, 126, 234, 0.1); }}
        .lang-option.active {{ background: rgba(102, 126, 234, 0.15); font-weight: 600; }}
        .post-content {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 40px;
            margin: 30px 0;
            box-shadow: var(--shadow);
            transition: background 0.4s;
            animation: fadeIn 0.5s ease;
        }}
        .post-date {{
            color: #888;
            font-size: 14px;
            margin-bottom: 15px;
        }}
        .post-title {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 20px;
            line-height: 1.3;
        }}
        .post-text {{
            font-size: 17px;
            line-height: 1.8;
        }}
        .post-text a {{ color: var(--accent); text-decoration: none; }}
        .post-text img {{
            display: block;
            max-width: 100%;
            border-radius: 12px;
            margin: 20px auto;
        }}
        .back-button {{
            display: inline-block;
            margin-top: 30px;
            padding: 12px 24px;
            background: var(--header-bg);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            transition: transform 0.3s;
        }}
        .back-button:hover {{ transform: scale(1.05); }}
        .footer {{
            text-align: center;
            padding: 30px 0;
            color: #888;
            font-size: 14px;
            border-top: 1px solid var(--border);
            margin-top: 20px;
            transition: border-color 0.4s;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .progress-bar {{
            position: fixed;
            top: 0;
            left: 0;
            height: 3px;
            background: var(--accent);
            width: 0%;
            z-index: 9999;
            transition: width 0.3s;
        }}
        
        .toast-container {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .toast {{
            background: var(--card-bg);
            color: var(--text);
            padding: 15px 20px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            border-left: 4px solid var(--accent);
            min-width: 280px;
            animation: slideInRight 0.4s ease;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .toast.favorite {{ border-left-color: var(--favorite); }}
        .toast-icon {{ font-size: 24px; }}
        .toast-content {{ flex: 1; font-size: 14px; }}
        
        @keyframes slideInRight {{
            from {{ opacity: 0; transform: translateX(100px); }}
            to {{ opacity: 1; transform: translateX(0); }}
        }}
        
        @media (max-width: 768px) {{
            .post-content {{ padding: 20px; }}
            .post-title {{ font-size: 22px; }}
            .header-content {{
                flex-direction: column;
                gap: 10px;
                text-align: center;
            }}
            .logo-link img {{ height: 32px; }}
            .logo-link .site-title {{ font-size: 18px; }}
        }}
    </style>
</head>
<body>
    <div class="progress-bar" id="progressBar"></div>
    
    <header>
        <div class="container">
            <div class="header-content">
                <a href="/Novikon-site/" class="logo-link">
                    <img src="../{LOGO_FILE}" alt="Новикон">
                    <span class="site-title">Новикон</span>
                </a>
                <div class="header-btns">
                    <button class="control-btn favorite" id="favBtn" onclick="toggleFavorite()" title="В избранное">⭐</button>
                    <div class="lang-dropdown">
                        <button class="control-btn" onclick="toggleLangMenu()" title="Язык">
                            🌐 <span id="currentLang">RU</span>
                        </button>
                        <div class="lang-menu" id="langMenu">
                            <div class="lang-option active" onclick="setLanguage('ru')">🇷🇺 Русский</div>
                            <div class="lang-option" onclick="setLanguage('en')">🇬🇧 English</div>
                            <div class="lang-option" onclick="setLanguage('de')">🇩🇪 Deutsch</div>
                            <div class="lang-option" onclick="setLanguage('es')">🇪🇸 Español</div>
                        </div>
                    </div>
                    <button class="control-btn" onclick="toggleTheme()" id="themeBtn">🌙</button>
                </div>
            </div>
        </div>
    </header>
    <div class="container">
        <div class="post-content">
            <div class="post-date">📅 {date_str}</div>
            <h1 class="post-title" id="postTitle">{html_module.escape(title)}</h1>
            {img_html}
            <div class="post-text" id="postText">{full_text}</div>
            <a href="/Novikon-site/" class="back-button" data-i18n="back">← На главную</a>
        </div>
    </div>
    <div class="footer">
        <div class="container">
            <p>© 2026 Новикон</p>
        </div>
    </div>
    
    <div class="toast-container" id="toastContainer"></div>
    
    <script>
        const POST_ID = {post["id"]};
        const ORIGINAL_TITLE = {title_json};
        const ORIGINAL_TEXT = {full_text_json};
        
        const translations = {{
            ru: {{ back: '← На главную', theme: 'Тема' }},
            en: {{ back: '← Back to home', theme: 'Theme' }},
            de: {{ back: '← Zurück zur Startseite', theme: 'Thema' }},
            es: {{ back: '← Volver al inicio', theme: 'Tema' }}
        }};
        
        let currentLang = localStorage.getItem('lang') || 'ru';
        
        async function translateText(text, targetLang) {{
            if (targetLang === 'ru') return text;
            if (!text || text.trim().length === 0) return text;
            
            try {{
                const url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=ru&tl=' + targetLang + '&dt=t&q=' + encodeURIComponent(text.substring(0, 4500));
                const response = await fetch(url);
                const data = await response.json();
                if (data && data[0]) return data[0].map(item => item[0]).join('');
                return text;
            }} catch (e) {{
                return text;
            }}
        }}
        
        async function translatePost(targetLang) {{
            const titleEl = document.getElementById('postTitle');
            const textEl = document.getElementById('postText');
            
            if (targetLang === 'ru') {{
                titleEl.textContent = ORIGINAL_TITLE;
                textEl.innerHTML = ORIGINAL_TEXT;
                return;
            }}
            
            showToast('🌐', 'Перевод статьи...');
            
            const translatedTitle = await translateText(ORIGINAL_TITLE, targetLang);
            titleEl.textContent = translatedTitle;
            
            const textParts = ORIGINAL_TEXT.split('<br>');
            const translatedParts = [];
            
            for (const part of textParts) {{
                if (part.trim()) {{
                    const translated = await translateText(part, targetLang);
                    translatedParts.push(translated);
                    await new Promise(r => setTimeout(r, 50));
                }} else {{
                    translatedParts.push(part);
                }}
            }}
            
            textEl.innerHTML = translatedParts.join('<br>');
            showToast('✅', 'Перевод завершён!');
        }}
        
        function toggleLangMenu() {{
            document.getElementById('langMenu').classList.toggle('active');
        }}
        
        async function setLanguage(lang) {{
            currentLang = lang;
            localStorage.setItem('lang', lang);
            document.querySelectorAll('.lang-option').forEach(el => el.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('currentLang').textContent = lang.toUpperCase();
            
            document.querySelectorAll('[data-i18n]').forEach(el => {{
                const key = el.getAttribute('data-i18n');
                if (translations[lang][key]) el.textContent = translations[lang][key];
            }});
            
            updateThemeBtn();
            document.getElementById('langMenu').classList.remove('active');
            await translatePost(lang);
        }}
        
        function toggleTheme() {{
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeBtn();
        }}
        
        function updateThemeBtn() {{
            document.getElementById('themeBtn').textContent = 
                document.documentElement.getAttribute('data-theme') === 'dark' ? '☀️' : '🌙';
        }}
        
        function getFavorites() {{
            return JSON.parse(localStorage.getItem('favorites') || '[]');
        }}
        
        function toggleFavorite() {{
            let favorites = getFavorites();
            const index = favorites.indexOf(POST_ID);
            const btn = document.getElementById('favBtn');
            
            if (index > -1) {{
                favorites.splice(index, 1);
                btn.classList.remove('active');
                showToast('💔', 'Удалено из избранного');
            }} else {{
                favorites.push(POST_ID);
                btn.classList.add('active');
                showToast('⭐', 'Добавлено в избранное', 'favorite');
            }}
            
            localStorage.setItem('favorites', JSON.stringify(favorites));
        }}
        
        function updateFavBtn() {{
            if (getFavorites().includes(POST_ID)) {{
                document.getElementById('favBtn').classList.add('active');
            }}
        }}
        
        function markAsRead() {{
            let readPosts = JSON.parse(localStorage.getItem('readPosts') || '[]');
            if (!readPosts.includes(POST_ID)) {{
                readPosts.push(POST_ID);
                localStorage.setItem('readPosts', JSON.stringify(readPosts));
            }}
        }}
        
        function showToast(icon, message, type = '') {{
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = 'toast ' + type;
            toast.innerHTML = `<div class="toast-icon">${{icon}}</div><div class="toast-content">${{message}}</div>`;
            container.appendChild(toast);
            setTimeout(() => {{
                toast.style.animation = 'slideInRight 0.4s ease reverse';
                setTimeout(() => toast.remove(), 400);
            }}, 3000);
        }}
        
        window.addEventListener('scroll', () => {{
            const scrollTop = window.pageYOffset;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            const scrollPercent = (scrollTop / docHeight) * 100;
            document.getElementById('progressBar').style.width = scrollPercent + '%';
        }});
        
        document.addEventListener('DOMContentLoaded', async function() {{
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-theme', savedTheme);
            updateThemeBtn();
            
            document.getElementById('currentLang').textContent = currentLang.toUpperCase();
            document.querySelectorAll('.lang-option').forEach(el => {{
                el.classList.remove('active');
                if (el.textContent.includes(currentLang === 'ru' ? 'Русский' : currentLang === 'en' ? 'English' : currentLang === 'de' ? 'Deutsch' : 'Español')) {{
                    el.classList.add('active');
                }}
            }});
            
            document.querySelectorAll('[data-i18n]').forEach(el => {{
                const key = el.getAttribute('data-i18n');
                if (translations[currentLang][key]) el.textContent = translations[currentLang][key];
            }});
            
            updateFavBtn();
            markAsRead();
            
            if (currentLang !== 'ru') {{
                setTimeout(() => translatePost(currentLang), 500);
            }}
            
            document.body.style.opacity = '0';
            document.body.style.transition = 'opacity 0.4s';
            setTimeout(() => {{ document.body.style.opacity = '1'; }}, 50);
            
            document.addEventListener('click', function(e) {{
                const langDropdown = document.querySelector('.lang-dropdown');
                if (langDropdown && !langDropdown.contains(e.target)) {{
                    document.getElementById('langMenu').classList.remove('active');
                }}
            }});
        }});
    </script>
</body>
</html>
'''
            
            with open(f'posts/post_{post["id"]}.html', 'w', encoding='utf-8') as f:
                f.write(html_output)
            
            if (i + 1) % 20 == 0:
                print(f"📄 Сгенерировано {i + 1} из {len(posts)} страниц")
                
        except Exception as e:
            print(f"❌ Ошибка при генерации страницы для поста {post['id']}: {e}")
            continue
    
    print(f"✅ Сгенерировано {len(posts)} отдельных страниц")

if __name__ == '__main__':
    asyncio.run(parse_channel())
