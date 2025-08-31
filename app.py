import os
import uuid
import json
import threading
import time
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, Response, flash, session, jsonify
from ultralytics import YOLO
import cv2
import math
from datetime import datetime

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(APP_ROOT, 'uploads')
OUTPUT_DIR = os.path.join(APP_ROOT, 'static', 'outputs')
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET_KEY", "fire-detection-app-secret-key")  # allow override

# Environment-configurable thresholds
def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default

CONF_THRESHOLD = _env_float('CONF_THRESHOLD', 0.50)      # draw boxes above this
ALERT_THRESHOLD = _env_float('ALERT_THRESHOLD', 0.70)    # trigger high confidence alert above this

# Model (loaded once) — allow overriding weight path via env
MODEL_PATH = os.environ.get('MODEL_PATH', './model/fire.pt')
try:
    MODEL = YOLO(MODEL_PATH)
except Exception as e:
    # Defer hard failure to first request; useful for building image w/o weights (optional)
    MODEL = None
    app.logger.error(f"Failed to load model at {MODEL_PATH}: {e}")
CLASSNAMES = ['fire']

# Shared detection state
LAST_HIGH_CONF_TIME = 0.0
LAST_HIGH_CONF_SCORE = 0.0
STATE_LOCK = threading.Lock()

def annotate_frame(frame):
    """Run detection on a single frame and draw bounding boxes. Returns (frame, high_conf_bool)."""
    global LAST_HIGH_CONF_TIME, LAST_HIGH_CONF_SCORE
    if MODEL is None:
        return frame, False
    results = MODEL(frame, stream=True)
    high_confidence_detection = False

    for r in results:
        for box in r.boxes:
            conf = float(box.conf[0])
            if conf >= CONF_THRESHOLD:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                # Color depends on alert threshold
                if conf >= ALERT_THRESHOLD:
                    color = (0, 0, 255)  # red
                    high_confidence_detection = True
                else:
                    color = (0, 255, 0)  # green

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)

                confidence_pct = math.ceil(conf * 100)
                label = f"{CLASSNAMES[int(box.cls[0])]} {confidence_pct}%"
                cv2.putText(frame, label, (x1 + 5, y1 + 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                if conf >= ALERT_THRESHOLD:
                    cv2.putText(frame, "ALERT!", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 3)
                    # Update shared state
                    with STATE_LOCK:
                        LAST_HIGH_CONF_TIME = time.time()
                        LAST_HIGH_CONF_SCORE = conf

    cv2.putText(frame, f"Alert Threshold: {int(ALERT_THRESHOLD * 100)}%",
                (10, frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    return frame, high_confidence_detection

def gen_live_stream():
    """Generate frames from a live source (webcam / RTSP). In containerized environments, a webcam may not exist."""
    source = os.environ.get('LIVE_SOURCE', '0')  # '0' for default webcam, or RTSP/file path
    try:
        source_int = int(source)
    except ValueError:
        source_int = source  # keep as string (e.g., RTSP)
    cap = cv2.VideoCapture(source_int)
    if not cap.isOpened():
        # Return a single empty stream so client can display a message
        app.logger.warning("Live source not available: %s", source)
        yield b''
        return
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame, high_confidence = annotate_frame(frame)

        if high_confidence:
            cv2.putText(frame, "HIGH CONFIDENCE FIRE DETECTED!", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.rectangle(frame, (5, 5), (frame.shape[1]-5, frame.shape[0]-5), (0, 0, 255), 5)

        ok, buffer = cv2.imencode('.jpg', frame)
        if not ok:
            continue
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    cap.release()

def process_video_stream(video_path):
    """Yield processed frames for streaming the uploaded video."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        yield b''
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame, high_confidence = annotate_frame(frame)

        if high_confidence:
            cv2.putText(frame, "HIGH CONFIDENCE FIRE DETECTED!", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.rectangle(frame, (5, 5), (frame.shape[1]-5, frame.shape[0]-5), (0, 0, 255), 5)

        ok, buffer = cv2.imencode('.jpg', frame)
        if not ok:
            continue
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    cap.release()

def process_video(input_path, output_path):
    """Background full processing to save annotated video to disk."""
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        return
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        annotated, _ = annotate_frame(frame)
        out.write(annotated)

    cap.release()
    out.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/healthz')
def health():
    """Basic health check for container orchestrators."""
    status = {
        "status": "ok",
        "model_loaded": MODEL is not None,
        "conf_threshold": CONF_THRESHOLD,
        "alert_threshold": ALERT_THRESHOLD
    }
    code = 200 if MODEL is not None else 503
    return jsonify(status), code

@app.route('/demo')
def demo():
    return render_template('demo.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'video' not in request.files:
        flash("No file part.")
        return redirect(url_for('demo'))
    file = request.files['video']
    if file.filename == '':
        flash("No selected file.")
        return redirect(url_for('demo'))
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ('.mp4', '.mov', '.avi', '.mkv'):
        flash("Unsupported format.")
        return redirect(url_for('demo'))

    uid = uuid.uuid4().hex
    input_path = os.path.join(UPLOAD_DIR, f"{uid}{ext}")
    output_filename = f"processed_{uid}.mp4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    file.save(input_path)

    session['input_path'] = input_path
    session['output_path'] = output_path
    session['output_filename'] = output_filename
    session['original_filename'] = file.filename
    return redirect(url_for('process_video_page'))

@app.route('/process')
def process_video_page():
    if 'input_path' not in session:
        flash("No video to process.")
        return redirect(url_for('demo'))
    return render_template('processing.html',
                           original_filename=session.get('original_filename'),
                           output_filename=session.get('output_filename'))

@app.route('/process_stream')
def process_stream():
    if 'input_path' not in session:
        return Response(b'', mimetype='multipart/x-mixed-replace; boundary=frame')
    input_path = session.get('input_path')
    output_path = session.get('output_path')

    threading.Thread(target=process_video, args=(input_path, output_path), daemon=True).start()

    return Response(process_video_stream(input_path),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/finish_processing')
def finish_processing():
    if 'output_filename' not in session:
        flash("Processing error.")
        return redirect(url_for('demo'))

    input_path = session.get('input_path')
    output_filename = session.get('output_filename')

    cap = cv2.VideoCapture(input_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    duration = frame_count / fps if fps > 0 else 0
    cap.release()

    msg = f"Processed {frame_count} frames ({duration:.1f} seconds)"

    for k in ['input_path', 'output_path', 'output_filename', 'original_filename']:
        session.pop(k, None)

    return render_template('result.html',
                           video_file=output_filename,
                           message=msg,
                           timestamp=datetime.utcnow())

@app.route('/outputs/<path:filename>')
def outputs(filename):
    return send_from_directory(OUTPUT_DIR, filename)

@app.route('/live')
def live():
    return render_template('live.html')

@app.route('/live_feed')
def live_feed():
    return Response(gen_live_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/check_high_confidence')
def check_high_confidence():
    """Return true only if a high-confidence detection occurred recently."""
    with STATE_LOCK:
        recent = (time.time() - LAST_HIGH_CONF_TIME) < 2.0  # 2-second window
        score = LAST_HIGH_CONF_SCORE
    return jsonify({
        "high_confidence": recent,
        "score": round(score, 4) if recent else None,
        "threshold": ALERT_THRESHOLD
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)