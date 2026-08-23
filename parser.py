import os
import json
import requests
from datetime import datetime
import re
import base64

# Получение данных из секретов
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

if not BOT_TOKEN or not CHANNEL_ID:
    print("❌ Ошибка: TELEGRAM_BOT_TOKEN или TELEGRAM_CHANNEL_ID не установлены")
    exit(1)

# URL для API Telegram
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def get_channel_posts():
    """Получение последних постов из канала через Bot API"""
    posts = []
    
    # Определяем chat_id
    chat_id = CHANNEL_ID
    if CHANNEL_ID.startswith('@'):
        chat_id = CHANNEL_ID
    else:
        try:
            # Если это числовой ID, используем как есть
            int(CHANNEL_ID)
        except ValueError:
            # Если не число, возможно это username без @
            chat_id = f"@{CHANNEL_ID}" if not CHANNEL_ID.startswith('@') else CHANNEL_ID
    
    print(f"📡 Подключение к каналу: {chat_id}")
    
    try:
        # Получаем обновления из канала
        url = f"{API_URL}/getUpdates"
        params = {
            'chat_id': chat_id,
            'limit': 40
        }
        
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if not data.get('ok'):
            print(f"❌ Ошибка API: {data.get('description', 'Unknown error')}")
            return []
        
        updates = data.get('result', [])
        print(f"📊 Получено {len(updates)} обновлений")
        
        # Если обновлений нет, пробуем другой метод
        if not updates:
            print("⚠️ Нет обновлений, пробуем прямой запрос к каналу...")
            return get_channel_messages_direct()
        
        # Обрабатываем обновления
        for update in updates:
            message = update.get('message')
            if not message:
                continue
            
            # Пропускаем служебные сообщения
            text = message.get('text', '')
            if text and text.startswith('/'):
                continue
            
            post = {
                'id': message.get('message_id'),
                'date': datetime.fromtimestamp(message.get('date')).isoformat(),
                'text': text,
                'image_url': None
            }
            
            # Проверяем наличие фото
            if 'photo' in message:
                try:
                    # Берем самое большое фото
                    photo = message['photo'][-1]
                    file_id = photo.get('file_id')
                    if file_id:
                        # Получаем ссылку на файл
                        file_url = f"{API_URL}/getFile"
                        file_response = requests.get(file_url, params={'file_id': file_id})
                        file_data = file_response.json()
                        if file_data.get('ok'):
                            file_path = file_data['result'].get('file_path')
                            if file_path:
                                # Скачиваем фото
                                download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                                img_response = requests.get(download_url)
                                if img_response.status_code == 200:
                                    # Сохраняем в assets
                                    os.makedirs('assets', exist_ok=True)
                                    filename = f"assets/post_{post['id']}.jpg"
                                    with open(filename, 'wb') as f:
                                        f.write(img_response.content)
                                    post['image_url'] = filename
                                    print(f"📸 Загружено фото: {filename}")
                except Exception as e:
                    print(f"⚠️ Ошибка загрузки фото: {e}")
            
            posts.append(post)
            print(f"✅ Обработан пост #{len(posts)} (ID: {post['id']})")
        
        return posts
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_channel_messages_direct():
    """Альтернативный метод - прямой запрос к каналу"""
    posts = []
    
    # Используем метод forwardMessage для получения сообщений
    url = f"{API_URL}/getChat"
    params = {'chat_id': CHANNEL_ID}
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data.get('ok'):
            print(f"✅ Канал найден: {data['result'].get('title', 'Unknown')}")
    except:
        pass
    
    # Пробуем получить сообщения через метод getUpdates с offset
    url = f"{API_URL}/getUpdates"
    params = {
        'limit': 40,
        'allowed_updates': ['message']
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if not data.get('ok'):
        print(f"❌ Ошибка: {data.get('description')}")
        return []
    
    updates = data.get('result', [])
    
    for update in updates:
        message = update.get('message')
        if not message:
            continue
        
        # Проверяем, что сообщение из нужного канала
        chat = message.get('chat', {})
        chat_id_str = str(chat.get('id', ''))
        channel_id_str = str(CHANNEL_ID).replace('-100', '').replace('@', '')
        
        # Если ID не совпадают, пропускаем
        if channel_id_str not in chat_id_str and CHANNEL_ID not in str(chat.get('username', '')):
            continue
        
        text = message.get('text', '')
        if text and text.startswith('/'):
            continue
        
        post = {
            'id': message.get('message_id'),
            'date': datetime.fromtimestamp(message.get('date')).isoformat(),
            'text': text,
            'image_url': None
        }
        
        # Проверяем наличие фото
        if 'photo' in message:
            try:
                photo = message['photo'][-1]
                file_id = photo.get('file_id')
                if file_id:
                    file_url = f"{API_URL}/getFile"
                    file_response = requests.get(file_url, params={'file_id': file_id})
                    file_data = file_response.json()
                    if file_data.get('ok'):
                        file_path = file_data['result'].get('file_path')
                        if file_path:
                            download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                            img_response = requests.get(download_url)
                            if img_response.status_code == 200:
                                os.makedirs('assets', exist_ok=True)
                                filename = f"assets/post_{post['id']}.jpg"
                                with open(filename, 'wb') as f:
                                    f.write(img_response.content)
                                post['image_url'] = filename
                                print(f"📸 Загружено фото: {filename}")
            except Exception as e:
                print(f"⚠️ Ошибка загрузки фото: {e}")
        
        posts.append(post)
        print(f"✅ Обработан пост #{len(posts)} (ID: {post['id']})")
    
    return posts

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
        
        try:
            date_obj = datetime.fromisoformat(post['date'])
            date_str = date_obj.strftime('%d.%m.%Y %H:%M')
        except:
            date_str = post['date']
        
        if post.get('image_url'):
            img_html = f'<img src="{post["image_url"]}" alt="News image" loading="lazy">'
        else:
            img_html = '<div class="no-image">📄</div>'
        
        # Экранируем опасные символы
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
    print("🚀 Запуск парсера...")
    posts = get_channel_posts()
    
    if posts:
        print(f"✅ Получено {len(posts)} постов")
        # Сохраняем в JSON
        with open('posts.json', 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        print("💾 Сохранен posts.json")
        
        generate_html(posts)
        print("✅ Парсинг завершен успешно!")
    else:
        print("❌ Не удалось получить посты")
        
        # Создаем тестовый HTML
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write('''<!DOCTYPE html>
<html>
<head><title>Novikon</title></head>
<body>
<h1>📰 Novikon</h1>
<p>Сайт настраивается. Первые новости появятся в ближайшее время.</p>
<p>Проверьте настройки бота и канала.</p>
</body>
</html>''')
        print("🌐 Создан тестовый index.html")
