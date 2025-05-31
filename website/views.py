from flask import Blueprint, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import base64
import cv2
import numpy as np
import os

views = Blueprint('views', __name__)
socketio = SocketIO()  # Akan diinisialisasi di __init__.py

# Muat cascade classifiers di luar fungsi untuk efisiensi
# Pastikan path ke file XML sudah benar
smile_cascade = cv2.CascadeClassifier(os.path.join('website', 'smile_ref.xml'))
eye_cascade = cv2.CascadeClassifier(os.path.join('website', 'eye_ref.xml'))
# Asumsikan Anda juga punya file haarcascade_frontalface_default.xml di folder website
# Jika tidak ada, Anda perlu mendapatkannya atau mengubah logika deteksi
face_cascade = cv2.CascadeClassifier(os.path.join('website', 'frontalface_ref.xml'))

@views.route('/')
def home():
    return render_template("home.html")

@views.route('/camera')
def camera():
    return render_template("camera.html")

@views.route('/process_image', methods=['POST'])
def process_image():
    # Kode ini untuk post-processing, mungkin tidak relevan lagi untuk real-time
    # Tapi biarkan saja dulu jika masih digunakan di tempat lain
    data = request.get_json()
    image_data = data['image']
    # Remove the header of the base64 string
    header, encoded = image_data.split(',', 1)
    img_bytes = base64.b64decode(encoded)
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Gunakan cascade smile_cascade yang sudah dimuat
    smiles = smile_cascade.detectMultiScale(gray, scaleFactor=1.8, minNeighbors=30) # Gunakan parameter yang sudah Anda sesuaikan

    # Draw rectangles
    for (x, y, w, h) in smiles:
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Encode the image back to base64
    _, buffer = cv2.imencode('.png', img)
    processed_image = base64.b64encode(buffer).decode('utf-8')
    processed_image_data = f"data:image/png;base64,{processed_image}"

    result = 'smile' if len(smiles) > 0 else 'no smile'
    return jsonify({'result': result, 'image': processed_image_data})

@socketio.on('frame')
def handle_frame(data):
    # Decode base64 image from client
    img_data = data['image'].split(',')[1]
    nparr = np.frombuffer(base64.b64decode(img_data), np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Convert to grayscale for detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Gunakan cascade global
    global smile_cascade, eye_cascade, face_cascade

    # 1. Deteksi Wajah
    # Parameter ini mungkin perlu disesuaikan
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    # Define text parameters for labels
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    font_thickness = 1
    text_color = (255, 255, 255) # White color for text

    # 2. Deteksi Mata dan Senyum di dalam setiap Wajah
    for (x_w, y_w, w_w, h_w) in faces:
        # Gambar kotak wajah
        cv2.rectangle(frame, (x_w, y_w), (x_w + w_w, y_w + h_w), (255, 0, 0), 2) # Kotak biru untuk wajah
        
        # Tambahkan label "face" di bawah kotak wajah
        label_face = "face"
        (text_width_f, text_height_f), baseline_f = cv2.getTextSize(label_face, font, font_scale, font_thickness)
        text_origin_x_f = x_w
        text_origin_y_f = y_w + h_w + text_height_f + 5 # 5 pixels below face rectangle
        # Gambar background dan teks untuk wajah
        cv2.rectangle(frame, (text_origin_x_f, text_origin_y_f - text_height_f - baseline_f), (text_origin_x_f + text_width_f, text_origin_y_f + baseline_f), (0, 0, 0), cv2.FILLED)
        cv2.putText(frame, label_face, (text_origin_x_f, text_origin_y_f), font, font_scale, text_color, font_thickness, cv2.LINE_AA)


        # Tentukan area of interest (ROI) untuk wajah
        roi_gray = gray[y_w:y_w + h_w, x_w:x_w + w_w]
        roi_color = frame[y_w:y_w + h_w, x_w:x_w + w_w]

        # Deteksi Mata di dalam ROI wajah
        # Parameter ini mungkin perlu disesuaikan untuk eye_ref.xml
        eyes = eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.4, minNeighbors=15) # Parameter mata umum: scaleFactor=1.1, minNeighbors=5

        # Gambar kotak mata dan label
        for (x_e, y_e, w_e, h_e) in eyes:
            cv2.rectangle(roi_color, (x_e, y_e), (x_e + w_e, y_e + h_e), (0, 255, 255), 2) # Kotak kuning untuk mata
            
            # Tambahkan label "eye"
            label_eye = "eye"
            (text_width_e, text_height_e), baseline_e = cv2.getTextSize(label_eye, font, font_scale, font_thickness)
            text_origin_x_e = x_e
            text_origin_y_e = y_e + h_e + text_height_e + 5 # Relative to ROI
            # Gambar background dan teks untuk mata
            cv2.rectangle(roi_color, (text_origin_x_e, text_origin_y_e - text_height_e - baseline_e), (text_origin_x_e + text_width_e, text_origin_y_e + baseline_e), (0, 0, 0), cv2.FILLED)
            cv2.putText(roi_color, label_eye, (text_origin_x_e, text_origin_y_e), font, font_scale, text_color, font_thickness, cv2.LINE_AA)


        # Deteksi Senyum di dalam ROI wajah (biasanya di bagian bawah wajah)
        # Parameter ini mungkin perlu disesuaikan untuk smile_ref.xml
        smiles = smile_cascade.detectMultiScale(roi_gray, scaleFactor=1.8, minNeighbors=30)

        # Gambar kotak senyum dan label
        for (x_s, y_s, w_s, h_s) in smiles:
            cv2.rectangle(roi_color, (x_s, y_s), (x_s + w_s, y_s + h_s), (0, 255, 0), 2) # Kotak hijau untuk senyum

            # Tambahkan label "smile"
            label_smile = "smile"
            (text_width_s, text_height_s), baseline_s = cv2.getTextSize(label_smile, font, font_scale, font_thickness)
            text_origin_x_s = x_s
            text_origin_y_s = y_s + h_s + text_height_s + 5 # Relative to ROI

            cv2.rectangle(roi_color, (text_origin_x_s, text_origin_y_s - text_height_s - baseline_s), (text_origin_x_s + text_width_s, text_origin_y_s + baseline_s), (0, 0, 0), cv2.FILLED)
            cv2.putText(roi_color, label_smile, (text_origin_x_s, text_origin_y_s), font, font_scale, text_color, font_thickness, cv2.LINE_AA)


    # Encode the processed frame back to base64
    _, buffer = cv2.imencode('.jpg', frame)
    result_b64 = base64.b64encode(buffer).decode('utf-8')
    emit('result', {'image': 'data:image/jpeg;base64,' + result_b64})
