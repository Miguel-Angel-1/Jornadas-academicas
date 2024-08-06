from flask import Flask, render_template, request, redirect, url_for, session, flash
import bcrypt
import mysql.connector

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Cambia esto por una clave segura

db_config = {
    'user': 'root',
    'host': 'localhost',
    'database': 'mi_base_de_datos'
}

def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, username, password, role FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                session['user_id'] = user['id']
                session['user_role'] = user['role']
                if user['role'] == 'profesor':
                    return redirect(url_for('profesor_dashboard'))
                elif user['role'] == 'alumno':
                    return redirect(url_for('alumno_dashboard'))
            else:
                flash('Nombre de usuario o contraseña incorrectos', 'error')
        except mysql.connector.Error as err:
            flash(f"Error en la base de datos: {err}", 'error')
    return render_template('login.html')

@app.route('/profesor_dashboard', methods=['GET', 'POST'])
def profesor_dashboard():
    if 'user_id' in session and session['user_role'] == 'profesor':
        if request.method == 'POST':
            if 'add_column' in request.form:
                column_name = request.form['column_name']
                if column_name:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("SHOW COLUMNS FROM tabla_profesores")
                        columns = [row[0] for row in cursor.fetchall()]

                        # Añadir nueva columna antes de 'Conteo'
                        if 'Conteo' in columns:
                            conteo_index = columns.index('Conteo')
                            cursor.execute(f"ALTER TABLE tabla_profesores ADD COLUMN `{column_name}` VARCHAR(255) AFTER `{columns[conteo_index-1]}`")
                        else:
                            cursor.execute(f"ALTER TABLE tabla_profesores ADD COLUMN `{column_name}` VARCHAR(255)")

                        conn.commit()
                        cursor.close()
                        conn.close()
                        flash('Columna agregada con éxito', 'success')
                    except mysql.connector.Error as err:
                        flash(f"Error en la base de datos: {err}", 'error')
            elif 'remove_column' in request.form:
                column_name = request.form['column_name']
                if column_name:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute(f"ALTER TABLE tabla_profesores DROP COLUMN `{column_name}`")
                        conn.commit()
                        cursor.close()
                        conn.close()
                        flash('Columna eliminada con éxito', 'success')
                    except mysql.connector.Error as err:
                        flash(f"Error en la base de datos: {err}", 'error')

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SHOW COLUMNS FROM tabla_profesores")
            columns = [row['Field'] for row in cursor.fetchall() if row['Field'] not in ['id', 'Nombres', 'aP', 'aM', 'ate', 'est']]
            
            # Ordenar las columnas
            if 'Conteo' in columns:
                conteo_index = columns.index('Conteo')
                columns = columns[:conteo_index]  # Obtener las columnas antes de 'Conteo'
                columns.append('Conteo')  # Asegurarse de que 'Conteo' esté en la lista

            cursor.execute("SELECT * FROM tabla_profesores")
            data = cursor.fetchall()
            cursor.close()
            conn.close()

            # Contar valores no nulos en columnas después de 'Nombres' y antes de 'Conteo'
            for row in data:
                count = sum(1 for key in row.keys() if key not in ['id', 'Nombres', 'aP', 'aM', 'ate', 'est', 'Conteo'] and row[key] is not None)
                row['Conteo'] = count

            # Insertar la columna en la posición correcta para el HTML
            columns = ['id', 'aP', 'aM', 'Nombres'] + columns + ['ate', 'est']
            
            return render_template('professor.html', data=data, columns=columns)
        except mysql.connector.Error as err:
            flash(f"Error en la base de datos: {err}", 'error')
            return redirect(url_for('login'))
    return redirect(url_for('login'))



















# Ruta para la edición del registro
@app.route('/edit_record/<int:record_id>', methods=['GET', 'POST'])
def edit_record(record_id):
    if 'user_id' in session and session['user_role'] == 'profesor':
        if request.method == 'POST':
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                for column, value in request.form.items():
                    # Evita actualizar la columna `id`
                    if column != 'id':
                        cursor.execute(f"UPDATE tabla_profesores SET {column} = %s WHERE id = %s", (value, record_id))
                conn.commit()
                cursor.close()
                conn.close()
                flash('Cambios guardados con éxito', 'success')
                return redirect(url_for('profesor_dashboard'))
            except mysql.connector.Error as err:
                flash(f"Error en la base de datos: {err}", 'error')

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)  # Usa dictionary=True para obtener resultados como diccionario
            cursor.execute("SELECT * FROM tabla_profesores WHERE id = %s", (record_id,))
            record = cursor.fetchone()
            cursor.close()
            conn.close()
            if record:
                return render_template('edit_record.html', record=record)
            else:
                flash('Registro no encontrado', 'error')
                return redirect(url_for('profesor_dashboard'))
        except mysql.connector.Error as err:
            flash(f"Error en la base de datos: {err}", 'error')
            return redirect(url_for('profesor_dashboard'))
    return redirect(url_for('login'))



# Ruta para eliminar un valor
@app.route('/delete_value/<int:record_id>', methods=['POST'])
def delete_value(record_id):
    column_name = request.form.get('column_name')  # Usar request.form para obtener el nombre de la columna
    if 'user_id' in session and session['user_role'] == 'profesor':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(f"UPDATE tabla_profesores SET `{column_name}` = NULL WHERE id = %s", (record_id,))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Valor eliminado con éxito', 'success')
        except mysql.connector.Error as err:
            flash(f"Error en la base de datos: {err}", 'error')
        return redirect(url_for('profesor_dashboard'))
    return redirect(url_for('login'))



@app.route('/alumno_dashboard')
def alumno_dashboard():
    if 'user_id' in session and session['user_role'] == 'alumno':
        return render_template('student.html')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_role', None)
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)