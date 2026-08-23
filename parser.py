import os
import json
import asyncio
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import shutil

# Получение данных из секретов
API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', '')
PHONE_NUMBER = os.getenv('PHONE_NUMBER', '')  # Ваш номер телефона

if not API_ID or not API_HASH:
    print("❌ Ошибка: API_ID или API_HASH не установлены")
    print("📌 Получите их на https://my.telegram.org/auth")
    exit(1)

if not CHANNEL_ID:
    print("❌ Ошибка: TELEGRAM_CHANNEL_ID не установлен")
    exit(1)

# Создаем клиент с API ID и Hash (для пользователя)
client = TelegramClient('session', API_ID, API_HASH)

async def parse_channel():
    try:
        # Вход как пользователь (не бот!)
        await client.start(phone=PHONE_NUMBER)
        print("✅ Пользователь успешно авторизован")
        
        # Определяем канал
        if CHANNEL_ID.startswith('@'):
            entity = await client.get_entity(CHANNEL_ID)
        else:
            try:
                entity = await client.get_entity(int(CHANNEL_ID))
            except ValueError:
                entity = await client.get_entity(CHANNEL_ID)
        
        print(f"📡 Подключен к каналу: {entity.title if hasattr(entity, 'title') else CHANNEL_ID}")
        
        posts = []
        limit = 40
        count = 0
        
        # Создаем папку для изображений
        os.makedirs('assets', exist_ok=True)
        
        # Получаем последние 40 сообщений (история!)
        async for message in client.iter_messages(entity, limit=limit):
            # Пропускаем служебные сообщения
            if message.text and message.text.startswith('/'):
                continue
            
            # Пропускаем пустые сообщения
            if not message.text and not message.media:
                continue
                
            post = {
                'id': message.id,
                'date': message.date.isoformat(),
                'text': message.text or '',
                'image_url': None
            }
            
            # Обработка медиа
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
        
        # Сохраняем в JSON
        with open('posts.json', 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        print("💾 Сохранен posts.json")
        
        # Генерируем HTML
        generate_html(posts)
        
        await client.disconnect()
        print("✅ Парсинг завершен успешно!")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        await client.disconnect()

def generate_html(posts):
    current_time = datetime.now().strftime('%d.%m.%Y %H:%M')
    
    html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Novikon - Новости</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        header h1 {{ font-size: 32px; font-weight: 700; }}
        header .subtitle {{ color: rgba(255,255,255,0.9); font-size: 16px; margin-top: 5px; }}
        .news-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
            padding: 30px 0;
        }}
        .news-card {{
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .news-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.12);
        }}
        .news-card img {{
            width: 100%;
            height: 220px;
            object-fit: cover;
            background: #e0e0e0;
        }}
        .news-content {{ padding: 20px; }}
        .news-date {{ color: #888; font-size: 13px; margin-bottom: 10px; }}
        .news-title {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 12px;
            line-height: 1.4;
        }}
        .news-text {{
            color: #555;
            font-size: 15px;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        .no-image {{
            height: 220px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 48px;
        }}
        .footer {{
            text-align: center;
            padding: 30px 0;
            color: #888;
            font-size: 14px;
            border-top: 1px solid #e0e0e0;
            margin-top: 20px;
        }}
        .update-time {{
            background: #e8e8e8;
            padding: 10px 20px;
            border-radius: 8px;
            display: inline-block;
            margin: 10px 0;
            font-size: 14px;
            color: #555;
        }}
        .stats {{
            text-align: center;
            color: #666;
            font-size: 14px;
            margin: 10px 0;
        }}
        @media (max-width: 768px) {{
            .news-grid {{
                grid-template-columns: 1fr;
                padding: 15px 0;
            }}
            header h1 {{ font-size: 24px; }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>📰 Novikon</h1>
            <div class="subtitle">Актуальные новости и события</div>
        </div>
    </header>
    <div class="container">
        <div style="text-align: center; margin: 15px 0;">
            <span class="update-time">🔄 Обновлено: {current_time}</span>
            <div class="stats">📊 Всего постов: {len(posts)}</div>
        </div>
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
        
        title = title.replace('"', '&quot;').replace("'", '&#39;').replace('<', '&lt;').replace('>', '&gt;')
        text_preview = text_preview.replace('"', '&quot;').replace("'", '&#39;').replace('<', '&lt;').replace('>', '&gt;')
        
        html += f'''
            <div class="news-card">
                {img_html}
                <div class="news-content">
                    <div class="news-date">{date_str}</div>
                    <div class="news-title">{title}</div>
                    <div class="news-text">{text_preview}</div>
                </div>
            </div>
'''

    html += '''
        </div>
    </div>
    <div class="footer">
        <div class="container">
            <p>© 2026 Novikon | Автоматический парсинг новостей</p>
            <p style="font-size: 12px; margin-top: 5px;">Обновляется каждые 30 минут</p>
        </div>
    </div>
</body>
</html>
'''
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("🌐 Сгенерирован index.html")

if __name__ == '__main__':
    asyncio.run(parse_channel())
