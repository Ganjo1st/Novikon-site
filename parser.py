import os
import json
import asyncio
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import shutil
import html as html_module  # Исправленный импорт

# Получение данных из секретов
API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', '')

if not API_ID or not API_HASH:
    print("❌ Ошибка: API_ID или API_HASH не установлены")
    print("📌 Получите их на https://my.telegram.org/apps")
    exit(1)

if not CHANNEL_ID:
    print("❌ Ошибка: TELEGRAM_CHANNEL_ID не установлен")
    exit(1)

client = TelegramClient('session', API_ID, API_HASH)

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
        limit = 40
        count = 0
        
        os.makedirs('assets', exist_ok=True)
        
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
        
        generate_html(posts)
        generate_post_pages(posts)
        
        await client.disconnect()
        print("✅ Парсинг завершен успешно!")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        await client.disconnect()

def generate_html(posts):
    html_output = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Novikon - Новости</title>
    <style>
        :root {
            --bg: #f5f5f5;
            --text: #333;
            --card-bg: white;
            --header-bg: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --shadow: 0 4px 15px rgba(0,0,0,0.08);
            --border: #e0e0e0;
        }
        [data-theme="dark"] {
            --bg: #1a1a2e;
            --text: #e0e0e0;
            --card-bg: #16213e;
            --header-bg: linear-gradient(135deg, #0f3460 0%, #1a1a2e 100%);
            --shadow: 0 4px 15px rgba(0,0,0,0.3);
            --border: #2a2a4a;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            transition: background 0.3s, color 0.3s;
        }
        header {
            background: var(--header-bg);
            color: white;
            padding: 30px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: background 0.3s;
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
        }
        header h1 { font-size: 32px; font-weight: 700; }
        header .subtitle { color: rgba(255,255,255,0.9); font-size: 16px; margin-top: 5px; }
        
        .theme-toggle {
            background: rgba(255,255,255,0.2);
            border: 2px solid rgba(255,255,255,0.3);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s;
        }
        .theme-toggle:hover {
            background: rgba(255,255,255,0.3);
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
            transition: transform 0.3s ease, box-shadow 0.3s ease, background 0.3s;
            cursor: pointer;
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
        .footer {
            text-align: center;
            padding: 30px 0;
            color: #888;
            font-size: 14px;
            border-top: 1px solid var(--border);
            margin-top: 20px;
            transition: border-color 0.3s;
        }
        .read-more {
            display: inline-block;
            margin-top: 12px;
            color: #667eea;
            font-weight: 600;
            text-decoration: none;
        }
        @media (max-width: 768px) {
            .news-grid {
                grid-template-columns: 1fr;
                padding: 15px 0;
            }
            header h1 { font-size: 24px; }
            .header-content {
                flex-direction: column;
                gap: 15px;
                text-align: center;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div class="header-content">
                <div>
                    <h1>📰 Novikon</h1>
                    <div class="subtitle">Актуальные новости и события</div>
                </div>
                <button class="theme-toggle" onclick="toggleTheme()">🌙 Тёмная тема</button>
            </div>
        </div>
    </header>
    <div class="container">
        <div class="news-grid">
'''

    for post in posts:
        title = post['text'][:70] + '...' if len(post['text']) > 70 else post['text']
        text_preview = post['text'][:150] + '...' if len(post['text']) > 150 else post['text']
        
        date_obj = datetime.fromisoformat(post['date'])
        date_str = date_obj.strftime('%d.%m.%Y %H:%M')
        
        if post.get('image_url'):
            img_html = f'<img src="{post["image_url"]}" alt="News image" loading="lazy">'
        else:
            img_html = '<div class="no-image">📄</div>'
        
        # Используем html_module.escape вместо html.escape
        title_escaped = html_module.escape(title)
        text_escaped = html_module.escape(text_preview)
        
        html_output += f'''
            <div class="news-card" onclick="window.location.href='/Novikon-site/posts/post_{post["id"]}.html'">
                {img_html}
                <div class="news-content">
                    <div class="news-date">{date_str}</div>
                    <div class="news-title">{title_escaped}</div>
                    <div class="news-text">{text_escaped}</div>
                    <span class="read-more">Читать далее →</span>
                </div>
            </div>
'''

    html_output += '''
        </div>
    </div>
    <div class="footer">
        <div class="container">
            <p>© 2026 Novikon | Автоматический парсинг новостей</p>
            <p style="font-size: 12px; margin-top: 5px;">Обновляется каждые 30 минут</p>
        </div>
    </div>
    <script>
        function toggleTheme() {
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            document.querySelector('.theme-toggle').textContent = newTheme === 'dark' ? '☀️ Светлая тема' : '🌙 Тёмная тема';
        }
        
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        document.querySelector('.theme-toggle').textContent = savedTheme === 'dark' ? '☀️ Светлая тема' : '🌙 Тёмная тема';
    </script>
</body>
</html>
'''
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_output)
    print("🌐 Сгенерирован index.html")

def generate_post_pages(posts):
    """Генерация отдельных страниц для каждого поста"""
    os.makedirs('posts', exist_ok=True)
    
    for post in posts:
        title = post['text'][:70] + '...' if len(post['text']) > 70 else post['text']
        
        date_obj = datetime.fromisoformat(post['date'])
        date_str = date_obj.strftime('%d.%m.%Y %H:%M')
        
        # Полный текст с заменой переносов
        full_text = post['text'].replace('\n', '<br>')
        
        # Изображение
        if post.get('image_url'):
            img_html = f'<img src="../{post["image_url"]}" alt="News image" style="max-width: 100%; border-radius: 12px; margin: 20px 0;">'
        else:
            img_html = ''
        
        title_escaped = html_module.escape(title)
        
        html_output = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title_escaped} - Novikon</title>
    <style>
        :root {{
            --bg: #f5f5f5;
            --text: #333;
            --card-bg: white;
            --header-bg: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --shadow: 0 4px 15px rgba(0,0,0,0.08);
            --border: #e0e0e0;
        }}
        [data-theme="dark"] {{
            --bg: #1a1a2e;
            --text: #e0e0e0;
            --card-bg: #16213e;
            --header-bg: linear-gradient(135deg, #0f3460 0%, #1a1a2e 100%);
            --shadow: 0 4px 15px rgba(0,0,0,0.3);
            --border: #2a2a4a;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.8;
            transition: background 0.3s, color 0.3s;
        }}
        header {{
            background: var(--header-bg);
            color: white;
            padding: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: background 0.3s;
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
        }}
        header a {{
            color: white;
            text-decoration: none;
            font-size: 18px;
        }}
        .theme-toggle {{
            background: rgba(255,255,255,0.2);
            border: 2px solid rgba(255,255,255,0.3);
            color: white;
            padding: 8px 16px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }}
        .theme-toggle:hover {{
            background: rgba(255,255,255,0.3);
            transform: scale(1.05);
        }}
        .post-content {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 40px;
            margin: 30px 0;
            box-shadow: var(--shadow);
            transition: background 0.3s;
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
            color: #667eea;
            text-decoration: none;
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
            transition: border-color 0.3s;
        }}
        @media (max-width: 768px) {{
            .post-content {{ padding: 20px; }}
            .post-title {{ font-size: 22px; }}
            .header-content {{
                flex-direction: column;
                gap: 10px;
                text-align: center;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div class="header-content">
                <a href="/Novikon-site/">← На главную</a>
                <button class="theme-toggle" onclick="toggleTheme()">🌙 Тёмная тема</button>
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
            <p>© 2026 Novikon | Автоматический парсинг новостей</p>
        </div>
    </div>
    <script>
        function toggleTheme() {{
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            document.querySelector('.theme-toggle').textContent = newTheme === 'dark' ? '☀️ Светлая тема' : '🌙 Тёмная тема';
        }}
        
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        document.querySelector('.theme-toggle').textContent = savedTheme === 'dark' ? '☀️ Светлая тема' : '🌙 Тёмная тема';
    </script>
</body>
</html>
'''
        
        with open(f'posts/post_{post["id"]}.html', 'w', encoding='utf-8') as f:
            f.write(html_output)
    
    print(f"📄 Сгенерировано {len(posts)} отдельных страниц")

if __name__ == '__main__':
    asyncio.run(parse_channel())
