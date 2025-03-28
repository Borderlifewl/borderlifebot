import sqlite3

DB_FILE = 'warns.db'

# Fonction pour se connecter à la base de données SQLite
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Permet d'accéder aux résultats comme des dictionnaires
    return conn

# Fonction pour créer la table 'warns' si elle n'existe pas
def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS warns (
                        member_id INTEGER PRIMARY KEY,
                        warn_count INTEGER NOT NULL DEFAULT 0
                    )''')
    
    conn.commit()
    conn.close()

# Fonction pour récupérer les avertissements d'un membre
def get_warns(member_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT warn_count FROM warns WHERE member_id = ?", (member_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row['warn_count']
    else:
        return 0  # Aucun avertissement pour ce membre

# Fonction pour ajouter un avertissement à un membre
def add_warn(member_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''INSERT INTO warns (member_id, warn_count)
                      VALUES (?, 1)
                      ON CONFLICT(member_id) 
                      DO UPDATE SET warn_count = warn_count + 1''', (member_id,))
    
    conn.commit()
    conn.close()

# Fonction pour supprimer un avertissement d'un membre
def remove_warn(member_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE warns SET warn_count = warn_count - 1 WHERE member_id = ?", (member_id,))
    conn.commit()
    conn.close()

# Fonction pour supprimer tous les avertissements d'un membre
def remove_all_warns(member_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM warns WHERE member_id = ?", (member_id,))
    conn.commit()
    conn.close()