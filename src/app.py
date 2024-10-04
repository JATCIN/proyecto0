from flask import Flask, jsonify, request, session, redirect, url_for, render_template, flash
import psycopg2
import psycopg2.extras
import re
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'EYg3OS1Q1LDAljkxr8ARdvYZUhdF_kYC')

# Configuración de la base de datos
DB_HOST = os.getenv('DB_HOST', 'dpg-crk7qkm8ii6s73ej2ep0-a')
DB_NAME = os.getenv('DB_NAME', 'proyecto_db_c7i9')
DB_USER = os.getenv('DB_USER', 'proyecto_user')
DB_PASS = os.getenv('DB_PASS', 'u7UC5KMyyivMpJ8oWmPODt0DABU0h9wm')

# Conexión a la base de datos
conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, sslmode='disable')

@app.route('/')
def home():
    if 'loggedin' in session:
        return render_template('home.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/login/', methods=['GET', 'POST'])
def login():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            password_rs = account['password']
            if check_password_hash(password_rs, password):
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                return redirect(url_for('home'))
            else:
                flash('Incorrect username/password', 'error')
        else:
            flash('Incorrect username/password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        fullname = request.form['fullname']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        _hashed_password = generate_password_hash(password)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            flash('Account already exists!')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address!')
        elif not re.match(r'[A-Za-z0-9]+', username):
            flash('Username must contain only characters and numbers!')
        elif not username or not password or not email:
            flash('Please fill out the form!')
        else:
            cursor.execute("INSERT INTO users (fullname, username, password, email) VALUES (%s,%s,%s,%s)", (fullname, username, _hashed_password, email))
            conn.commit()
            flash('You have successfully registered!')
    elif request.method == 'POST':
        flash('Please fill out the form!')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/new_banco')
def new_banco():
    return render_template('new_banco.html')

@app.route('/payment', methods=['POST'])
def payment():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    forma_liquidacion = request.form.get('forma_liquidacion')
    cuenta_beneficiario = request.form.get('cuenta_beneficiario')
    beneficiario = request.form.get('beneficiario')
    plaza_beneficiario = request.form.get('plaza_beneficiario')
    pais_beneficiario = request.form.get('pais_beneficiario')
    banco = request.form.get('banco')
    aba = request.form.get('aba')
    ordenante = request.form.get('ordenante')

    if not forma_liquidacion:
        return jsonify(status='error', message='Por favor, seleccione la forma de liquidación')
    elif not cuenta_beneficiario:
        return jsonify(status='error', message='Por favor, ingrese la cuenta del beneficiario')
    elif not beneficiario:
        return jsonify(status='error', message='Por favor, ingrese el nombre del beneficiario')
    elif not plaza_beneficiario:
        return jsonify(status='error', message='Por favor, ingrese la plaza del beneficiario')
    elif not pais_beneficiario:
        return jsonify(status='error', message='Por favor, ingrese el país del beneficiario')
    elif not banco:
        return jsonify(status='error', message='Por favor, ingrese el nombre del banco')
    elif not aba:
        return jsonify(status='error', message='Por favor, ingrese el código ABA')
    elif not ordenante:
        return jsonify(status='error', message='Por favor, ingrese el nombre del ordenante')
    else:
        try:
            cursor.execute("""
                INSERT INTO payments (forma_liquidacion, cuenta_beneficiario, beneficiario, plaza_beneficiario, pais_beneficiario, banco, aba, ordenante) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (forma_liquidacion, cuenta_beneficiario, beneficiario, plaza_beneficiario, pais_beneficiario, banco, aba, ordenante))
            conn.commit()
            cursor.close()
            return jsonify(status='success', message='Registrado exitosamente')
        except Exception as e:
            cursor.close()
            return jsonify(status='error', message=str(e))

@app.route('/profile')
def profile():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM users WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        return render_template('profile.html', account=account)
    return redirect(url_for('login'))

@app.route('/list_banco')
def list_banco():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT * FROM payments')
    records = cursor.fetchall()
    return render_template('list_banco.html', records=records)

@app.route('/edit_banco/<int:record_id>')
def edit_record(record_id):
 
    return f'Edit record {record_id}'

@app.route('/delete_banco/<int:record_id>')
def delete_record(record_id):
    cursor = conn.cursor()
    cursor.execute('DELETE FROM payments WHERE id = %s', (record_id,))
    conn.commit()
    cursor.close()
    return redirect(url_for('list_banco'))

@app.route('/new_casa_de_bolsa')
def new_casa_de_bolsa():
    return render_template('new_casa_de_bolsa.html')

@app.route('/new_casa_de_bolsav2', methods=['POST'])
def new_casa_de_bolsav2():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Obtener los valores del formulario
    nombre = request.form.get('nombre')
    direccion = request.form.get('direccion')
    representante = request.form.get('representante')
    telefono_contacto = request.form.get('telefono_contacto')
    correo_contacto = request.form.get('correo_contacto')
    sitio_web = request.form.get('sitio_web')
    
    # Validar que los campos requeridos no estén vacíos
    if not nombre:
        return jsonify(status='error', message='Por favor, ingrese el nombre')
    elif not direccion:
        return jsonify(status='error', message='Por favor, ingrese la dirección')
    elif not representante:
        return jsonify(status='error', message='Por favor, ingrese el representante')
    elif not telefono_contacto:
        return jsonify(status='error', message='Por favor, ingrese el teléfono de contacto')
    elif not correo_contacto:
        return jsonify(status='error', message='Por favor, ingrese el correo de contacto')
    elif not sitio_web:
        return jsonify(status='error', message='Por favor, ingrese el sitio web')
    else:
        try:
            # Insertar los datos en la tabla `casa_de_bolsa`
            cursor.execute("""
                INSERT INTO casa_de_bolsa (nombre, direccion, representante, telefono_contacto, correo_contacto, sitio_web, borrado)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (nombre, direccion, representante, telefono_contacto, correo_contacto, sitio_web, False))  # El campo borrado se establece en false
            
            conn.commit()  # Confirmar los cambios
            cursor.close()
            return jsonify(status='success', message='Casa de bolsa registrada exitosamente')
        except Exception as e:
            cursor.close()
            return jsonify(status='error', message=str(e))
        
@app.route('/list_casa_de_bolsa')
def list_casa_de_bolsa():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT * FROM casa_de_bolsa')
    records = cursor.fetchall()
    return render_template('list_casa_de_bolsa.html', records=records)

@app.route('/delete_casa_de_bolsa/<int:record_id>', methods=['POST'])
def delete_casa_de_bolsa(record_id):
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM casa_de_bolsa WHERE id = %s', (record_id,))
        conn.commit()
        cursor.close()
        flash('Casa de Bolsa eliminada correctamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar la Casa de Bolsa: {str(e)}', 'danger')
    return redirect(url_for('list_casa_de_bolsa'))

@app.route('/list_users')
def list_users():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT * FROM users')
    records = cursor.fetchall()
    return render_template('list_users.html', records=records)

@app.route('/delete_users/<int:record_id>', methods=['POST'])
def delete_users(record_id):
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = %s', (record_id,))
        conn.commit()
        cursor.close()
        flash('Usuario eliminado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar usuario: {str(e)}', 'danger')
    return redirect(url_for('list_users '))

@app.route('/new_pact')
def new_pact():
    return render_template('new_pacto.html')

@app.route('/pacto', methods=['POST'])
def pacto():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Obtener los valores del formulario
    banco_origen = request.form.get('banco_origen')
    banco_destino = request.form.get('banco_destino')
    monto = request.form.get('monto')
    cuenta_origen = request.form.get('cuenta_origen')
    cuenta_destino = request.form.get('cuenta_destino')
    tipo_cambio = request.form.get('tipo_cambio')
    comision = request.form.get('comision')
    
    # Validar que los campos requeridos no estén vacíos
    if not banco_origen:
        return jsonify(status='error', message='Por favor, ingrese el banco de origen')
    elif not banco_destino:
        return jsonify(status='error', message='Por favor, ingrese el banco de destino')
    elif not monto:
        return jsonify(status='error', message='Por favor, ingrese el monto')
    elif not cuenta_origen:
        return jsonify(status='error', message='Por favor, ingrese la cuenta de origen')
    elif not cuenta_destino:
        return jsonify(status='error', message='Por favor, ingrese la cuenta de destino')
    elif not tipo_cambio:
        return jsonify(status='error', message='Por favor, ingrese el tipo de cambio')
    elif not comision:
        return jsonify(status='error', message='Por favor, ingrese la comisión')
    else:
        try:
            # Insertar los datos en la tabla `pacto`
            cursor.execute("""
                INSERT INTO pacto (banco_origen, banco_destino, monto, cuenta_origen, cuenta_destino, tipo_cambio, comision, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (banco_origen, banco_destino, monto, cuenta_origen, cuenta_destino, tipo_cambio, comision, True))  
            
            conn.commit()  # Confirmar los cambios
            cursor.close()
            return jsonify(status='success', message='Pacto registrado exitosamente')
        except Exception as e:
            cursor.close()
            return jsonify(status='error', message=str(e))
        
@app.route('/list_pactos')
def list_pactos():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT * FROM pacto')
    records = cursor.fetchall()
    return render_template('list_pactos.html', records=records)
    
@app.route('/delete_pacto/<int:record_id>', methods=['POST'])
def delete_pacto(record_id):
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM pacto WHERE id = %s', (record_id,))
        conn.commit()
        cursor.close()
        flash('Pacto eliminado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar Pacto: {str(e)}', 'danger')
    return redirect(url_for('list_pactos'))

@app.route('/new_transfer1')
def new_transfer1():
    if 'user_id' in session:
        print(f"User ID en la sesión: {session['user_id']}")
    else:
        print("No se encontró el user_id en la sesión")
    return render_template('new_transfer.html')

@app.route('/new_transfer', methods=['GET', 'POST'])
def new_transfer():
    if not session.get('loggedin'):  # Verifica si el usuario ha iniciado sesión
        flash('Debes iniciar sesión para acceder a esta página.', 'danger')
        return redirect(url_for('login'))  # Redirige a la página de inicio de sesión

    if request.method == 'POST':
        # Validar que los campos no estén vacíos
        origin_bank = request.form.get('origin_bank')
        destination_bank = request.form.get('destination_bank')
        origin_account = request.form.get('origin_account')
        destination_account = request.form.get('destination_account')
        amount = request.form.get('amount')
        exchange_rate = request.form.get('exchange_rate')
        commission = request.form.get('commission')

        # Verificar que no haya campos vacíos
        if all([origin_bank, destination_bank, origin_account, destination_account, amount, exchange_rate, commission]):
            try:
                # Obtener el ID del usuario desde la sesión
                user_id = session['id']
                pact_id = None  # Este campo será asignado en otra etapa

                # Crear la nueva instancia del modelo Transfer
                cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cursor.execute(""" 
                    INSERT INTO transfers (user_id, pact_id, origin_bank, destination_bank, origin_account, destination_account, amount, exchange_rate, commission, updated_at, active) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), TRUE) 
                """, (user_id, pact_id, origin_bank, destination_bank, origin_account, destination_account, float(amount), float(exchange_rate), float(commission)))

                conn.commit()
                cursor.close()

                # Redirigir a una página de éxito o lista de transferencias
                flash('Transferencia creada exitosamente', 'success')
                return redirect(url_for('transfer_list'))

            except Exception as e:
                # En caso de error en la base de datos o la lógica
                conn.rollback()
                flash(f'Ocurrió un error al crear la transferencia: {str(e)}', 'danger')
                return redirect(url_for('new_transfer'))

        else:
            # Si algún campo está vacío, mostrar mensaje de error
            flash('Todos los campos son obligatorios', 'danger')
            return redirect(url_for('new_transfer'))

    # En caso de GET, renderizamos el formulario de nueva transferencia
    return render_template('new_transfer.html')

if __name__ == "__main__":
    app.run(debug=True)

