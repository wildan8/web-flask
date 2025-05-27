from flask import Blueprint, render_template, request, jsonify
from flask_socketio import emit
import base64
import cv2
import numpy as np
import os
import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack, RTCIceCandidate
from aiortc.contrib.media import MediaRelay, MediaStreamTrack
import logging

pcs = set()
relay = None

# PASTIKAN PATH INI BENAR!
# Karena views.py dan smile_ref.xml berada di direktori yang sama (website/),
# kita hanya perlu os.path.dirname(os.path.abspath(__file__))
SMILE_CASCADE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'smile_ref.xml')

# Tambahkan ini untuk debugging lokasi file (sangat direkomendasikan):
print(f"DEBUG: Cascade Path: {SMILE_CASCADE_PATH}, Exists: {os.path.exists(SMILE_CASCADE_PATH)}")

# Tambahkan ini untuk debugging lokasi file:
# print(f"DEBUG: Cascade Path: {SMILE_CASCADE_PATH}, Exists: {os.path.exists(SMILE_CASCADE_PATH)}")


def init_views_blueprint(socketio_instance):
    views = Blueprint('views', __name__)

    smile_cascade_instance = cv2.CascadeClassifier(SMILE_CASCADE_PATH)
    if smile_cascade_instance.empty():
        print(f"ERROR: smile_ref.xml not found or loaded for main classifier at {SMILE_CASCADE_PATH}")

    # --- ROUTE LAMA (Upload Foto) ---
    @views.route('/')
    def home():
        return render_template("home.html")

    @views.route('/camera')
    def camera():
        return render_template("camera.html")

    @views.route('/process_image', methods=['POST'])
    def process_image():
        data = request.get_json()
        image_data = data['image']
        header, encoded = image_data.split(',', 1)
        img_bytes = base64.b64decode(encoded)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if not smile_cascade_instance.empty():
            gray = cv2.cvtColor(img, cv2.BGR2GRAY)
            smiles = smile_cascade_instance.detectMultiScale(gray, scaleFactor=1.8, minNeighbors=30, minSize=(10, 20))
            for (x, y, w, h) in smiles:
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            result = 'smile' if len(smiles) > 0 else 'no smile'
        else:
            print(f"WARNING: Classifier not loaded for process_image. Path: {SMILE_CASCADE_PATH}")
            result = 'Error: Classifier not available.'
            
        _, buffer = cv2.imencode('.png', img)
        processed_image = base64.b64encode(buffer).decode('utf-8')
        processed_image_data = f"data:image/png;base64,{processed_image}"

        return jsonify({'result': result, 'image': processed_image_data})

    # --- ROUTE BARU (WebRTC Live Stream dengan aiortc) ---
    @views.route('/webrtc_stream')
    def webrtc_stream():
        return render_template("webrtc_stream.html")

    # --- EVENT SOCKET.IO UNTUK WEBRTC ---
    @socketio_instance.on('connect', namespace='/webrtc')
    def handle_connect():
        print(f"Client connected to WebRTC namespace: {request.sid}")

    @socketio_instance.on('offer', namespace='/webrtc')
    async def handle_offer(sid, message): # sid ditambahkan
        global relay

        offer = RTCSessionDescription(sdp=message['sdp'], type=message['type'])
        pc = RTCPeerConnection()
        pcs.add(pc)

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print(f"Connection state for {sid} is {pc.connectionState}")
            if pc.connectionState == "closed":
                pcs.discard(pc)

        @pc.on("icecandidate")
        async def on_icecandidate(candidate):
            if candidate:
                print(f"Sending ICE candidate for {sid}: {candidate.sdp}")
                socketio_instance.emit('ice_candidate', {'sdpMLineIndex': candidate.sdpMLineIndex, 'candidate': candidate.candidate}, room=sid, namespace='/webrtc')

        @pc.on("track")
        async def on_track(track):
            print(f"Track {track.kind} received from client {sid}")
            if track.kind == "video":
                if not smile_cascade_instance.empty():
                    # Pastikan VideoTransformTrack sudah didefinisikan di dalam init_views_blueprint
                    local_video = VideoTransformTrack(track, smile_cascade_instance)
                    pc.addTrack(local_video)
                else:
                    print(f"WARNING: smile_cascade not loaded for WebRTC stream. Path: {SMILE_CASCADE_PATH}. Sending original track.")
                    pc.addTrack(track)
                
        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        print(f"Sending Answer SDP for {sid}: {answer.sdp}")
        socketio_instance.emit('answer', {'sdp': answer.sdp, 'type': answer.type}, room=sid, namespace='/webrtc')

    @socketio_instance.on('ice_candidate', namespace='/webrtc')
    async def handle_ice_candidate(sid, message): # sid ditambahkan
        # Untuk aplikasi multi-user, Anda perlu mekanisme identifikasi PC yang lebih baik
        # Misalnya, menyimpan pc dalam dictionary dengan sid sebagai key
        # Untuk contoh sederhana ini, kita masih mengasumsikan satu pc per sid (tidak robust)
        if pcs:
            pc_found = None
            for existing_pc in pcs:
                # Ini adalah pendekatan yang sangat dasar.
                # Dalam aplikasi multi-klien yang sebenarnya, Anda perlu mengelola RTCPeerConnection berdasarkan SID atau ID unik lainnya.
                # Misalnya, menyimpan mapping {sid: RTCPeerConnection}
                # Untuk saat ini, kita ambil saja yang pertama (akan bermasalah jika ada 2+ klien)
                pc_found = existing_pc
                break
            
            if pc_found:
                candidate = RTCIceCandidate(
                    sdpMLineIndex=message['sdpMLineIndex'],
                    candidate=message['candidate']
                )
                try:
                    await pc_found.addIceCandidate(candidate)
                    print(f"Received ICE candidate for {sid}: {candidate.candidate}")
                except Exception as e:
                    print(f"Error adding ICE candidate for {sid}: {e}")
            else:
                print(f"WARNING: No active PeerConnection found for sid: {sid} to add ICE candidate.")


    # --- KELAS UNTUK MEMPROSES FRAME VIDEO DENGAN OPENCV (AIORTC) ---
    # KELAS INI HARUS BERADA DI DALAM FUNGSI init_views_blueprint
    # SEBELUM 'return views' TERAKHIR!
    class VideoTransformTrack(MediaStreamTrack):
        kind = "video"

        def __init__(self, track, smile_cascade_classifier):
            super().__init__()
            self.track = track
            self.smile_cascade = smile_cascade_classifier

        async def recv(self):
            frame = await self.track.recv()
            img = frame.to_ndarray(format="bgr24")

            if not self.smile_cascade.empty():
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                smiles = self.smile_cascade.detectMultiScale(gray, scaleFactor=1.8, minNeighbors=30, minSize=(10, 20))
                for (x, y, w, h) in smiles:
                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            else:
                pass # Jika classifier tidak dimuat, kembalikan frame asli tanpa modifikasi

            new_frame = frame.from_ndarray(img, format="bgr24")
            return new_frame

    return views # Mengembalikan instance Blueprint dari fungsi