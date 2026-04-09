from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, jsonify, redirect, url_for, abort
import sqlite3
from datetime import datetime
import json
import os
from functools import wraps


app = Flask(__name__)

# Конфигурация
SECRET_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'wedding2026')  # Через переменные окружения безопаснее
DATABASE = 'wedding.db'


# ===== ДЕКОРАТОР ДЛЯ ЗАЩИТЫ АДМИНКИ =====
def admin_required(f):
    """Декоратор для проверки пароля админ-панели"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        password = request.args.get('password')
        if password != SECRET_PASSWORD:
            abort(401)  # Используем abort вместо возврата строки
        return f(*args, **kwargs)

    return decorated_function


# ===== РАБОТА С БАЗОЙ ДАННЫХ =====
def get_db():
    """Подключение к БД с обработкой ошибок"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Ошибка подключения к БД: {e}")
        return None


def execute_query(query, params=(), fetch_one=False, fetch_all=False):
    """Универсальная функция для выполнения запросов к БД"""
    conn = get_db()
    if not conn:
        return None if fetch_one or fetch_all else False

    cursor = conn.cursor()
    try:
        cursor.execute(query, params)

        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.lastrowid

        conn.close()
        return result
    except sqlite3.Error as e:
        print(f"Ошибка запроса: {e}")
        conn.close()
        return None if fetch_one or fetch_all else False


# ===== МАРШРУТЫ =====
@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')


@app.route('/rsvp', methods=['GET', 'POST'])
def rsvp():
    """Страница подтверждения присутствия"""
    if request.method == 'POST':
        guest_name = request.form.get('guest_name', '').strip()

        # Валидация имени
        if not guest_name:
            return "Пожалуйста, укажите ваше имя", 400

        if len(guest_name) > 100:
            return "Имя слишком длинное (максимум 100 символов)", 400

        # Сбор данных из формы с безопасными значениями по умолчанию
        data = {
            'guest_name': guest_name,
            'attending': request.form.get('attending'),
            'guests_count': int(request.form.get('guests_count', 1)),
            'gift_type': request.form.get('gift_type', 'money'),
            'message': request.form.get('message', '').strip()[:500],  # Ограничение длины
            'food_no_meat': 1 if request.form.get('food_no_meat') else 0,
            'food_no_fish': 1 if request.form.get('food_no_fish') else 0,
            'food_vegan': 1 if request.form.get('food_vegan') else 0,
            'alcohol_red': 1 if request.form.get('alcohol_red') else 0,
            'alcohol_white': 1 if request.form.get('alcohol_white') else 0,
            'alcohol_champagne': 1 if request.form.get('alcohol_champagne') else 0,
            'alcohol_whiskey': 1 if request.form.get('alcohol_whiskey') else 0,
            'alcohol_vodka': 1 if request.form.get('alcohol_vodka') else 0,
            'alcohol_none': 1 if request.form.get('alcohol_none') else 0
        }

        # Проверка обязательного поля attending
        if data['attending'] not in ['yes', 'no']:
            return "Некорректное значение поля присутствия", 400

        # Вставка в БД
        query = '''
                INSERT INTO rsvp_responses (guest_name, attending, guests_count, gift_type, message, \
                                            food_no_meat, food_no_fish, food_vegan, \
                                            alcohol_red, alcohol_white, alcohol_champagne, \
                                            alcohol_whiskey, alcohol_vodka, alcohol_none) \
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) \
                '''

        result = execute_query(query, (
            data['guest_name'], data['attending'], data['guests_count'],
            data['gift_type'], data['message'], data['food_no_meat'],
            data['food_no_fish'], data['food_vegan'], data['alcohol_red'],
            data['alcohol_white'], data['alcohol_champagne'], data['alcohol_whiskey'],
            data['alcohol_vodka'], data['alcohol_none']
        ))

        if not result and result != 0:
            return "Ошибка при сохранении ответа. Пожалуйста, попробуйте позже.", 500

        return render_template('thanks.html', name=guest_name)

    return render_template('rsvp.html')


# ===== ФИЛЬТР ДЛЯ ШАБЛОНОВ =====
def pluralize_filter(value, forms):
    """Формирует правильное окончание для русских слов"""
    try:
        value = int(value)
    except (ValueError, TypeError):
        return str(value)

    forms_list = forms.split(',')
    if len(forms_list) != 3:
        return str(value)

    if value % 10 == 1 and value % 100 != 11:
        return forms_list[0]
    elif value % 10 in (2, 3, 4) and value % 100 not in (12, 13, 14):
        return forms_list[1]
    else:
        return forms_list[2]


app.jinja_env.filters['pluralize'] = pluralize_filter


# ===== АДМИН-ПАНЕЛЬ =====
@app.route('/admin')
@admin_required
def admin():
    """Админ-панель с просмотром ответов"""
    conn = get_db()
    if not conn:
        return "Ошибка подключения к базе данных", 500

    cursor = conn.cursor()
    cursor.execute('SELECT * FROM rsvp_responses ORDER BY created_at DESC')
    responses = cursor.fetchall()
    conn.close()

    # Подсчёт статистики
    total_responses = len(responses)
    total_guests = 0
    attending_guests = 0

    for r in responses:
        guests_count = r['guests_count'] if r['guests_count'] else 1
        total_guests += guests_count
        if r['attending'] == 'yes':
            attending_guests += guests_count

    not_attending_guests = total_guests - attending_guests

    return render_template('admin.html',
                           responses=responses,
                           total_responses=total_responses,
                           total_guests=total_guests,
                           attending_guests=attending_guests,
                           not_attending_guests=not_attending_guests)


@app.route('/admin/delete/<int:response_id>')
@admin_required
def delete_response(response_id):
    """Удаление ответа по ID"""
    conn = get_db()
    if not conn:
        return "Ошибка подключения к базе данных", 500

    cursor = conn.cursor()
    cursor.execute('DELETE FROM rsvp_responses WHERE id = ?', (response_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()

    if affected == 0:
        return "Ответ не найден", 404

    return redirect(url_for('admin', password=SECRET_PASSWORD))


@app.route('/admin/export')
@admin_required
def export_json():
    """Экспорт всех ответов в JSON"""
    conn = get_db()
    if not conn:
        return "Ошибка подключения к базе данных", 500

    cursor = conn.cursor()
    cursor.execute('SELECT * FROM rsvp_responses ORDER BY created_at DESC')
    responses = cursor.fetchall()
    conn.close()

    data = []
    for row in responses:
        item = dict(row)
        # Преобразуем created_at в строку для JSON
        if 'created_at' in item and item['created_at']:
            item['created_at'] = str(item['created_at'])
        data.append(item)

    return app.response_class(
        response=json.dumps(data, ensure_ascii=False, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment; filename=wedding_responses.json'}
    )


# ===== ОБРАБОТЧИКИ ОШИБОК =====
@app.errorhandler(401)
def unauthorized(error):
    """Страница при ошибке доступа"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Доступ запрещён</title>
        <style>
            body { font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 0; }
            .card { background: white; padding: 40px; border-radius: 20px; text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.2); }
            input { padding: 10px; margin: 10px; border-radius: 10px; border: 1px solid #ddd; width: 200px; }
            button { background: #764ba2; color: white; border: none; padding: 10px 30px; border-radius: 25px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>🔒 Доступ к админ-панели</h2>
            <p>Введите пароль для просмотра ответов гостей</p>
            <form method="get">
                <input type="password" name="password" placeholder="Пароль" autofocus>
                <button type="submit">Войти</button>
            </form>
        </div>
    </body>
    </html>
    ''', 401


@app.errorhandler(404)
def not_found(error):
    """Страница 404"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Страница 500"""
    return "<h1>Внутренняя ошибка сервера</h1><p>Пожалуйста, попробуйте позже.</p>", 500


if __name__ == '__main__':
    app.run(debug=True)