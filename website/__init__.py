from flask import Flask
from flask_socketio import SocketIO

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret' # Pastikan ini adalah kunci rahasia yang kuat untuk produksi!

    # Inisialisasi SocketIO di sini, sebelum mengimpor views
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

    # --- PERUBAHAN DI SINI ---
    # Import fungsi blueprint dari views.py
    # Asumsi Anda telah mengubah views.py menjadi fungsi seperti yang saya contohkan
    from .views import init_views_blueprint # IMPORT FUNGSI views_blueprint

    from .auth import auth

    # Daftarkan blueprint views dengan memanggil fungsinya dan meneruskan socketio
    app.register_blueprint(init_views_blueprint(socketio), url_prefix='/') # Panggil fungsi views_blueprint dengan socketio
    # --- AKHIR PERUBAHAN ---

    app.register_blueprint(auth, url_prefix='/auth/')

    return app, socketio
