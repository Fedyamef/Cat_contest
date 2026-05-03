import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from PIL import Image
from models import db, CatPhoto, Vote, Comment, Notification
from forms import CatPhotoForm

cats_bp = Blueprint('cats', __name__)


def save_photo(file, cat_name):
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        with Image.open(filepath) as img:
            img.thumbnail((800, 800))
            img.save(filepath, optimize=True, quality=85)
    except Exception as e:
        print(f"Ошибка обработки изображения: {e}")

    return filename


@cats_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    photos = CatPhoto.query.order_by(CatPhoto.upload_date.desc()).paginate(page=page, per_page=12)
    return render_template('index.html', photos=photos)


@cats_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = CatPhotoForm()
    if form.validate_on_submit():
        filename = save_photo(form.photo.data, form.cat_name.data)

        photo = CatPhoto(
            filename=filename,
            original_filename=form.photo.data.filename,
            cat_name=form.cat_name.data,
            description=form.description.data,
            user_id=current_user.id
        )
        db.session.add(photo)
        db.session.commit()

        flash(f'Фото кота {form.cat_name.data} успешно загружено!', 'success')
        return redirect(url_for('cats.index'))

    return render_template('upload.html', form=form)


@cats_bp.route('/vote/<int:photo_id>', methods=['POST'])
@login_required
def vote(photo_id):
    photo = CatPhoto.query.get_or_404(photo_id)

    if photo.user_id == current_user.id:
        flash('Нельзя голосовать за своего кота!', 'warning')
        return redirect(url_for('cats.index'))

    existing_vote = Vote.query.filter_by(user_id=current_user.id, photo_id=photo_id).first()
    if existing_vote:
        flash('Вы уже голосовали за это фото!', 'warning')
        return redirect(url_for('cats.index'))

    vote = Vote(user_id=current_user.id, photo_id=photo_id)
    db.session.add(vote)
    photo.votes_count += 1

    notification = Notification(
        user_id=photo.user_id,
        message=f'{current_user.username} проголосовал за вашего кота "{photo.cat_name}"!',
        type='vote',
        link='/'
    )
    db.session.add(notification)

    db.session.commit()

    flash('Голос учтён! Спасибо за поддержку котика', 'success')
    return redirect(url_for('cats.index'))


@cats_bp.route('/leaderboard')
def leaderboard():
    top_photos = CatPhoto.query.order_by(CatPhoto.votes_count.desc()).limit(10).all()
    return render_template('leaderboard.html', top_photos=top_photos)


@cats_bp.route('/my_uploads')
@login_required
def my_uploads():
    photos = CatPhoto.query.filter_by(user_id=current_user.id).order_by(CatPhoto.upload_date.desc()).all()
    return render_template('my_uploads.html', photos=photos)


@cats_bp.route('/delete_photo/<int:photo_id>', methods=['POST'])
@login_required
def delete_photo(photo_id):
    photo = CatPhoto.query.get_or_404(photo_id)

    if photo.user_id != current_user.id:
        flash('Нельзя удалить чужое фото', 'danger')
        return redirect(url_for('cats.index'))

    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], photo.filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(photo)
    db.session.commit()

    flash('Фото удалено', 'success')
    return redirect(url_for('cats.my_uploads'))


@cats_bp.route('/add_comment/<int:photo_id>', methods=['POST'])
@login_required
def add_comment(photo_id):
    photo = CatPhoto.query.get_or_404(photo_id)
    text = request.form.get('comment_text', '').strip()

    if not text:
        flash('Комментарий не может быть пустым', 'warning')
        return redirect(url_for('cats.index'))

    comment = Comment(
        text=text,
        user_id=current_user.id,
        photo_id=photo_id
    )
    db.session.add(comment)

    if photo.user_id != current_user.id:
        notification = Notification(
            user_id=photo.user_id,
            message=f'{current_user.username} оставил комментарий под фото "{photo.cat_name}": "{text[:50]}..."',
            type='comment',
            link='/'
        )
        db.session.add(notification)

    db.session.commit()
    flash('Комментарий добавлен!', 'success')
    return redirect(url_for('cats.index'))