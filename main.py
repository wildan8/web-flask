# main.py
from website import create_app

# create_app sekarang mengembalikan tuple (app, socketio)
app, socketio = create_app() # Tangkap kedua nilai yang dikembalikan

if __name__ == '__main__':
    # Anda harus menggunakan socketio.run() untuk menjalankan aplikasi Flask-SocketIO
    # Jangan menggunakan app.run() lagi
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    # debug=True: Untuk mode pengembangan, otomatis reload saat ada perubahan kode
    # host='0.0.0.0': Agar bisa diakses dari jaringan lokal (bukan hanya localhost)
    # port=5000: Port default Flask