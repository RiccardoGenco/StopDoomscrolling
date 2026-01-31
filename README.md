# Focus Guardian Pro 🛡️

**Focus Guardian Pro** è un sistema di monitoraggio intelligente progettato per combattere la distrazione digitale. Utilizzando la potenza della computer vision (YOLOv8), il sistema rileva in tempo reale quando l'utente utilizza il proprio smartphone durante una sessione di lavoro o studio e interviene con una notifica visiva a schermo intero.

##  Funzionalità
- **Monitoraggio in tempo reale**: Utilizza la webcam per analizzare l'ambiente di lavoro.
- **Rilevamento IA**: Sfrutta YOLOv8 per identificare specificamente l'uso dello smartphone (Classe COCO 67).
- **Interfaccia Web Automatica**: Apre automaticamente una finestra browser in modalità "App" (senza bordi) che funge da pannello di allerta.
- **Feedback Immediato**: Quando viene rilevata una distrazione, viene riprodotto un video di avviso a tutto schermo per riportare il focus.
- **Debug View**: Finestra OpenCV integrata per vedere cosa vede l'IA in tempo reale.

##  Requisiti Tecnologici
Il progetto è basato su:
- **Python 3.x**
- **Ultralytics YOLOv8**: Per il rilevamento degli oggetti.
- **Flask & Flask-SocketIO**: Per il server web e la comunicazione bidirezionale in tempo reale.
- **OpenCV**: Per la gestione del flusso video della webcam.
- **HTML/CSS/JS**: Per l'interfaccia utente front-end.

##  Installazione

1. **Clona la repository**:
   ```bash
   git clone <url-progetto>
   cd yolo2
   ```

2. **Crea un ambiente virtuale (consigliato)**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Su Windows: venv\Scripts\activate
   ```

3. **Installa le dipendenze**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Modelli YOLO**:
   Assicurati che i file `yolov8n.pt` siano presenti nella cartella principale. Se non presenti, verranno scaricati automaticamente al primo avvio.

## 🚦 Utilizzo

1. **Configurazione Percorsi**:
   Apri `SmartObserver_Web.py` e configura i percorsi necessari:
   - `VIDEO_FOLDER`: La cartella contenente il video di allerta.
   - `VIDEO_FILENAME`: Il nome del file video.
   - `CHROME_PATH`: Il percorso dell'eseguibile di Google Chrome.

2. **Avvio**:
   ```bash
   python SmartObserver_Web.py
   ```

3. **Inizializzazione**:
   Una volta aperta la finestra di Chrome, **clicca in un punto qualsiasi** della pagina per abilitare il fullscreen e la riproduzione automatica dei contenuti audio/video (necessario per le politiche di sicurezza dei browser).

---

