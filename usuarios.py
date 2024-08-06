from flask_bcrypt import Bcrypt
import mysql.connector

bcrypt = Bcrypt()

db_config = {
    'user': 'root',
    'host': 'localhost',
    'database': 'mi_base_de_datos'
}

def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn

def create_user(username, password, role):
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (username, password, role) VALUES (%s, %s, %s)', (username, hashed_password, role))
    conn.commit()
    cursor.close()
    conn.close()

# Crear usuarios
create_user('profesor1', 'cont1', 'profesor')
create_user('alumno1', 'cont1', 'alumno')
