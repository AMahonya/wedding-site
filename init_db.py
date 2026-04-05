import sqlite3

def init_db():
    conn = sqlite3.connect('wedding.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rsvp_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_name TEXT NOT NULL,
            attending TEXT NOT NULL,
            guests_count INTEGER DEFAULT 1,
            gift_type TEXT,
            message TEXT,
            food_no_meat BOOLEAN DEFAULT 0,
            food_no_fish BOOLEAN DEFAULT 0,
            food_vegan BOOLEAN DEFAULT 0,
            alcohol_red BOOLEAN DEFAULT 0,
            alcohol_white BOOLEAN DEFAULT 0,
            alcohol_champagne BOOLEAN DEFAULT 0,
            alcohol_whiskey BOOLEAN DEFAULT 0,
            alcohol_vodka BOOLEAN DEFAULT 0,
            alcohol_none BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ База данных создана!")

if __name__ == '__main__':
    init_db()