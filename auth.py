from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['email'] = user['email']
            return redirect(url_for('main.dashboard'))
        
        return render_template('login.html', error='Email veya şifre hatalı')
    
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (email, password) VALUES (%s, %s)",
                (email, generate_password_hash(password))
            )
            db.commit()
            cursor.close()
            db.close()
            return redirect(url_for('auth.login'))
        except:
            cursor.close()
            db.close()
            return render_template('register.html', error='Bu email zaten kayıtlı')
    
    return render_template('register.html')

@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))