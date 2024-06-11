from flask import Flask, jsonify, request, session, redirect, url_for, render_template, flash
import psycopg2
import psycopg2.extras
import re
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'EYg3OS1Q1LDAljkxr8ARdvYZUhdF_kYC')

# Configuración de la base de datos
DB_HOST = os.getenv('DB_HOST', 'dpg-cpkb0knsc6pc73eq9930-a')
DB_NAME = os.getenv('DB_NAME', 'proyecto_db_3fqv')
DB_USER = os.getenv('DB_USER', 'proyecto_user')
DB_PASS = os.getenv('DB_PASS', '5XcWSgOeGs9bDJk2pEtPOnUwomId0OmR')

# Conexión a la base de datos
conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)

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
                flash('Incorrect username/password')
        else:
            flash('Incorrect username/password')
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

