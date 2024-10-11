from flask import Flask, jsonify, request, session, redirect, url_for, render_template, flash, send_file
from fpdf import FPDF
import io
import tempfile
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
            """, (banco_origen, banco_destino, monto, cuenta_origen, cuenta_destino, tipo_cambio, comision, 'EN PROCESO'))  
            
            conn.commit()  # Confirmar los cambios
            cursor.close()
            return jsonify(status='success', message='Pacto registrado exitosamente')
        except Exception as e:
            cursor.close()
            return jsonify(status='error', message=str(e))
        
@app.route('/list_pactos')
def list_pactos():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT * FROM pacto ORDER BY fecha_hora ASC;')
    records = cursor.fetchall()
    return render_template('list_pactos.html', records=records)
    
@app.route('/delete_pacto/<int:record_id>', methods=['POST'])
def delete_pacto(record_id):
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM pacto WHERE id_pacto = %s', (record_id,))
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
    # Verificamos si el usuario ha iniciado sesión
    if 'loggedin' in session:
        id = session['id']  # Obtenemos el user_id de la sesión
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        if request.method == 'POST':  # Procesar los datos cuando se envía el formulario
            # Recoger datos del formulario
            origin_bank = request.form.get('origin_bank')
            destination_bank = request.form.get('destination_bank')
            origin_account = request.form.get('origin_account')
            destination_account = request.form.get('destination_account')  
            amount = request.form.get('amount')  
            exchange_rate = request.form.get('exchange_rate')  
            commission = request.form.get('commission')  
           
            # Validar que los campos requeridos no estén vacíos
            if not destination_account:
                return jsonify(status='error', message='Por favor, ingrese la cuenta beneficiario')
            elif not amount:
                return jsonify(status='error', message='Por favor, ingrese el monto')
            elif not destination_bank:
                return jsonify(status='error', message='Por favor, ingrese el banco destino')
            elif not exchange_rate:
                return jsonify(status='error', message='Por favor, ingrese el tipo de cambio')
            elif not commission:
                return jsonify(status='error', message='Por favor, ingrese la comisión')
            elif not origin_bank:
                return jsonify(status='error', message='Por favor, ingrese el banco origen')
            elif not origin_account:
                return jsonify(status='error', message='Por favor, ingrese la cuenta origen')
            else:
                try:
                    # Convertir los valores numéricos a float
                    amount = float(amount)
                    exchange_rate = float(exchange_rate)
                    commission = float(commission)

                    # Insertar la nueva transferencia en la base de datos
                    cursor.execute("""
                        INSERT INTO transferencias (user_id, pacto_id, destination_account, amount, destination_bank, exchange_rate, commission, origin_bank, origin_account) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (id, None, destination_account, amount, destination_bank, exchange_rate, commission, origin_bank, origin_account))
                    
                    conn.commit()  # Confirmar los cambios
                    return jsonify(status='success', message='Transferencia realizada con éxito')
                except Exception as e:
                    conn.rollback()  # Revertir en caso de error
                    return jsonify(status='error', message=str(e))
                finally:
                    cursor.close()  # Cerrar el cursor siempre

        else:
            # Mostrar el formulario si es un GET request
            return render_template('new_transfer.html', id=id)

    else:
        # Si no ha iniciado sesión, redirigir a la página de login
        return jsonify(status='error', message='Por favor, inicia sesión para realizar una transferencia')
    
@app.route('/list_transferencias', methods=['GET'])
def list_transferencias():
    # Verificamos si el usuario ha iniciado sesión
    if 'loggedin' in session:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        try:
            cursor.execute("""
                SELECT t.*, u.fullname, u.email
                FROM transferencias t
                JOIN users u ON t.user_id = u.id;
            """)
            records = cursor.fetchall()  # Guardamos las transferencias en 'transferencias'
            
            return render_template('list_transfers.html', records=records)
        
        except Exception as e:
            return jsonify(status='error', message=str(e))
        
        finally:
            cursor.close()  # Cerrar el cursor

    else:
        return jsonify(status='error', message='Por favor, inicia sesión para ver las transferencias')
    
@app.route('/delete_transfer/<int:record_id>', methods=['POST'])
def delete_transfer(record_id):
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM transferencias WHERE id = %s', (record_id,))
        conn.commit()
        cursor.close()
        flash('Transferencia eliminada correctamente.', 'success')
    except Exception as e:
        flash(f'Error al eliminar transferencia: {str(e)}', 'danger')
    return redirect(url_for('list_transferencias'))

@app.route('/asignar_pactos', methods=['GET'])
def asignar_pactos():
    # Verificamos si el usuario ha iniciado sesión
    if 'loggedin' in session:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        try:
            # Ejecutar la consulta para obtener las transferencias con detalles del usuario
            cursor.execute("""
             SELECT t.*, u.fullname, u.email
            FROM transferencias t
            JOIN users u ON t.user_id = u.id
            WHERE t.pacto_id IS NULL;
            """)           
            records = cursor.fetchall()  # Obtener todos los registros

            cursor.execute("""
            SELECT p.* 
            FROM pacto p
            LEFT JOIN transferencias t ON p.id_pacto = t.pacto_id
            WHERE t.pacto_id IS NULL
            ORDER BY p.fecha_hora ASC;
            """)  # Consulta para obtener los pactos
            pactos = cursor.fetchall()
            
            return render_template('asignar_pactos.html', records=records, pactos=pactos)
        
        except Exception as e:
            return jsonify(status='error', message=str(e))
        
        finally:
            cursor.close()  # Cerrar el cursor

    else:
        return jsonify(status='error', message='Por favor, inicia sesión para ver las transferencias')
    
@app.route('/editar_transferencia/<int:record_id>', methods=['POST'])
def editar_transferencia(record_id):
    if 'loggedin' in session:
        pacto_id = request.form['pacto_id']  # Obtén el pacto_id del formulario enviado

        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
        try:
            # Actualizar la transferencia con el pacto seleccionado
            cursor.execute("""
                UPDATE transferencias
                SET pacto_id = %s
                WHERE id = %s
            """, (pacto_id, record_id))  # transfer_id viene de la URL y pacto_id del formulario
            
            conn.commit()  # Confirmar los cambios en la base de datos

            # Redirigir nuevamente a la página de asignación de pactos
            return redirect(url_for('asignar_pactos'))

        except Exception as e:
            return jsonify(status='error', message=str(e))

        finally:
            cursor.close()  # Cerrar el cursor

    else:
        return jsonify(status='error', message='Por favor, inicia sesión para asignar un pacto')
    

@app.route('/export-pdf', methods=['GET'])
def export_pdf():
    # Verificamos si el usuario ha iniciado sesión
    if 'loggedin' in session:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        try:
            cursor.execute("""
                SELECT t.*, u.fullname, u.email
                FROM transferencias t
                JOIN users u ON t.user_id = u.id;
            """)
            records = cursor.fetchall()  # Guardamos las transferencias en 'records'

            # Crear un PDF con los resultados en orientación horizontal
            pdf = FPDF(orientation='L', unit='mm', format='A4')  # Cambiar a 'L' para horizontal
            pdf.add_page()

            # Configurar el título y encabezado
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(300, 10, txt="Reporte Transferencias", ln=True, align='C')

            # Agregar una tabla con los datos
            pdf.set_font('Arial', 'B', 7)
            pdf.cell(22, 10, "ID Transferencia", 1)
            pdf.cell(22, 10, "Usuario", 1)
            pdf.cell(32, 10, "Email", 1)
            pdf.cell(22, 10, "Banco Origen", 1)
            pdf.cell(22, 10, "Cuenta Origen", 1)
            pdf.cell(22, 10, "Banco Destino", 1)
            pdf.cell(22, 10, "Cuenta Destino", 1)
            pdf.cell(22, 10, "Monto", 1)
            pdf.cell(22, 10, "Tipo de cambio", 1)
            pdf.cell(22, 10, "Comision", 1)
            pdf.cell(22, 10, "Fecha", 1)
            pdf.cell(22, 10, "Id pacto asignado", 1)
            pdf.ln()

            # Agregar datos al PDF
            pdf.set_font('Arial', '', 7)
            for row in records:
                pdf.cell(22, 10, str(row['id']), 1)
                pdf.cell(22, 10, row['fullname'], 1)
                pdf.cell(32, 10, row['email'], 1)
                pdf.cell(22, 10, row['origin_bank'], 1)
                pdf.cell(22, 10, row['origin_account'], 1)
                pdf.cell(22, 10, row['destination_bank'], 1)
                pdf.cell(22, 10, row['destination_account'], 1)
                pdf.cell(22, 10, str(row['amount']), 1)
                pdf.cell(22, 10, str(row['exchange_rate']), 1)
                pdf.cell(22, 10, str(row['commission']), 1)
                pdf.cell(22, 10, row['created_at'].strftime("%Y-%m-%d"), 1)
                pdf.cell(22, 10, str(row['pacto_id']), 1)
                pdf.ln()

            # Guardar el PDF en un archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                pdf.output(temp_file.name)
                temp_file.seek(0)
                temp_file_name = temp_file.name

            return send_file(temp_file_name, as_attachment=True, download_name='transferencias.pdf', mimetype='application/pdf')
        
        except Exception as e:
            return jsonify(status='error', message=str(e))
        
        finally:
            cursor.close()  # Cerrar el cursor
    else:
        return jsonify(status='error', message='Por favor, inicia sesión para exportar las transferencias')
    

   

if __name__ == "__main__":
    app.run(debug=True)

