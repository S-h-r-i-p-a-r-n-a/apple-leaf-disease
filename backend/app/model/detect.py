import sys
import os
import uuid
import torch
import cv2
import platform
import pathlib
from pathlib import Path

# ✅ Fix for Windows path compatibility
if platform.system() == "Windows":
    pathlib.PosixPath = pathlib.WindowsPath

# ✅ Add YOLOv5 path to Python import path
yolov5_path = Path(__file__).resolve().parents[2] / "yolov5"
if yolov5_path.exists():
    sys.path.append(str(yolov5_path))
else:
    raise RuntimeError(f"YOLOv5 path not found at: {yolov5_path}")

# ✅ Import from YOLOv5 modules
from utils.general import non_max_suppression, scale_boxes
from utils.torch_utils import select_device
from models.common import DetectMultiBackend

# ✅ Load model
model_path = Path(__file__).parent / "apple_leaf_yolov5.pt"
device = select_device("cpu")
model = DetectMultiBackend(str(model_path), device=device)
model.model.eval()

def predict_and_annotate(image_path):
    try:
        original = cv2.imread(image_path)
        img = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img, (640, 640))
        img_tensor = torch.from_numpy(img_resized).permute(2, 0, 1).float().unsqueeze(0) / 255.0
        img_tensor = img_tensor.to(device)

        with torch.no_grad():
            pred = model(img_tensor)
        pred = non_max_suppression(pred, conf_thres=0.25)[0]

        disease_names = set()
        disease_conf_list = []

        if pred is not None and len(pred):
            pred = pred[torch.argmax(pred[:, 4])]
            pred = pred.unsqueeze(0)
            pred[:, :4] = scale_boxes((640, 640), pred[:, :4], original.shape[:2]).round()

            for *xyxy, conf, cls in pred:
                label = model.names[int(cls)]
                confidence = float(conf)
                disease_names.add(label)
                disease_conf_list.append({"name": label, "confidence": round(confidence, 2)})

                x1, y1, x2, y2 = map(int, xyxy)
                cv2.rectangle(original, (x1, y1), (x2, y2), (0, 255, 100), 3)
                label_text = f"{label} {confidence:.2f}"
                (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                cv2.rectangle(original, (x1, y1 - th - 10), (x1 + tw + 6, y1), (0, 255, 100), -1)
                cv2.putText(original, label_text, (x1 + 3, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        else:
            disease_names.add("healthy")
            disease_conf_list.append({"name": "healthy", "confidence": 1.0})

        os.makedirs("downloads", exist_ok=True)
        filename = f"result_{uuid.uuid4().hex[:8]}.jpg"
        image_out_path = os.path.join("downloads", filename)
        cv2.imwrite(image_out_path, original)

        return image_out_path, disease_conf_list

    except Exception as e:
        print(f"Error during prediction: {e}")
        raise

class Predictor:
    def __init__(self):
        self.annotate = predict_and_annotate
