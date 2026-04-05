from flask import Flask, render_template, request, jsonify
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

    return render_template('admin.html', responses=responses)


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