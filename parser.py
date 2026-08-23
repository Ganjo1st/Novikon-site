import os
import json
import asyncio
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import re

# Получение данных из секретов
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('TELEGRAM_CHANNEL_ID'))

# Создание клиента
client = TelegramClient('session', api_id=0, api_hash='')  # Бот не требует api_id

async def parse_channel():
    await client.start(bot_token=BOT_TOKEN)
    
    posts = []
    limit = 40
    
    async for message in client.iter_messages(CHANNEL_ID, limit=limit):
        # Пропускаем служебные сообщения
        if message.text and message.text.startswith('/'):
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
                if isinstance(message.media, MessageMediaPhoto):
                    # Скачиваем фото
                    path = await client.download_media(message.media, file=f'temp_{message.id}.jpg')
                    if path:
                        # Сохраняем в assets
                        import shutil
                        os.makedirs('assets', exist_ok=True)
                        new_path = f'assets/post_{message.id}.jpg'
                        shutil.move(path, new_path)
                        post['image_url'] = new_path
                        
                elif isinstance(message.media, MessageMediaDocument):
                    # Проверяем, что это изображение
                    if message.media.document and message.media.document.mime_type and message.media.document.mime_type.startswith('image/'):
                        path = await client.download_media(message.media, file=f'temp_{message.id}.jpg')
                        if path:
                            os.makedirs('assets', exist_ok=True)
                            new_path = f'assets/post_{message.id}.jpg'
                            shutil.move(path, new_path)
                            post['image_url'] = new_path
            except Exception as e:
                print(f"Ошибка загрузки медиа: {e}")
                
        posts.append(post)
    
    # Сохраняем в JSON
    with open('posts.json', 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    
    # Генерируем HTML
    generate_html(posts)
    
    await client.disconnect()

def generate_html(posts):
    html = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Novikon - Новости</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        header {
            background: #1a1a2e;
            color: white;
            padding: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }
        header h1 {
            font-size: 28px;
            font-weight: 700;
        }
        header .subtitle {
            color: #a8a8b3;
            font-size: 14px;
        }
        .news-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
            padding: 30px 0;
        }
        .news-card {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .news-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.12);
        }
        .news-card img {
            width: 100%;
            height: 220px;
            object-fit: cover;
            background: #e0e0e0;
        }
        .news-content {
            padding: 20px;
        }
        .news-date {
            color: #888;
            font-size: 13px;
            margin-bottom: 10px;
        }
        .news-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 12px;
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        .news-text {
            color: #555;
            font-size: 15px;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        .no-image {
            height: 220px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
            border-top: 1px solid #e0e0e0;
            margin-top: 20px;
        }
        .update-time {
            background: #e8e8e8;
            padding: 10px 20px;
            border-radius: 8px;
            display: inline-block;
            margin: 10px 0;
            font-size: 14px;
            color: #555;
        }
        @media (max-width: 768px) {
            .news-grid {
                grid-template-columns: 1fr;
                padding: 15px 0;
            }
            header h1 {
                font-size: 22px;
            }
        }
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
            <span class="update-time">🔄 Обновлено: ''' + datetime.now().strftime('%d.%m.%Y %H:%M') + '''</span>
        </div>
        <div class="news-grid">
'''

    for post in posts:
        # Обрезка текста для заголовка (первые 70 символов)
        title = post['text'][:70] + '...' if len(post['text']) > 70 else post['text']
        # Обрезка текста для карточки (первые 150 символов)
        text_preview = post['text'][:150] + '...' if len(post['text']) > 150 else post['text']
        
        # Форматирование даты
        date_obj = datetime.fromisoformat(post['date'])
        date_str = date_obj.strftime('%d.%m.%Y %H:%M')
        
        # Изображение
        if post.get('image_url'):
            img_html = f'<img src="{post["image_url"]}" alt="News image" loading="lazy">'
        else:
            img_html = '<div class="no-image">📄</div>'
        
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

if __name__ == '__main__':
    asyncio.run(parse_channel())
