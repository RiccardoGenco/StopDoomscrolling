import cv2
import threading
import time
import subprocess
import os
import sys
import logging
import ctypes
from flask import Flask, render_template_string, send_from_directory
from flask_socketio import SocketIO
from ultralytics import YOLO
from dotenv import load_dotenv

# --- WINDOWS API CONSTANTS ---
SW_HIDE = 0
SW_SHOW = 5
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOSIZE = 1
SWP_NOMOVE = 2
WINDOW_TITLE = "Focus Guardian Pro | Dashboard"

# --- INITIALIZATION ---
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- WINDOW MANAGEMENT HELPERS ---
def get_window_handle():
    """Find the window handle (HWND) for the Chrome app by title."""
    return ctypes.windll.user32.FindWindowW(None, WINDOW_TITLE)

def toggle_window(visible: bool):
    """Hide or show the window and set TopMost status."""
    hwnd = get_window_handle()
    if not hwnd:
        return False
    
    if visible:
        # Show and bring to front
        ctypes.windll.user32.ShowWindow(hwnd, SW_SHOW)
        ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
    else:
        # Hide
        ctypes.windll.user32.ShowWindow(hwnd, SW_HIDE)
    return True

# --- DYNAMIC PATHS ---
def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- CONFIGURATION ---
VIDEO_FOLDER = os.getenv("FG_VIDEO_VIDEO_FOLDER", get_resource_path("."))
VIDEO_FILENAME = os.getenv("FG_VIDEO_VIDEO_FILENAME", "sound.mp4")
CONFIDENCE_THRESHOLD = float(os.getenv("FG_DETECTION_CONFIDENCE_THRESHOLD", 0.35))
CHROME_PATH = os.getenv("FG_BROWSER_CHROME_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe")
PORT = int(os.getenv("FG_WEB_PORT", 5000))
DISTRACTION_CLASSES = [int(c) for c in os.getenv("FG_DETECTION_DISTRACTION_CLASSES", "67").split(",")]

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global state for stealth mode
stealth_active = False

# Caricamento Modello
try:
    model_path = get_resource_path(os.getenv("FG_DETECTION_MODEL_PATH", "yolov8n.pt"))
    model = YOLO(model_path)
    names = model.names
    logger.info(f"✅ Modello caricato: {model_path}")
except Exception as e:
    logger.error(f"❌ Errore caricamento modello: {e}")
    names = {}

@app.route('/')
def index():
    try:
        with open(get_resource_path("index.html"), "r", encoding="utf-8") as f:
            return render_template_string(f.read())
    except FileNotFoundError:
        return "Errore: index.html non trovato!"

@app.route('/video')
def serve_video():
    return send_from_directory(VIDEO_FOLDER, VIDEO_FILENAME)

@socketio.on('ready_to_hide')
def handle_stealth_request():
    global stealth_active
    stealth_active = True
    logger.info("👤 Stealth Mode attivata: la finestra si nasconderà durante il focus.")
    toggle_window(False)

def detection_loop():
    global stealth_active
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("❌ Impossibile accedere alla webcam.")
        return

    active = False
    off_counter = 0
    buffer_size = 5
    detection_history = []

    logger.info("🧐 Monitoraggio avviato.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        results = model(frame, verbose=False, conf=CONFIDENCE_THRESHOLD)
        distraction_found = False

        for box in results[0].boxes:
            if int(box.cls[0]) in DISTRACTION_CLASSES:
                distraction_found = True

        detection_history.append(distraction_found)
        if len(detection_history) > buffer_size:
            detection_history.pop(0)
        
        is_distracted = sum(detection_history) >= (buffer_size // 2 + 1)

        if is_distracted:
            off_counter = 0
            if not active:
                active = True
                socketio.emit('status', {'active': True})
                if stealth_active:
                    toggle_window(True) # Pop up!
                logger.warning("🚨 DISTRAZIONE RILEVATA!")
        else:
            off_counter += 1
            if off_counter > 15 and active:
                active = False
                socketio.emit('status', {'active': False})
                if stealth_active:
                    toggle_window(False) # Hide!
                logger.info("✅ FOCUS RIPRISTINATO")

        # Visualizzazione debug opzionale (puoi commentare per stealth totale)
        cv2.imshow("Focus Guardian Debug", results[0].plot())
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

def open_browser():
    time.sleep(int(os.getenv("FG_BROWSER_DELAY_SECONDS", 2)))
    url = f"http://127.0.0.1:{PORT}"
    try:
        if os.path.exists(CHROME_PATH):
            subprocess.Popen([CHROME_PATH, f"--app={url}"])
            logger.info("🚀 Finestra Browser avviata.")
        else:
            import webbrowser
            webbrowser.open(url)
    except Exception as e:
        logger.error(f"⚠️ Errore apertura browser: {e}")

if __name__ == '__main__':
    threading.Thread(target=detection_loop, daemon=True).start()
    if os.getenv("FG_BROWSER_AUTO_OPEN", "true").lower() == "true":
        threading.Thread(target=open_browser, daemon=True).start()
    
    socketio.run(app, port=PORT, debug=False, use_reloader=False)

