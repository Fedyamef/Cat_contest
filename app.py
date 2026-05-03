from flask import Flask
from flask_login import LoginManager
import os

from config import Config
from models import db, User
from auth import auth_bp
from cats import cats_bp
from api_client import api_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        os.makedirs('instance', exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('static/images', exist_ok=True)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите для голосования'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(cats_bp)
    app.register_blueprint(api_bp)

    return app


app = create_app()

with app.app_context():
    db.create_all()
    print("✅ База данных и таблицы созданы!")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
