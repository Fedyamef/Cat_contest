from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Notification
from forms import LoginForm, RegistrationForm
import os

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('cats.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Добро пожаловать, {user.username}!', 'success')
            return redirect(next_page or url_for('cats.index'))
        flash('Неверное имя пользователя или пароль', 'danger')

    return render_template('login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('cats.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Имя пользователя уже занято', 'danger')
            return render_template('register.html', form=form)

        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('Email уже зарегистрирован', 'danger')
            return render_template('register.html', form=form)

        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()

        flash('Регистрация успешна! Теперь вы можете войти', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('cats.index'))


@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@auth_bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user = current_user

    for photo in user.photos:
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], photo.filename)
        if os.path.exists(filepath):
            os.remove(filepath)

    db.session.delete(user)
    db.session.commit()

    logout_user()
    flash('Ваша учётная запись успешно удалена', 'info')
    return redirect(url_for('cats.index'))


@auth_bp.route('/mark_notifications_read', methods=['POST'])
@login_required
def mark_notifications_read():
    for notif in current_user.notifications:
        if not notif.is_read:
            notif.is_read = True
    db.session.commit()
    flash('Все уведомления отмечены как прочитанные', 'info')
    return redirect(request.referrer or url_for('cats.index'))