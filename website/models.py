# website/models.py
from . import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from flask import current_app  # ✅ Import di sini
from itsdangerous import URLSafeTimedSerializer  # ✅ Import di sini

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    business_name = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        """Helper untuk mengatur password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=3600):
        """
        Buat token reset password (berlaku 1 jam)
        """
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_password_token(token):
        """
        Verifikasi token dan kembalikan user
        """
        try:
            s = URLSafeTimedSerializer(current_app._get_current_object().config['SECRET_KEY'])
            data = s.loads(token, max_age=3600)
            return User.query.get(data['user_id'])
        except:
            return None

class DetectionResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    result = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    # prob_sehat = db.Column(db.Float)  # tambahan
    # prob_moler = db.Column(db.Float)  # tambahan
    aktif = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Deteksi {self.result} oleh user {self.user_id}>"

