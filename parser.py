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

if not API_ID or not API_HASH:
    print("❌ Ошибка: API_ID или API_HASH не установлены")
    exit(1)

if not CHANNEL_ID:
    print("❌ Ошибка: TELEGRAM_CHANNEL_ID не установлен")
    exit(1)

client = TelegramClient('session', API_ID, API_HASH)

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
        limit = 42
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
    # Подготовка данных для поиска
    posts_json = json.dumps(posts, ensure_ascii=False)
    
    html_output = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Novikon - Новости</title>
    <link rel="icon" href="logo%20Novikon.png" type="image/png">
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
        
        /* Toast уведомления */
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
        .toast-icon {
            font-size: 24px;
        }
        .toast-content {
            flex: 1;
            font-size: 14px;
        }
        .toast-title {
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        /* Анимации */
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
        
        /* Прогресс-бар */
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
        
        /* Language dropdown */
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
                        <img src="logo%20Novikon.png" alt="Novikon Logo">
                        <div>
                            <div class="site-title">Novikon</div>
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
        
        title_escaped = html_module.escape(title)
        text_escaped = html_module.escape(preview_text)
        
        html_output += f'''
            <div class="news-card" data-post-id="{post["id"]}" data-title="{html_module.escape(title.lower())}" data-text="{html_module.escape(preview_text.lower())}">
                <div class="card-actions">
                    <button class="action-btn favorite" onclick="event.preventDefault(); event.stopPropagation(); toggleFavorite({post["id"]}, this)" title="В избранное">⭐</button>
                    <button class="action-btn read-toggle" onclick="event.preventDefault(); event.stopPropagation(); toggleRead({post["id"]}, this)" title="Отметить прочитанным">👁️</button>
                </div>
                <a href="/Novikon-site/posts/post_{post["id"]}.html" style="text-decoration: none; color: inherit;" onclick="markAsRead({post["id"]})">
                    {img_html}
                    <div class="news-content">
                        <div class="news-date">{date_str}</div>
                        <div class="news-title">{title_escaped}</div>
                        <div class="news-text">{text_escaped}</div>
                        <span class="read-more">Читать далее →</span>
                    </div>
                </a>
            </div>
'''

    html_output += '''
        </div>
        <div class="no-results" id="noResults" style="display:none;">
            <p>😔 Ничего не найдено</p>
        </div>
    </div>
    <div class="footer">
        <div class="container">
            <p>© 2026 Novikon</p>
        </div>
    </div>
    
    <div class="toast-container" id="toastContainer"></div>
    
    <script>
        // ============ ДАННЫЕ ============
        const postsData = ''' + posts_json + ''';
        
        // ============ ПЕРЕВОДЫ ============
        const translations = {
            ru: {
                subtitle: 'Актуальные новости и события',
                search: 'Поиск',
                favorites: 'Избранное',
                unread: 'Новые',
                theme: 'Тема',
                all: 'Все',
                filterFav: '⭐ Избранные',
                filterUnread: '📬 Непрочитанные',
                filterRead: '✅ Прочитанные',
                searchPlaceholder: 'Поиск по новостям...',
                readMore: 'Читать далее →',
                noResults: '😔 Ничего не найдено',
                addedToFav: 'Добавлено в избранное',
                removedFromFav: 'Удалено из избранного',
                newArticles: 'новых статей'
            },
            en: {
                subtitle: 'Latest news and events',
                search: 'Search',
                favorites: 'Favorites',
                unread: 'New',
                theme: 'Theme',
                all: 'All',
                filterFav: '⭐ Favorites',
                filterUnread: '📬 Unread',
                filterRead: '✅ Read',
                searchPlaceholder: 'Search news...',
                readMore: 'Read more →',
                noResults: '😔 Nothing found',
                addedToFav: 'Added to favorites',
                removedFromFav: 'Removed from favorites',
                newArticles: 'new articles'
            },
            de: {
                subtitle: 'Aktuelle Nachrichten und Ereignisse',
                search: 'Suche',
                favorites: 'Favoriten',
                unread: 'Neu',
                theme: 'Thema',
                all: 'Alle',
                filterFav: '⭐ Favoriten',
                filterUnread: '📬 Ungelesen',
                filterRead: '✅ Gelesen',
                searchPlaceholder: 'Nachrichten durchsuchen...',
                readMore: 'Weiterlesen →',
                noResults: '😔 Nichts gefunden',
                addedToFav: 'Zu Favoriten hinzugefügt',
                removedFromFav: 'Aus Favoriten entfernt',
                newArticles: 'neue Artikel'
            },
            es: {
                subtitle: 'Últimas noticias y eventos',
                search: 'Buscar',
                favorites: 'Favoritos',
                unread: 'Nuevo',
                theme: 'Tema',
                all: 'Todos',
                filterFav: '⭐ Favoritos',
                filterUnread: '📬 No leídos',
                filterRead: '✅ Leídos',
                searchPlaceholder: 'Buscar noticias...',
                readMore: 'Leer más →',
                noResults: '😔 Nada encontrado',
                addedToFav: 'Añadido a favoritos',
                removedFromFav: 'Eliminado de favoritos',
                newArticles: 'nuevos artículos'
            }
        };
        
        let currentLang = localStorage.getItem('lang') || 'ru';
        let currentFilter = 'all';
        
        // ============ ТЕМА ============
        function toggleTheme() {
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeButton(newTheme);
        }
        
        function updateThemeButton(theme) {
            const btn = document.getElementById('themeBtn');
            const t = translations[currentLang];
            btn.innerHTML = theme === 'dark' ? '☀️ <span>' + t.theme + '</span>' : '🌙 <span>' + t.theme + '</span>';
        }
        
        // ============ ЯЗЫК ============
        function toggleLangMenu() {
            document.getElementById('langMenu').classList.toggle('active');
        }
        
        function setLanguage(lang) {
            currentLang = lang;
            localStorage.setItem('lang', lang);
            
            // Обновляем активный пункт меню
            document.querySelectorAll('.lang-option').forEach(el => el.classList.remove('active'));
            event.target.classList.add('active');
            
            // Обновляем код языка
            document.getElementById('currentLang').textContent = lang.toUpperCase();
            
            // Обновляем все элементы с data-i18n
            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.getAttribute('data-i18n');
                if (translations[lang][key]) {
                    el.textContent = translations[lang][key];
                }
            });
            
            // Обновляем placeholder поиска
            document.getElementById('searchInput').placeholder = translations[lang].searchPlaceholder;
            
            // Обновляем "Читать далее"
            document.querySelectorAll('.read-more').forEach(el => {
                el.textContent = translations[lang].readMore;
            });
            
            // Обновляем кнопку темы
            updateThemeButton(document.documentElement.getAttribute('data-theme') || 'light');
            
            // Закрываем меню
            document.getElementById('langMenu').classList.remove('active');
            
            showToast('🌐', 'Language: ' + lang.toUpperCase());
        }
        
        // ============ ИЗБРАННОЕ ============
        function getFavorites() {
            return JSON.parse(localStorage.getItem('favorites') || '[]');
        }
        
        function toggleFavorite(postId, btn) {
            let favorites = getFavorites();
            const index = favorites.indexOf(postId);
            
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
            const favorites = getFavorites();
            const badge = document.getElementById('favBadge');
            if (favorites.length > 0) {
                badge.textContent = favorites.length;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        }
        
        function toggleFavorites() {
            const btn = document.getElementById('favBtn');
            btn.classList.toggle('active');
            
            if (btn.classList.contains('active')) {
                filterPosts('favorites');
            } else {
                filterPosts('all');
            }
        }
        
        // ============ ПРОЧИТАННЫЕ ============
        function getReadPosts() {
            return JSON.parse(localStorage.getItem('readPosts') || '[]');
        }
        
        function markAsRead(postId) {
            let readPosts = getReadPosts();
            if (!readPosts.includes(postId)) {
                readPosts.push(postId);
                localStorage.setItem('readPosts', JSON.stringify(readPosts));
                updateUnreadBadge();
            }
        }
        
        function toggleRead(postId, btn) {
            let readPosts = getReadPosts();
            const index = readPosts.indexOf(postId);
            
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
            const readPosts = getReadPosts();
            const totalPosts = postsData.length;
            const unreadCount = totalPosts - readPosts.length;
            
            const badge = document.getElementById('unreadBadge');
            if (unreadCount > 0) {
                badge.textContent = unreadCount;
                badge.style.display = 'flex';
                badge.classList.add('pulse');
                setTimeout(() => badge.classList.remove('pulse'), 2000);
            } else {
                badge.style.display = 'none';
            }
        }
        
        // ============ ПОИСК ============
        function toggleSearch() {
            const searchBar = document.getElementById('searchBar');
            searchBar.classList.toggle('active');
            
            if (searchBar.classList.contains('active')) {
                setTimeout(() => document.getElementById('searchInput').focus(), 100);
            } else {
                document.getElementById('searchInput').value = '';
                performSearch();
            }
        }
        
        function performSearch() {
            const query = document.getElementById('searchInput').value.toLowerCase().trim();
            const cards = document.querySelectorAll('.news-card');
            let visibleCount = 0;
            
            cards.forEach(card => {
                const title = card.getAttribute('data-title') || '';
                const text = card.getAttribute('data-text') || '';
                
                if (!query || title.includes(query) || text.includes(query)) {
                    card.style.display = '';
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                }
            });
            
            document.getElementById('noResults').style.display = visibleCount === 0 ? 'block' : 'none';
        }
        
        // ============ ФИЛЬТРЫ ============
        function filterPosts(filter, btn) {
            currentFilter = filter;
            
            // Обновляем активную кнопку
            if (btn) {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            }
            
            const favorites = getFavorites();
            const readPosts = getReadPosts();
            const cards = document.querySelectorAll('.news-card');
            let visibleCount = 0;
            
            cards.forEach(card => {
                const postId = parseInt(card.getAttribute('data-post-id'));
                let show = true;
                
                if (filter === 'favorites') {
                    show = favorites.includes(postId);
                } else if (filter === 'unread') {
                    show = !readPosts.includes(postId);
                } else if (filter === 'read') {
                    show = readPosts.includes(postId);
                }
                
                card.style.display = show ? '' : 'none';
                if (show) visibleCount++;
            });
            
            document.getElementById('noResults').style.display = visibleCount === 0 ? 'block' : 'none';
            
            // Обновляем кнопку избранного
            const favBtn = document.getElementById('favBtn');
            if (filter === 'favorites') {
                favBtn.classList.add('active');
            } else {
                favBtn.classList.remove('active');
            }
        }
        
        // ============ УВЕДОМЛЕНИЯ ============
        function showToast(icon, message, type = '') {
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = 'toast ' + type;
            toast.innerHTML = `
                <div class="toast-icon">${icon}</div>
                <div class="toast-content">${message}</div>
            `;
            container.appendChild(toast);
            
            setTimeout(() => {
                toast.style.animation = 'slideInRight 0.4s ease reverse';
                setTimeout(() => toast.remove(), 400);
            }, 3000);
        }
        
        // ============ ПРОГРЕСС-БАР ============
        window.addEventListener('scroll', () => {
            const scrollTop = window.pageYOffset;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            const scrollPercent = (scrollTop / docHeight) * 100;
            document.getElementById('progressBar').style.width = scrollPercent + '%';
        });
        
        // ============ ЗАГРУЗКА СТРАНИЦЫ ============
        document.addEventListener('DOMContentLoaded', function() {
            // Тема
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-theme', savedTheme);
            updateThemeButton(savedTheme);
            
            // Язык
            document.getElementById('currentLang').textContent = currentLang.toUpperCase();
            document.querySelectorAll('.lang-option').forEach(el => {
                el.classList.remove('active');
                if (el.textContent.includes(currentLang === 'ru' ? 'Русский' : currentLang === 'en' ? 'English' : currentLang === 'de' ? 'Deutsch' : 'Español')) {
                    el.classList.add('active');
                }
            });
            
            // Обновляем переводы
            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.getAttribute('data-i18n');
                if (translations[currentLang][key]) {
                    el.textContent = translations[currentLang][key];
                }
            });
            document.getElementById('searchInput').placeholder = translations[currentLang].searchPlaceholder;
            document.querySelectorAll('.read-more').forEach(el => {
                el.textContent = translations[currentLang].readMore;
            });
            
            // Обновляем избранное
            const favorites = getFavorites();
            document.querySelectorAll('.news-card').forEach(card => {
                const postId = parseInt(card.getAttribute('data-post-id'));
                const favBtn = card.querySelector('.favorite');
                if (favorites.includes(postId) && favBtn) {
                    favBtn.classList.add('active');
                }
            });
            updateFavBadge();
            
            // Обновляем непрочитанные
            updateUnreadBadge();
            
            // Анимация появления карточек
            document.querySelectorAll('.news-card').forEach((card, index) => {
                setTimeout(() => {
                    card.style.animationDelay = (index * 0.05) + 's';
                }, 0);
            });
            
            // Закрываем меню языка при клике вне
            document.addEventListener('click', function(e) {
                const langDropdown = document.querySelector('.lang-dropdown');
                if (langDropdown && !langDropdown.contains(e.target)) {
                    document.getElementById('langMenu').classList.remove('active');
                }
            });
            
            // Показываем уведомление о новых статьях
            const lastVisit = localStorage.getItem('lastVisit');
            const now = Date.now();
            if (lastVisit) {
                const timeDiff = now - parseInt(lastVisit);
                // Если прошло больше 1 часа
                if (timeDiff > 3600000) {
                    const unreadCount = postsData.length - getReadPosts().length;
                    if (unreadCount > 0) {
                        setTimeout(() => {
                            showToast('🔔', unreadCount + ' ' + translations[currentLang].newArticles);
                        }, 1000);
                    }
                }
            }
            localStorage.setItem('lastVisit', now.toString());
        });
        
        // ============ ПЕРЕХОДЫ С АНИМАЦИЕЙ ============
        document.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', function(e) {
                if (this.hostname === window.location.hostname) {
                    e.preventDefault();
                    document.body.style.opacity = '0';
                    document.body.style.transition = 'opacity 0.3s';
                    setTimeout(() => {
                        window.location.href = this.href;
                    }, 300);
                }
            });
        });
    </script>
</body>
</html>
'''
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_output)
    print("🌐 Сгенерирован index.html со всеми функциями")

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
            
            title_escaped = html_module.escape(title)
            
            html_output = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title_escaped} - Novikon</title>
    <link rel="icon" href="../logo%20Novikon.png" type="image/png">
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
        .post-text a {{
            color: var(--accent);
            text-decoration: none;
        }}
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
        .back-button:hover {{
            transform: scale(1.05);
        }}
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
        
        /* Прогресс-бар */
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
        
        /* Toast уведомления */
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
        .toast.favorite {{
            border-left-color: var(--favorite);
        }}
        .toast-icon {{
            font-size: 24px;
        }}
        .toast-content {{
            flex: 1;
            font-size: 14px;
        }}
        
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
            .logo-link img {{
                height: 32px;
            }}
            .logo-link .site-title {{
                font-size: 18px;
            }}
        }}
    </style>
</head>
<body>
    <div class="progress-bar" id="progressBar"></div>
    
    <header>
        <div class="container">
            <div class="header-content">
                <a href="/Novikon-site/" class="logo-link">
                    <img src="../logo%20Novikon.png" alt="Novikon">
                    <span class="site-title">Novikon</span>
                </a>
                <div class="header-btns">
                    <button class="control-btn favorite" id="favBtn" onclick="toggleFavorite()" title="В избранное">⭐</button>
                    <button class="control-btn" onclick="toggleTheme()" id="themeBtn">🌙</button>
                </div>
            </div>
        </div>
    </header>
    <div class="container">
        <div class="post-content">
            <div class="post-date">📅 {date_str}</div>
            <h1 class="post-title">{title_escaped}</h1>
            {img_html}
            <div class="post-text">{full_text}</div>
            <a href="/Novikon-site/" class="back-button">← На главную</a>
        </div>
    </div>
    <div class="footer">
        <div class="container">
            <p>© 2026 Novikon</p>
        </div>
    </div>
    
    <div class="toast-container" id="toastContainer"></div>
    
    <script>
        const POST_ID = {post["id"]};
        
        // ============ ТЕМА ============
        function toggleTheme() {{
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            document.getElementById('themeBtn').textContent = newTheme === 'dark' ? '☀️' : '🌙';
        }}
        
        // ============ ИЗБРАННОЕ ============
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
            const favorites = getFavorites();
            if (favorites.includes(POST_ID)) {{
                document.getElementById('favBtn').classList.add('active');
            }}
        }}
        
        // ============ ПРОЧИТАННЫЕ ============
        function markAsRead() {{
            let readPosts = JSON.parse(localStorage.getItem('readPosts') || '[]');
            if (!readPosts.includes(POST_ID)) {{
                readPosts.push(POST_ID);
                localStorage.setItem('readPosts', JSON.stringify(readPosts));
            }}
        }}
        
        // ============ УВЕДОМЛЕНИЯ ============
        function showToast(icon, message, type = '') {{
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = 'toast ' + type;
            toast.innerHTML = `
                <div class="toast-icon">${{icon}}</div>
                <div class="toast-content">${{message}}</div>
            `;
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
        document.addEventListener('DOMContentLoaded', function() {{
            // Тема
            const savedTheme = localStorage.getItem('theme') || 'light';
            document.documentElement.setAttribute('data-theme', savedTheme);
            document.getElementById('themeBtn').textContent = savedTheme === 'dark' ? '☀️' : '🌙';
            
            // Избранное
            updateFavBtn();
            
            // Отмечаем как прочитанное
            markAsRead();
            
            // Анимация перехода
            document.body.style.opacity = '0';
            document.body.style.transition = 'opacity 0.4s';
            setTimeout(() => {{
                document.body.style.opacity = '1';
            }}, 50);
        }});
    </script>
</body>
</html>
'''
            
            with open(f'posts/post_{post["id"]}.html', 'w', encoding='utf-8') as f:
                f.write(html_output)
            
            if (i + 1) % 10 == 0:
                print(f"📄 Сгенерировано {i + 1} из {len(posts)} страниц")
                
        except Exception as e:
            print(f"❌ Ошибка при генерации страницы для поста {post['id']}: {e}")
            continue
    
    print(f"✅ Сгенерировано {len(posts)} отдельных страниц")

if __name__ == '__main__':
    asyncio.run(parse_channel())
