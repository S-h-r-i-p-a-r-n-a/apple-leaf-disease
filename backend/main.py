from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os, shutil, uuid, logging

from app.model.detect import Predictor

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# ✅ Enable CORS (Allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific origin(s) in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Optional: Limit upload file size to 5MB
@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    if request.headers.get("content-length"):
        size = int(request.headers["content-length"])
        if size > 5 * 1024 * 1024:  # 5MB
            return JSONResponse(status_code=413, content={"detail": "File too large"})
    return await call_next(request)

# ✅ Create downloads directory and mount as static
DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
app.mount("/downloads", StaticFiles(directory=DOWNLOADS_DIR), name="downloads")

# ✅ Predictor instance
predictor = Predictor()

@app.get("/")
def root():
    return {"message": "🍏 Apple Leaf Disease Detection API is running!"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    # ✅ Validate file type
    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        raise HTTPException(status_code=400, detail="Only .jpg/.jpeg/.png files are allowed")
    
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid image content-type")

    # ✅ Save uploaded image to temp directory
    temp_dir = os.path.join(os.path.dirname(__file__), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # ✅ Run prediction
        image_path, disease_confidence_list = predictor.annotate(temp_path)
        logging.info(f"Prediction done: {disease_confidence_list}")

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
