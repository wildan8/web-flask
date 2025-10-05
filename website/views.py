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
from .models import DetectionResult
from .import db
views = Blueprint('views', __name__)

# Load model
model = load_model('model_moler_old.h5')
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
@login_required
def riwayat():
    """Halaman riwayat deteksi dengan paginasi"""
    user_id = session['_user_id']
    
    # Ambil parameter halaman dari URL (default: 1)
    page = request.args.get('page', 1, type=int)
    
    # Jumlah data per halaman
    per_page = 10  # Bisa diubah: 5, 10, 20, dll
    
    # Query dengan paginasi
    results = DetectionResult.query.filter_by(user_id=user_id, aktif=True) \
        .order_by(DetectionResult.timestamp.desc()) \
        .paginate(
            page=page,
            per_page=per_page,
            error_out=False  # Jangan error jika halaman di luar jangkauan
        )
    
    return render_template('riwayat.html', results=results)

# views.py
@views.route('/riwayat/nonaktifkan/<int:result_id>', methods=['POST'])
@login_required
def nonaktifkan_riwayat(result_id):
    user_id = session['_user_id']

    result = DetectionResult.query.filter_by(id=result_id, user_id=user_id).first()
    if not result:
        flash("Data tidak ditemukan.", "error")
    elif not result.aktif:
        flash("Data sudah tidak aktif.", "info")
    else:
        result.aktif = False
        db.session.commit()
        flash("Entri berhasil dinonaktifkan dari riwayat.", "success")

    return redirect(request.referrer or url_for('views.riwayat'))
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
    """Proses deteksi dari gambar"""
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
    # print("timestamp",timestamp)
    # print("datenow",datetime.now())
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
    print("prediction",predictions)

    confidence = float(predictions[0])  # unpack
    # confidence = float(prediction_res)
    print("prob Result:", confidence)
    # prob_moler = float(prob_moler)

    # confidence = max(prob_sehat, prob_moler)
    predicted_class = "sehat" if confidence > 0.5 else "moler"
    # print("prob",prob_sehat > prob_moler)
    # Interpretasi hasil

    result = predicted_class
     # 🔽 SIMPAN KE DATABASE
    new_result = DetectionResult(
        user_id=int(session['_user_id']),
        image_path=f'/static/uploads/{filename}',
        result=predicted_class,
        confidence=confidence,
        # timestamp = timestamp,
        # prob_sehat=prob_sehat,
        # prob_moler=prob_moler,
        aktif = True
    )
    db.session.add(new_result)
    db.session.commit()

    # print(f"✅ Deteksi selesai untuk user {user_id}: {result}")

    # Return JSON (tanpa variabel yang tidak ada)
    return jsonify({
        'result': result,
        'confidence': confidence,
        # 'prob_sehat': prob_sehat,
        # 'prob_moler': prob_moler,
        'saved_path': f'/static/uploads/{filename}',
        'original_path': f'/static/uploads/{filename}',
        'detection_id': new_result.id  # opsional
    })