from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os, shutil, uuid, logging

from app.model.detect import Predictor

app = FastAPI()
logging.basicConfig(level=logging.INFO)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.path.exists("downloads"):
    os.makedirs("downloads")
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")

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

        image_path, disease_confidence_list = predictor.annotate(temp_path)

        return {
            "detected_diseases": disease_confidence_list,
            "annotated_image": f"/downloads/{os.path.basename(image_path)}"
        }

    except Exception as e:
        logging.exception("Prediction failed")
        raise HTTPException(status_code=500, detail="Prediction failed")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
