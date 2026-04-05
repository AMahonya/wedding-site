from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
from datetime import datetime
import json

app = Flask(__name__)


def get_db():
    conn = sqlite3.connect('wedding.db')
    conn.row_factory = sqlite3.Row
    return conn


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


# Добавляем фильтр pluralize
def pluralize_filter(value, forms):
    """Формирует правильное окончание для русских слов"""
    if not isinstance(value, int):
        value = int(value) if value.isdigit() else 0

    forms_list = forms.split(',')
    if len(forms_list) != 3:
        return str(value)

    if value % 10 == 1 and value % 100 != 11:
        return forms_list[0]
    elif value % 10 in (2, 3, 4) and value % 100 not in (12, 13, 14):
        return forms_list[1]
    else:
        return forms_list[2]


# Регистрируем фильтр
app.jinja_env.filters['pluralize'] = pluralize_filter


@app.route('/admin')
def admin():
    password = request.args.get('password')
    if password != 'wedding2026':
        return "Доступ запрещён", 401

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM rsvp_responses ORDER BY created_at DESC')
    responses = cursor.fetchall()
    conn.close()

    # Подсчёт статистики с учётом количества гостей
    total_guests = 0
    attending_guests = 0
    total_responses = len(responses)

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
def delete_response(response_id):
    password = request.args.get('password')
    if password != 'wedding2026':
        return "Доступ запрещён", 401

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM rsvp_responses WHERE id = ?', (response_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('admin', password=password))


@app.route('/admin/export')
def export_json():
    password = request.args.get('password')
    if password != 'wedding2026':
        return "Доступ запрещён", 401

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