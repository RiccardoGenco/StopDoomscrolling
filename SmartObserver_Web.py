import cv2
import threading
import time
import subprocess
import os
from flask import Flask, render_template_string, send_from_directory
from flask_socketio import SocketIO
from ultralytics import YOLO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# --- CONFIGURAZIONE ---
VIDEO_FOLDER = r"C:\Users\genco\Pictures"
VIDEO_FILENAME = "skeleton_banging_on_shield_480P.mp4"
CONFIDENCE_THRESHOLD = 0.35 # Alzata leggermente per ridurre falsi positivi
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# ID COCO delle distrazioni (67 = cell phone, 73 = book, 65 = remote, 77 = cigarette, 34 )
DISTRACTION_CLASSES = [67] 

# Caricamento Modello
try:
    model = YOLO('yolov8n.pt')
    names = model.names # Mappa ID -> Nome (es. 67 -> 'cell phone')
except Exception as e:
    print(f"❌ Errore caricamento modello: {e}")
    names = {}

@app.route('/')
def index():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return render_template_string(f.read())
    except FileNotFoundError:
        return "Errore: index.html non trovato!"

@app.route('/video')
def serve_video():
    return send_from_directory(VIDEO_FOLDER, VIDEO_FILENAME)

def detection_loop():
    cap = cv2.VideoCapture(0)
    active = False
    off_counter = 0

    print("\n🧐 Monitoraggio avviato. Cosa sto cercando?")
    for cls_id in DISTRACTION_CLASSES:
        print(f" - {names.get(cls_id, cls_id)}")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        results = model(frame, verbose=False, conf=CONFIDENCE_THRESHOLD)
        annotated_frame = results[0].plot() 
        
        # Estrazione oggetti rilevati per log e logica
        detected_objects = []
        distraction_found = False

        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            name = names.get(cls_id, f"ID {cls_id}")
            detected_objects.append(f"{name} ({conf:.2f})")
            
            if cls_id in DISTRACTION_CLASSES:
                distraction_found = True

        # Log nel terminale (solo se cambia qualcosa o ogni 30 frame per non intasare)
        if detected_objects:
             print(f"🔎 Visto: {', '.join(detected_objects)}", end="\r")

        if distraction_found:
            off_counter = 0
            if not active:
                active = True
                socketio.emit('status', {'active': True})
                print("\n🚨 DISTRAZIONE RILEVATA!")
        else:
            off_counter += 1
            if off_counter > 20 and active:
                active = False
                socketio.emit('status', {'active': False})
                print("\n✅ FOCUS RIPRISTINATO")

        cv2.imshow("DEBUG IA - Premi Q per uscire", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

def open_browser():
    """Lancia Chrome in modalità App Desktop (Borderless)"""
    time.sleep(2)
    url = "http://127.0.0.1:5000"
    try:
        subprocess.Popen([CHROME_PATH, f"--app={url}"])
        print("🚀 Finestra Borderless avviata.")
    except Exception as e:
        print(f"⚠️ Impossibile aprire Chrome in modalità App: {e}")

if __name__ == '__main__':
    # Thread IA
    threading.Thread(target=detection_loop, daemon=True).start()
    # Thread Browser
    threading.Thread(target=open_browser, daemon=True).start()
    
    socketio.run(app, port=5000, debug=False, use_reloader=False)