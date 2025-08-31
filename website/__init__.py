# website/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail, Message

db = SQLAlchemy()
csrf = CSRFProtect()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'flask-bm.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Konfigurasi Email
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'wildanjerry65@gmail.com'      # Ganti dengan email
    app.config['MAIL_PASSWORD'] = 'jweb rlyr vtly ebbw'       # Gunakan App Password, bukan password login!
    app.config['MAIL_DEFAULT_SENDER'] = ('Admin', 'wildanjerry65@gmail.com')

    db.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    print("Database URI:", app.config['SQLALCHEMY_DATABASE_URI'])
    db_path = os.path.join(os.getcwd(), 'flask-bm.db')
    print("Full path to database:", db_path)

    # Import model di sini setelah db.init_app(app)
    from .models import User, DetectionResult

    # Setup login manager setelah app
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .views import views
    from .auth import auth
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/auth')

    with app.app_context():
        db.create_all()

    return app
