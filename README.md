# Fire Detection Model

Real-time fire detection using a custom-trained YOLOv8 model.

## Features
- YOLOv8-based object detection (class: fire)
- Real-time video / file inference
- Simple training pipeline via notebook

## Project Structure
```
fire.py                      # Inference script
Fire_Detection_Model.ipynb   # Training (YOLOv8) notebook
model/fire.pt                # Trained weights (expected path)
video/fire2.mp4              # Sample input video (expected path)
```

## Requirements
- Python 3.9+
- GPU optional (CUDA recommended)
- Packages:
  ```
  pip install ultralytics opencv-python cvzone
  ```
(Recommended quick setup)
```
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
```
If you prefer manual install:
```
pip install ultralytics opencv-python cvzone flask
```
(Optional GPU CUDA support comes from your PyTorch inside ultralytics; it auto-installs a CPU build. For CUDA, separately install a matching torch/torchvision build before ultralytics.)

## Running (Summary)
CLI detection (sample video or webcam):
```
python fire.py
```

Start web landing page + demo:
```
python app.py
```
Open http://127.0.0.1:5000/

## Container / Defang Deployment

This project includes a `Dockerfile` for deployment on platforms like Defang.

Build & run locally:
```
docker build -t fire-detection .
docker run -p 5000:5000 -e CONF_THRESHOLD=0.5 -e ALERT_THRESHOLD=0.7 fire-detection
```
Then open: http://localhost:5000/

Health check endpoint (used by orchestrators):
```
/healthz
```

Adjustable environment variables:
| Variable | Description | Default |
|----------|-------------|---------|
| PORT | Container port (Gunicorn bind) | 5000 |
| CONF_THRESHOLD | Draw boxes above this confidence | 0.5 |
| ALERT_THRESHOLD | Trigger high confidence alert | 0.7 |
| MODEL_PATH | Path to model weights | ./model/fire.pt |
| LIVE_SOURCE | Webcam index or RTSP/file path for /live | 0 |
| APP_SECRET_KEY | Flask session secret | fire-detection-app-secret-key |

Defang quick steps:
1. Add repository in Defang and enable build using the provided `Dockerfile`.
2. Set runtime env vars as needed (see table above).
3. Expose port `5000` (Defang may auto-detect via `EXPOSE`).
4. (Optional) Mount persistent storage if you want to retain processed videos beyond pod life.
5. Deploy and visit the generated URL. Use `/healthz` for liveness checks.

Production notes:
- Gunicorn used with 1 worker / 4 threads (CPU-bound with some I/O). Increase workers if CPU capacity allows.
- Model loads at startup; if load fails container returns 503 on `/healthz`.
- Webcam access inside containers typically unavailable; supply an RTSP stream via `LIVE_SOURCE`.

## Training (Notebook)
1. Mount / make dataset; ensure data.yaml is correct.
2. In notebook:
   - Cell 1 installs ultralytics.
   - Cell 2 trains:
     ```
     !yolo task=detect mode=train model=yolov8n.pt data=/path/to/data.yaml epochs=15 imgsz=640
     ```
3. Best weights saved under `runs/detect/train*/weights/best.pt` — copy to `model/fire.pt`.

## Inference (fire.py)
```
python fire.py
```
Adjust video source:
```python
cap = cv2.VideoCapture(0)              # webcam
cap = cv2.VideoCapture('./video/fire2.mp4')
```
Adjust confidence threshold (default 50):
```python
if confidence > 50:
    ...
```

## Web Demo (Landing Page + Try Free Demo)
A simple Flask app provides:
- Landing page with Try Free Demo
- Upload a video for fire detection (processed server-side)
- Live webcam fire detection (streamed)
- Contact section

### Install extra dependency
```
pip install flask
```

### Run web app
```
python app.py
```
Then open: http://127.0.0.1:5000/

### Structure Added
```
app.py
templates/
  index.html
  result.html
  live.html
static/
  style.css
  outputs/        # processed videos
uploads/          # temporary uploaded files
```

### Notes
- Processing large videos may take time; progress is not streamed (simple implementation).
- Live demo uses first webcam (index 0).
- Adjust confidence threshold inside app.py (CONF_THRESHOLD).

## Notes
- Ensure `model/fire.pt` exists.
- Resize logic fixed at (640,480); match training size if needed.
- To save output, add:
  ```python
  writer = cv2.VideoWriter('out.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 30, (640,480))
  writer.write(frame)
  ```

## Troubleshooting
- Black window: check codec / video path.
- Slow FPS: use smaller model (yolov8n) or enable GPU.
- No detections: verify dataset quality and class name alignment.

## Future Improvements
- Add alerting (sound / email)
- Multi-class (smoke, flame)
- FPS overlay & logging
- Progress bar for video processing
- User auth / rate limiting for SaaS

## Acknowledgments
- Ultralytics YOLOv8
- OpenCV
