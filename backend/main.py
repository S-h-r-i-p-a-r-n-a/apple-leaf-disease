from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os, shutil, uuid, logging

# Import once and load model on startup
from app.model.detect import Predictor

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve downloads
if not os.path.exists("downloads"):
    os.makedirs("downloads")
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")

# Load model only once
predictor = Predictor()

@app.get("/")
def root():
    return {"message": "🍏 Apple Leaf Disease Detection API is running!"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        raise HTTPException(status_code=400, detail="Only .jpg/.jpeg/.png files are allowed")

    os.makedirs("temp", exist_ok=True)
    temp_path = f"temp/{uuid.uuid4()}_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        image_path, report_json, _, _, disease_confidence_list = predictor.annotate(temp_path)

        return {
            "detected_diseases": disease_confidence_list,
            "treatment_report": report_json,
            "annotated_image": f"/downloads/{os.path.basename(image_path)}"
        }

    except Exception as e:
        logging.exception("Prediction failed")
        raise HTTPException(status_code=500, detail="Prediction failed")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/report")
async def generate_full_report(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        raise HTTPException(status_code=400, detail="Only .jpg/.jpeg/.png files are allowed")

    os.makedirs("temp", exist_ok=True)
    temp_path = f"temp/{uuid.uuid4()}_{file.filename}"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        image_path, report_json, pdf_path, audio_path, disease_confidence_list = predictor.annotate(temp_path)

        return {
            "detected_diseases": disease_confidence_list,
            "treatment_report": report_json,
            "annotated_image": f"/downloads/{os.path.basename(image_path)}",
            "pdf_report": f"/downloads/{os.path.basename(pdf_path)}",
            "voice_report": f"/downloads/{os.path.basename(audio_path)}"
        }

    except Exception as e:
        logging.exception("Report generation failed")
        raise HTTPException(status_code=500, detail="Report generation failed")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join("downloads", filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
