import pathlib
import platform



# Ensure compatibility with Windows paths
if platform.system() == "Windows":
    pathlib.PosixPath = pathlib.WindowsPath

import sys, os, uuid, json, torch, cv2
from pathlib import Path
import numpy as np
from gtts import gTTS
from fpdf import FPDF

# Add YOLOv5 path
yolov5_path = Path(__file__).resolve().parents[2] / "yolov5"
sys.path.append(str(yolov5_path))

from models.common import DetectMultiBackend
from utils.general import non_max_suppression, scale_boxes
from utils.torch_utils import select_device

# Load model
model_path = Path(__file__).parent / "apple_leaf_yolov5.pt"
device = select_device('cpu')
model = DetectMultiBackend(str(model_path), device=device)
model.model.eval()

# Load treatment info
with open(Path(__file__).parent / "treatments.json", "r", encoding="utf-8") as f:
    TREATMENTS = json.load(f)

def sanitize(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def generate_pdf(filename_no_ext, detected, image_path):
    pdf_path = os.path.join("downloads", f"{filename_no_ext}.pdf")
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, sanitize("Apple Leaf Disease Diagnosis Report"), ln=True, align="C")
    pdf.line(10, 25, 200, 25)
    pdf.ln(10)

    for disease in detected:
        details = TREATMENTS.get(disease, {})

        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, sanitize(f"Disease Detected: {details.get('title', disease.title())}"), ln=True)

        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 8, sanitize(details.get('summary', 'No summary available.')))
        pdf.ln(2)

        if "fungicides" in details and details["fungicides"]:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, "Recommended Fungicides:", ln=True)
            pdf.set_font("Arial", "", 12)
            for item in details["fungicides"]:
                pdf.cell(0, 8, f"- {sanitize(item)}", ln=True)
            pdf.ln(2)

        if "steps" in details and details["steps"]:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, "Treatment Steps:", ln=True)
            pdf.set_font("Arial", "", 12)
            for step in details["steps"]:
                pdf.multi_cell(0, 8, f"-> {sanitize(step)}")
            pdf.ln(2)

        if "prevention" in details:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, "Prevention Tips:", ln=True)
            pdf.set_font("Arial", "", 12)
            pdf.multi_cell(0, 8, sanitize(details["prevention"]))
            pdf.ln(4)

    # Annotated Image
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Annotated Image:", ln=True)
    try:
        pdf.image(image_path, x=30, w=140)
    except:
        pdf.cell(0, 10, "Image could not be added.", ln=True)

    pdf.output(pdf_path)
    return pdf_path

import gc  # Garbage collector

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
                (text_w, text_h), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                label_y = max(y1 - text_h - 12, 0)
                label_x = max(x1, 0)

                cv2.rectangle(original, (label_x, label_y), (label_x + text_w + 8, label_y + text_h + 8), (0, 255, 100), -1)
                cv2.putText(original, label_text, (label_x + 4, label_y + text_h),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 3)
                cv2.putText(original, label_text, (label_x + 4, label_y + text_h),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
        else:
            disease_names.add("healthy")
            disease_conf_list.append({"name": "healthy", "confidence": 1.0})

        os.makedirs("downloads", exist_ok=True)
        main_disease = next(iter(disease_names)).replace(" ", "_").lower()
        uid = str(uuid.uuid4())[:8]
        filename_no_ext = f"appleleaf_{main_disease}_{uid}"

        image_out_path = os.path.join("downloads", f"{filename_no_ext}.jpg")
        pdf_path = os.path.join("downloads", f"{filename_no_ext}.pdf")
        audio_path = os.path.join("downloads", f"{filename_no_ext}.mp3")

        # Save annotated image
        cv2.imwrite(image_out_path, original)

        # Treatment report (brief)
        brief_report = {d: TREATMENTS.get(d, {}).get("brief", "No treatment available.") for d in disease_names}

        # Hindi Voice
        if "healthy" in disease_names:
            speech = "Patta swasth hai. Koi upchaar ki zarurat nahi hai."
        else:
            speech = "\n".join([f"{d} ke liye upaay hai: {TREATMENTS[d]['brief']}" for d in disease_names])
        gTTS(speech, lang="hi").save(audio_path)

        # PDF generation
        full_pdf_path = generate_pdf(filename_no_ext, disease_names, image_out_path)

        # Memory cleanup
        del img_tensor, img_resized, original, pred
        gc.collect()

        return image_out_path, brief_report, full_pdf_path, audio_path, disease_conf_list

    except Exception as e:
        print(f"Error during prediction: {e}")
        raise

class Predictor:
    def __init__(self):
        self.annotate = predict_and_annotate
