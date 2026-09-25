import os
import json
import asyncio
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import shutil
import html as html_module
import re

API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', '')

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
        limit = 200
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
            print(f"✅ Обработан пост #{count} (ID: {message.id})")
        
        print(f"📊 Всего обработано {len(posts)} постов")
        
        with open('posts.json', 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        print("💾 Сохранен posts.json")
        
        print("📝 Генерация HTML страниц...")
        generate_html(posts)
        generate_post_pages(posts)
        
        posts_files = os.listdir('posts')
        print(f"📁 В папке posts создано {len(posts_files)} файлов")
        
        await client.disconnect()
        print("✅ Парсинг завершен успешно!")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        await client.disconnect()


def generate_html(posts):
    posts_json = json.dumps(posts, ensure_ascii=False)
    
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
            --premium: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
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
            gap: 8px;
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
            font-family: inherit;
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
            padding: 20px;
        }
        .modal.active {
            display: flex;
        }
        .modal-content {
            background: var(--card-bg);
            border-radius: 16px;
            padding: 40px;
            max-width: 480px;
            width: 100%;
            max-height: 90vh;
            overflow-y: auto;
            position: relative;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .modal-close {
            position: absolute;
            top: 15px;
            right: 20px;
            font-size: 28px;
            cursor: pointer;
            color: #888;
            background: none;
            border: none;
            transition: color 0.3s;
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
        .modal-content button[type="submit"] {
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
        .modal-content button[type="submit"]:hover {
            transform: scale(1.02);
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
        .plan.best {
            border-color: #fda085;
            background: linear-gradient(135deg, rgba(246,211,101,0.1) 0%, rgba(253,160,133,0.1) 100%);
        }
        .plan.best::before {
            content: "ВЫГОДНО";
            position: absolute;
            top: -12px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--premium);
            color: white;
            font-size: 10px;
            font-weight: 700;
            padding: 3px 12px;
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
        .plan p {
            font-size: 13px;
            color: #888;
        }
        .premium-badge {
            position: absolute;
            top: 10px;
            left: 10px;
            background: var(--premium);
            color: white;
            font-size: 11px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 12px;
            z-index: 10;
            letter-spacing: 0.5px;
        }
        .search-bar {
            max-width: 1200px;
            margin: 20px auto 0;
            padding: 0 20px;
            display: none;
        }
        .search-bar.active {
            display: block;
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
            font-family: inherit;
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
            font-family: inherit;
        }
        .filter-btn:hover {
            border-color: var(--accent);
        }
        .filter-btn.active {
            background: var(--accent);
            color: white;
            border-color: var(--accent);
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
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .toast.favorite { border-left-color: var(--favorite); }
        .toast.premium { border-left-color: #fda085; }
        .toast-icon { font-size: 24px; }
        .toast-content { flex: 1; font-size: 14px; }
        .badge.pulse { animation: pulse 1s ease infinite; }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
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
        .lang-option:hover { background: rgba(102, 126, 234, 0.1); }
        .lang-option.active {
            background: rgba(102, 126, 234, 0.15);
            font-weight: 600;
        }
        .upgrade-banner {
            grid-column: 1 / -1;
            background: var(--premium);
            color: white;
            padding: 25px;
            border-radius: 16px;
            text-align: center;
            margin: 20px 0;
            box-shadow: 0 8px 25px rgba(253, 160, 133, 0.3);
        }
        .upgrade-banner h3 { font-size: 22px; margin-bottom: 10px; }
        .upgrade-banner p { margin-bottom: 15px; opacity: 0.95; }
        .upgrade-banner button {
            background: white;
            color: #fda085;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: transform 0.3s;
            font-family: inherit;
        }
        .upgrade-banner button:hover { transform: scale(1.05); }
        .payment-methods {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
            margin-bottom: 20px;
        }
        .payment-method {
            padding: 12px;
            border: 2px solid var(--border);
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            text-align: center;
            font-size: 13px;
        }
        .payment-method:hover { border-color: var(--accent); }
        .payment-method.active {
            border-color: var(--accent);
            background: rgba(102, 126, 234, 0.1);
        }
        .payment-method span {
            display: block;
            font-weight: 600;
            margin-bottom: 3px;
            color: var(--text);
        }
        .payment-method small { font-size: 11px; color: #888; }
        @media (max-width: 768px) {
            .news-grid { grid-template-columns: 1fr; padding: 15px 0; }
            .logo-container img { height: 40px; }
            .site-title { font-size: 22px; }
            .header-content {
                flex-direction: column;
                gap: 10px;
                text-align: center;
            }
            .header-controls { justify-content: center; }
            .control-btn { font-size: 13px; padding: 7px 12px; }
            .plans { grid-template-columns: 1fr; }
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
                    <button type="button" class="control-btn" id="searchBtn">
                        🔍 <span data-i18n="search">Поиск</span>
                    </button>
                    <button type="button" class="control-btn" id="favBtn">
                        ⭐ <span data-i18n="favorites">Избранное</span>
                        <span class="badge" id="favBadge" style="display:none">0</span>
                    </button>
                    <button type="button" class="control-btn" id="unreadBtn">
                        📬 <span data-i18n="unread">Новые</span>
                        <span class="badge" id="unreadBadge" style="display:none">0</span>
                    </button>
                    <div class="lang-dropdown">
                        <button type="button" class="control-btn" id="langBtn">
                            🌐 <span id="currentLang">RU</span>
                        </button>
                        <div class="lang-menu" id="langMenu">
                            <div class="lang-option active" data-lang="ru">🇷🇺 Русский</div>
                            <div class="lang-option" data-lang="en">🇬🇧 English</div>
                            <div class="lang-option" data-lang="de">🇩🇪 Deutsch</div>
                            <div class="lang-option" data-lang="es">🇪🇸 Español</div>
                        </div>
                    </div>
                    <button type="button" class="control-btn" id="themeBtn">🌙 <span data-i18n="theme">Тема</span></button>
                    <button type="button" class="control-btn" id="subBtn">⭐ <span id="subBtnText">Подписка</span></button>
                    <button type="button" class="control-btn" id="authBtn">👤 <span id="authBtnText">Войти</span></button>
                </div>
            </div>
        </div>
    </header>
    
    <div class="search-bar" id="searchBar">
        <div class="container" style="padding: 0;">
            <input type="text" id="searchInput" placeholder="Поиск по новостям...">
        </div>
    </div>
    
    <div class="container">
        <div class="filter-bar">
            <button type="button" class="filter-btn active" data-filter="all" data-i18n="all">Все</button>
            <button type="button" class="filter-btn" data-filter="favorites" data-i18n="filterFav">⭐ Избранные</button>
            <button type="button" class="filter-btn" data-filter="unread" data-i18n="filterUnread">📬 Непрочитанные</button>
            <button type="button" class="filter-btn" data-filter="read" data-i18n="filterRead">✅ Прочитанные</button>
        </div>
        
        <div class="news-grid" id="newsGrid">
'''

    visible_posts = posts[:42]
    
    for post in visible_posts:
        text_lines = post['text'].split('\n')
        raw_title = text_lines[0] if text_lines else ''
        title = clean_title(raw_title)
        
        preview_text = ''
        for line in text_lines[1:]:
            clean_line = clean_text(line)
            if clean_line:
                if preview_text:
                    preview_text += ' ' + clean_line
                else:
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
        
        title_for_search = html_module.escape(title.lower(), quote=True)
        text_for_search = html_module.escape(preview_text.lower(), quote=True)
        
        html_output += f'''
            <div class="news-card" data-post-id="{post["id"]}" data-title="{title_for_search}" data-text="{text_for_search}">
                <div class="card-actions">
                    <button type="button" class="action-btn favorite" data-fav-id="{post["id"]}" title="В избранное">⭐</button>
                    <button type="button" class="action-btn read-toggle" data-read-id="{post["id"]}" title="Отметить прочитанным">👁️</button>
                </div>
                <a href="/Novikon-site/posts/post_{post["id"]}.html" style="text-decoration: none; color: inherit;" data-read-link="{post["id"]}">
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

    hidden_posts = posts[42:200]
    
    html_output += '<div id="premiumArticles" style="display: contents;">'
    
    for post in hidden_posts:
        text_lines = post['text'].split('\n')
        raw_title = text_lines[0] if text_lines else ''
        title = clean_title(raw_title)
        
        preview_text = ''
        for line in text_lines[1:]:
            clean_line = clean_text(line)
            if clean_line:
                if preview_text:
                    preview_text += ' ' + clean_line
                else:
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
        
        title_for_search = html_module.escape(title.lower(), quote=True)
        text_for_search = html_module.escape(preview_text.lower(), quote=True)
        
        html_output += f'''
            <div class="news-card premium-only" style="display: none;" data-post-id="{post["id"]}" data-title="{title_for_search}" data-text="{text_for_search}">
                <div class="card-actions">
                    <button type="button" class="action-btn favorite" data-fav-id="{post["id"]}" title="В избранное">⭐</button>
                    <button type="button" class="action-btn read-toggle" data-read-id="{post["id"]}" title="Отметить прочитанным">👁️</button>
                </div>
                <a href="/Novikon-site/posts/post_{post["id"]}.html" style="text-decoration: none; color: inherit;" data-read-link="{post["id"]}">
                    <div class="premium-badge">⭐ PREMIUM</div>
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
    
    html_output += '</div>'
    
    if len(posts) > 42:
        html_output += f'''
        <div class="upgrade-banner" id="upgradeBanner">
            <h3>⭐ Откройте все {len(posts)} статей!</h3>
            <p>Вы видите только первые 42 статьи. Оформите подписку за 149 ₽/мес и получите доступ ко всем материалам.</p>
            <button type="button" id="upgradeBtn">Оформить подписку</button>
        </div>
        '''
    
    html_output += '''
        </div>
        <div class="no-results" id="noResults" style="display:none;">
            <p data-i18n="noResults">😔 Ничего не найдено</p>
        </div>
    </div>
    <div class="footer">
        <div class="container">
            <p>© 2026 Новикон</p>
        </div>
    </div>
    
    <div class="toast-container" id="toastContainer"></div>
    
    <div id="authModal" class="modal">
        <div class="modal-content">
            <button type="button" class="modal-close" id="authClose">&times;</button>
            <h2 id="authTitle">Вход</h2>
            <form id="authForm">
                <input type="email" id="authEmail" placeholder="Email" required autocomplete="email">
                <input type="password" id="authPassword" placeholder="Пароль" required autocomplete="current-password" minlength="6">
                <button type="submit" id="authSubmitBtn">Войти</button>
            </form>
            <p style="text-align:center; margin-top:15px; font-size:14px;">
                <a href="#" id="authSwitch" style="color: var(--accent); text-decoration: none;">
                    <span id="authSwitchText">Нет аккаунта? Зарегистрироваться</span>
                </a>
            </p>
        </div>
    </div>
    
    <div id="subscriptionModal" class="modal">
        <div class="modal-content">
            <button type="button" class="modal-close" id="subClose">&times;</button>
            <h2>⭐ Премиум подписка</h2>
            <p style="text-align:center; color:#888; margin: 10px 0 20px;">Доступ ко всем 200 статьям</p>
            
            <div style="margin-bottom: 20px;">
                <label style="font-size: 14px; color: #888; display: block; margin-bottom: 8px;">Способ оплаты:</label>
                <div class="payment-methods">
                    <div class="payment-method active" data-currency="USDT">
                        <span>💵 USDT</span>
                        <small>TRC20 / ERC20</small>
                    </div>
                    <div class="payment-method" data-currency="TON">
                        <span>💎 TON</span>
                        <small>Telegram</small>
                    </div>
                    <div class="payment-method" data-currency="BTC">
                        <span>₿ BTC</span>
                        <small>Bitcoin</small>
                    </div>
                    <div class="payment-method" data-currency="ETH">
                        <span>Ξ ETH</span>
                        <small>Ethereum</small>
                    </div>
                    <div class="payment-method" data-currency="RUB">
                        <span>💳 Карта/СБП</span>
                        <small>Рубли</small>
                    </div>
                </div>
            </div>
            
            <div class="plans">
                <div class="plan" data-plan="monthly">
                    <h3>Месяц</h3>
                    <div class="price">149 ₽</div>
                    <p>в месяц</p>
                </div>
                <div class="plan best" data-plan="yearly">
                    <h3>Год</h3>
                    <div class="price">1 490 ₽</div>
                    <p>экономия 290 ₽</p>
                </div>
            </div>
            <p style="text-align:center; margin-top:20px; font-size:12px; color:#888;">
                🔒 Безопасная оплата через Cryptomus
            </p>
        </div>
    </div>
    
    <script>
    (function() {
        'use strict';
        
        // ============ ПЕРЕВОДЫ ============
        var translations = {
            ru: { subtitle: 'Актуальные новости и события', search: 'Поиск', favorites: 'Избранное', unread: 'Новые', theme: 'Тема', all: 'Все', filterFav: '⭐ Избранные', filterUnread: '📬 Непрочитанные', filterRead: '✅ Прочитанные', searchPlaceholder: 'Поиск по новостям...', readMore: 'Читать далее →', noResults: '😔 Ничего не найдено', addedToFav: 'Добавлено в избранное', removedFromFav: 'Удалено из избранного', newArticles: 'новых статей', login: 'Войти', subscription: 'Подписка', logout: 'Выйти', premium: 'Премиум', welcome: 'Добро пожаловать', loggedOut: 'Вы вышли из аккаунта' },
            en: { subtitle: 'Latest news and events', search: 'Search', favorites: 'Favorites', unread: 'New', theme: 'Theme', all: 'All', filterFav: '⭐ Favorites', filterUnread: '📬 Unread', filterRead: '✅ Read', searchPlaceholder: 'Search news...', readMore: 'Read more →', noResults: '😔 Nothing found', addedToFav: 'Added to favorites', removedFromFav: 'Removed from favorites', newArticles: 'new articles', login: 'Login', subscription: 'Subscribe', logout: 'Logout', premium: 'Premium', welcome: 'Welcome', loggedOut: 'Logged out' },
            de: { subtitle: 'Aktuelle Nachrichten und Ereignisse', search: 'Suche', favorites: 'Favoriten', unread: 'Neu', theme: 'Thema', all: 'Alle', filterFav: '⭐ Favoriten', filterUnread: '📬 Ungelesen', filterRead: '✅ Gelesen', searchPlaceholder: 'Nachrichten durchsuchen...', readMore: 'Weiterlesen →', noResults: '😔 Nichts gefunden', addedToFav: 'Zu Favoriten hinzugefügt', removedFromFav: 'Aus Favoriten entfernt', newArticles: 'neue Artikel', login: 'Anmelden', subscription: 'Abonnieren', logout: 'Abmelden', premium: 'Premium', welcome: 'Willkommen', loggedOut: 'Abgemeldet' },
            es: { subtitle: 'Últimas noticias y eventos', search: 'Buscar', favorites: 'Favoritos', unread: 'Nuevo', theme: 'Tema', all: 'Todos', filterFav: '⭐ Favoritos', filterUnread: '📬 No leídos', filterRead: '✅ Leídos', searchPlaceholder: 'Buscar noticias...', readMore: 'Leer más →', noResults: '😔 Nada encontrado', addedToFav: 'Añadido a favoritos', removedFromFav: 'Eliminado de favoritos', newArticles: 'nuevos artículos', login: 'Iniciar sesión', subscription: 'Suscribirse', logout: 'Cerrar sesión', premium: 'Premium', welcome: 'Bienvenido', loggedOut: 'Sesión cerrada' }
        };
        
        // ============ СОСТОЯНИЕ ============
        var currentUser = null;
        var userProfile = null;
        var authMode = 'login';
        var currentLang = localStorage.getItem('lang') || 'ru';
        var currentFilter = 'all';
        var originalTexts = new Map();
        var supabaseClient = null;
        
        var postsData = ''' + posts_json + ''';
        
        // ============ ИНИЦИАЛИЗАЦИЯ SUPABASE ============
        var SUPABASE_URL = 'YOUR_SUPABASE_URL';
        var SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY';
        
        if (window.supabase && SUPABASE_URL !== 'YOUR_SUPABASE_URL') {
            supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        }
        
        // ============ УТИЛИТЫ ============
        function $(id) { return document.getElementById(id); }
        function $$(sel) { return document.querySelectorAll(sel); }
        
        function showToast(icon, message, type) {
            type = type || '';
            var container = $('toastContainer');
            if (!container) return;
            var toast = document.createElement('div');
            toast.className = 'toast ' + type;
            toast.innerHTML = '<div class="toast-icon">' + icon + '</div><div class="toast-content">' + message + '</div>';
            container.appendChild(toast);
            setTimeout(function() {
                toast.style.opacity = '0';
                setTimeout(function() { toast.remove(); }, 400);
            }, 3000);
        }
        
        // ============ ТЕМА ============
        function toggleTheme() {
            var html = document.documentElement;
            var currentTheme = html.getAttribute('data-theme');
            var newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeButton(newTheme);
        }
        
        function updateThemeButton(theme) {
            var btn = $('themeBtn');
            var t = translations[currentLang];
            if (btn) {
                btn.innerHTML = theme === 'dark' ? '☀️ <span>' + t.theme + '</span>' : '🌙 <span>' + t.theme + '</span>';
            }
        }
        
        // ============ ЯЗЫК ============
        function toggleLangMenu() {
            var menu = $('langMenu');
            if (menu) menu.classList.toggle('active');
        }
        
        function setLanguage(lang) {
            currentLang = lang;
            localStorage.setItem('lang', lang);
            
            $$('.lang-option').forEach(function(el) {
                el.classList.remove('active');
                if (el.getAttribute('data-lang') === lang) {
                    el.classList.add('active');
                }
            });
            
            var cl = $('currentLang');
            if (cl) cl.textContent = lang.toUpperCase();
            
            $$('[data-i18n]').forEach(function(el) {
                var key = el.getAttribute('data-i18n');
                if (translations[lang][key]) {
                    el.textContent = translations[lang][key];
                }
            });
            
            var si = $('searchInput');
            if (si) si.placeholder = translations[lang].searchPlaceholder;
            updateThemeButton(document.documentElement.getAttribute('data-theme') || 'light');
            updateAuthUI();
            
            var menu = $('langMenu');
            if (menu) menu.classList.remove('active');
            
            translateAllPosts(lang);
        }
        
        // ============ ПЕРЕВОД ============
        function translateText(text, targetLang) {
            if (targetLang === 'ru') return Promise.resolve(text);
            if (!text || text.trim().length === 0) return Promise.resolve(text);
            
            var url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=ru&tl=' + targetLang + '&dt=t&q=' + encodeURIComponent(text.substring(0, 1500));
            return fetch(url)
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data && data[0]) {
                        return data[0].map(function(item) { return item[0]; }).join('');
                    }
                    return text;
                })
                .catch(function() { return text; });
        }
        
        async function translateAllPosts(targetLang) {
            var cards = $$('.news-card');
            showToast('🌐', 'Перевод статей...');
            
            for (var i = 0; i < cards.length; i++) {
                var card = cards[i];
                var titleEl = card.querySelector('.news-title');
                var textEl = card.querySelector('.news-text');
                
                if (!titleEl || !textEl) continue;
                
                if (!originalTexts.has(card)) {
                    originalTexts.set(card, {
                        title: titleEl.textContent,
                        text: textEl.textContent
                    });
                }
                
                var original = originalTexts.get(card);
                
                if (targetLang === 'ru') {
                    titleEl.textContent = original.title;
                    textEl.textContent = original.text;
                } else {
                    var results = await Promise.all([
                        translateText(original.title, targetLang),
                        translateText(original.text, targetLang)
                    ]);
                    
                    titleEl.textContent = results[0];
                    textEl.textContent = results[1];
                    
                    card.setAttribute('data-title', results[0].toLowerCase());
                    card.setAttribute('data-text', results[1].toLowerCase());
                }
                
                await new Promise(function(r) { setTimeout(r, 100); });
            }
            
            showToast('✅', 'Перевод завершён!');
        }
        
        // ============ ИЗБРАННОЕ ============
        function getFavorites() {
            try { return JSON.parse(localStorage.getItem('favorites') || '[]'); }
            catch (e) { return []; }
        }
        
        function toggleFavorite(postId, btn) {
            var favorites = getFavorites();
            var index = favorites.indexOf(postId);
            
            if (index > -1) {
                favorites.splice(index, 1);
                if (btn) btn.classList.remove('active');
                showToast('💔', translations[currentLang].removedFromFav);
            } else {
                favorites.push(postId);
                if (btn) btn.classList.add('active');
                showToast('⭐', translations[currentLang].addedToFav, 'favorite');
            }
            
            localStorage.setItem('favorites', JSON.stringify(favorites));
            updateFavBadge();
            
            if (currentFilter === 'favorites') {
                filterPosts('favorites');
            }
        }
        
        function updateFavBadge() {
            var favorites = getFavorites();
            var badge = $('favBadge');
            if (!badge) return;
            if (favorites.length > 0) {
                badge.textContent = favorites.length;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }
        
        function toggleFavorites() {
            var btn = $('favBtn');
            if (!btn) return;
            btn.classList.toggle('active');
            
            if (btn.classList.contains('active')) {
                filterPosts('favorites');
            } else {
                filterPosts('all');
                var allBtn = document.querySelector('.filter-btn[data-filter="all"]');
                if (allBtn) {
                    $$('.filter-btn').forEach(function(b) { b.classList.remove('active'); });
                    allBtn.classList.add('active');
                }
            }
        }
        
        // ============ ПРОЧИТАННЫЕ ============
        function getReadPosts() {
            try { return JSON.parse(localStorage.getItem('readPosts') || '[]'); }
            catch (e) { return []; }
        }
        
        function markAsRead(postId) {
            var readPosts = getReadPosts();
            if (readPosts.indexOf(postId) === -1) {
                readPosts.push(postId);
                localStorage.setItem('readPosts', JSON.stringify(readPosts));
                updateUnreadBadge();
            }
        }
        
        function toggleRead(postId, btn) {
            var readPosts = getReadPosts();
            var index = readPosts.indexOf(postId);
            
            if (index > -1) {
                readPosts.splice(index, 1);
                showToast('📬', 'Отмечено как непрочитанное');
            } else {
                readPosts.push(postId);
                showToast('✅', 'Отмечено как прочитанное');
            }
            
            localStorage.setItem('readPosts', JSON.stringify(readPosts));
            updateUnreadBadge();
            
            if (currentFilter === 'unread' || currentFilter === 'read') {
                filterPosts(currentFilter);
            }
        }
        
        function updateUnreadBadge() {
            var readPosts = getReadPosts();
            var visibleCards = $$('.news-card:not([style*="display: none"])');
            var unreadCount = 0;
            
            visibleCards.forEach(function(card) {
                var id = parseInt(card.getAttribute('data-post-id'));
                if (readPosts.indexOf(id) === -1) unreadCount++;
            });
            
            var badge = $('unreadBadge');
            if (!badge) return;
            if (unreadCount > 0) {
                badge.textContent = unreadCount;
                badge.style.display = 'flex';
                badge.classList.add('pulse');
                setTimeout(function() { badge.classList.remove('pulse'); }, 2000);
            } else {
                badge.style.display = 'none';
            }
        }
        
        // ============ ПОИСК ============
        function toggleSearch() {
            var searchBar = $('searchBar');
            if (!searchBar) return;
            searchBar.classList.toggle('active');
            
            if (searchBar.classList.contains('active')) {
                setTimeout(function() {
                    var si = $('searchInput');
                    if (si) si.focus();
                }, 100);
            } else {
                var si = $('searchInput');
                if (si) si.value = '';
                performSearch();
            }
        }
        
        function performSearch() {
            var si = $('searchInput');
            var query = si ? si.value.toLowerCase().trim() : '';
            var cards = $$('.news-card');
            var visibleCount = 0;
            
            cards.forEach(function(card) {
                var title = card.getAttribute('data-title') || '';
                var text = card.getAttribute('data-text') || '';
                
                if (card.classList.contains('premium-only') && (!userProfile || !userProfile.is_subscriber)) {
                    card.style.display = 'none';
                    return;
                }
                
                if (!query || title.indexOf(query) > -1 || text.indexOf(query) > -1) {
                    card.style.display = '';
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                }
            });
            
            var nr = $('noResults');
            if (nr) nr.style.display = visibleCount === 0 ? 'block' : 'none';
        }
        
        // ============ ФИЛЬТРЫ ============
        function filterPosts(filter) {
            currentFilter = filter;
            
            $$('.filter-btn').forEach(function(b) {
                b.classList.remove('active');
                if (b.getAttribute('data-filter') === filter) {
                    b.classList.add('active');
                }
            });
            
            var favorites = getFavorites();
            var readPosts = getReadPosts();
            var cards = $$('.news-card');
            var visibleCount = 0;
            
            cards.forEach(function(card) {
                var postId = parseInt(card.getAttribute('data-post-id'));
                var show = true;
                
                if (card.classList.contains('premium-only') && (!userProfile || !userProfile.is_subscriber)) {
                    card.style.display = 'none';
                    return;
                }
                
                if (filter === 'favorites') {
                    show = favorites.indexOf(postId) > -1;
                } else if (filter === 'unread') {
                    show = readPosts.indexOf(postId) === -1;
                } else if (filter === 'read') {
                    show = readPosts.indexOf(postId) > -1;
                }
                
                card.style.display = show ? '' : 'none';
                if (show) visibleCount++;
            });
            
            var nr = $('noResults');
            if (nr) nr.style.display = visibleCount === 0 ? 'block' : 'none';
            
            var favBtn = $('favBtn');
            if (favBtn) {
                if (filter === 'favorites') {
                    favBtn.classList.add('active');
                } else {
                    favBtn.classList.remove('active');
                }
            }
        }
        
        // ============ АВТОРИЗАЦИЯ ============
        function openAuthModal() {
            var modal = $('authModal');
            if (modal) modal.classList.add('active');
        }
        
        function closeAuthModal() {
            var modal = $('authModal');
            if (modal) modal.classList.remove('active');
        }
        
        function toggleAuthModal() {
            if (currentUser) {
                if (confirm(translations[currentLang].logout + '?')) {
                    logout();
                }
                return;
            }
            openAuthModal();
        }
        
        function toggleAuthMode(e) {
            e.preventDefault();
            authMode = authMode === 'login' ? 'register' : 'login';
            $('authTitle').textContent = authMode === 'login' ? 'Вход' : 'Регистрация';
            $('authSubmitBtn').textContent = authMode === 'login' ? 'Войти' : 'Зарегистрироваться';
            $('authSwitchText').textContent = authMode === 'login' 
                ? 'Нет аккаунта? Зарегистрироваться' 
                : 'Уже есть аккаунт? Войти';
        }
        
        async function handleAuth(e) {
            e.preventDefault();
            
            if (!supabaseClient) {
                showToast('❌', 'Supabase не настроен. Укажите SUPABASE_URL и SUPABASE_ANON_KEY.');
                return;
            }
            
            var email = $('authEmail').value;
            var password = $('authPassword').value;
            var submitBtn = $('authSubmitBtn');
            
            submitBtn.disabled = true;
            submitBtn.textContent = 'Загрузка...';
            
            try {
                var result;
                if (authMode === 'login') {
                    result = await supabaseClient.auth.signInWithPassword({ email: email, password: password });
                } else {
                    result = await supabaseClient.auth.signUp({ email: email, password: password });
                }
                
                if (result.error) throw result.error;
                
                currentUser = result.data.user;
                await loadUserProfile();
                
                closeAuthModal();
                updateAuthUI();
                showToast('✅', translations[currentLang].welcome + ', ' + email + '!');
                
            } catch (error) {
                showToast('❌', error.message);
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = authMode === 'login' ? 'Войти' : 'Зарегистрироваться';
            }
        }
        
        async function logout() {
            if (supabaseClient) {
                await supabaseClient.auth.signOut();
            }
            currentUser = null;
            userProfile = null;
            updateAuthUI();
            hidePremiumArticles();
            showToast('👋', translations[currentLang].loggedOut);
        }
        
        async function loadUserProfile() {
            if (!currentUser || !supabaseClient) return;
            
            try {
                var result = await supabaseClient
                    .from('profiles')
                    .select('*')
                    .eq('id', currentUser.id)
                    .single();
                
                if (result.error) throw result.error;
                userProfile = result.data;
                
                if (userProfile.subscription_until) {
                    var until = new Date(userProfile.subscription_until);
                    if (until < new Date()) {
                        userProfile.is_subscriber = false;
                    }
                }
            } catch (e) {
                console.warn('Профиль не найден');
            }
        }
        
        function updateAuthUI() {
            var authBtnText = $('authBtnText');
            var subBtn = $('subBtn');
            var subBtnText = $('subBtnText');
            
            var t = translations[currentLang];
            
            if (currentUser) {
                if (authBtnText) authBtnText.textContent = currentUser.email.split('@')[0];
                
                if (userProfile && userProfile.is_subscriber) {
                    if (subBtnText) subBtnText.textContent = t.premium + ' ⭐';
                    if (subBtn) subBtn.classList.add('premium');
                    showPremiumArticles();
                } else {
                    if (subBtnText) subBtnText.textContent = t.subscription;
                    if (subBtn) subBtn.classList.remove('premium');
                    hidePremiumArticles();
                }
            } else {
                if (authBtnText) authBtnText.textContent = t.login;
                if (subBtnText) subBtnText.textContent = t.subscription;
                if (subBtn) subBtn.classList.remove('premium');
                hidePremiumArticles();
            }
        }
        
        function showPremiumArticles() {
            $$('.premium-only').forEach(function(card) {
                card.style.display = '';
            });
            var banner = $('upgradeBanner');
            if (banner) banner.style.display = 'none';
        }
        
        function hidePremiumArticles() {
            $$('.premium-only').forEach(function(card) {
                card.style.display = 'none';
            });
            var banner = $('upgradeBanner');
            if (banner) banner.style.display = '';
        }
        
        // ============ ПОДПИСКА ============
        function openSubscriptionModal() {
            var modal = $('subscriptionModal');
            if (modal) modal.classList.add('active');
        }
        
        function closeSubscriptionModal() {
            var modal = $('subscriptionModal');
            if (modal) modal.classList.remove('active');
        }
        
        function handleSubscriptionClick() {
            if (!currentUser) {
                showToast('⚠️', 'Сначала войдите в аккаунт');
                openAuthModal();
                return;
            }
            
            if (userProfile && userProfile.is_subscriber) {
                var until = new Date(userProfile.subscription_until);
                var daysLeft = Math.ceil((until - new Date()) / (1000 * 60 * 60 * 24));
                showToast('⭐', 'Подписка активна до ' + until.toLocaleDateString() + '. Осталось ' + daysLeft + ' дн.', 'premium');
                return;
            }
            
            openSubscriptionModal();
        }
        
        async function subscribe(plan) {
            if (!currentUser) return;
            
            if (!supabaseClient) {
                showToast('❌', 'Supabase не настроен');
                return;
            }
            
            var currency = localStorage.getItem('preferred_crypto') || 'USDT';
            
            try {
                showToast('⏳', 'Создание платежа...');
                
                var result = await supabaseClient.functions.invoke('create-cryptomus-payment', {
                    body: {
                        plan: plan,
                        user_id: currentUser.id,
                        email: currentUser.email,
                        currency: currency
                    }
                });
                
                if (result.error) throw result.error;
                
                if (result.data && result.data.confirmation_url) {
                    localStorage.setItem('pending_payment', result.data.payment_id);
                    window.location.href = result.data.confirmation_url;
                } else {
                    throw new Error('Не удалось создать платеж');
                }
                
            } catch (error) {
                console.error('Payment error:', error);
                showToast('❌', 'Ошибка: ' + error.message);
            }
        }
        
        function checkPaymentReturn() {
            var urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('payment') === 'success') {
                showToast('✅', 'Платеж обрабатывается...', 'premium');
                
                setTimeout(async function() {
                    await loadUserProfile();
                    updateAuthUI();
                    
                    if (userProfile && userProfile.is_subscriber) {
                        showToast('⭐', 'Подписка активирована! Доступно 200 статей.', 'premium');
                    }
                    window.history.replaceState({}, '', window.location.pathname);
                }, 3000);
            }
        }
        
        // ============ ПРИВЯЗКА СОБЫТИЙ ============
        function bindEvents() {
            // Кнопки в хедере
            var searchBtn = $('searchBtn');
            if (searchBtn) searchBtn.addEventListener('click', toggleSearch);
            
            var favBtn = $('favBtn');
            if (favBtn) favBtn.addEventListener('click', toggleFavorites);
            
            var unreadBtn = $('unreadBtn');
            if (unreadBtn) {
                unreadBtn.addEventListener('click', function() {
                    filterPosts('unread');
                });
            }
            
            var langBtn = $('langBtn');
            if (langBtn) langBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                toggleLangMenu();
            });
            
            var themeBtn = $('themeBtn');
            if (themeBtn) themeBtn.addEventListener('click', toggleTheme);
            
            var subBtn = $('subBtn');
            if (subBtn) subBtn.addEventListener('click', handleSubscriptionClick);
            
            var authBtn = $('authBtn');
            if (authBtn) authBtn.addEventListener('click', toggleAuthModal);
            
            // Языки
            $$('.lang-option').forEach(function(el) {
                el.addEventListener('click', function() {
                    setLanguage(el.getAttribute('data-lang'));
                });
            });
            
            // Фильтры
            $$('.filter-btn').forEach(function(btn) {
                btn.addEventListener('click', function() {
                    filterPosts(btn.getAttribute('data-filter'));
                });
            });
            
            // Поиск
            var searchInput = $('searchInput');
            if (searchInput) searchInput.addEventListener('input', performSearch);
            
            // Кнопки на карточках
            $$('.favorite').forEach(function(btn) {
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    var id = parseInt(btn.getAttribute('data-fav-id'));
                    toggleFavorite(id, btn);
                });
            });
            
            $$('.read-toggle').forEach(function(btn) {
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    var id = parseInt(btn.getAttribute('data-read-id'));
                    toggleRead(id, btn);
                });
            });
            
            $$('[data-read-link]').forEach(function(link) {
                link.addEventListener('click', function() {
                    var id = parseInt(link.getAttribute('data-read-link'));
                    markAsRead(id);
                });
            });
            
            // Кнопка апгрейда
            var upgradeBtn = $('upgradeBtn');
            if (upgradeBtn) upgradeBtn.addEventListener('click', handleSubscriptionClick);
            
            // Модальные окна
            var authClose = $('authClose');
            if (authClose) authClose.addEventListener('click', closeAuthModal);
            
            var authSwitch = $('authSwitch');
            if (authSwitch) authSwitch.addEventListener('click', toggleAuthMode);
            
            var authForm = $('authForm');
            if (authForm) authForm.addEventListener('submit', handleAuth);
            
            var subClose = $('subClose');
            if (subClose) subClose.addEventListener('click', closeSubscriptionModal);
            
            // Платежные методы
            $$('.payment-method').forEach(function(el) {
                el.addEventListener('click', function() {
                    $$('.payment-method').forEach(function(m) { m.classList.remove('active'); });
                    el.classList.add('active');
                    localStorage.setItem('preferred_crypto', el.getAttribute('data-currency'));
                });
            });
            
            // Планы
            $$('.plan').forEach(function(el) {
                el.addEventListener('click', function() {
                    subscribe(el.getAttribute('data-plan'));
                });
            });
            
            // Закрытие модалок по клику вне
            $$('.modal').forEach(function(modal) {
                modal.addEventListener('click', function(e) {
                    if (e.target === modal) {
                        modal.classList.remove('active');
                    }
                });
            });
            
            // Закрытие меню языков по клику вне
            document.addEventListener('click', function(e) {
                var langDropdown = document.querySelector('.lang-dropdown');
                if (langDropdown && !langDropdown.contains(e.target)) {
                    var menu = $('langMenu');
                    if (menu) menu.classList.remove('active');
                }
            });
            
            // Прогресс-бар
            window.addEventListener('scroll', function() {
                var scrollTop = window.pageYOffset;
                var docHeight = document.documentElement.scrollHeight - window.innerHeight;
                var scrollPercent = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
                var pb = $('progressBar');
                if (pb) pb.style.width = scrollPercent + '%';
            });
        }
        
        // ============ ИНИЦИАЛИЗАЦИЯ ============
        document.addEventListener('DOMContentLoaded', async function() {
            // Применяем тему
            var savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-theme', savedTheme);
            updateThemeButton(savedTheme);
            
            // Применяем язык
            var cl = $('currentLang');
            if (cl) cl.textContent = currentLang.toUpperCase();
            
            $$('.lang-option').forEach(function(el) {
                el.classList.remove('active');
                if (el.getAttribute('data-lang') === currentLang) {
                    el.classList.add('active');
                }
            });
            
            $$('[data-i18n]').forEach(function(el) {
                var key = el.getAttribute('data-i18n');
                if (translations[currentLang][key]) {
                    el.textContent = translations[currentLang][key];
                }
            });
            
            var si = $('searchInput');
            if (si) si.placeholder = translations[currentLang].searchPlaceholder;
            
            // Обновляем активные избранные
            var favorites = getFavorites();
            $$('.news-card').forEach(function(card) {
                var postId = parseInt(card.getAttribute('data-post-id'));
                var favBtn = card.querySelector('.favorite');
                if (favorites.indexOf(postId) > -1 && favBtn) {
                    favBtn.classList.add('active');
                }
            });
            
            updateFavBadge();
            updateUnreadBadge();
            
            // Привязываем события
            bindEvents();
            
            // Проверяем Supabase сессию
            if (supabaseClient) {
                try {
                    var sessionResult = await supabaseClient.auth.getSession();
                    if (sessionResult.data && sessionResult.data.session) {
                        currentUser = sessionResult.data.session.user;
                        await loadUserProfile();
                        updateAuthUI();
                    }
                    
                    supabaseClient.auth.onAuthStateChange(async function(event, session) {
                        if (session) {
                            currentUser = session.user;
                            await loadUserProfile();
                        } else {
                            currentUser = null;
                            userProfile = null;
                        }
                        updateAuthUI();
                    });
                } catch (e) {
                    console.warn('Supabase session error:', e);
                }
            }
            
            checkPaymentReturn();
            
            if (currentLang !== 'ru') {
                setTimeout(function() { translateAllPosts(currentLang); }, 500);
            }
        });
    })();
    </script>
</body>
</html>
'''
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_output)
    print("🌐 Сгенерирован index.html")


def generate_post_pages(posts):
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
            is_premium = i >= 42
            
            template = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>__PAGE_TITLE__ - Новикон</title>
    <link rel="icon" href="../__LOGO__" type="image/png">
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
            line-height: 1.8;
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
            max-width: 800px;
            margin: 0 auto;
            padding: 0 20px;
        }
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }
        .logo-link {
            display: flex;
            align-items: center;
            gap: 12px;
            color: white;
            text-decoration: none;
        }
        .logo-link img {
            height: 40px;
            width: auto;
            border-radius: 6px;
        }
        .logo-link .site-title {
            font-size: 22px;
            font-weight: 700;
        }
        .header-btns {
            display: flex;
            gap: 8px;
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
            font-family: inherit;
        }
        .control-btn:hover {
            background: rgba(255,255,255,0.3);
            transform: scale(1.05);
        }
        .control-btn.favorite.active {
            background: var(--favorite);
            border-color: var(--favorite);
            color: white;
        }
        .post-content {
            background: var(--card-bg);
            border-radius: 12px;
            padding: 40px;
            margin: 30px 0;
            box-shadow: var(--shadow);
            transition: background 0.4s;
        }
        .post-date {
            color: #888;
            font-size: 14px;
            margin-bottom: 15px;
        }
        .post-title {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 20px;
            line-height: 1.3;
        }
        .post-text {
            font-size: 17px;
            line-height: 1.8;
        }
        .post-text a {
            color: var(--accent);
            text-decoration: none;
        }
        .post-text img {
            display: block;
            max-width: 100%;
            border-radius: 12px;
            margin: 20px auto;
        }
        .back-button {
            display: inline-block;
            margin-top: 30px;
            padding: 12px 24px;
            background: var(--header-bg);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            transition: transform 0.3s;
        }
        .back-button:hover {
            transform: scale(1.05);
        }
        .premium-lock {
            text-align: center;
            padding: 60px 20px;
            background: linear-gradient(135deg, rgba(246,211,101,0.1) 0%, rgba(253,160,133,0.1) 100%);
            border-radius: 12px;
            margin: 20px 0;
        }
        .premium-lock h2 {
            font-size: 24px;
            margin-bottom: 15px;
        }
        .premium-lock p {
            color: #888;
            margin-bottom: 20px;
        }
        .premium-lock button {
            background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
            color: white;
            border: none;
            padding: 14px 30px;
            border-radius: 25px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: transform 0.3s;
            font-family: inherit;
        }
        .premium-lock button:hover {
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
            animation: slideInRight 0.4s ease;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .toast.favorite {
            border-left-color: var(--favorite);
        }
        .toast-icon {
            font-size: 24px;
        }
        .toast-content {
            flex: 1;
            font-size: 14px;
        }
        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(100px); }
            to { opacity: 1; transform: translateX(0); }
        }
        @media (max-width: 768px) {
            .post-content { padding: 20px; }
            .post-title { font-size: 22px; }
            .header-content {
                flex-direction: column;
                gap: 10px;
                text-align: center;
            }
            .logo-link img {
                height: 32px;
            }
            .logo-link .site-title {
                font-size: 18px;
            }
        }
    </style>
</head>
<body>
    <div class="progress-bar" id="progressBar"></div>
    
    <header>
        <div class="container">
            <div class="header-content">
                <a href="/Novikon-site/" class="logo-link">
                    <img src="../__LOGO__" alt="Новикон">
                    <span class="site-title">Новикон</span>
                </a>
                <div class="header-btns">
                    <button type="button" class="control-btn favorite" id="favBtn" title="В избранное">⭐</button>
                    <button type="button" class="control-btn" id="themeBtn">🌙</button>
                </div>
            </div>
        </div>
    </header>
    <div class="container">
        <div class="post-content">
            <div class="post-date">📅 __DATE__ __PREMIUM_MARK__</div>
            <h1 class="post-title" id="postTitle">__TITLE__</h1>
            <div id="postContent">
                __IMG__
                <div class="post-text" id="postText">__FULL_TEXT__</div>
            </div>
            <div id="premiumLock" class="premium-lock" style="display:none;">
                <h2>🔒 Премиум контент</h2>
                <p>Эта статья доступна только подписчикам Новикон</p>
                <button type="button" id="openSubBtn">Оформить подписку за 149 ₽/мес</button>
            </div>
            <a href="/Novikon-site/" class="back-button">← На главную</a>
        </div>
    </div>
    <div class="footer">
        <div class="container">
            <p>© 2026 Новикон</p>
        </div>
    </div>
    
    <div class="toast-container" id="toastContainer"></div>
    
    <script>
    (function() {
        'use strict';
        
        var SUPABASE_URL = 'YOUR_SUPABASE_URL';
        var SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY';
        var supabaseClient = null;
        
        if (window.supabase && SUPABASE_URL !== 'YOUR_SUPABASE_URL') {
            supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        }
        
        var POST_ID = __POST_ID__;
        var IS_PREMIUM = __IS_PREMIUM__;
        var ORIGINAL_TITLE = __ORIGINAL_TITLE__;
        var ORIGINAL_TEXT = __ORIGINAL_TEXT__;
        
        var currentUser = null;
        var userProfile = null;
        
        function $(id) { return document.getElementById(id); }
        
        function showToast(icon, message, type) {
            type = type || '';
            var container = $('toastContainer');
            if (!container) return;
            var toast = document.createElement('div');
            toast.className = 'toast ' + type;
            toast.innerHTML = '<div class="toast-icon">' + icon + '</div><div class="toast-content">' + message + '</div>';
            container.appendChild(toast);
            setTimeout(function() {
                toast.style.opacity = '0';
                setTimeout(function() { toast.remove(); }, 400);
            }, 3000);
        }
        
        async function checkPremiumAccess() {
            if (!IS_PREMIUM) {
                $('postContent').style.display = 'block';
                $('premiumLock').style.display = 'none';
                return;
            }
            
            if (!supabaseClient) {
                $('postContent').style.display = 'none';
                $('premiumLock').style.display = 'block';
                return;
            }
            
            try {
                var sessionResult = await supabaseClient.auth.getSession();
                if (sessionResult.data && sessionResult.data.session) {
                    currentUser = sessionResult.data.session.user;
                    var profileResult = await supabaseClient
                        .from('profiles')
                        .select('is_subscriber, subscription_until')
                        .eq('id', currentUser.id)
                        .single();
                    
                    if (!profileResult.error && profileResult.data) {
                        var data = profileResult.data;
                        var isActive = data.subscription_until && new Date(data.subscription_until) > new Date();
                        if (data.is_subscriber && isActive) {
                            $('postContent').style.display = 'block';
                            $('premiumLock').style.display = 'none';
                            return;
                        }
                    }
                }
            } catch (e) {
                console.warn('Premium check error:', e);
            }
            
            $('postContent').style.display = 'none';
            $('premiumLock').style.display = 'block';
        }
        
        function toggleTheme() {
            var html = document.documentElement;
            var currentTheme = html.getAttribute('data-theme');
            var newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            $('themeBtn').textContent = newTheme === 'dark' ? '☀️' : '🌙';
        }
        
        function getFavorites() {
            try { return JSON.parse(localStorage.getItem('favorites') || '[]'); }
            catch (e) { return []; }
        }
        
        function toggleFavorite() {
            var favorites = getFavorites();
            var index = favorites.indexOf(POST_ID);
            var btn = $('favBtn');
            
            if (index > -1) {
                favorites.splice(index, 1);
                btn.classList.remove('active');
                showToast('💔', 'Удалено из избранного');
            } else {
                favorites.push(POST_ID);
                btn.classList.add('active');
                showToast('⭐', 'Добавлено в избранное', 'favorite');
            }
            
            localStorage.setItem('favorites', JSON.stringify(favorites));
        }
        
        function markAsRead() {
            try {
                var readPosts = JSON.parse(localStorage.getItem('readPosts') || '[]');
                if (readPosts.indexOf(POST_ID) === -1) {
                    readPosts.push(POST_ID);
                    localStorage.setItem('readPosts', JSON.stringify(readPosts));
                }
            } catch (e) {}
        }
        
        window.addEventListener('scroll', function() {
            var scrollTop = window.pageYOffset;
            var docHeight = document.documentElement.scrollHeight - window.innerHeight;
            var scrollPercent = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
            var pb = $('progressBar');
            if (pb) pb.style.width = scrollPercent + '%';
        });
        
        document.addEventListener('DOMContentLoaded', async function() {
            var savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-theme', savedTheme);
            $('themeBtn').textContent = savedTheme === 'dark' ? '☀️' : '🌙';
            
            var favBtn = $('favBtn');
            if (favBtn) favBtn.addEventListener('click', toggleFavorite);
            
            var themeBtn = $('themeBtn');
            if (themeBtn) themeBtn.addEventListener('click', toggleTheme);
            
            var openSubBtn = $('openSubBtn');
            if (openSubBtn) {
                openSubBtn.addEventListener('click', function() {
                    window.location.href = '/Novikon-site/#subscription';
                });
            }
            
            if (getFavorites().indexOf(POST_ID) > -1) {
                $('favBtn').classList.add('active');
            }
            
            await checkPremiumAccess();
            markAsRead();
            
            document.body.style.opacity = '0';
            document.body.style.transition = 'opacity 0.4s';
            setTimeout(function() {
                document.body.style.opacity = '1';
            }, 50);
        });
    })();
    </script>
</body>
</html>'''
            
            html_output = template.replace('__PAGE_TITLE__', html_module.escape(title))
            html_output = html_output.replace('__LOGO__', LOGO_FILE)
            html_output = html_output.replace('__DATE__', date_str)
            html_output = html_output.replace('__PREMIUM_MARK__', '⭐ PREMIUM' if is_premium else '')
            html_output = html_output.replace('__TITLE__', html_module.escape(title))
            html_output = html_output.replace('__IMG__', img_html)
            html_output = html_output.replace('__FULL_TEXT__', full_text)
            html_output = html_output.replace('__POST_ID__', str(post["id"]))
            html_output = html_output.replace('__IS_PREMIUM__', str(is_premium).lower())
            html_output = html_output.replace('__ORIGINAL_TITLE__', title_json)
            html_output = html_output.replace('__ORIGINAL_TEXT__', full_text_json)
            
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
