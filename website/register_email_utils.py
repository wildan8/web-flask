# website/utils.py
from flask_mail import Message
from . import mail

def send_registration_email(email, full_name):
    msg = Message(
        subject="Selamat Datang! Akun Anda Berhasil Dibuat",
        recipients=[email]
    )
    msg.body = f"""
Halo {full_name},

Terima kasih telah mendaftar di aplikasi kami. Akun Anda telah berhasil dibuat.

Sekarang Anda bisa login dan mulai menggunakan layanan kami.

Salam,
Tim Aplikasi
"""
    msg.html = f"""
<h3>Halo {full_name},</h3>
<p>Terima kasih telah mendaftar di aplikasi kami. Akun Anda telah berhasil dibuat.</p>
<p>Sekarang Anda bisa <a href="http://127.0.0.1:5000/auth/login">login</a> dan mulai menggunakan layanan kami.</p>
<p>Salam,<br><strong>Tim Aplikasi</strong></p>
"""
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error mengirim email: {str(e)}")