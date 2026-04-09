from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3
from datetime import datetime
import json
import os
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'секретный_ключ_для_сессии')

# Конфигурация
SECRET_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'wedding2026')
DATABASE = 'wedding.db'


# ===== ДЕКОРАТОР ДЛЯ ЗАЩИТЫ АДМИНКИ (с проверкой сессии) =====
def admin_required(f):
    """Декоратор для проверки авторизации в админ-панели"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Проверяем сессию
        if session.get('admin_logged_in'):
            return f(*args, **kwargs)

        # Проверяем пароль в URL (для обратной совместимости)
        password = request.args.get('password')
        if password and password == SECRET_PASSWORD:
            session['admin_logged_in'] = True
            return f(*args, **kwargs)

        # Если это AJAX запрос, возвращаем 401
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return "Unauthorized", 401

        # Иначе показываем форму входа
        return render_template('admin_login.html')

    return decorated_function


@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    if password == SECRET_PASSWORD:
        session['admin_logged_in'] = True
        return redirect(url_for('admin'))
    return "Неверный пароль", 401


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login_page'))


@app.route('/admin/login-page')
def admin_login_page():
    return render_template('admin_login.html')


# ===== ОСТАЛЬНЫЕ МАРШРУТЫ =====
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/rsvp', methods=['GET', 'POST'])
def rsvp():
    if request.method == 'POST':
        guest_name = request.form.get('guest_name', '').strip()

        if not guest_name:
            return "Пожалуйста, укажите ваше имя", 400

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
                       INSERT INTO rsvp_responses (guest_name, attending, guests_count, gift_type, message,
                                                   food_no_meat, food_no_fish, food_vegan,
                                                   alcohol_red, alcohol_white, alcohol_champagne,
                                                   alcohol_whiskey, alcohol_vodka, alcohol_none)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ''', (
                           guest_name,
                           request.form.get('attending'),
                           request.form.get('guests_count', 1),
                           request.form.get('gift_type'),
                           request.form.get('message', ''),
                           1 if request.form.get('food_no_meat') else 0,
                           1 if request.form.get('food_no_fish') else 0,
                           1 if request.form.get('food_vegan') else 0,
                           1 if request.form.get('alcohol_red') else 0,
                           1 if request.form.get('alcohol_white') else 0,
                           1 if request.form.get('alcohol_champagne') else 0,
                           1 if request.form.get('alcohol_whiskey') else 0,
                           1 if request.form.get('alcohol_vodka') else 0,
                           1 if request.form.get('alcohol_none') else 0
                       ))

        conn.commit()
        conn.close()

        return render_template('thanks.html', name=guest_name)

    return render_template('rsvp.html')


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/admin')
@admin_required
def admin():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM rsvp_responses ORDER BY created_at DESC')
    responses = cursor.fetchall()
    conn.close()

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
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM rsvp_responses WHERE id = ?', (response_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()

    if affected == 0:
        return "Ответ не найден", 404

    return "", 200


@app.route('/admin/export')
@admin_required
def export_json():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM rsvp_responses ORDER BY created_at DESC')
    responses = cursor.fetchall()
    conn.close()

    data = [dict(row) for row in responses]
    return app.response_class(
        response=json.dumps(data, ensure_ascii=False, indent=2, default=str),
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment; filename=wedding_responses.json'}
    )


if __name__ == '__main__':
    app.run(debug=True)