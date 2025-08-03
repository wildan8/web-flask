from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
import base64
import cv2
import numpy as np
import os
from datetime import datetime
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from flask_login import login_required, current_user  # Import decorator dari auth.py

views = Blueprint('views', __name__)

# Load model
model = load_model('model_daunbawang.h5')
print("✅ Model .h5 berhasil dimuat!")

# Cek input shape model
print("📌 Input shape model:", model.input_shape)

# Ambil ukuran dari model (lebih aman)
IMG_HEIGHT = model.input_shape[1]
IMG_WIDTH = model.input_shape[2]

if IMG_HEIGHT is None or IMG_WIDTH is None:
    IMG_HEIGHT, IMG_WIDTH = 128, 128  # fallback

CLASS_NAMES = ['sehat', 'moler']

@views.route('/')
def home():
    """Halaman utama"""
    return render_template("home.html")

@views.route('/camera')
@login_required  # Proteksi: hanya user yang login bisa akses
def camera():
    """Halaman kamera untuk deteksi smile"""
    return render_template("camera.html")

@views.route('/riwayat')
@login_required  # Proteksi: hanya user yang login bisa akses
def riwayat():
    """Halaman riwayat deteksi"""
    return render_template("riwayat.html")
    
@views.route('/tentang')
def tentang():
    """Halaman tentang aplikasi"""
    return render_template("tentang.html")

@views.route('/check_login')
@login_required
def check_login():
    if current_user.is_authenticated:
        return jsonify({
            'logged_in': True,
            'username': current_user.username,
            'email': current_user.email
        })
    else:
        return jsonify({
            'logged_in': False
        }), 401

@views.route('/process_image', methods=['POST'])
@login_required  # Proteksi: hanya user yang login bisa akses
def process_image():
    """Proses deteksi smile dari gambar"""
    data = request.get_json()
    image_data = data['image']
    # print(image_data)
    
    # Pisahkan header dan data base64
    header, encoded = image_data.split(',', 1)
    img_bytes = base64.b64decode(encoded)

    # Siapkan folder untuk menyimpan gambar
    file_ext = header.split('/')[1].split(';')[0]  # e.g. 'png' or 'jpeg'
    save_folder = os.path.join('website', 'static', 'uploads')
    os.makedirs(save_folder, exist_ok=True)
    
    # Buat nama file unik dengan user_id
    print(session)
    user_id = session['_user_id']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    filename = f"user_{user_id}_img_{timestamp}.{file_ext}"
    file_path = os.path.join(save_folder, filename)
    
    # Simpan gambar asli
    with open(file_path, 'wb') as f:
        f.write(img_bytes)

    # Load gambar
    img = load_img(file_path, target_size=(IMG_HEIGHT, IMG_WIDTH))
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0 

    # Prediksi
    predictions = model.predict(img_array)
    print(predictions)

    prob_sehat, prob_moler = predictions[0]  # unpack
    prob_sehat = float(prob_sehat)
    prob_moler = float(prob_moler)

    print(prob_sehat, prob_moler)
    predicted_class = "sehat" if prob_sehat > prob_moler else "moler"
    print("prob",prob_sehat > prob_moler)
    # Interpretasi hasil
    # if predictions.shape[1] == 1:
    #     prob = predictions[0][0]
    #     predicted_class = 'sehat' if prob_sehat > prob_moler else 'moler'
    #     confidence = max(prob, 1 - prob)
    # else:
    #     confidence = np.max(predictions)
    #     predicted_class = CLASS_NAMES[np.argmax(predictions)]

    result = predicted_class

    # print(f"✅ Deteksi selesai untuk user {user_id}: {result}")

    # Return JSON (tanpa variabel yang tidak ada)
    return jsonify({
        'result': result,
        'saved_path': f'/static/uploads/{filename}',
        'original_path': f'/static/uploads/{filename}'
        # Tambahkan field lain jika perlu
    })