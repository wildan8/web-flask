from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import re
from flask_mail import Message
from . import db, mail
from .models import User
from .forms import LoginForm, RegisterForm, ResetPasswordRequestForm, ResetPasswordForm
from .register_email_utils import send_registration_email

auth = Blueprint('auth', __name__)

def is_valid_password(password):
    return (
        len(password) >= 8 and
        re.search(r'[A-Z]', password) and
        re.search(r'[a-z]', password)
    )
@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        full_name = form.full_name.data
        business_name = form.business_name.data
        username = form.username.data
        email = form.email.data
        password = form.password.data

        # Cek duplikasi username atau email
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username atau email sudah digunakan.', 'warning')
            return redirect(url_for('auth.register'))

        # Buat user baru
        new_user = User(
            full_name=full_name,
            business_name=business_name,
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )

        db.session.add(new_user)
        db.session.commit()

        send_registration_email(email, full_name)

        flash('Akun berhasil dibuat. Silakan login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            # flash(f'Selamat datang, {user.full_name}!', 'success')
            return redirect(url_for('views.home'))
        else:
            flash('Username atau password salah.', 'danger')
    return render_template('login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Berhasil logout.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/reset_pass_request', methods=['GET', 'POST'])
def reset_pass_request():
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        username_or_email = form.username_or_email.data
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if user:
            # Kirim email hanya jika user ditemukan
            send_password_reset_email(user)
            flash('Cek email Anda untuk instruksi reset password.', 'info')
        else:
            flash('Username atau email tidak ditemukan.', 'warning')

        return redirect(url_for('auth.login'))

    return render_template('reset_pass_request.html', form=form)


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    msg = Message(
        subject="Permintaan Reset Password",
        recipients=[user.email]
    )
    msg.html = render_template('reset_pass_email.html', user=user, token=token)
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Gagal kirim email: {e}")


@auth.route('/reset_pass/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Token tidak valid atau telah kedaluwarsa.', 'danger')
        return redirect(url_for('auth.login'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password_hash = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Password Anda berhasil direset. Silakan login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_pass.html', form=form)
    