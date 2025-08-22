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

## Acknowledgments
- Ultralytics YOLOv8
- OpenCV
