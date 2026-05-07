import os
import io
import re
import json
import random
import string
import datetime
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
import qrcode
import requests

app = Flask(__name__)
app.secret_key = os.urandom(24)

TEMPLATE_PATH = 'template.png'

# --- Настройки координат, масок и шрифтов ---
TICKET_PRESET = {
    "poster": {
        "mask": [
            0,
            0,
            0,
            0
        ],
        "pos": [
            25,
            23
        ],
        "size": [
            108,
            153
        ],
        "bg": "#E5EED0"
    },
    "title": {
        "mask": [
            0,
            0,
            0,
            0
        ],
        "pos": [
            170,
            22
        ],
        "bg": "#c1dea4",
        "font_size": 43,
        "bold": False,
        "color": "black"
    },
    "year_genres": {
        "mask": [
            0,
            0,
            0,
            0
        ],
        "pos": [
            167,
            78
        ],
        "bg": "#E5EED0",
        "font_size": 23,
        "bold": False,
        "color": "#2f3f29"
    },
    "duration": {
        "mask": [
            0,
            0,
            0,
            0
        ],
        "pos": [
            164,
            114
        ],
        "bg": "#E5EED0",
        "font_size": 19,
        "bold": False,
        "color": "#333333"
    },
    "age": {
        "mask": [
            0,
            0,
            0,
            0
        ],
        "pos": [
            0,
            -100
        ],
        "bg": "#FFC107",
        "font_size": 35,
        "bold": True,
        "color": "white"
    },
    "time": {
        "mask": [
            20,
            240,
            210,
            300
        ],
        "pos": [
            15,
            227
        ],
        "bg": "white",
        "font_size": 76,
        "bold": True,
        "color": "black"
    },
    "date": {
        "mask": [
            250,
            240,
            350,
            266
        ],
        "pos": [
            256,
            235
        ],
        "bg": "white",
        "font_size": 35,
        "bold": False,
        "color": "#000000"
    },
    "weekday": {
        "mask": [
            250,
            270,
            400,
            300
        ],
        "pos": [
            256,
            273
        ],
        "bg": "white",
        "font_size": 26,
        "bold": False,
        "color": "#666666"
    },
    "hall": {
        "mask": [
            0,
            0,
            0,
            0
        ],
        "pos": [
            0,
            -100
        ],
        "bg": "white",
        "font_size": 35,
        "bold": False,
        "color": "black"
    },
    "row_seat": {
        "mask": [
            20,
            430,
            200,
            455
        ],
        "pos": [
            20,
            429
        ],
        "bg": "white",
        "font_size": 23,
        "bold": False,
        "color": "#333333"
    },
    "price": {
        "mask": [
            550,
            430,
            630,
            460
        ],
        "pos": [
            553,
            430
        ],
        "bg": "white",
        "font_size": 22,
        "bold": False,
        "color": "#333333"
    },
    "total": {
        "mask": [
            0,
            0,
            0,
            0
        ],
        "pos": [
            0,
            -100
        ],
        "bg": "white",
        "font_size": 32,
        "bold": False,
        "color": "black"
    },
    "total_price": {
        "mask": [
            540,
            480,
            630,
            500
        ],
        "pos": [
            540,
            474
        ],
        "bg": "white",
        "font_size": 27,
        "bold": False,
        "color": "black"
    },
    "pushkin": {
        "mask": [
            20,
            545,
            500,
            566
        ],
        "pos": [
            24,
            540
        ],
        "bg": "white",
        "font_size": 26,
        "bold": False,
        "color": "#333333"
    },
    "fio": {
        "mask": [
            20,
            580,
            430,
            600
        ],
        "pos": [
            25,
            577
        ],
        "bg": "white",
        "font_size": 22,
        "bold": False,
        "color": "#333333"
    },
    "email": {
        "mask": [
            20,
            605,
            330,
            625
        ],
        "pos": [
            25,
            601
        ],
        "bg": "white",
        "font_size": 22,
        "bold": False,
        "color": "#333333"
    },
    "phone": {
        "mask": [
            20,
            628,
            300,
            650
        ],
        "pos": [
            25,
            623
        ],
        "bg": "white",
        "font_size": 21,
        "bold": False,
        "color": "#333333"
    },
    "qr_box": {
        "mask": [
            745,
            425,
            985,
            665
        ],
        "pos": [
            660,
            419
        ],
        "bg": "white",
        "size": 187
    },
    "qr_code": {
        "mask": [
            700,
            615,
            810,
            633
        ],
        "pos": [
            810,
            613
        ],
        "bg": "white",
        "font_size": 24,
        "bold": True,
        "color": "black"
    }
}

def get_font(size, bold=False):
    font_names =[
        "arialbd.ttf" if bold else "arial.ttf",
        "Arial Bold.ttf" if bold else "Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf"
    ]
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except IOError:
            continue
    return ImageFont.load_default()

def get_weekday(date_str):
    months = {'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4, 'мая': 5, 'июн': 6, 'июл': 7, 'авг': 8, 'сен': 9, 'окт': 10, 'ноя': 11, 'дек': 12}
    days =['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    try:
        parts = date_str.split(' ')
        if len(parts) >= 2:
            d = int(parts[0])
            m_str = parts[1].lower()
            for ru_mon, m_num in months.items():
                if m_str.startswith(ru_mon):
                    dt = datetime.date(2026, m_num, d)
                    return days[dt.weekday()]
    except Exception:
        pass
    return ""

def parse_p24_url(url):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import time
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    data = {
        "title": "Неизвестный сеанс", "age": "12+", "poster_url": "", 
        "year_genres": "2026, Россия, Драма", "duration": "1 час 30 минут", "sessions":[]
    }
    
    try:
        driver.get(url)
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1, h2")))
        except Exception:
            pass
        time.sleep(1.5)
        html = driver.page_source
    finally:
        driver.quit()

    soup = BeautifulSoup(html, 'html.parser')
    
    h1 = soup.find(['h1', 'h2'])
    if h1:
        title_text = ''.join([t for t in h1.find_all(string=True, recursive=False)]).strip()
        if title_text: data['title'] = title_text
        age_el = h1.find(attrs={'data-age': True})
        if age_el: data['age'] = age_el.get('data-age', '12+')

    poster_container = soup.find(attrs={'data-alt': True})
    if poster_container:
        img = poster_container.find('img')
        if img:
            if img.has_attr('srcset'):
                urls = [part.strip().split(' ')[0] for part in img['srcset'].split(',')]
                data['poster_url'] = urls[-1]
            elif img.has_attr('src'):
                data['poster_url'] = img['src']

    for small in soup.find_all('small'):
        text = small.get_text(strip=True).lower()
        if text in['хроно', 'продолжительность']:
            val_div = small.find_next_sibling('div')
            if val_div: data['duration'] = val_div.get_text(strip=True)

    tags_list = []
    for tag_el in soup.find_all('div', class_='tag'):
        txt = tag_el.get_text(strip=True)
        if txt and txt.lower() not in ["в прокате", ""]:
            # Делаем первую букву каждого тега заглавной, не трогая остальные (чтобы сохранить "США" и т.д.)
            txt = txt[0].upper() + txt[1:]
            
            if txt not in tags_list:
                tags_list.append(txt)
    
    if tags_list:
        # Убираем .capitalize() здесь, так как теги уже отформатированы
        data['year_genres'] = ", ".join(tags_list[:5])

    for a in soup.find_all('a'):
        href = a.get('href', '')
        if '/event/' not in href.lower():
            continue
        
        a_text = a.get_text(separator=' ')
        
        time_match = re.search(r'\b(\d{1,2})\s*:\s*(\d{2})\b', a_text)
        if not time_match: continue
        time_str = f"{time_match.group(1)}:{time_match.group(2)}"
        
        price_str = "0 ₽"
        for string_part in a.stripped_strings:
            if '₽' in string_part:
                price_str = string_part.replace('\u2009', ' ').strip()
                break
        
        h4 = a.find_previous('h4')
        date_str = h4.get_text(strip=True) if h4 else "Неизвестная дата"
        weekday_str = get_weekday(date_str)
        
        data['sessions'].append({
            'id': str(len(data['sessions'])),
            'date': date_str,
            'weekday': weekday_str,
            'time': time_str,
            'price': price_str
        })

    return data

def draw_masked_element(draw, config, text=None, is_image=False):
    # Явно приводим маску к tuple во избежание конфликтов Pillow
    draw.rectangle(tuple(config['mask']), fill=config['bg'])
    if not is_image and text:
        font = get_font(config['font_size'], config['bold'])
        draw.text(tuple(config['pos']), text, fill=config['color'], font=font)

def process_ticket(data, custom_preset=None):
    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(f"Файл {TEMPLATE_PATH} не найден в корне!")

    img = Image.open(TEMPLATE_PATH).convert('RGB')
    draw = ImageDraw.Draw(img)

    preset = custom_preset if custom_preset else TICKET_PRESET

    draw_masked_element(draw, preset['poster'], is_image=True)
    if data.get('poster_url'):
        try:
            p_res = requests.get(data['poster_url'], timeout=5)
            poster = Image.open(io.BytesIO(p_res.content)).convert('RGB')
            poster = poster.resize(tuple(preset['poster']['size']), Image.Resampling.LANCZOS)
            img.paste(poster, tuple(preset['poster']['pos']))
        except Exception as e:
            print("Ошибка загрузки обложки:", e)

    draw_masked_element(draw, preset['title'], data['title'])
    draw_masked_element(draw, preset['year_genres'], data['year_genres'])
    draw_masked_element(draw, preset['duration'], data['duration'])
    draw_masked_element(draw, preset['age'], data['age'])
    
    draw_masked_element(draw, preset['time'], data['time'])
    draw_masked_element(draw, preset['date'], data['date'])
    draw_masked_element(draw, preset['weekday'], data['weekday'])
    draw_masked_element(draw, preset['hall'], "Звёздный зал")
    
    row_seat_str = f"{data['row']} ряд {data['seat']} место"
    draw_masked_element(draw, preset['row_seat'], row_seat_str)
    draw_masked_element(draw, preset['price'], data['price'])
    draw_masked_element(draw, preset['total'], "Итого")
    draw_masked_element(draw, preset['total_price'], data['price'])

    draw_masked_element(draw, preset['pushkin'], "В рамках программы «Пушкинская карта»")
    draw_masked_element(draw, preset['fio'], f"ФИО: {data['name']}")
    draw_masked_element(draw, preset['email'], f"Email: {data['email']}")
    draw_masked_element(draw, preset['phone'], f"Телефон: {data['phone']}")

    numeric_code = ''.join(random.choices(string.digits, k=6))
    qr = qrcode.QRCode(version=1, box_size=10, border=0)
    qr.add_data(numeric_code)
    qr.make(fit=True)
    qr_size = preset['qr_box']['size']
    qr_img = qr.make_image(fill_color="black", back_color="white").resize((qr_size, qr_size))
    
    draw_masked_element(draw, preset['qr_box'], is_image=True)
    img.paste(qr_img, tuple(preset['qr_box']['pos']))

    draw_masked_element(draw, preset['qr_code'], is_image=True)
    font_qr = get_font(preset['qr_code']['font_size'], preset['qr_code']['bold'])
    bbox = draw.textbbox((0, 0), numeric_code, font=font_qr)
    text_w = bbox[2] - bbox[0]
    text_x = preset['qr_box']['pos'][0] + (qr_size - text_w) / 2
    draw.text((text_x, preset['qr_code']['pos'][1]), numeric_code, fill=preset['qr_code']['color'], font=font_qr)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

@app.route('/')
def index():
    # Отдаем JSON в шаблон
    return render_template('index.html', preset_json=json.dumps(TICKET_PRESET, ensure_ascii=False))

@app.route('/api/fetch-info', methods=['POST'])
def fetch_info():
    try:
        url = request.json.get('url', '')
        if not url: return jsonify({"error": "Ссылка обязательна"}), 400
        parsed_data = parse_p24_url(url)
        if not parsed_data['sessions']:
            return jsonify({"error": "Сеансы не найдены. Убедитесь, что ссылка корректна."}), 404
        return jsonify(parsed_data)
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-ticket', methods=['POST'])
def generate_ticket():
    try:
        data = request.json
        custom_preset = data.get('preset') 
        result_buffer = process_ticket(data, custom_preset)
        return send_file(result_buffer, mimetype='image/png')
    except Exception as e:
        print(f"Ошибка генерации: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=True)