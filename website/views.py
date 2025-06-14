from flask import Blueprint, render_template, request, jsonify
import base64
import cv2
import numpy as np
import os

views = Blueprint('views', __name__)

smile_cascade = cv2.CascadeClassifier(os.path.join('website', 'smile_ref.xml'))

@views.route('/')
def home():
    return render_template("home.html")

@views.route('/camera')
def camera():
    return render_template("camera.html")

@views.route('/riwayat')
def riwayat():
    return render_template("riwayat.html")
    
@views.route('/tentang')
def tentang():
    return render_template("tentang.html")

@views.route('/process_image', methods=['POST'])
def process_image():
    data = request.get_json()
    image_data = data['image']
    # Remove the header of the base64 string
    header, encoded = image_data.split(',', 1)
    img_bytes = base64.b64decode(encoded)
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Here you would run your CNN model on 'img'
    # For now, just return a dummy result
    # result = 'dummy_cnn_result'  # Replace with your CNN logic

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    smile_cascade = cv2.CascadeClassifier(os.path.join('website', 'smile_ref.xml'))  # Make sure the path and name are correct!
    smiles = smile_cascade.detectMultiScale(gray, scaleFactor=1.8, minNeighbors=30, minSize=(10, 20))

    # Draw rectangles
    for (x, y, w, h) in smiles:
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Encode the image back to base64
    _, buffer = cv2.imencode('.png', img)
    processed_image = base64.b64encode(buffer).decode('utf-8')
    processed_image_data = f"data:image/png;base64,{processed_image}"

    result = 'smile' if len(smiles) > 0 else 'no smile'
    return jsonify({'result': result, 'image': processed_image_data})
